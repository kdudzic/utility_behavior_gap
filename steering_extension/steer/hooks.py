"""Forward hooks for additive steering and directional ablation on decoder-block outputs.

Additive steering: h <- h + c_i * v at one layer, where c_i is a per-sample coefficient
(so one batch can mix doses and signs). Position modes:
  * "response": applied only to generated tokens (decode steps, seq_len == 1), never to the
    prompt prefill; this is the proposal's default.
  * "all": applied to every position including the prompt.
  * "prompt": applied only during the prompt prefill (pre-generation); generated tokens are untouched
    except through the KV cache / recurrent state built from the steered prefill.
Multi-layer steering: `steering()` accepts {layer_idx: hook} so several layers get their own vector
and coefficients in one forward pass (Persona Vectors style; the dose is split across layers by the caller).
Directional ablation: h <- h - (h . r_hat) r_hat at block outputs, all positions (Arditi et al.); with
per-layer directions, each layer removes its own direction.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import torch
from torch import nn


def _split_output(output):
    if isinstance(output, tuple):
        return output[0], output[1:]
    return output, None


def _join_output(hidden, rest):
    if rest is None:
        return hidden
    return (hidden, *rest)


class AdditiveSteer:
    def __init__(self, vector: torch.Tensor, coefs: torch.Tensor, mode: str = "response") -> None:
        if mode not in {"response", "all", "prompt"}:
            raise ValueError(mode)
        self.vector = vector  # (d,)
        self.coefs = coefs  # (batch,)
        self.mode = mode
        self.prefill_seen = False

    def __call__(self, module: nn.Module, args, output):
        hidden, rest = _split_output(output)
        seq_len = hidden.shape[1]
        if self.mode == "response" and seq_len > 1:
            # prompt prefill: leave untouched
            return output
        if self.mode == "prompt" and seq_len == 1:
            # decode step: leave untouched
            return output
        delta = self.coefs.to(hidden.dtype)[:, None, None] * self.vector.to(hidden.dtype)[None, None, :]
        return _join_output(hidden + delta, rest)


class DirectionalAblation:
    def __init__(self, direction: torch.Tensor, mask: torch.Tensor | None = None) -> None:
        self.unit = direction / direction.norm()
        self.mask = mask  # (batch,) bool; None = all samples

    def __call__(self, module: nn.Module, args, output):
        hidden, rest = _split_output(output)
        unit = self.unit.to(hidden.dtype)
        proj = (hidden @ unit)[..., None] * unit
        if self.mask is not None:
            proj = proj * self.mask.to(hidden.dtype)[:, None, None]
        return _join_output(hidden - proj, rest)


@contextmanager
def steering(layers: nn.ModuleList, layer_idx: int | None, hook) -> Iterator[None]:
    """hook may be a single callable (applied at layer_idx, or at every layer when layer_idx is None)
    or a dict {layer_idx: callable} for per-layer hooks."""
    handles = []
    if isinstance(hook, dict):
        for idx, h in hook.items():
            handles.append(layers[idx].register_forward_hook(h))
    elif hook is not None:
        if layer_idx is None:
            for layer in layers:
                handles.append(layer.register_forward_hook(hook))
        else:
            handles.append(layers[layer_idx].register_forward_hook(hook))
    try:
        yield
    finally:
        for handle in handles:
            handle.remove()


class ResidualCapture:
    """Capture per-layer masked residual sums during a single forward pass.

    Set `mask` (batch, seq) for one readout (results in `sums[layer]`, `sq_norm_sums[layer]`), or
    `masks` {name: (batch, seq)} for several readouts in one pass (results in `multi[name][layer]`;
    `sq_norm_sums` then uses masks["rmean"] if present, else the first mask).
    """

    def __init__(self, layers: nn.ModuleList) -> None:
        self.layers = layers
        self.sums: dict[int, torch.Tensor] = {}
        self.sq_norm_sums: dict[int, torch.Tensor] = {}
        self.multi: dict[str, dict[int, torch.Tensor]] = {}
        self.mask: torch.Tensor | None = None  # (batch, seq) float
        self.masks: dict[str, torch.Tensor] | None = None
        self.handles = []

    def _make_hook(self, idx: int):
        def hook(module, args, output):
            hidden, _ = _split_output(output)
            if self.masks is not None:
                sq_mask = self.masks.get("rmean", next(iter(self.masks.values())))
                for name, mask in self.masks.items():
                    m = mask.to(hidden.dtype)[..., None]
                    self.multi.setdefault(name, {})[idx] = (hidden * m).sum(dim=1).float()
                self.sq_norm_sums[idx] = ((hidden.float().norm(dim=-1) ** 2) * sq_mask).sum(dim=1)
                return None
            mask = self.mask
            if mask is None:
                return None
            m = mask.to(hidden.dtype)[..., None]
            self.sums[idx] = (hidden * m).sum(dim=1).float()  # (batch, d)
            self.sq_norm_sums[idx] = ((hidden.float().norm(dim=-1) ** 2) * mask).sum(dim=1)  # (batch,)
            return None

        return hook

    def __enter__(self):
        for idx, layer in enumerate(self.layers):
            self.handles.append(layer.register_forward_hook(self._make_hook(idx)))
        return self

    def __exit__(self, *exc):
        for handle in self.handles:
            handle.remove()
        self.handles = []
