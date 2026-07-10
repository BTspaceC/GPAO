#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Case State 3.0 的确定性结构规则。"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

SCHEMA_VERSION = "3.0"
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
