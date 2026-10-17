"""vast.ai orchestration for the steering extension: the laptop is the caller, one rented
instance does all GPU work, results are rsynced back continuously.

Subcommands (run as `.venv/bin/python -m steering_extension.vast.vast <cmd> ...`):

  search   [--gpu A100_PCIE] [--min-vram 40] [--num-gpus 1] [--disk 100]   rank offers by $/h
  up       --offer ID | --gpu NAME [--num-gpus N] [--disk GB] [--label L]  create, attach ssh key, wait
  status                                                                    list instances on the account
  ssh      [-- remote command]                                              open shell / run a command
  push     [--full]                                                         rsync repo (+ manifests, vectors) up
  pull     [RUN_DIR ...]                                                    rsync outputs/steering back
  bootstrap                                                                 install env + weights on the instance
  run      [--shards N] [--gpus-per-shard K] [--name J] <module> [args...]   launch shards in tmux, detached
  tail     [--name J]                                                       show the shard logs
  jobs                                                                      list tmux sessions on the instance
  down     [--yes]                                                          destroy the instance (irreversible)

State: `outputs/steering/vast/instance.json` holds the current instance id, ssh host/port, and
offer details. Credentials (via steering_extension/local/keys.py): VAST_API_KEY env, else
`~/.config/utility_behavior_gap/secrets.env`, else `steering_extension/spar_vastai.txt`, else `.env`.
The key is passed to the vastai CLI with --api-key and is never printed.

Money: `up` starts billing until `down`. Stopped instances still bill disk. Nothing here runs
without an explicit subcommand.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / "outputs" / "steering" / "vast"
STATE = STATE_DIR / "instance.json"
VASTAI = str(ROOT / ".venv" / "bin" / "vastai")
REMOTE_ROOT = "/workspace/utility_behavior_gap"
REMOTE_HF = "/workspace/.hf_cache"
DEFAULT_IMAGE = "pytorch/pytorch:2.8.0-cuda12.8-cudnn9-devel"
ONSTART = (
    "apt-get update -qq && apt-get install -y -qq rsync tmux git curl >/dev/null 2>&1; "
    "curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1; "
    "mkdir -p /workspace; touch /workspace/.onstart_done"
)

# repo paths needed on the GPU box; outputs are pushed selectively
PUSH_INCLUDES = [
    "pyproject.toml", "requirements.txt", "src/", "data/inputs/", "steering_extension/",
]
PUSH_EXCLUDES = [
    ".git", ".venv", "__pycache__", "*.pyc", "*.pdf", "*.pptx", "spar_*.txt", ".openrouter.txt", ".env",
    "outputs/", "academic_resources/",
]


# --------------------------------------------------------------------------- helpers

def api_key() -> str:
    """vast.ai key: env > ~/.config/utility_behavior_gap/secrets.env > spar_vastai.txt > .env (never printed)."""
    try:
        from steering_extension.local.keys import resolve_key
    except ImportError:  # run as a plain script rather than with -m
        sys.path.insert(0, str(ROOT))
        from steering_extension.local.keys import resolve_key
    key, _source = resolve_key("VAST_API_KEY")
    if not key:
        sys.exit(
            "no vast.ai key: set VAST_API_KEY, add VAST_API_KEY=... to ~/.config/utility_behavior_gap/secrets.env, "
            "or create steering_extension/spar_vastai.txt"
        )
    return key


def vastai(*args: str, raw: bool = True, check: bool = True) -> object:
    cmd = [VASTAI, *args, "--api-key", api_key()]
    if raw:
        cmd.append("--raw")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        sys.exit(f"vastai {' '.join(args)} failed:\n{proc.stdout}\n{proc.stderr}")
    if not raw:
        return proc.stdout
    out = proc.stdout.strip()
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return out


def load_state() -> dict:
    if not STATE.exists():
        sys.exit(f"no instance recorded in {STATE}; run `up` first")
    return json.loads(STATE.read_text())


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1))


def ssh_base(state: dict) -> list[str]:
    return [
        "ssh", "-p", str(state["ssh_port"]), "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null", "-o", "LogLevel=ERROR", "-o", "ServerAliveInterval=30",
        f"root@{state['ssh_host']}",
    ]


def ssh_run(state: dict, remote_cmd: str, *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run([*ssh_base(state), remote_cmd], check=check, text=True, capture_output=capture)


def rsync(state: dict, src: str, dst: str, *, excludes: list[str] = (), includes: list[str] | None = None, delete: bool = False) -> None:
    rsh = " ".join(shlex.quote(x) for x in ssh_base(state)[:-1])
    cmd = ["rsync", "-az", "--info=stats1", "-e", rsh]
    if delete:
        cmd.append("--delete")
    for e in excludes:
        cmd += ["--exclude", e]
    if includes is not None:
        for i in includes:
            cmd += ["--include", i]
    cmd += [src, dst]
    subprocess.run(cmd, check=True)


def pubkey() -> str:
    for name in ("id_ed25519.pub", "id_rsa.pub", "id_ecdsa.pub"):
        p = Path.home() / ".ssh" / name
        if p.exists():
            return p.read_text().strip()
    sys.exit("no ssh public key in ~/.ssh; create one with ssh-keygen -t ed25519")


def instance_info(iid: int) -> dict:
    for inst in vastai("show", "instances"):
        if int(inst["id"]) == int(iid):
            return inst
    return {}


# --------------------------------------------------------------------------- commands

def cmd_search(a: argparse.Namespace) -> None:
    q = [
        f"num_gpus={a.num_gpus}", "rentable=true", "verified=true", f"reliability>{a.min_reliability}",
        f"disk_space>={a.disk}", "cuda_vers>=12.4", "direct_port_count>=1", f"gpu_ram>={a.min_vram}",
        f"inet_down>={a.min_down}",
    ]
    if a.gpu:
        q.append(f"gpu_name={a.gpu}")
    rows = vastai("search", "offers", " ".join(q), "-o", "dph", "--limit", str(a.limit))
    if not isinstance(rows, list):
        sys.exit(str(rows))
    print(f"{'id':>10} {'gpu':16} {'n':>2} {'$/h':>6} {'vram':>5} {'disk':>6} {'down':>6} {'rel':>5} {'cuda':>5} loc")
    for r in rows:
        print(f"{r['id']:>10} {r['gpu_name']:16} {r['num_gpus']:>2} {r['dph_total']:>6.2f} {r['gpu_ram']/1024:>5.0f} {r['disk_space']:>6.0f} {r['inet_down']:>6.0f} {r['reliability2']:>5.3f} {r['cuda_max_good']:>5} {r['geolocation']}")


def cmd_up(a: argparse.Namespace) -> None:
    if STATE.exists():
        st = json.loads(STATE.read_text())
        info = instance_info(st["instance_id"])
        if info and info.get("actual_status") not in (None, "exited"):
            sys.exit(f"instance {st['instance_id']} already recorded and {info.get('actual_status')}; `down` it first")
    offer = a.offer
    if offer is None:
        q = f"num_gpus={a.num_gpus} rentable=true verified=true reliability>{a.min_reliability} disk_space>={a.disk} cuda_vers>=12.4 direct_port_count>=1 gpu_ram>={a.min_vram} inet_down>={a.min_down}"
        if a.gpu:
            q += f" gpu_name={a.gpu}"
        rows = vastai("search", "offers", q, "-o", "dph", "--limit", "1")
        if not rows:
            sys.exit("no offer matches")
        offer = rows[0]["id"]
        print(f"picked offer {offer}: {rows[0]['gpu_name']} x{rows[0]['num_gpus']} ${rows[0]['dph_total']:.2f}/h {rows[0]['geolocation']}")
    res = vastai(
        "create", "instance", str(offer), "--image", a.image, "--disk", str(a.disk), "--ssh", "--direct",
        "--label", a.label, "--onstart-cmd", ONSTART, "--env", "-e HF_HOME=/workspace/.hf_cache -e TOKENIZERS_PARALLELISM=false",
    )
    if not isinstance(res, dict) or not res.get("success"):
        sys.exit(f"create failed: {res}")
    iid = int(res["new_contract"])
    print(f"instance {iid} created; attaching ssh key and waiting for it to boot")
    vastai("attach", "ssh", str(iid), pubkey(), raw=False)
    state = {"instance_id": iid, "offer_id": offer, "label": a.label, "image": a.image, "disk_gb": a.disk, "created": time.strftime("%Y-%m-%dT%H:%M:%S")}
    save_state(state)
    wait_ready(state, timeout=a.timeout)


def wait_ready(state: dict, timeout: int = 900) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout:
        info = instance_info(state["instance_id"])
        status = info.get("actual_status")
        host, port = info.get("ssh_host"), info.get("ssh_port")
        # prefer direct port mapping when present
        ports = (info.get("ports") or {}).get("22/tcp") or []
        if ports and info.get("public_ipaddr"):
            host, port = info["public_ipaddr"], int(ports[0]["HostPort"])
        if status == "running" and host and port:
            state.update({"ssh_host": host, "ssh_port": int(port), "gpu_name": info.get("gpu_name"), "num_gpus": info.get("num_gpus"), "dph_total": info.get("dph_total")})
            save_state(state)
            try:
                ssh_run(state, "test -f /workspace/.onstart_done", capture=True)
                print(f"ready: ssh -p {port} root@{host}  ({info.get('gpu_name')} x{info.get('num_gpus')}, ${info.get('dph_total', 0):.2f}/h)")
                return
            except subprocess.CalledProcessError:
                pass
        print(f"  status={status} host={host} port={port} elapsed={time.time()-t0:.0f}s", flush=True)
        time.sleep(15)
    sys.exit("timed out waiting for the instance; check `status` and `down` it if it never booted")


def cmd_status(a: argparse.Namespace) -> None:
    insts = vastai("show", "instances")
    mine = json.loads(STATE.read_text())["instance_id"] if STATE.exists() else None
    print(f"{'id':>10} {'gpu':16} {'n':>2} {'status':10} {'$/h':>6} {'label':12} {'ssh'}")
    for i in insts:
        mark = "*" if i["id"] == mine else " "
        print(f"{mark}{i['id']:>9} {str(i.get('gpu_name')):16} {str(i.get('num_gpus')):>2} {str(i.get('actual_status')):10} {i.get('dph_total', 0):>6.2f} {str(i.get('label')):12} {i.get('ssh_host')}:{i.get('ssh_port')}")
    if mine:
        print(f"(* = recorded in {STATE.relative_to(ROOT)})")


def cmd_ssh(a: argparse.Namespace) -> None:
    state = load_state()
    if a.remote:
        os.execvp("ssh", [*ssh_base(state), " ".join(a.remote)])
    os.execvp("ssh", ssh_base(state))


def cmd_push(a: argparse.Namespace) -> None:
    state = load_state()
    ssh_run(state, f"mkdir -p {REMOTE_ROOT}/outputs/steering")
    excl = list(PUSH_EXCLUDES)
    for item in PUSH_INCLUDES:
        src = ROOT / item
        if not src.exists():
            continue
        dst = f"root@{state['ssh_host']}:{REMOTE_ROOT}/{item}"
        if src.is_dir():
            ssh_run(state, f"mkdir -p {REMOTE_ROOT}/{item}")
            rsync(state, str(src) + "/", dst, excludes=excl, delete=a.full)
        else:
            rsync(state, str(src), dst)
    # job inputs: manifests, contrast sets, vectors (small); never generations from the laptop unless --full
    for sub in ("runs", "contrasts", "vectors"):
        src = ROOT / "outputs" / "steering" / sub
        if src.exists():
            ssh_run(state, f"mkdir -p {REMOTE_ROOT}/outputs/steering/{sub}")
            ex = [] if a.full else ["generations*.jsonl", "responses.shard*.jsonl", "judge_votes.jsonl", "coherence.jsonl"]
            rsync(state, str(src) + "/", f"root@{state['ssh_host']}:{REMOTE_ROOT}/outputs/steering/{sub}/", excludes=ex)
    print("push done")


def cmd_pull(a: argparse.Namespace) -> None:
    state = load_state()
    targets = a.paths or ["runs", "vectors", "contrasts", "logs"]
    for t in targets:
        rel = t if not t.startswith("outputs/steering/") else t[len("outputs/steering/"):]
        rel = rel.rstrip("/")
        local = ROOT / "outputs" / "steering" / rel
        local.mkdir(parents=True, exist_ok=True)
        try:
            rsync(state, f"root@{state['ssh_host']}:{REMOTE_ROOT}/outputs/steering/{rel}/", str(local) + "/")
        except subprocess.CalledProcessError as e:  # missing remote dir is fine
            print(f"  (skip {rel}: {e})")
    print("pull done")


def cmd_bootstrap(a: argparse.Namespace) -> None:
    state = load_state()
    models = a.models
    cmd = (
        f"cd {REMOTE_ROOT} && export PATH=$HOME/.local/bin:$PATH HF_HOME={REMOTE_HF} UV_CACHE_DIR=/workspace/.uv_cache "
        f"STEER_MODELS={shlex.quote(models)} HF_HUB_ENABLE_HF_TRANSFER=1 && mkdir -p outputs/steering/logs && "
        f"tmux new-session -d -s bootstrap 'bash steering_extension/remote/bootstrap.sh > outputs/steering/logs/bootstrap.log 2>&1'"
    )
    ssh_run(state, cmd)
    print("bootstrap running in tmux session `bootstrap`; follow with: vast tail --name bootstrap")
    if a.wait:
        while True:
            r = ssh_run(state, f"tail -n 3 {REMOTE_ROOT}/outputs/steering/logs/bootstrap.log 2>/dev/null; tmux has-session -t bootstrap 2>/dev/null && echo RUNNING || echo FINISHED", capture=True, check=False)
            print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "...", flush=True)
            if "FINISHED" in r.stdout:
                break
            time.sleep(30)
        r = ssh_run(state, f"tail -n 1 {REMOTE_ROOT}/outputs/steering/logs/bootstrap.log", capture=True, check=False)
        if "BOOTSTRAP_DONE" not in r.stdout:
            sys.exit("bootstrap did not finish cleanly; see outputs/steering/logs/bootstrap.log on the instance")
        print("bootstrap done")


def cmd_run(a: argparse.Namespace) -> None:
    state = load_state()
    n_gpu = int(state.get("num_gpus") or 1)
    shards = a.shards or max(1, n_gpu // a.gpus_per_shard)
    name = a.name or a.module.split(".")[-1]
    module_args = " ".join(shlex.quote(x) for x in a.args)
    env_prefix = "".join(f"{shlex.quote(kv)} " for kv in (a.env or []))
    cmd = (
        f"cd {REMOTE_ROOT} && mkdir -p outputs/steering/logs && "
        f"tmux new-session -d -s {shlex.quote(name)} "
        f"\"{env_prefix}JOB_NAME={shlex.quote(name)} NUM_SHARDS={shards} GPUS_PER_SHARD={a.gpus_per_shard} HF_HOME={REMOTE_HF} bash steering_extension/vast/run_shards.sh {a.module} {module_args} "
        f"> outputs/steering/logs/{name}.log 2>&1\""
    )
    ssh_run(state, cmd)
    print(f"launched `{name}`: {shards} shard(s) x {a.gpus_per_shard} GPU(s); logs outputs/steering/logs/{name}.log and {name}.shard*.log")


def cmd_tail(a: argparse.Namespace) -> None:
    state = load_state()
    name = a.name
    pat = f"{REMOTE_ROOT}/outputs/steering/logs/{name}*.log"
    ssh_run(state, f"for f in {pat}; do echo \"== $f\"; tail -n {a.lines} \"$f\"; done; tmux has-session -t {shlex.quote(name)} 2>/dev/null && echo '[still running]' || echo '[finished]'", check=False)


def cmd_jobs(a: argparse.Namespace) -> None:
    state = load_state()
    ssh_run(state, "tmux ls 2>/dev/null || echo 'no tmux sessions'; nvidia-smi --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader", check=False)


def cmd_down(a: argparse.Namespace) -> None:
    state = load_state()
    iid = state["instance_id"]
    info = instance_info(iid)
    if not a.yes:
        print(f"about to DESTROY instance {iid} ({info.get('gpu_name')} x{info.get('num_gpus')}, status {info.get('actual_status')}). All data on it is lost.")
        if input("type the instance id to confirm: ").strip() != str(iid):
            sys.exit("aborted")
    # The API can report success while the instance keeps running; retry and verify it is gone.
    for attempt in range(1, 6):
        vastai("destroy", "instance", str(iid), "--yes", raw=False, check=False)  # --yes: the CLI otherwise prompts and aborts silently
        time.sleep(20)
        if not instance_info(iid):
            STATE.rename(STATE_DIR / f"instance.{iid}.destroyed.json")
            print(f"instance {iid} destroyed (verified gone after attempt {attempt})")
            return
        print(f"  attempt {attempt}: instance {iid} still listed as {instance_info(iid).get('actual_status')}", flush=True)
    sys.exit(f"instance {iid} STILL LISTED after 5 destroy attempts: destroy it in the vast.ai console now (it is billing)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def offer_args(p):
        p.add_argument("--gpu", default=None, help="gpu_name, spaces as underscores (A100_PCIE, H100_NVL, RTX_4090)")
        p.add_argument("--num-gpus", type=int, default=1)
        p.add_argument("--min-vram", type=float, default=40, help="GB per GPU")
        p.add_argument("--disk", type=int, default=100, help="GB")
        p.add_argument("--min-reliability", type=float, default=0.97)
        p.add_argument("--min-down", type=float, default=300, help="Mbps")

    p = sub.add_parser("search"); offer_args(p); p.add_argument("--limit", type=int, default=15); p.set_defaults(fn=cmd_search)
    p = sub.add_parser("up"); offer_args(p)
    p.add_argument("--offer", type=int, default=None); p.add_argument("--image", default=DEFAULT_IMAGE); p.add_argument("--label", default="steer")
    p.add_argument("--timeout", type=int, default=900); p.set_defaults(fn=cmd_up)
    p = sub.add_parser("status"); p.set_defaults(fn=cmd_status)
    p = sub.add_parser("ssh"); p.add_argument("remote", nargs="*"); p.set_defaults(fn=cmd_ssh)
    p = sub.add_parser("push"); p.add_argument("--full", action="store_true", help="also push generations/votes and mirror-delete remote code dirs"); p.set_defaults(fn=cmd_push)
    p = sub.add_parser("pull"); p.add_argument("paths", nargs="*"); p.set_defaults(fn=cmd_pull)
    p = sub.add_parser("bootstrap"); p.add_argument("--models", default="Qwen/Qwen3.5-9B"); p.add_argument("--wait", action="store_true"); p.set_defaults(fn=cmd_bootstrap)
    p = sub.add_parser("run"); p.add_argument("module"); p.add_argument("args", nargs=argparse.REMAINDER)
    p.add_argument("--shards", type=int, default=None); p.add_argument("--gpus-per-shard", type=int, default=1); p.add_argument("--name", default=None)
    p.add_argument("--env", action="append", default=None, help="KEY=VALUE for the remote job (repeatable), e.g. STEER_USE_KERNELS=1"); p.set_defaults(fn=cmd_run)
    p = sub.add_parser("tail"); p.add_argument("--name", default="generate"); p.add_argument("--lines", type=int, default=5); p.set_defaults(fn=cmd_tail)
    p = sub.add_parser("jobs"); p.set_defaults(fn=cmd_jobs)
    p = sub.add_parser("down"); p.add_argument("--yes", action="store_true"); p.set_defaults(fn=cmd_down)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
