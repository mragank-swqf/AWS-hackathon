"""SQS job handlers for ingest and analysis."""

from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID

from app.agents.runner import run_analysis
from app.db.models import ImpactAnalysis
from app.db.session import get_session_factory
from app.services.ingest import ingest_policy, ingest_regulation

logger = logging.getLogger("regimpact.worker")


def _with_session(fn) -> None:
    session = get_session_factory()()
    try:
        fn(session)
        session.commit()
    except Exception:
        try:
            session.commit()
        except Exception:
            session.rollback()
        raise
    finally:
        session.close()


def handle_ingest_regulation(body: dict[str, Any]) -> None:
    document_id = UUID(body["document_id"])

    def work(session) -> None:
        ingest_regulation(session, document_id)

    _with_session(work)


def handle_ingest_policy(body: dict[str, Any]) -> None:
    document_id = UUID(body["document_id"])

    def work(session) -> None:
        ingest_policy(session, document_id)

    _with_session(work)


def handle_run_analysis(body: dict[str, Any]) -> None:
    analysis_id = UUID(body["analysis_id"])

    def work(session) -> None:
        if session.get(ImpactAnalysis, analysis_id) is None:
            time.sleep(2)
        run_analysis(session, analysis_id)

    _with_session(work)