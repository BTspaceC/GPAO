#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Case State 3.0 的确定性结构规则。"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "3.0"
PATCH_SCHEMA_VERSION = "3.1"
REQUIRED_FIELDS = {
    "schema_version",
    "case_id",
    "stage",
    "scope",
    "sources",
    "claims",
    "rubric_items",
    "constraints",
    "findings",
    "open_questions",
    "authorization_state",
    "history",
    "state_changes",
}
AUTHORITY_VALUES = {
    "official", "direct_feedback", "observed", "secondhand",
    "user_hypothesis", "unknown",
}
VERIFICATION_VALUES = {
    "verified", "supported", "contradicted", "evidence_insufficient",
}
CONFIDENCE_VALUES = {"high", "medium", "low", "unknown"}
AUTHORIZATION_STATES = {
    "PREVIEW_ONLY", "APPLY_APPROVED", "APPLIED_AND_REAUDIT_REQUIRED",
}
TRANSFER_STATES = {"false", "candidate", "confirmed"}
PATCH_OPERATIONS = {"append", "set", "update_item"}
LIST_FIELDS = {
    "sources", "claims", "rubric_items", "constraints", "findings",
    "open_questions", "history",
}
SCALAR_FIELDS = {"stage", "scope"}
ITEM_ID_FIELDS = (
    "source_id", "claim_id", "rubric_id", "constraint_id", "finding_id",
    "question_id", "event_id",
)

FIELD_OWNERS = {
    "/诊断": {"stage", "scope", "findings", "open_questions"},
    "/规划": {"rubric_items", "constraints", "findings", "open_questions"},
    "/审计": {"claims", "findings", "open_questions"},
    "/修改": {"authorization_state", "claims", "findings"},
    "/画像": {"claims"},
    "/复盘": {"claims", "history", "findings"},
}


def new_case_state(case_id: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "stage": "intake",
        "scope": {"teacher": None, "course": None, "assignment": None},
        "sources": [],
        "claims": [],
        "rubric_items": [],
        "constraints": [],
        "findings": [],
        "open_questions": [],
        "authorization_state": "PREVIEW_ONLY",
        "history": [],
        "state_changes": [],
    }


def new_state_patch(case_id: str, workflow: str, *, base_state_available: bool) -> dict:
    """Return the only state-update envelope emitted by V3.1 workflows."""

    if workflow not in FIELD_OWNERS:
        raise ValueError(f"unknown workflow: {workflow}")
    return {
        "schema_version": PATCH_SCHEMA_VERSION,
        "case_id": case_id,
        "workflow": workflow,
        "base_state_available": base_state_available,
        "operations": [],
    }


def _is_string_list(value) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def validate_state_patch(patch: dict) -> list[str]:
    """Validate a compact, closed-world Case State Patch 3.1 object."""

    errors: list[str] = []
    required = {
        "schema_version", "case_id", "workflow", "base_state_available",
        "operations",
    }
    missing = required - set(patch)
    extras = set(patch) - required
    if missing:
        errors.append(f"missing patch fields: {', '.join(sorted(missing))}")
    if extras:
        errors.append(f"unexpected patch fields: {', '.join(sorted(extras))}")
    if patch.get("schema_version") != PATCH_SCHEMA_VERSION:
        errors.append("patch schema_version must be 3.1")
    if not isinstance(patch.get("case_id"), str) or not patch.get("case_id", "").strip():
        errors.append("patch case_id must be a non-empty string")
    workflow = patch.get("workflow")
    if workflow not in FIELD_OWNERS:
        errors.append("patch workflow is invalid")
    if type(patch.get("base_state_available")) is not bool:
        errors.append("base_state_available must be a boolean")
    operations = patch.get("operations")
    if not isinstance(operations, list):
        return errors + ["operations must be a list"]

    for index, operation in enumerate(operations):
        label = f"operation {index}"
        if not isinstance(operation, dict):
            errors.append(f"{label} must be an object")
            continue
        op = operation.get("op")
        field = operation.get("field")
        if op not in PATCH_OPERATIONS:
            errors.append(f"{label} has invalid op")
            continue
        if field not in LIST_FIELDS | SCALAR_FIELDS:
            errors.append(f"{label} has invalid field")
        if not isinstance(operation.get("reason"), str) or not operation.get("reason", "").strip():
            errors.append(f"{label} requires reason")
        if not _is_string_list(operation.get("evidence_ids")):
            errors.append(f"{label} requires non-empty evidence_ids")

        if op == "append":
            expected = {"op", "field", "value", "reason", "evidence_ids"}
            if field not in LIST_FIELDS:
                errors.append(f"{label} append requires a list field")
        elif op == "set":
            expected = {"op", "field", "value", "reason", "evidence_ids"}
            if field not in SCALAR_FIELDS:
                errors.append(f"{label} set requires a scalar field")
            if patch.get("base_state_available") is False and field not in {"stage", "scope"}:
                errors.append(f"{label} cannot set existing state without a base state")
        else:
            expected = {
                "op", "field", "item_id", "before", "updates", "reason",
                "evidence_ids",
            }
            if field not in LIST_FIELDS:
                errors.append(f"{label} update_item requires a list field")
            if patch.get("base_state_available") is not True:
                errors.append(f"{label} update_item requires an available base state")
            if not isinstance(operation.get("item_id"), str) or not operation.get("item_id", "").strip():
                errors.append(f"{label} requires item_id")
            if not isinstance(operation.get("before"), dict) or not operation.get("before"):
                errors.append(f"{label} requires explicit non-empty before values")
            if not isinstance(operation.get("updates"), dict) or not operation.get("updates"):
                errors.append(f"{label} requires non-empty updates")

        missing_operation = expected - set(operation)
        extra_operation = set(operation) - expected
        if missing_operation:
            errors.append(
                f"{label} missing fields: {', '.join(sorted(missing_operation))}"
            )
        if extra_operation:
            errors.append(
                f"{label} unexpected fields: {', '.join(sorted(extra_operation))}"
            )
    return errors


def _find_item(items: list, item_id: str):
    for item in items:
        if isinstance(item, dict) and any(item.get(key) == item_id for key in ITEM_ID_FIELDS):
            return item
    return None


def apply_state_patch(state: dict, patch: dict) -> dict:
    """Validate and apply a State Patch without inventing unavailable before-values."""

    state_errors = validate_case_state(state)
    patch_errors = validate_state_patch(patch)
    if state_errors or patch_errors:
        raise ValueError("; ".join(state_errors + patch_errors))
    if state["case_id"] != patch["case_id"]:
        raise ValueError("patch case_id does not match state")
    if patch["base_state_available"] is False and state != new_case_state(state["case_id"]):
        raise ValueError("base_state_available=false can only initialize a new default state")

    source_ids = {
        source.get("source_id")
        for source in state.get("sources", [])
        if isinstance(source, dict) and source.get("source_id")
    }
    source_ids.update(
        operation["value"].get("source_id")
        for operation in patch["operations"]
        if operation.get("op") == "append"
        and operation.get("field") == "sources"
        and isinstance(operation.get("value"), dict)
        and operation["value"].get("source_id")
    )
    for operation in patch["operations"]:
        unknown_ids = set(operation["evidence_ids"]) - source_ids
        if unknown_ids:
            raise ValueError(f"unknown evidence_ids: {sorted(unknown_ids)}")

    result = deepcopy(state)
    workflow = patch["workflow"]
    for operation in patch["operations"]:
        field = operation["field"]
        if operation["op"] == "append":
            updated = deepcopy(result[field])
            updated.append(deepcopy(operation["value"]))
        elif operation["op"] == "set":
            updated = deepcopy(operation["value"])
        else:
            updated = deepcopy(result[field])
            item = _find_item(updated, operation["item_id"])
            if item is None:
                raise KeyError(f"item not found: {operation['item_id']}")
            for key, expected in operation["before"].items():
                if item.get(key) != expected:
                    raise ValueError(
                        f"before-value mismatch for {operation['item_id']}.{key}"
                    )
            item.update(deepcopy(operation["updates"]))
        apply_state_change(
            result,
            workflow,
            field,
            updated,
            reason=operation["reason"],
            evidence_ids=operation["evidence_ids"],
        )
    return result


def validate_case_state(state: dict) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_FIELDS - set(state)
    if missing:
        errors.append(f"missing fields: {', '.join(sorted(missing))}")
    if state.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 3.0")
    if state.get("authorization_state") not in AUTHORIZATION_STATES:
        errors.append("invalid authorization_state")
    for field in ("sources", "claims", "rubric_items", "constraints", "findings", "open_questions", "history", "state_changes"):
        if field in state and not isinstance(state[field], list):
            errors.append(f"{field} must be a list")
    for claim in state.get("claims", []):
        if claim.get("authority") not in AUTHORITY_VALUES:
            errors.append(f"claim {claim.get('claim_id', '?')} has invalid authority")
        if claim.get("verification") not in VERIFICATION_VALUES:
            errors.append(f"claim {claim.get('claim_id', '?')} has invalid verification")
        if claim.get("confidence") not in CONFIDENCE_VALUES:
            errors.append(f"claim {claim.get('claim_id', '?')} has invalid confidence")
        if claim.get("transfer_state", "false") not in TRANSFER_STATES:
            errors.append(f"claim {claim.get('claim_id', '?')} has invalid transfer_state")
    return errors


def migrate_legacy_evidence(entry: dict) -> dict:
    """保守导入旧证据；没有原始证据时绝不从标签推断新等级。"""
    migrated = deepcopy(entry)
    legacy_label = migrated.pop("level", migrated.get("legacy_label"))
    migrated["legacy_label"] = legacy_label
    migrated["authority"] = "unknown"
    migrated["verification"] = "evidence_insufficient"
    migrated["confidence"] = "unknown"
    migrated.setdefault("transfer_state", "false")
    return migrated


def apply_state_change(
    state: dict,
    workflow: str,
    field: str,
    value,
    *,
    reason: str = "",
    evidence_ids: list[str] | None = None,
) -> dict:
    if workflow not in FIELD_OWNERS:
        raise ValueError(f"unknown workflow: {workflow}")
    if field not in REQUIRED_FIELDS - {"schema_version", "case_id"}:
        raise ValueError(f"unknown or immutable field: {field}")
    if field == "sources":
        before_sources = state.get("sources", [])
        if not isinstance(value, list) or value[: len(before_sources)] != before_sources:
            raise PermissionError("sources are append-only; preserve existing records")
    cross_scope = field not in FIELD_OWNERS[workflow]
    if cross_scope and (not reason or not evidence_ids):
        raise PermissionError("cross-field changes require reason and evidence_ids")
    before = deepcopy(state.get(field))
    state[field] = value
    state["state_changes"].append({
        "workflow": workflow,
        "field": field,
        "before": before,
        "after": deepcopy(value),
        "reason": reason or "primary field update",
        "evidence_ids": list(evidence_ids or []),
        "changed_at": datetime.now(timezone.utc).isoformat(),
    })
    return state


def preference_transfer_state(evidence: list[dict], *, explicitly_confirmed: bool = False) -> str:
    direct = [e for e in evidence if e.get("authority") in {"direct_feedback", "observed"}]
    courses = {e.get("course") for e in direct if e.get("course")}
    templates = {e.get("template_id") for e in direct if e.get("template_id")}
    semantic_keys = {e.get("semantic_key") for e in direct if e.get("semantic_key")}
    has_contradiction = any(e.get("verification") == "contradicted" for e in evidence)
    template_reuse_only = len(templates) == 1 and len(direct) > 1
    candidate = (
        len(direct) >= 2
        and len(courses) >= 2
        and len(semantic_keys) == 1
        and not has_contradiction
        and not template_reuse_only
    )
    if candidate and explicitly_confirmed:
        return "confirmed"
    if candidate:
        return "candidate"
    return "false"


def transition_authorization(
    current: str,
    target: str,
    *,
    explicit_user_approval: bool = False,
    write_succeeded: bool = False,
    reaudit_completed: bool = False,
) -> str:
    """执行唯一允许的授权转换；复审完成后回到安全的预览态。"""
    if current not in AUTHORIZATION_STATES or target not in AUTHORIZATION_STATES:
        raise ValueError("invalid authorization state")
    if current == target:
        return current
    if current == "PREVIEW_ONLY" and target == "APPLY_APPROVED":
        if not explicit_user_approval:
            raise PermissionError("explicit user approval is required")
        return target
    if current == "APPLY_APPROVED" and target == "APPLIED_AND_REAUDIT_REQUIRED":
        if not write_succeeded:
            raise PermissionError("successful write is required")
        return target
    if current == "APPLIED_AND_REAUDIT_REQUIRED" and target == "PREVIEW_ONLY":
        if not reaudit_completed:
            raise PermissionError("reaudit completion is required")
        return target
    raise PermissionError(f"forbidden authorization transition: {current} -> {target}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate-patch")
    validate.add_argument("patch", type=Path)
    apply_parser = subparsers.add_parser("apply-patch")
    apply_parser.add_argument("--state", type=Path, required=True)
    apply_parser.add_argument("--patch", type=Path, required=True)
    apply_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    patch = json.loads(args.patch.read_text(encoding="utf-8"))
    errors = validate_state_patch(patch)
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False))
        return 1
    if args.command == "validate-patch":
        print(json.dumps({"valid": True}, ensure_ascii=False))
        return 0
    state = json.loads(args.state.read_text(encoding="utf-8"))
    result = apply_state_patch(state, patch)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"valid": True, "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
