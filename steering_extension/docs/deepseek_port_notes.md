# DeepSeek V3.2 white-box port: preparation notes (DS0)

Written 2026-11-17. Preparation only: nothing was rented, no paid call was made, nothing was committed.
Nothing in this file has been run on a GPU. Every statement about the rented machine is a reading of
source code or an estimate, and is marked as such.

## Verdict

White-box steering of the full-precision (FP8) DeepSeek V3.2 looks feasible with the stack we already
have. Stock transformers has the architecture natively, loads the FP8 weights as FP8, and its decoder
blocks return the residual stream as a plain tensor, so our hooks work with two small changes.
The smoke test should fit the planned $35 to $45 on the 8 x RTX PRO 6000 machine. It does not fit that
budget on the 8 x H200 machine (about $45 to $105).

The main risk is the GPU type, not the method: the FP8 kernel has not been tried by us on RTX PRO 6000
cards. The chain checks this in the first 15 to 20 minutes (about $4), before the 690 GB download.

## What was read

Downloaded to the scratchpad and read, never executed. No weight files were downloaded.

| Source | What it settled |
|---|---|
| HF API `models/deepseek-ai/DeepSeek-V3.2` (sha `a7e62ac`) | 163 safetensors shards, 689,483,049,129 bytes (642.1 GiB). Tags `deepseek_v32`, `fp8`. No `modeling_*.py`, no `auto_map`, no Jinja template. |
| `config.json` | Architecture and quantization fields quoted below. Identical to the `DeepSeek-V3.2-Exp` `config.json` (checked with diff). |
| `generation_config.json` | `do_sample: true`, `temperature: 1.0`, `top_p: 0.95`. |
| `tokenizer_config.json` | `LlamaTokenizerFast`, `add_bos_token: false`, pad token equals EOS, no `chat_template` field. |
| `README.md` (model card) | "This release does not include a Jinja-format chat template." Points to `encoding/` and to the V3.2-Exp repo for local running. |
| `encoding/encoding_dsv32.py` | The chat prompt rules, including how thinking is switched off. |
| `inference/README.md`, `model.py`, `generate.py`, `convert.py`, `kernel.py`, `requirements.txt` | DeepSeek's reference inference code. |
| `model.safetensors.index.json` (first 400 kB) and the headers of shards 1 and 2 | Tensor names, dtypes and shapes. `total_size` is 1,370,793,842,752, which is the BF16 size, not the stored size. |
| GitHub `deepseek-ai/DeepSeek-V3.2-Exp` README | Official ways to run: reference code, SGLang, vLLM. |
| transformers `main` at commit `0e6e6d6` (version 5.24.0.dev0): `models/deepseek_v32/modeling_deepseek_v32.py`, `docs/.../model_doc/deepseek_v32.md`, `integrations/finegrained_fp8.py`, `quantizers/quantizer_finegrained_fp8.py`, `utils/quantization_config.py`, `quantizers/auto.py`, `docs/.../quantization/finegrained_fp8.md`, `setup.py` | Native support, FP8 loading, multi-GPU behaviour, dependency pins. |
| vLLM `main`: `model_executor/models/registry.py`, `deepseek_v2.py` | vLLM registers `DeepseekV32ForCausalLM`. |

Checked on the laptop (CPU): the real DeepSeek tokenizer (tokenizer files only) and a tiny randomly
initialised `DeepseekV32ForCausalLM`.

## 1. Can stock transformers load it and run it with residual hooks?

Yes, natively. No `trust_remote_code`.

- The checkpoint ships no model code. `config.json` has `architectures: ["DeepseekV32ForCausalLM"]` and
  `model_type: "deepseek_v32"`, and no `auto_map`.
- transformers has `models/deepseek_v32` in `main`. Its doc page says it was "contributed to Hugging Face
  Transformers on 2026-06-10". The laptop's released transformers 5.20.1 already imports
  `DeepseekV32ForCausalLM` and `FineGrainedFP8Config`. The newest release on PyPI is 5.23.0. Our remote
  environment installs `main`, which is 5.24.0.dev0 today. The chain pins commit `0e6e6d6`, the one read here.
- `config.json` says `transformers_version: 4.44.2`. That is the tool that wrote the file, not a requirement.

Architecture, from `config.json`:

| Field | Value |
|---|---|
| `num_hidden_layers` | 61 |
| `hidden_size` | 7168 |
| `vocab_size` | 129280 |
| Dense layers | the first 3 (`first_k_dense_replace: 3`), `intermediate_size` 18432 |
| MoE layers | the other 58: `n_routed_experts` 256, `n_shared_experts` 1, `num_experts_per_tok` 8, `n_group` 8, `topk_group` 4, `moe_intermediate_size` 2048, `scoring_func` sigmoid, `routed_scaling_factor` 2.5 |
| Attention | Multi-head Latent Attention: `num_attention_heads` 128, `q_lora_rank` 1536, `kv_lora_rank` 512, `qk_nope_head_dim` 128, `qk_rope_head_dim` 64, `v_head_dim` 128 |
| Sparse attention | DeepSeek Sparse Attention indexer in every layer: `index_n_heads` 64, `index_head_dim` 128, `index_topk` 2048 |
| Positions | RoPE with yarn scaling, `max_position_embeddings` 163840 |
| Extra | `num_nextn_predict_layers: 1`: the weights contain a 62nd block (`model.layers.61`, multi-token prediction). transformers ignores it (`_keys_to_ignore_on_load_unexpected`), and so does the reference `convert.py`. |

The indexer keeps the top 2,048 earlier tokens for each query. For a sequence of up to 2,048 tokens it
keeps all of them, so attention is dense and the indexer changes nothing. Essay and grant runs stay under
that length. Postmortem runs (3,000 new tokens) can exceed it.

Hooks. In `modeling_deepseek_v32.py` the blocks are `model.model.layers`, an `nn.ModuleList` of 61
`DeepseekV32DecoderLayer`. Each `forward` ends with `hidden_states = residual + hidden_states;
return hidden_states`. So a forward hook on a block sees the residual stream after that block as one
tensor, the same as for Qwen. Checked on the tiny CPU model:

- the hook output at block L equals `output_hidden_states[L + 1]` (for the last block the listed hidden
  state is after the final norm, so the comparison goes through the norm);
- `AdditiveSteer` shifts the stream by exactly the vector and the change reaches later blocks;
- `DirectionalAblation` at every block leaves no component along the direction;
- "response" mode touches only decode steps under `generate` with the cache.

This is different in DeepSeek's own reference code: there a block returns two tensors (branch output and
residual) and the stream is their sum. Hooks written for transformers would not transfer to it unchanged.

## 2. FP8: run as FP8, or upcast?

They run as FP8. No upcast is needed.

What is stored (shard headers 1 and 2): the linear weights are `F8_E4M3`, each with a `weight_scale_inv`
tensor in `F32` holding one scale per 128 x 128 block (for example `q_a_proj.weight` is [1536, 7168] and
its scale is [12, 56]). `embed_tokens` and `indexer.weights_proj` are `BF16`. Norm weights are `F32`.
`config.json` `quantization_config`: `quant_method: fp8`, `fmt: e4m3`, `weight_block_size: [128, 128]`,
`activation_scheme: dynamic`, `scale_fmt: ue8m0`.

How transformers runs it (`integrations/finegrained_fp8.py`): every `nn.Linear` becomes an `FP8Linear`
that keeps the FP8 weight and its scales, quantises the incoming activations to FP8 for each call, and
does the matrix product in an FP8 kernel. The MoE experts become `FP8Experts`. This is the same scheme as
DeepSeek's reference `linear()` in `inference/model.py` (`act_quant` then `fp8_gemm`). The transformers
doc page for this model gives the load call we use:
`FineGrainedFP8Config(modules_to_not_convert=["model.layers.*.mlp.gate.*", "*.self_attn.indexer.weights_proj.*"], weight_block_size=(128, 128))`,
`device_map="auto"`.

Three details from the source that matter for us:

- Two kernels exist. DeepGEMM is the fast one (the doc says 3 to 6 times faster). The loader switches it
  off when one process spreads the model over several GPUs (`_disable_deepgemm_on_multi_device`: its
  kernels "produce garbage across devices"). We load with `device_map="auto"` on 8 GPUs, so we get the
  slower Triton kernel, loaded through the `kernels` package from `kernels-community/finegrained-fp8`.
- The settings in the checkpoint's own `quantization_config` win over the ones passed in. Only
  `dequantize` and `modules_to_not_convert` are taken from our call (`quantizers/auto.py`,
  `get_loading_attributes`). So `scale_fmt: ue8m0` applies, and the scale parameters get the dtype
  `torch.float8_e8m0fnu`. The installed torch must have that dtype. The preflight checks it.
- If a GPU has compute capability below 8.9, the loader silently dequantises to BF16. That would need
  twice the memory and fail. The preflight checks capability, and the load stage checks that more than
  90% of the parameters are still FP8.

Two known numeric differences from DeepSeek's reference code, both in the transformers port: the indexer
scores are computed in BF16/FP32 instead of FP8 after a Hadamard rotation (the doc page says so), and I
did not find the reference's FP8 round trip of the cached keys and values in the port (unverified). Neither
matters for sequences up to 2,048 tokens as far as the indexer goes.

Official inference instructions (V3.2 README points to the V3.2-Exp repo README):

1. DeepSeek's reference demo: `convert.py` then `torchrun --nproc-per-node 8 generate.py`. Needs
   `tilelang==0.1.6` and `fast_hadamard_transform`.
2. SGLang: docker image `lmsysorg/sglang:dsv32`, `--tp 8 --dp 8 --enable-dp-attention`. The image list is
   headed "H200".
3. vLLM: "day-0 support", see its recipes page. vLLM `main` registers `DeepseekV32ForCausalLM`.

### The paths compared

Memory arithmetic: the shards hold 642.1 GiB. The unused 62nd block is about 14 GiB (one MoE block plus an
embedding and a head, my estimate), so about 630 GiB goes onto the GPUs. One MoE block is about 10.7 GiB.
In BF16 the model would be 1,277 GiB (`total_size` in the index file).

vast lists the 8 x RTX PRO 6000 machine as 765 GB. One such card reports 97,887 MiB, which is 95.6 GiB,
and 8 x 95.6 = 765. So vast's number is GiB, and the comparison is 630 GiB of weights against 765 GiB.
That leaves about 135 GiB, not the 75 GB in `week9_plan.txt` (which compared 690 decimal GB against
765 GiB). Unverified until the load.

| Path | Runs FP8 as FP8 | Residual read and steering | GPU memory | Fits on | State |
|---|---|---|---|---|---|
| A. transformers, FP8, one process, `device_map="auto"` | yes (Triton kernel) | yes, our existing hooks | about 630 GiB weights plus activations | 8 x RTX PRO 6000 (765), 8 x H200 (1,123), 8 x B200 | prepared here, recommended |
| B. transformers, dequantised to BF16 (`dequantize=True`) | no | yes | about 1,250 to 1,280 GiB | only 8 x B200 (1,432), about $70/h | not needed |
| C. DeepSeek reference code, 8 processes | yes (tilelang kernels) | possible, but hooks must be rewritten (two-tensor block output, eight processes that must stay in step) and its `generate.py` calls `apply_chat_template`, which this checkpoint cannot serve | about 80 GiB per GPU plus fixed caches | 8 x RTX PRO 6000 likely, unverified | not prepared. `convert.py` holds the whole model in CPU RAM (about 690 GB) and needs another 690 GB of disk |
| D. vLLM or SGLang | yes | not without patching the server's model class inside its worker processes and adding a way to pass a vector per request and to return activations | built for 8 x H200 | 8 x H200 | not prepared; fast, but days of engineering and a new code path to validate |

Memory inside path A on 8 x RTX PRO 6000. `device_map="auto"` cannot split a block. 58 MoE blocks over
8 GPUs means some GPUs hold 8 blocks (about 86 GiB), which leaves about 10 GiB on those GPUs. Decode steps
need little. The heavy step is a full forward pass over prompt plus response (extraction and projection):
attention scores take batch x 128 heads x length x length x 2 bytes, and the indexer scores batch x length
x 64 x length x 4 bytes. At 3,000 tokens that is about 2.3 GiB each for one sequence, and about 9 GiB each
for a batch of 4. So on this machine: batch 1 or 2 for long forward passes, larger batches for generation.
On 8 x H200 there are about 490 GiB spare and this limit goes away. All of this is arithmetic, not measured.

## 3. Chat template and thinking off

The paper called OpenRouter model `deepseek/deepseek-v3.2` with reasoning disabled. The paper's scripts
send `{"effort": "none"}` for this (for example `src/utility_behavior_gap/scripts/run_r0_generations.py`).

The checkpoint has no Jinja template (`tokenizer_config.json` has no `chat_template`; model card note 1).
`tokenizer.apply_chat_template` therefore fails, and our Qwen flag `enable_thinking=False` has nothing to
act on. The rules are in `encoding/encoding_dsv32.py`:

- `user_msg_template = "<｜User｜>{content}<｜Assistant｜>"`;
- after the last user message the encoder appends `<think>` in `thinking_mode="thinking"` and `</think>`
  in `thinking_mode="chat"`;
- a system message is plain text between BOS and the user token, with no role token.

So thinking off is: open the assistant turn with a closing think tag. With a blank system prompt:

`<｜begin▁of▁sentence｜><｜User｜>{prompt}<｜Assistant｜></think>`

`steer/model.py` now builds exactly this string for the DeepSeek family and tokenises it without adding
special tokens. Checked with the real tokenizer on the laptop: "1+1=?" gives
`[0, 128803, 19, 13, 19, 127252, 128804, 128799]`. The model card's example has the same ids for BOS (0),
User (128803), the text, and Assistant (128804); 128799 is `</think>` there too.

Unverified: that OpenRouter's provider for `deepseek/deepseek-v3.2` with reasoning off sends this same
prompt. It is the checkpoint's own non-thinking mode, so it is the natural reading. DS1 (re-measuring the
sandbagging cell on the hosted model) is the test.

Sampling: the pipeline keeps the paper's temperature 1.0 and passes `top_p=1.0`, as for Qwen. The
checkpoint's default is `top_p=0.95`, which we override. What OpenRouter's provider used is unknown.

## 4. Expected generation speed (all estimates)

Nothing was measured. Basis for path A: Qwen3.5-9B on one A100 does about 670 tokens/s at batch 32 in our
logs, which is about 48 ms per decode step for 32 blocks, 1.5 ms per block. A DeepSeek block has more
parts (five FP8 projections in attention, the indexer, a router, grouped expert products, activation
quantisation before every FP8 product, hops between GPUs), and uses the slower Triton kernel. If a block
costs 3 to 6 times a Qwen block, a decode step over 61 blocks takes about 0.2 to 0.6 s. Step time should
grow slowly with batch size until the expert products dominate.

| Path | Estimate | Basis |
|---|---|---|
| A, batch 1 | 2 to 5 tokens/s | 0.2 to 0.6 s per step |
| A, batch 16 | 30 to 80 tokens/s in total | same step time, 16 sequences |
| A, batch 32 | 50 to 150 tokens/s in total | if memory and step time hold; least certain |
| C, reference code | 1 to 5 tokens/s per sequence, poor batching | Python loop over up to 256 experts per block, cross-process reductions in every block; guess |
| D, vLLM or SGLang | hundreds to thousands of tokens/s in total | what these servers are built for; no number checked; no hooks |

The smoke test measures batch 4 (the four 900-token essays) and a batch-16 probe (96 tokens). Those two
numbers replace this table and the DS1 to DS5 cost in `week9_plan.txt`. At 30 to 80 tokens/s the planned
1.8M tokens take 6 to 17 hours, about $85 to $225 at $13.5/h. The plan's two cases (20 and 100 tokens/s)
bracket this.

## 5. What in `steer/` was Qwen-specific

| Place | Qwen-specific part | Status |
|---|---|---|
| `model.py` `chat_input_ids` | `apply_chat_template(..., enable_thinking=False)` | changed: DeepSeek family builds the prompt above; other models unchanged |
| `model.py` `load_model` | plain BF16 load; `STEER_USE_KERNELS` adds `use_kernels=True` for Qwen's hub kernels | changed: DeepSeek family adds `FineGrainedFP8Config`; optional `STEER_MAX_MEMORY_GIB` cap per GPU. Leave `STEER_USE_KERNELS=0` for DeepSeek |
| `model.py` `find_decoder_layers` | heuristic: the longest `ModuleList` | changed: DeepSeek family takes `model.model.layers` and checks the count. The heuristic finds the same list on the tiny model, but FP8 expert modules were not ruled out as a longer list |
| `model.py` `LoadedModel` | no notion of a model family | changed: new field `family`, default `"default"` |
| `hooks.py` all three hooks | vectors, coefficients and masks were moved to the block's dtype but not to its device | changed: they now move to the block's device too, and captured sums come back on the mask's device. Needed whenever `device_map` spreads blocks over GPUs. A no-op on one GPU |
| `generate.py`, `extract.py`, `project.py` | defaults only: `--model` default, `--layers 8,...,24`, batch sizes 16 to 32; `success_row` records `"backend": "hf_transformers"` | not changed. Pass `--model deepseek-ai/DeepSeek-V3.2`, layers out of 61, and small batches for `extract`/`project` |
| `generate.py` "response" mode | relies on decode steps having sequence length 1 | works for DeepSeek under `generate` with the cache (tiny-model test) |
| `extract.py` `tail2..tail6`, `astart` | the template tokens at the end of the prompt differ: for DeepSeek the last two are `<｜Assistant｜>` and `</think>` | no change needed; `vectors_report.json` names them |
| `kl_check.py` | uses `past_key_values` on the model output | not ported. transformers `main` renames this to `cache` for this model. Check before using it on DeepSeek |
| `vast/run_shards.sh` | one process per GPU | use `NUM_SHARDS=1 GPUS_PER_SHARD=8` |
| `requirements-remote.txt` | `kernels>=0.17,<0.18` | not changed. transformers `main` now asks for `kernels>=0.18.2,<0.19` (`setup.py`). The DS0 chain installs that range and the pinned transformers commit after the normal bootstrap. The Qwen pin looks stale against today's `main`; that is a separate decision |
| `remote/bootstrap.sh` | always downloads weights | one opt-in switch added: `STEER_SKIP_WEIGHTS=1` sets up the environment only. Default behaviour unchanged |

Qwen behaviour: the default-family code path is the old code. A snapshot of hook outputs on a fixed tiny
model (logits under additive steering, multi-layer steering, ablation, steered `generate`, both capture
modes at 10 layers) was taken before the edit and is bit-identical after it.

## Recommended path, machine, and smoke-test cost

Path A (transformers, FP8, one process over 8 GPUs) on the 8 x RTX PRO 6000 machine.

Search filters: 8 GPUs, at least 90 GB each, at least 900 GB of disk, download speed of 2,000 Mbit/s or
more. The download dominates the session, so a slow line costs more than a slightly dearer machine.

| Step | Time (estimate) | Basis |
|---|---|---|
| Boot, push, environment | 15 min | the README gives about 10 min for the Qwen bootstrap |
| Preflight without weights | 3 to 5 min | small downloads and one tiny kernel test |
| Download 690 GB | 30 to 95 min | 3 Gbit/s to 1 Gbit/s sustained |
| Load onto 8 GPUs | 10 to 25 min | 642 GiB read from disk, experts restacked on load; guess |
| Smoke stages | 10 to 20 min | 4 x 900 tokens at 0.2 to 0.6 s per step, plus short runs |
| Pull and grace wait | 5 to 20 min | grace is capped at 20 min |
| Total | 75 to 180 min | hard limit in the chain: 180 min |

| Machine | Price | Smoke-test cost | Comment |
|---|---|---|---|
| 8 x RTX PRO 6000 | about $13.5/h | $17 to $41, capped near $41 by the hard limit | fits the $35 to $45 plan; GPU type untested with the FP8 kernel |
| 8 x H200 NVL | about $35/h | $44 to $105 | the GPU class the transformers and SGLang docs name; over the plan |
| 8 x B200 | about $70/h | $88 to $210 | only needed for the BF16 upcast, which we do not need |

If the preflight fails on the RTX PRO 6000 machine because of the FP8 kernel, the loss is about $4, and
the next step is the H200 machine, which needs a new go because it is over the planned amount.

A stopped instance still bills for its disk and cannot be reached by ssh. Always finish with `vast down`.

## Blockers and unknowns

Blockers before launch:

1. A vast instance is recorded right now (`outputs/steering/vast/instance.json`: label `w9_qwen_sandbag`,
   created 2026-11-17). `vast.py` keeps one state file and `up` refuses while that instance runs. DS0 has
   to wait for it, or `vast.py` needs a second state file.
2. Renting needs the PI's go for this spend. Nothing here was authorised or launched.

Unknown until the first run (the preflight and the smoke report answer 3 to 8):

3. Whether the Triton FP8 kernel builds and gives correct numbers on RTX PRO 6000 (Blackwell workstation
   cards; I expect compute capability 12.0, unverified). The docs name H100-class GPUs. The preflight runs
   one small FP8 product on the first and last GPU and compares it with the dequantised product.
4. Whether the torch build that works with the host driver has `float8_e8m0fnu`. The README's fallback
   for old drivers is `torch<2.10`; I do not know whether that build has the dtype. The preflight checks.
5. Whether loading the F32 scales into `ue8m0` parameters works for this checkpoint. The transformers doc
   shows this load for V3.2-Exp, whose `config.json` is identical, but we have not run it.
6. Real memory headroom and the largest safe batch for long forward passes.
7. Real speed. Section 4 is a guess.
8. Download speed from the Hub without a token. The repo has no Hugging Face token handling. The chain
   passes `HF_TOKEN` through if it is set and never prints it.
9. Whether stopping from inside works on vast (`CONTAINER_ID`, `CONTAINER_API_KEY`). The chain tries the
   `vastai` CLI and then the REST call that `w9_chain.sh` uses, five times, and reads the two variables
   from PID 1's environment when tmux did not inherit them. This was exercised only against stubs on the
   laptop. If it fails it writes `logs/ds0.STOP_FAILED` and says so in the log. The laptop-side
   `vast down` remains the real end of billing.
10. Whether the hosted model matches what the paper measured through OpenRouter (provider quantisation,
    prompt, `top_p`). This is DS1, as planned.

Not done:

11. `kl_check.py` is not ported (item in section 5).
12. No DeepSeek manifests were built. `LOCAL_ACTOR` in `local/common.py` is the Qwen actor id; DS1 needs
    its own actor id and model field. That is a design choice for DS1, not made here.
13. The README was not changed.

## Files

- `steering_extension/steer/model.py`: model family, DeepSeek prompt, FP8 load, layer path.
- `steering_extension/steer/hooks.py`: device moves for multi-GPU models.
- `steering_extension/remote/bootstrap.sh`: `STEER_SKIP_WEIGHTS=1`.
- `steering_extension/remote/deepseek_smoke.py`: preflight and smoke test, JSON report.
- `steering_extension/vast/ds0_chain.sh`: the instance-side chain with markers, grace wait, hard limit, self-stop.
- `steering_extension/tests/test_model_adapter.py`: CPU tests. Run with
  `.venv/bin/python -m pytest steering_extension/tests -q` (7 tests; the repo's default `pytest` does not collect them).

How to launch is in the header of `ds0_chain.sh`. The smoke report is `outputs/steering/ds0/smoke_report.json`.
Its doses (0.5, 2 and 8 times the layer's RMS residual norm, random direction, layer 30) are smoke-test
values chosen to see a change, not scientific choices.
