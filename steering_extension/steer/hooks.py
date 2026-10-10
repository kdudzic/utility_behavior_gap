"""Forward hooks for additive steering and directional ablation on decoder-block outputs.

Additive steering: h <- h + c_i * v at one layer, where c_i is a per-sample coefficient
(so one batch can mix doses and signs). Position modes:
  * "response": applied only to generated tokens (decode steps, seq_len == 1), never to the
    prompt prefill; this is the proposal's default.
  * "all": applied to every position including the prompt.
Directional ablation: h <- h - (h . r_hat) r_hat at every layer and all positions (Arditi et al.).
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
        if mode not in {"response", "all"}:
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
    handles = []
    if hook is not None:
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
    """Capture per-layer mean residual over a token mask during a single forward pass."""

    def __init__(self, layers: nn.ModuleList) -> None:
        self.layers = layers
        self.sums: dict[int, torch.Tensor] = {}
        self.sq_norm_sums: dict[int, torch.Tensor] = {}
        self.mask: torch.Tensor | None = None  # (batch, seq) float
        self.handles = []

    def _make_hook(self, idx: int):
        def hook(module, args, output):
            hidden, _ = _split_output(output)
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
