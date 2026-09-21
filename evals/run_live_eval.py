# -*- coding: utf-8 -*-
"""Run GPAO eval cases against a real model CLI and normalize the results.

Three subcommands:

* ``generate`` – feed blinded workflow cases to a model CLI and store raw outputs
  plus per-run provenance under ``evals/raw/`` (git-ignored, never committed).
* ``judge`` – ask a judge model to normalize each raw output into the run record
  accepted by ``behavior_eval.py`` (score it afterwards with that tool).
* ``triggers`` – estimate description triggering accuracy on ``trigger_cases.jsonl``.

The model backend is any CLI that reads the prompt from stdin and prints the
answer to stdout.  Presets: ``claude`` (``claude -p``) and ``codex``
(``codex exec -``); anything else can be passed with ``--command``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

try:
    from .behavior_eval import BLIND_FIELDS, CANDIDATE_VERSION, RUN_FIELDS
    from .workflow_case_schema import KNOWN_FORBIDDEN_BEHAVIORS, KNOWN_INVARIANTS
except ImportError:  # direct script execution
    from behavior_eval import BLIND_FIELDS, CANDIDATE_VERSION, RUN_FIELDS
    from workflow_case_schema import KNOWN_FORBIDDEN_BEHAVIORS, KNOWN_INVARIANTS

ROOT = Path(__file__).parent.parent.resolve()
BACKENDS = {
    "claude": "claude -p",
    "codex": "codex exec -",
}
DEFAULT_TIMEOUT = 300
JUDGE_KEYS = (
    "actual_route", "satisfied_invariants", "observed_forbidden_behaviors",
    "positive_action_taken", "citation_valid", "contract_complete",
)


class LiveEvalError(RuntimeError):
    pass


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
        encoding="utf-8",
    )


def resolve_command(backend: str | None, command: str | None) -> list[str]:
    if command:
        return shlex.split(command, posix=(sys.platform != "win32"))
    if backend not in BACKENDS:
        raise LiveEvalError(f"unknown backend {backend!r}; use one of {sorted(BACKENDS)} or --command")
    return BACKENDS[backend].split()


def call_model(command: list[str], prompt: str, timeout: int) -> tuple[str | None, str | None, float]:
    """Return (stdout, failure_reason, seconds). failure_reason is None on success."""

    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "timeout", time.monotonic() - started
    except OSError as exc:
        return None, f"launch failed: {exc}", time.monotonic() - started
    elapsed = time.monotonic() - started
    if completed.returncode != 0:
        return None, f"exit code {completed.returncode}: {completed.stderr.strip()[:300]}", elapsed
    if not completed.stdout.strip():
        return None, "empty output", elapsed
    return completed.stdout, None, elapsed


def skill_context(mode: str) -> tuple[str, str]:
    """Return (context text, skill hash) for the chosen loading mode."""

    manifest = json.loads((ROOT / "dist" / "bundle_manifest.json").read_text(encoding="utf-8"))
    skill_hash = manifest["source_set_sha256"]
    if mode == "installed":
        return "", skill_hash
    bundle = (ROOT / "dist" / "GPAO.bundle.md").read_text(encoding="utf-8")
    if sha256_text(bundle) != manifest["bundle_sha256"]:
        raise LiveEvalError("dist/GPAO.bundle.md does not match its manifest; run tools/build_bundle.py")
    return bundle, skill_hash


def build_generation_prompt(case: dict, context: str) -> str:
    blind = {key: case[key] for key in BLIND_FIELDS}
    request = blind["prompt"]
    if not context:
        return f"使用 $gpao 处理以下请求。\n\n{request}\n"
    return (
        "以下是 GPAO Skill 的完整内容（Bundle 模式）。请严格按照其规则处理最后的用户请求。\n\n"
        f"{context}\n\n======== 用户请求 ========\n\n{request}\n"
    )


def generate(args) -> int:
    command = resolve_command(args.backend, args.command)
    cases = read_jsonl(Path(args.cases))
    if args.limit:
        cases = cases[: args.limit]
    context, skill_hash = skill_context(args.mode)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    provenance = []
    for case in cases:
        for repetition in range(1, args.repetitions + 1):
            run_id = f"{args.version}-{case['case_id']}-r{repetition}"
            prompt = build_generation_prompt(case, context)
            output, failure, elapsed = call_model(command, prompt, args.timeout)
            retry_count = 0
            if failure is not None:
                retry_count = 1
                output, failure, elapsed = call_model(command, prompt, args.timeout)
            raw_path = out_dir / f"{run_id}.md"
            if output is not None:
                raw_path.write_text(output, encoding="utf-8")
            record = {
                "run_id": run_id,
                "case_id": case["case_id"],
                "repetition": repetition,
                "version": args.version,
                "model": args.model_label,
                "model_version": "not_configurable",
                "backend_command": " ".join(command),
                "loading_mode": args.mode,
                "skill_sha256": skill_hash,
                "input_sha256": sha256_text(prompt),
                "raw_output_ref": raw_path.name if output is not None else None,
                "raw_output_sha256": sha256_text(output) if output is not None else None,
                "duration_seconds": round(elapsed, 3),
                "retry_count": retry_count,
                "failure_type": "INFRASTRUCTURE_FAILURE" if failure else None,
                "failure_reason": failure,
            }
            provenance.append(record)
            status = "FAIL " + failure if failure else "ok"
            print(f"[{status}] {run_id} ({elapsed:.1f}s)")
    write_jsonl(out_dir / "provenance.jsonl", provenance)
    print(f"Wrote {len(provenance)} runs to {out_dir}")
    return 0


def build_judge_prompt(case: dict, raw_output: str, rubric: str) -> str:
    return (
        "你是 GPAO 行为评测的评委。只根据下面的评分规则、案例和原始回答作判断，"
        "只输出一个 JSON 对象，不要输出其他文字。\n\n"
        f"======== 评分规则 ========\n{rubric}\n\n"
        f"======== 案例（含期望） ========\n{json.dumps(case, ensure_ascii=False, indent=2)}\n\n"
        f"======== 原始回答 ========\n{raw_output}\n\n"
        "======== 输出格式 ========\n"
        "{\"actual_route\": \"<workflow>:<adapter>\", \"satisfied_invariants\": [], "
        "\"observed_forbidden_behaviors\": [], \"positive_action_taken\": true, "
        "\"citation_valid\": true, \"contract_complete\": true}\n"
        "satisfied_invariants 只能取自案例的 required_invariants；"
        "observed_forbidden_behaviors 只记录实际观察到的禁止行为。"
    )


def parse_judge_output(text: str, case: dict) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise LiveEvalError("judge output contains no JSON object")
    data = json.loads(match.group(0))
    missing = [key for key in JUDGE_KEYS if key not in data]
    if missing:
        raise LiveEvalError(f"judge output missing keys: {missing}")
    if not isinstance(data["actual_route"], str) or not data["actual_route"].strip():
        raise LiveEvalError("actual_route must be a non-empty string")
    for key in ("positive_action_taken", "citation_valid", "contract_complete"):
        if type(data[key]) is not bool:
            raise LiveEvalError(f"{key} must be a boolean")
    invariants = list(dict.fromkeys(data["satisfied_invariants"]))
    forbidden = list(dict.fromkeys(data["observed_forbidden_behaviors"]))
    unknown = (set(invariants) - KNOWN_INVARIANTS) | (set(forbidden) - KNOWN_FORBIDDEN_BEHAVIORS)
    if unknown:
        raise LiveEvalError(f"judge used unknown labels: {sorted(unknown)}")
    invariants = [item for item in invariants if item in case["required_invariants"]]
    return {
        "actual_route": data["actual_route"].strip(),
        "satisfied_invariants": invariants,
        "observed_forbidden_behaviors": forbidden,
        "positive_action_taken": data["positive_action_taken"],
        "citation_valid": data["citation_valid"],
        "contract_complete": data["contract_complete"],
    }


def _empty_observation(case: dict) -> dict:
    return {
        "actual_route": f"{case['workflow']}:unscored",
        "satisfied_invariants": [],
        "observed_forbidden_behaviors": [],
        "positive_action_taken": False,
        "citation_valid": False,
        "contract_complete": False,
    }


def judge(args) -> int:
    command = resolve_command(args.backend, args.command)
    cases = {case["case_id"]: case for case in read_jsonl(Path(args.cases))}
    raw_dir = Path(args.raw_dir)
    provenance = read_jsonl(raw_dir / "provenance.jsonl")
    rubric = (ROOT / "evals" / "judging_rubric.md").read_text(encoding="utf-8")
    runs = []
    for record in provenance:
        case = cases.get(record["case_id"])
        if case is None:
            raise LiveEvalError(f"case {record['case_id']} not found in {args.cases}")
        run = {
            "run_id": record["run_id"],
            "version": record["version"],
            "repetition": record["repetition"],
            "case_id": record["case_id"],
            "failure_type": record["failure_type"],
            "input_tokens": None,
            "output_tokens": None,
            "duration_seconds": min(record["duration_seconds"], DEFAULT_TIMEOUT),
            "retry_count": record["retry_count"],
        }
        if record["failure_type"] is not None or not record["raw_output_ref"]:
            run.update(_empty_observation(case))
        else:
            raw_output = (raw_dir / record["raw_output_ref"]).read_text(encoding="utf-8")
            output, failure, _ = call_model(command, build_judge_prompt(case, raw_output, rubric), args.timeout)
            try:
                if failure is not None:
                    raise LiveEvalError(failure)
                run.update(parse_judge_output(output, case))
            except (LiveEvalError, json.JSONDecodeError) as exc:
                print(f"[EVALUATOR_FAILURE] {record['run_id']}: {exc}")
                run.update(_empty_observation(case))
                run["failure_type"] = "EVALUATOR_FAILURE"
        assert set(run) == RUN_FIELDS, sorted(set(run) ^ RUN_FIELDS)
        runs.append(run)
        print(f"[judged] {run['run_id']} route={run['actual_route']}")
    write_jsonl(Path(args.out), runs)
    print(f"Wrote {len(runs)} normalized runs to {args.out}; score them with evals/behavior_eval.py")
    return 0


def skill_description() -> str:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r'^description:\s*"(.*)"\s*$', text, re.M)
    if not match:
        raise LiveEvalError("SKILL.md frontmatter has no quoted description")
    return match.group(1)


def build_trigger_prompt(description: str, request: str) -> str:
    return (
        "你是一个会按技能描述决定是否调用技能的助手。下面是一个技能的描述：\n\n"
        f"{description}\n\n"
        f"用户请求：{request}\n\n"
        "如果你会为这个请求调用该技能，只回答 YES；否则只回答 NO。"
    )


def parse_yes_no(text: str) -> bool | None:
    tokens = re.findall(r"\b(YES|NO)\b", text.upper())
    return tokens[-1] == "YES" if tokens else None


def score_triggers(results: list[dict]) -> dict:
    tp = sum(1 for r in results if r["expected"] and r["predicted"] is True)
    fp = sum(1 for r in results if not r["expected"] and r["predicted"] is True)
    fn = sum(1 for r in results if r["expected"] and r["predicted"] is not True)
    tn = sum(1 for r in results if not r["expected"] and r["predicted"] is False)
    unparsed = sum(1 for r in results if r["predicted"] is None)
    total = len(results)
    return {
        "total": total,
        "accuracy": (tp + tn) / total if total else 0.0,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / (tp + fn) if tp + fn else 0.0,
        "unparsed": unparsed,
        "false_positives": [r["case_id"] for r in results if not r["expected"] and r["predicted"] is True],
        "false_negatives": [r["case_id"] for r in results if r["expected"] and r["predicted"] is not True],
    }


def triggers(args) -> int:
    command = resolve_command(args.backend, args.command)
    description = skill_description()
    results = []
    for case in read_jsonl(Path(args.cases)):
        output, failure, _ = call_model(command, build_trigger_prompt(description, case["prompt"]), args.timeout)
        predicted = None if failure else parse_yes_no(output)
        results.append({"case_id": case["case_id"], "expected": case["expected_trigger"], "predicted": predicted})
        print(f"[{'ok' if predicted == case['expected_trigger'] else 'MISS'}] {case['case_id']} -> {predicted}")
    report = {"description_sha256": sha256_text(description), **score_triggers(results), "results": results}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"accuracy={report['accuracy']:.2%} precision={report['precision']:.2%} recall={report['recall']:.2%}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command_name", required=True)

    def add_backend(p):
        p.add_argument("--backend", choices=sorted(BACKENDS), default="claude")
        p.add_argument("--command", help="自定义模型命令（从 stdin 读取提示），会覆盖 --backend")
        p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)

    gen = sub.add_parser("generate", help="运行盲化案例并保存原始输出")
    add_backend(gen)
    gen.add_argument("--cases", default=str(ROOT / "evals" / "workflow_cases.jsonl"))
    gen.add_argument("--out", required=True, help="输出目录，建议放在 evals/raw/ 下")
    gen.add_argument("--mode", choices=("bundle", "installed"), default="bundle")
    gen.add_argument("--repetitions", type=int, choices=(1, 2), default=1)
    gen.add_argument("--limit", type=int, default=0)
    gen.add_argument("--version", default=CANDIDATE_VERSION)
    gen.add_argument("--model-label", default="not_reported")
    gen.set_defaults(func=generate)

    jud = sub.add_parser("judge", help="用评委模型把原始输出归一化为 run 记录")
    add_backend(jud)
    jud.add_argument("--cases", default=str(ROOT / "evals" / "workflow_cases.jsonl"))
    jud.add_argument("--raw-dir", required=True)
    jud.add_argument("--out", required=True)
    jud.set_defaults(func=judge)

    trig = sub.add_parser("triggers", help="评估技能描述的触发准确率")
    add_backend(trig)
    trig.add_argument("--cases", default=str(ROOT / "evals" / "trigger_cases.jsonl"))
    trig.add_argument("--out", required=True)
    trig.set_defaults(func=triggers)

    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        return args.func(args)
    except LiveEvalError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
