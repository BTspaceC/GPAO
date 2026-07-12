# -*- coding: utf-8 -*-
from enum import Enum


class EntailmentLabel(Enum):
    ENTAILED = "ENTAILED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    OVERCLAIM = "OVERCLAIM"
    MISATTRIBUTED = "MISATTRIBUTED"
    UNVERIFIED_AS_FACT = "UNVERIFIED_AS_FACT"


EXPECTED_GROUPS = [
    "事实与引用",
    "统计结论",
    "教师偏好",
    "工作流冲突"
]


# A dangerous false negative occurs when a case that should be rejected or
# qualified is accepted as entailed. Confusing two non-entailed labels is still
# inaccurate, but it is not this specific safety failure.
DANGEROUS_EXPECTED_LABELS = frozenset(
    label.value for label in EntailmentLabel if label is not EntailmentLabel.ENTAILED
)


def is_dangerous_false_negative(expected_label, predicted_label):
    """Return True when an unsafe claim was incorrectly accepted as entailed."""
    return (
        expected_label in DANGEROUS_EXPECTED_LABELS
        and predicted_label == EntailmentLabel.ENTAILED.value
    )
