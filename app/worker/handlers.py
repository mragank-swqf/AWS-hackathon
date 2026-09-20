"""SQS job handlers for ingest and analysis."""

from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID

from app.agents.runner import run_analysis
from app.db.models import ImpactAnalysis, PortfolioRun
from app.db.session import get_session_factory
from app.services.ingest import ingest_policy, ingest_regulation
from app.services.portfolio import run_portfolio
from app.services.regulatory_ingest import sync_rbi_corpus

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


def handle_sync_corpus(body: dict[str, Any]) -> None:
    def work(session) -> None:
        sync_rbi_corpus(session)

    _with_session(work)


def handle_run_portfolio(body: dict[str, Any]) -> None:
    run_id = UUID(body["run_id"])

    def work(session) -> None:
        if session.get(PortfolioRun, run_id) is None:
            time.sleep(2)
        run_portfolio(session, run_id)

    _with_session(work)