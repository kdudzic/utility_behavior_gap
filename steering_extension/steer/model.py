"""Load Qwen3.5 text models for hooked generation.

Thinking is disabled via the chat template flag so generation matches the paper's
`reasoning: none` setting. Works for Qwen/Qwen3.5-9B (32 layers, d=4096) and
Qwen/Qwen3.5-27B (64 layers, d=5120); the 27B needs two 40 GB GPUs (device_map=auto).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import torch
from torch import nn
from transformers import AutoModelForCausalLM, AutoTokenizer

DEFAULT_MODEL = os.environ.get("STEER_MODEL", "Qwen/Qwen3.5-9B")


@dataclass
class LoadedModel:
    name: str
    model: nn.Module
    tokenizer: object
    layers: nn.ModuleList
    hidden_size: int

    @property
    def num_layers(self) -> int:
        return len(self.layers)

    @property
    def device(self) -> torch.device:
        return next(self.model.parameters()).device


def find_decoder_layers(model: nn.Module) -> nn.ModuleList:
    """Return the longest ModuleList whose children look like decoder layers."""
    best: nn.ModuleList | None = None
    for name, module in model.named_modules():
        if isinstance(module, nn.ModuleList) and len(module) >= 8:
            if "vision" in name.lower() or "visual" in name.lower():
                continue
            if best is None or len(module) > len(best):
                best = module
    if best is None:
        raise RuntimeError("could not locate decoder layers")
    return best


def load_model(name: str = DEFAULT_MODEL, *, dtype: torch.dtype = torch.bfloat16, device_map: str = "auto") -> LoadedModel:
    tokenizer = AutoTokenizer.from_pretrained(name, padding_side="left")
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    kwargs = {}
    if os.environ.get("STEER_USE_KERNELS", "0") == "1":
        # Hub kernels (kernels-community/mamba-ssm) supply causal_conv1d; pre-cache them on a
        # networked node with `kernels.get_kernel("kernels-community/mamba-ssm", version=3)`.
        kwargs["use_kernels"] = True
    model = AutoModelForCausalLM.from_pretrained(name, dtype=dtype, device_map=device_map, **kwargs)
    model.eval()
    layers = find_decoder_layers(model)
    hidden = getattr(getattr(model.config, "text_config", model.config), "hidden_size")
    return LoadedModel(name=name, model=model, tokenizer=tokenizer, layers=layers, hidden_size=hidden)


def chat_input_ids(loaded: LoadedModel, system_prompt: str, user_prompt: str) -> list[int]:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    text = loaded.tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
    )
    return loaded.tokenizer(text, add_special_tokens=False)["input_ids"]


def strip_think(text: str) -> str:
    """Remove any residual empty think block the template may emit."""
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    return text.strip()
