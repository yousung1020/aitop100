"""지식 베이스 로더 모듈 (loader.py)

docs/KNOWLEDGE_BASE.md 원문 및 정형화된 정책 규칙을 메모리에 캐싱하고 조회하는 인터페이스를 제공합니다.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any

from app.knowledge.rules import (
    GYODONG_POLICY,
    GAETMAEUL_POLICY,
    COMMON_POLICIES,
    VillagePolicy,
)


@lru_cache(maxsize=1)
def load_raw_knowledge_base() -> str:
    """docs/KNOWLEDGE_BASE.md 원본 마크다운 파일을 로드하여 반환"""
    project_root = Path(__file__).resolve().parent.parent.parent
    kb_path = project_root / "docs" / "KNOWLEDGE_BASE.md"

    if kb_path.exists():
        return kb_path.read_text(encoding="utf-8")
    return ""


def get_village_policies() -> Dict[str, VillagePolicy]:
    """마을별 정책 딕셔너리 반환"""
    return {
        "gyodong": GYODONG_POLICY,
        "gaetmaeul": GAETMAEUL_POLICY,
    }


def get_common_policies():
    """공통 정책 세트 반환"""
    return COMMON_POLICIES
