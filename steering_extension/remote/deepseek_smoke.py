"""DS0 smoke test for white-box work on deepseek-ai/DeepSeek-V3.2 (see docs/deepseek_port_notes.md).

Runs ON THE GPU INSTANCE. It answers, with numbers, the questions DS0 exists for:
  1. does the FP8 checkpoint load in transformers across the GPUs, and how long does that take;
  2. does generation work with thinking off (4 texts, paper essay prompts, temperature 1.0);
  3. can residuals be read at 3 layers (the project.py capture path);
  4. does adding a random vector at one layer change the output (the generate.py steering path),
     while a zero vector leaves it unchanged;
  5. tokens per second (batch 4 and a batch-16 probe) and peak GPU memory.
It uses the same functions the real pipeline uses (steer.model.load_model, steer.generate.generate_batch,
steer.project.encode_and_capture, steer.hooks.AdditiveSteer), so a pass here is a pass for those paths.

The report JSON is rewritten after every stage, so a crash still leaves the stages that finished.
Exit code 0 only if every required stage passed.

  --preflight-only   no weights needed: checks GPUs, library support, the FP8 kernel on this GPU type,
                     the tokenizer and the chat prompt. Run it BEFORE the 690 GB download.

No paid API calls. Doses here are smoke-test values, not scientific choices.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from steering_extension.steer import model as steer_model  # noqa: E402
from steering_extension.steer.hooks import AdditiveSteer, steering  # noqa: E402

DEFAULT_MODEL = "deepseek-ai/DeepSeek-V3.2"
FALLBACK_PROMPTS = [
    "Write a short essay on whether cities should ban private cars from their centres.",
    "Write a short essay on what makes a scientific explanation good.",
    "Write a short essay on the costs and benefits of remote work.",
    "Write a short essay on whether museums should return objects taken in colonial times.",
]


class Report:
    def __init__(self, path: Path, meta: dict) -> None:
        self.path = path
        self.data: dict = {"meta": meta, "stages": {}, "pass": False}
        self.private: dict = {}  # stage results whose key starts with "_" (live objects); never written
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.save()

    def save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=1, ensure_ascii=False, default=str))
        tmp.replace(self.path)

    def stage(self, name: str, fn, *, required: bool = True):
        """Run one stage, record its result and wall time, never raise."""
        t0 = time.time()
        entry: dict = {"required": required}
        result = None
        try:
            result = fn()
            result = result if isinstance(result, dict) else {"value": result}
            self.private[name] = {k: v for k, v in result.items() if k.startswith("_")}
            entry.update({k: v for k, v in result.items() if not k.startswith("_")})
            entry.setdefault("ok", True)
        except Exception as exc:  # noqa: BLE001 - the report must survive any failure
            entry.update({"ok": False, "error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()[-4000:]})
            if isinstance(exc, torch.cuda.OutOfMemoryError):
                torch.cuda.empty_cache()
        entry["seconds"] = round(time.time() - t0, 1)
        self.data["stages"][name] = entry
        self.save()
        print(f"[{name}] ok={entry['ok']} {entry['seconds']}s" + (f" error={entry.get('error') or entry.get('problems')}" if not entry["ok"] else ""), flush=True)
        return entry

    def finish(self) -> bool:
        ok = all(s["ok"] for s in self.data["stages"].values() if s["required"])
        self.data["pass"] = ok
        self.save()
        return ok


# --------------------------------------------------------------------------- environment

def gpu_memory() -> list[dict]:
    rows = []
    for i in range(torch.cuda.device_count()):
        free, total = torch.cuda.mem_get_info(i)
        rows.append({
            "index": i,
            "name": torch.cuda.get_device_name(i),
            "total_gib": round(total / 2**30, 1),
            "used_gib": round((total - free) / 2**30, 1),
            "peak_allocated_gib": round(torch.cuda.max_memory_allocated(i) / 2**30, 1),
        })
    return rows


def env_facts(min_total_vram_gib: float, min_gpus: int) -> dict:
    import transformers

    facts: dict = {
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "cuda_available": torch.cuda.is_available(),
        "has_float8_e4m3fn": hasattr(torch, "float8_e4m3fn"),
        # the checkpoint's quantization_config says scale_fmt=ue8m0; transformers then needs this dtype
        "has_float8_e8m0fnu": hasattr(torch, "float8_e8m0fnu"),
        "nvcc": shutil.which("nvcc"),
    }
    problems: list[str] = []
    try:
        import kernels

        facts["kernels"] = getattr(kernels, "__version__", "unknown")
    except ImportError:
        facts["kernels"] = None
        problems.append("the `kernels` package is missing (the FP8 Triton kernel is loaded through it)")
    try:
        from transformers import DeepseekV32ForCausalLM, FineGrainedFP8Config  # noqa: F401

        facts["transformers_has_deepseek_v32"] = True
    except ImportError:
        facts["transformers_has_deepseek_v32"] = False
        problems.append("this transformers build has no DeepseekV32ForCausalLM / FineGrainedFP8Config")
    if not facts["has_float8_e8m0fnu"]:
        problems.append("torch has no float8_e8m0fnu dtype (needed for scale_fmt=ue8m0); install a newer torch")
    if not facts["cuda_available"]:
        problems.append("CUDA is not available (driver/torch mismatch? see README, 'Driver check after bootstrap')")
        return {**facts, "problems": problems, "ok": False}
    facts["gpus"] = gpu_memory()
    facts["compute_capability"] = [list(torch.cuda.get_device_capability(i)) for i in range(torch.cuda.device_count())]
    facts["total_vram_gib"] = round(sum(g["total_gib"] for g in facts["gpus"]), 1)
    if len(facts["gpus"]) < min_gpus:
        problems.append(f"{len(facts['gpus'])} GPUs visible, expected at least {min_gpus}")
    if facts["total_vram_gib"] < min_total_vram_gib:
        problems.append(f"total VRAM {facts['total_vram_gib']} GiB is below the {min_total_vram_gib} GiB needed for the FP8 weights plus headroom")
    if any(tuple(cc) < (8, 9) for cc in facts["compute_capability"]):
        problems.append("a GPU has compute capability below 8.9; transformers would silently dequantize to BF16 (about 1.28 TiB)")
    hf_home = os.environ.get("HF_HOME")
    if hf_home and Path(hf_home).exists():
        facts["hf_home_free_gb"] = round(shutil.disk_usage(hf_home).free / 1e9, 1)
    return {**facts, "problems": problems, "ok": not problems}


def fp8_kernel_microtest() -> dict:
    """Run one small FP8 linear through the transformers kernel on the first and last GPU and compare it
    with the dequantized matmul. Catches a kernel that does not build or gives garbage on this GPU type
    before any weights are downloaded."""
    from torch.nn import functional as F
    from transformers.integrations.finegrained_fp8 import FP8Linear

    out: dict = {"devices": {}}
    n_out, n_in, blk = 384, 256, 128
    for dev in sorted({0, torch.cuda.device_count() - 1}):
        device = torch.device(f"cuda:{dev}")
        gen = torch.Generator().manual_seed(1234)
        w = (torch.randn(n_out, n_in, generator=gen) * 0.05).to(device)
        blocks = w.view(n_out // blk, blk, n_in // blk, blk)
        scale = blocks.abs().amax(dim=(1, 3)) / 448.0  # (n_out/blk, n_in/blk); dequant = fp8 * scale
        w_q = (blocks / scale[:, None, :, None]).reshape(n_out, n_in).to(torch.float8_e4m3fn)
        w_deq = (w_q.float().view(n_out // blk, blk, n_in // blk, blk) * scale[:, None, :, None]).reshape(n_out, n_in)
        lin = FP8Linear(n_in, n_out, block_size=(blk, blk))
        lin.weight = torch.nn.Parameter(w_q, requires_grad=False)
        lin.weight_scale_inv = torch.nn.Parameter(scale.float(), requires_grad=False)
        lin = lin.to(device)
        x = torch.randn(3, 5, n_in, generator=gen).to(device=device, dtype=torch.bfloat16)
        with torch.inference_mode():
            y = lin(x).float()
            ref = F.linear(x.float(), w_deq)
        rel = float((y - ref).norm() / ref.norm())
        out["devices"][str(dev)] = {"rel_error_vs_dequantized": round(rel, 5), "finite": bool(torch.isfinite(y).all())}
    worst = max(d["rel_error_vs_dequantized"] for d in out["devices"].values())
    # activations are quantised to FP8 too, so a few percent of error is expected; garbage is of order 1
    out["ok"] = worst < 0.1 and all(d["finite"] for d in out["devices"].values())
    return out


def template_check(tokenizer) -> dict:
    """The prompt must start with exactly one BOS, then the user token, and end with Assistant + </think>."""
    text = steer_model.deepseek_v32_chat_prompt("", "1+1=?")
    ids = tokenizer(text, add_special_tokens=False)["input_ids"]
    want_head = [tokenizer.bos_token_id, tokenizer.convert_tokens_to_ids(steer_model.DSV32_USER)]
    want_tail = [tokenizer.convert_tokens_to_ids(steer_model.DSV32_ASSISTANT), tokenizer.convert_tokens_to_ids(steer_model.DSV32_THINK_END)]
    # reference ids from the model card (README, "Chat Template"): BOS 0, User 128803, Assistant 128804, </think> 128799
    return {
        "prompt_text": text,
        "ids": ids,
        "head": ids[:2],
        "tail": ids[-2:],
        "has_jinja_template": bool(getattr(tokenizer, "chat_template", None)),
        "ok": ids[:2] == want_head and ids[-2:] == want_tail and None not in want_head + want_tail and ids.count(tokenizer.bos_token_id) == 1,
    }


# --------------------------------------------------------------------------- model stages

def paper_prompts(n: int) -> tuple[list[str], str]:
    """First n essay prompts in the paper's framed-neutral form (byte for byte, via local/common.py)."""
    try:
        from steering_extension.local.common import framed_neutral_prompt, task_items

        rows = task_items("essay")[:n]
        if len(rows) == n:
            return [framed_neutral_prompt(r) for r in rows], "paper framed-neutral essay prompts"
    except Exception as exc:  # noqa: BLE001
        print(f"paper prompts unavailable ({type(exc).__name__}: {exc}); using fallback prompts", flush=True)
    return FALLBACK_PROMPTS[:n], "fallback prompts (paper inputs not found)"


def requests(prompts: list[str]) -> list[dict]:
    return [{"system_prompt": "", "prompt": p} for p in prompts]


def stage_generate(loaded, prompts: list[str], max_new_tokens: int, temperature: float) -> dict:
    from steering_extension.steer.generate import generate_batch

    t0 = time.time()
    gens = generate_batch(loaded, requests(prompts), temperature=temperature, max_tokens=max_new_tokens, hook=None, layer_idx=None)
    dt = time.time() - t0
    toks = sum(g["completion_tokens"] for g in gens)
    texts = [g["text"] for g in gens]
    return {
        "batch": len(prompts),
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "completion_tokens": [g["completion_tokens"] for g in gens],
        "prompt_tokens": [g["prompt_tokens"] for g in gens],
        "finish_reasons": [g["finish_reason"] for g in gens],
        "tokens_per_s_total": round(toks / dt, 2),
        "tokens_per_s_per_sequence": round(toks / dt / len(prompts), 2),
        "texts": texts,
        "think_tag_in_output": any("<think>" in t or "</think>" in t for t in texts),
        # thinking off: answers must be non-empty and must not open a think block
        "ok": all(len(t.strip()) > 20 for t in texts) and not any("<think>" in t for t in texts),
    }


def stage_capture(loaded, prompts: list[str], responses: list[str], layers: list[int], batch_size: int) -> dict:
    from steering_extension.steer.project import encode_and_capture

    items = [{"system_prompt": "", "prompt": p, "response": r} for p, r in zip(prompts, responses)]
    per_layer: dict[int, dict[str, list[float]]] = {l: {"rmean_norm": [], "astart_norm": [], "rms": []} for l in layers}
    finite = True
    for i in range(0, len(items), batch_size):
        res = encode_and_capture(loaded, items[i : i + batch_size])
        for l in layers:
            r = res[l]
            if r["rmean"].shape[-1] != loaded.hidden_size:
                raise RuntimeError(f"layer {l}: residual width {r['rmean'].shape[-1]} != hidden size {loaded.hidden_size}")
            finite &= bool(torch.isfinite(r["rmean"]).all() and torch.isfinite(r["astart"]).all() and torch.isfinite(r["rms"]).all())
            per_layer[l]["rmean_norm"] += [round(float(x), 3) for x in r["rmean"].norm(dim=-1)]
            per_layer[l]["astart_norm"] += [round(float(x), 3) for x in r["astart"].norm(dim=-1)]
            per_layer[l]["rms"] += [round(float(x), 3) for x in r["rms"]]
    rms_mean = {l: sum(v["rms"]) / len(v["rms"]) for l, v in per_layer.items()}
    return {
        "layers": layers,
        "hidden_size": loaded.hidden_size,
        "num_layers": loaded.num_layers,
        "per_layer": {str(l): v for l, v in per_layer.items()},
        "rms_mean_by_layer": {str(l): round(v, 3) for l, v in rms_mean.items()},
        "ok": finite and all(v > 0 for v in rms_mean.values()),
    }


@torch.inference_mode()
def next_token_logits(loaded, prompt: str, hook, layer: int | None) -> torch.Tensor:
    ids = torch.tensor([steer_model.chat_input_ids(loaded, "", prompt)], device=loaded.device)
    with steering(loaded.layers, layer, hook):
        out = loaded.model(input_ids=ids, attention_mask=torch.ones_like(ids))
    return out.logits[0, -1].float().cpu()


def stage_steer(loaded, prompt: str, layer: int, rms: float, doses: list[float], max_new_tokens: int, seed: int) -> dict:
    """Greedy decoding so that any change is caused by the vector, not by sampling."""
    from steering_extension.steer.generate import generate_batch

    gen = torch.Generator().manual_seed(seed)
    unit = torch.randn(loaded.hidden_size, generator=gen)
    unit = unit / unit.norm()

    def run(hook):
        g = generate_batch(loaded, requests([prompt]), temperature=0.0, max_tokens=max_new_tokens, hook=hook, layer_idx=layer if hook is not None else None)[0]
        return g["text"]

    def add(r: float, mode: str = "response"):
        return AdditiveSteer((unit * r * rms).to(loaded.device), torch.ones(1, device=loaded.device), mode)

    base = run(None)
    base_again = run(None)
    zero = run(AdditiveSteer(unit.to(loaded.device), torch.zeros(1, device=loaded.device), "response"))
    cells = []
    for r in doses:
        text = run(add(r))
        cells.append({"dose_fraction_of_rms": r, "text_changed": text != base, "text": text})
    l0 = next_token_logits(loaded, prompt, None, None)
    l1 = next_token_logits(loaded, prompt, add(doses[0], "all"), layer)
    logit_diff = float((l0 - l1).abs().max())
    deterministic = base == base_again
    return {
        "layer": layer,
        "rms_at_layer": round(rms, 3),
        "baseline_text": base,
        "baseline_deterministic": deterministic,
        "zero_vector_matches_baseline": zero == base,
        "cells": cells,
        "first_step_max_abs_logit_diff_at_lowest_dose": round(logit_diff, 4),
        # pass: the vector reaches the logits, some dose changes the text, and a zero vector does not
        "ok": logit_diff > 0 and any(c["text_changed"] for c in cells) and (zero == base or not deterministic),
    }


def stage_speed_probe(loaded, prompts: list[str], batch: int, max_new_tokens: int) -> dict:
    from steering_extension.steer.generate import generate_batch

    reqs = requests([prompts[i % len(prompts)] for i in range(batch)])
    t0 = time.time()
    gens = generate_batch(loaded, reqs, temperature=1.0, max_tokens=max_new_tokens, hook=None, layer_idx=None)
    dt = time.time() - t0
    toks = sum(g["completion_tokens"] for g in gens)
    return {"batch": batch, "max_new_tokens": max_new_tokens, "tokens_per_s_total": round(toks / dt, 2), "tokens_per_s_per_sequence": round(toks / dt / batch, 2), "includes_prompt_prefill": True}


def run_model_stages(report: Report, loaded, args) -> None:
    """Everything after the model is loaded; also used by the CPU test with a tiny random model."""
    layers = [int(x) for x in args.layers.split(",")]
    prompts, source = paper_prompts(args.n_texts)
    report.data["meta"]["prompt_source"] = source
    gen = report.stage("generate", lambda: stage_generate(loaded, prompts, args.max_new_tokens, 1.0))
    if not gen["ok"] and "texts" not in gen:
        return
    cap = report.stage("capture", lambda: stage_capture(loaded, prompts, gen["texts"], layers, args.capture_batch))
    rms = float(cap.get("rms_mean_by_layer", {}).get(str(args.steer_layer), 0.0)) if cap["ok"] else 0.0
    if rms > 0:
        doses = [float(x) for x in args.doses.split(",")]
        report.stage("steer", lambda: stage_steer(loaded, prompts[0], args.steer_layer, rms, doses, args.steer_tokens, args.seed))
    else:
        report.data["stages"]["steer"] = {"required": True, "ok": False, "error": "skipped: no residual norm from the capture stage", "seconds": 0}
    if args.speed_batch > 0:
        report.stage("speed_probe", lambda: stage_speed_probe(loaded, prompts, args.speed_batch, args.speed_tokens), required=False)
    if torch.cuda.is_available():
        report.data["gpu_memory_end"] = gpu_memory()
        report.data["peak_allocated_gib_total"] = round(sum(g["peak_allocated_gib"] for g in report.data["gpu_memory_end"]), 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=os.environ.get("STEER_MODEL", DEFAULT_MODEL))
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "steering" / "ds0" / "smoke_report.json")
    ap.add_argument("--preflight-only", action="store_true", help="environment, FP8 kernel and tokenizer checks only; no weights")
    ap.add_argument("--skip-kernel-test", action="store_true", help="do not run the FP8 kernel micro-test")
    ap.add_argument("--min-total-vram-gib", type=float, default=700.0, help="FP8 weights are about 630 GiB on the GPUs")
    ap.add_argument("--min-gpus", type=int, default=2)
    ap.add_argument("--n-texts", type=int, default=4)
    ap.add_argument("--max-new-tokens", type=int, default=900, help="paper essay limit")
    ap.add_argument("--layers", default="15,30,45", help="3 layers to read residuals at (of 61)")
    ap.add_argument("--steer-layer", type=int, default=30)
    ap.add_argument("--doses", default="0.5,2,8", help="random-vector norms as fractions of the layer's RMS residual norm (smoke values)")
    ap.add_argument("--steer-tokens", type=int, default=48)
    ap.add_argument("--capture-batch", type=int, default=1, help="prompt+response forward passes are the memory-heavy step")
    ap.add_argument("--speed-batch", type=int, default=16, help="0 disables the batched throughput probe")
    ap.add_argument("--speed-tokens", type=int, default=96)
    ap.add_argument("--seed", type=int, default=20261117)
    args = ap.parse_args()
    if args.steer_layer not in [int(x) for x in args.layers.split(",")]:
        ap.error("--steer-layer must be one of --layers (its RMS norm sets the dose)")

    torch.manual_seed(args.seed)
    report = Report(args.out, {"model": args.model, "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "argv": sys.argv[1:], "preflight_only": args.preflight_only})
    env = report.stage("environment", lambda: env_facts(args.min_total_vram_gib, args.min_gpus))
    if env["ok"] and not args.skip_kernel_test:
        report.stage("fp8_kernel", fp8_kernel_microtest)

    def tok_stage():
        from transformers import AutoTokenizer

        return template_check(AutoTokenizer.from_pretrained(args.model, padding_side="left"))

    report.stage("chat_template", tok_stage)
    if args.preflight_only or not report.finish():
        ok = report.finish()
        print(f"preflight {'PASSED' if ok else 'FAILED'} -> {args.out}", flush=True)
        return 0 if ok else 1

    def load():
        loaded = steer_model.load_model(args.model)
        devmap = getattr(loaded.model, "hf_device_map", None) or {}
        per_dev: dict[str, int] = {}
        for dev in devmap.values():
            per_dev[str(dev)] = per_dev.get(str(dev), 0) + 1
        fp8 = sum(p.numel() for p in loaded.model.parameters() if p.dtype == torch.float8_e4m3fn)
        total = sum(p.numel() for p in loaded.model.parameters())
        return {
            "_loaded": loaded,
            "family": loaded.family,
            "num_layers": loaded.num_layers,
            "hidden_size": loaded.hidden_size,
            "modules_per_device": per_dev,
            "params_total_b": round(total / 1e9, 2),
            "params_fp8_b": round(fp8 / 1e9, 2),
            "gpu_memory_after_load": gpu_memory(),
            # FP8 must have stayed FP8: a silent dequantize would need about twice the memory
            "ok": loaded.family == steer_model.FAMILY_DEEPSEEK_V32 and fp8 / max(total, 1) > 0.9,
        }

    report.stage("load", load)
    loaded = report.private.get("load", {}).get("_loaded")
    if loaded is not None:
        run_model_stages(report, loaded, args)
    ok = report.finish()
    print(f"smoke test {'PASSED' if ok else 'FAILED'} -> {args.out}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
