"""Load Qwen3.5 text models for hooked generation.

Thinking is disabled via the chat template flag so generation matches the paper's
`reasoning: none` setting. Works for Qwen/Qwen3.5-9B (32 layers, d=4096) and
Qwen/Qwen3.5-27B (64 layers, d=5120); the 27B needs two 40 GB GPUs (device_map=auto).

Second model family (2026-11-17, see docs/deepseek_port_notes.md): deepseek-ai/DeepSeek-V3.2
(61 layers, d=7168, FP8 weights). It is detected from the model name (or STEER_MODEL_FAMILY) and
differs from the default path in three places only: FP8 loading (`FineGrainedFP8Config`), the decoder
layer path (`model.model.layers`), and the chat prompt (the checkpoint ships no Jinja template, so the
non-thinking prompt is built here from the checkpoint's `encoding/encoding_dsv32.py` rules). Every other
model takes the unchanged default path.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import torch
from torch import nn
from transformers import AutoModelForCausalLM, AutoTokenizer

DEFAULT_MODEL = os.environ.get("STEER_MODEL", "Qwen/Qwen3.5-9B")

FAMILY_DEFAULT = "default"
FAMILY_DEEPSEEK_V32 = "deepseek_v32"

# DeepSeek-V3.2 chat markup, copied from the checkpoint's encoding/encoding_dsv32.py (the vertical bars
# are U+FF5C and the word separators U+2581, not ASCII).
DSV32_BOS = "<\uff5cbegin\u2581of\u2581sentence\uff5c>"
DSV32_USER = "<\uff5cUser\uff5c>"
DSV32_ASSISTANT = "<\uff5cAssistant\uff5c>"
DSV32_THINK_END = "</think>"
# Modules the checkpoint stores in BF16 rather than FP8 (transformers docs, model_doc/deepseek_v32.md).
# transformers matches each entry with re.match (anchored at the start of the module name) or as a name suffix,
# so the entries must be valid regular expressions; the doc page's glob form "*.self_attn..." raises re.error
# (DS0 attempt 2, 2026-11-17).
DSV32_FP8_SKIP = [r"model\.layers\.\d+\.mlp\.gate", r".*\.self_attn\.indexer\.weights_proj"]


def model_family(name: str) -> str:
    """Model family from the model name; STEER_MODEL_FAMILY overrides (e.g. for a local path)."""
    forced = os.environ.get("STEER_MODEL_FAMILY")
    if forced:
        return forced
    low = name.lower().replace("_", ".").replace("-", ".")
    if "deepseek" in low and ("v3.2" in low or "v32" in low):
        return FAMILY_DEEPSEEK_V32
    return FAMILY_DEFAULT


def deepseek_v32_chat_prompt(system_prompt: str, user_prompt: str) -> str:
    """Single-turn prompt in non-thinking ("chat") mode: the assistant turn is opened with a closing
    think tag, which is how the checkpoint's own encoder turns reasoning off. A blank system prompt adds
    nothing (system text has no role token; it sits between BOS and the user token)."""
    return f"{DSV32_BOS}{system_prompt or ''}{DSV32_USER}{user_prompt}{DSV32_ASSISTANT}{DSV32_THINK_END}"


@dataclass
class LoadedModel:
    name: str
    model: nn.Module
    tokenizer: object
    layers: nn.ModuleList
    hidden_size: int
    family: str = FAMILY_DEFAULT

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
    family = model_family(name)
    kwargs = {}
    if family == FAMILY_DEEPSEEK_V32:
        # FP8 weights stay FP8 (about 630 GiB on the GPUs); activations are quantised per call by the
        # transformers FP8 kernels. STEER_MAX_MEMORY_GIB caps what device_map=auto puts on each GPU.
        from transformers import FineGrainedFP8Config

        kwargs["quantization_config"] = FineGrainedFP8Config(modules_to_not_convert=list(DSV32_FP8_SKIP), weight_block_size=(128, 128))
        cap = os.environ.get("STEER_MAX_MEMORY_GIB")
        if cap:
            kwargs["max_memory"] = {i: f"{cap}GiB" for i in range(torch.cuda.device_count())}
    if os.environ.get("STEER_USE_KERNELS", "0") == "1":
        # Hub kernels (kernels-community/mamba-ssm) supply causal_conv1d; pre-cache them on a
        # networked node with `kernels.get_kernel("kernels-community/mamba-ssm", version=3)`.
        kwargs["use_kernels"] = True
    model = AutoModelForCausalLM.from_pretrained(name, dtype=dtype, device_map=device_map, **kwargs)
    model.eval()
    if family == FAMILY_DEEPSEEK_V32:
        layers = model.model.layers
        if len(layers) != model.config.num_hidden_layers:
            raise RuntimeError(f"expected {model.config.num_hidden_layers} decoder layers, found {len(layers)}")
    else:
        layers = find_decoder_layers(model)
    hidden = getattr(getattr(model.config, "text_config", model.config), "hidden_size")
    return LoadedModel(name=name, model=model, tokenizer=tokenizer, layers=layers, hidden_size=hidden, family=family)


def chat_input_ids(loaded: LoadedModel, system_prompt: str, user_prompt: str) -> list[int]:
    if getattr(loaded, "family", FAMILY_DEFAULT) == FAMILY_DEEPSEEK_V32:
        text = deepseek_v32_chat_prompt(system_prompt, user_prompt)
        return loaded.tokenizer(text, add_special_tokens=False)["input_ids"]
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
