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
