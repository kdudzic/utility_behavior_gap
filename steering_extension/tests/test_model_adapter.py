"""CPU tests for the second-model adapter in steer/model.py and steer/hooks.py, and for the DS0 smoke
script's stage logic. No GPU, no network, no weights: a tiny randomly initialised DeepseekV32 model and
an in-memory tokenizer stand in for the real ones.

Run: .venv/bin/python -m pytest steering_extension/tests -q
(not collected by the repo's default `pytest`, whose testpaths is `tests/`).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from steering_extension.steer import model as sm  # noqa: E402
from steering_extension.steer.hooks import AdditiveSteer, DirectionalAblation, ResidualCapture, steering  # noqa: E402


def tiny_tokenizer():
    from tokenizers import Tokenizer, models, pre_tokenizers
    from transformers import PreTrainedTokenizerFast

    eos = "<｜end▁of▁sentence｜>"
    specials = [sm.DSV32_BOS, eos, sm.DSV32_USER, sm.DSV32_ASSISTANT, sm.DSV32_THINK_END, "<think>"]
    vocab = {t: i for i, t in enumerate(specials + ["[UNK]"] + [f"w{i}" for i in range(40)])}
    tok = Tokenizer(models.WordLevel(vocab, unk_token="[UNK]"))
    tok.pre_tokenizer = pre_tokenizers.Whitespace()
    fast = PreTrainedTokenizerFast(tokenizer_object=tok, bos_token=sm.DSV32_BOS, eos_token=eos, pad_token=eos, padding_side="left")
    fast.add_special_tokens({"additional_special_tokens": [sm.DSV32_USER, sm.DSV32_ASSISTANT]})
    fast.add_tokens([sm.DSV32_THINK_END, "<think>"])
    return fast


def tiny_loaded(family: str = sm.FAMILY_DEEPSEEK_V32) -> sm.LoadedModel:
    from transformers import DeepseekV32Config, DeepseekV32ForCausalLM

    torch.manual_seed(0)
    tok = tiny_tokenizer()
    cfg = DeepseekV32Config(
        vocab_size=len(tok), hidden_size=64, intermediate_size=96, moe_intermediate_size=32, num_hidden_layers=10,
        num_attention_heads=4, num_key_value_heads=4, n_routed_experts=8, kv_lora_rank=16, q_lora_rank=32,
        qk_rope_head_dim=8, v_head_dim=8, qk_nope_head_dim=8, n_group=2, topk_group=1, num_experts_per_tok=2,
        index_topk=8, index_head_dim=16, index_n_heads=4, first_k_dense_replace=2, max_position_embeddings=512,
        bos_token_id=tok.bos_token_id, eos_token_id=tok.eos_token_id, pad_token_id=tok.pad_token_id,
    )
    model = DeepseekV32ForCausalLM(cfg).eval()
    return sm.LoadedModel(name="tiny", model=model, tokenizer=tok, layers=model.model.layers, hidden_size=64, family=family)


def test_family_detection(monkeypatch):
    monkeypatch.delenv("STEER_MODEL_FAMILY", raising=False)
    assert sm.model_family("Qwen/Qwen3.5-9B") == sm.FAMILY_DEFAULT
    assert sm.model_family("Qwen/Qwen3.5-27B") == sm.FAMILY_DEFAULT
    assert sm.model_family("deepseek-ai/DeepSeek-V3.2") == sm.FAMILY_DEEPSEEK_V32
    assert sm.model_family("/workspace/models/deepseek_v32") == sm.FAMILY_DEEPSEEK_V32
    assert sm.model_family("deepseek-ai/DeepSeek-V3") == sm.FAMILY_DEFAULT
    monkeypatch.setenv("STEER_MODEL_FAMILY", sm.FAMILY_DEEPSEEK_V32)
    assert sm.model_family("/some/local/path") == sm.FAMILY_DEEPSEEK_V32


def test_deepseek_prompt_matches_checkpoint_encoder_rules():
    # encoding/encoding_dsv32.py, thinking_mode="chat": BOS + system text + <User>content<Assistant> + </think>
    assert sm.deepseek_v32_chat_prompt("", "1+1=?") == "<｜begin▁of▁sentence｜><｜User｜>1+1=?<｜Assistant｜></think>"
    assert sm.deepseek_v32_chat_prompt("SYS", "hi") == "<｜begin▁of▁sentence｜>SYS<｜User｜>hi<｜Assistant｜></think>"


def test_default_family_still_uses_the_tokenizer_template():
    """Qwen path: the call into apply_chat_template is unchanged (same messages, same flags)."""
    calls = {}

    class Tok:
        def apply_chat_template(self, messages, **kw):
            calls["messages"], calls["kw"] = messages, kw
            return "TEXT"

        def __call__(self, text, **kw):
            calls["tokenized"], calls["tok_kw"] = text, kw
            return {"input_ids": [1, 2, 3]}

    loaded = sm.LoadedModel(name="Qwen/Qwen3.5-9B", model=None, tokenizer=Tok(), layers=None, hidden_size=1)
    assert loaded.family == sm.FAMILY_DEFAULT
    assert sm.chat_input_ids(loaded, "", "hello") == [1, 2, 3]
    assert calls["messages"] == [{"role": "user", "content": "hello"}]
    assert calls["kw"] == {"tokenize": False, "add_generation_prompt": True, "enable_thinking": False}
    assert calls["tokenized"] == "TEXT" and calls["tok_kw"] == {"add_special_tokens": False}
    sm.chat_input_ids(loaded, "sys", "hello")
    assert calls["messages"] == [{"role": "system", "content": "sys"}, {"role": "user", "content": "hello"}]


def test_deepseek_chat_ids_and_layers():
    loaded = tiny_loaded()
    ids = sm.chat_input_ids(loaded, "", "w1 w2 w3")
    tok = loaded.tokenizer
    assert ids[0] == tok.bos_token_id and ids.count(tok.bos_token_id) == 1
    assert ids[1] == tok.convert_tokens_to_ids(sm.DSV32_USER)
    assert ids[-2:] == [tok.convert_tokens_to_ids(sm.DSV32_ASSISTANT), tok.convert_tokens_to_ids(sm.DSV32_THINK_END)]
    # the generic heuristic and the explicit path agree on this architecture
    assert sm.find_decoder_layers(loaded.model) is loaded.model.model.layers


def test_hooks_on_deepseek_blocks():
    """Block outputs are the residual stream: capture at layer L equals hidden_states[L+1], additive
    steering shifts it by exactly the vector, ablation removes the direction."""
    loaded = tiny_loaded()
    model, layers = loaded.model, loaded.layers
    ids = torch.randint(7, len(loaded.tokenizer), (2, 9))
    att = torch.ones_like(ids)
    mask = torch.ones(2, 9)
    with torch.inference_mode():
        ref = model(input_ids=ids, attention_mask=att, output_hidden_states=True).hidden_states
        with ResidualCapture(layers) as cap:
            cap.mask = mask
            model.model(input_ids=ids, attention_mask=att)
        for l in (0, 4, 8):
            assert torch.allclose(cap.sums[l], ref[l + 1].sum(dim=1), atol=1e-5)
        # hidden_states[-1] is the last block's output after the final norm, so compare through the norm
        last = {}
        handle = layers[9].register_forward_hook(lambda m, a, o: last.setdefault("h", o))
        model.model(input_ids=ids, attention_mask=att)
        handle.remove()
        assert torch.allclose(model.model.norm(last["h"]), ref[-1], atol=1e-5)
        assert torch.allclose(cap.sums[9], last["h"].sum(dim=1), atol=1e-5)
        vec = torch.randn(64)
        with steering(layers, 4, AdditiveSteer(vec, torch.tensor([1.0, 1.0]), "all")):
            with ResidualCapture(layers) as cap2:
                cap2.mask = mask
                model.model(input_ids=ids, attention_mask=att)
        assert torch.allclose(cap2.sums[4] - cap.sums[4], vec[None, :] * 9, atol=1e-4)
        assert not torch.allclose(cap2.sums[5], cap.sums[5], atol=1e-4)  # and it propagates downstream
        with steering(layers, None, DirectionalAblation(vec)):
            with ResidualCapture(layers) as cap3:
                cap3.mask = mask
                model.model(input_ids=ids, attention_mask=att)
        unit = vec / vec.norm()
        assert float((cap3.sums[9] @ unit).abs().max()) < 1e-4


def test_response_mode_only_touches_decode_steps():
    loaded = tiny_loaded()
    ids = torch.tensor([sm.chat_input_ids(loaded, "", "w1 w2 w3 w4")])
    kw = dict(input_ids=ids, attention_mask=torch.ones_like(ids), do_sample=False, max_new_tokens=6, min_new_tokens=6, pad_token_id=loaded.tokenizer.pad_token_id)
    vec = torch.randn(64) * 5
    with torch.inference_mode():
        base = loaded.model.generate(**kw)
        with steering(loaded.layers, 5, AdditiveSteer(vec, torch.zeros(1), "response")):
            zero = loaded.model.generate(**kw)
        with steering(loaded.layers, 5, AdditiveSteer(vec, torch.ones(1), "response")):
            steered = loaded.model.generate(**kw)
    assert torch.equal(base, zero)
    n = ids.shape[1]
    assert torch.equal(base[:, : n + 1], steered[:, : n + 1])  # first new token comes from the unsteered prefill
    assert not torch.equal(base, steered)


def test_smoke_stages_run_end_to_end_on_cpu(tmp_path):
    from steering_extension.remote import deepseek_smoke as smoke

    loaded = tiny_loaded()
    check = smoke.template_check(loaded.tokenizer)
    assert check["ok"], check
    args = argparse.Namespace(layers="2,5,7", steer_layer=5, doses="0.5,2,8", steer_tokens=12, n_texts=4, max_new_tokens=24,
                              capture_batch=2, speed_batch=8, speed_tokens=8, seed=1)
    report = smoke.Report(tmp_path / "r.json", {"model": "tiny"})
    smoke.run_model_stages(report, loaded, args)
    data = json.loads((tmp_path / "r.json").read_text())
    stages = data["stages"]
    assert set(stages) == {"generate", "capture", "steer", "speed_probe"}
    for name in ("capture", "steer", "speed_probe"):
        assert stages[name]["ok"], stages[name]
    assert len(stages["generate"]["texts"]) == 4 and "error" not in stages["generate"]
    assert stages["capture"]["hidden_size"] == 64 and set(stages["capture"]["per_layer"]) == {"2", "5", "7"}
    assert stages["steer"]["baseline_deterministic"] and stages["steer"]["zero_vector_matches_baseline"]
    assert stages["steer"]["first_step_max_abs_logit_diff_at_lowest_dose"] > 0
    assert any(c["text_changed"] for c in stages["steer"]["cells"])
    assert stages["speed_probe"]["tokens_per_s_total"] > 0
