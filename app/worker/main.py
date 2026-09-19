"""SQS worker. Ingestion and analysis handlers are wired in later stages.

Unhandled jobs stay on the queue (visibility is extended) so a restart does not
lose work (spec 06 AC-004).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from app.services.queue import (
    JOB_INGEST_POLICY,
    JOB_INGEST_REGULATION,
    JOB_RUN_ANALYSIS,
    JOB_RUN_PORTFOLIO,
    JOB_SYNC_CORPUS,
    delete_job,
    enqueue_sync_corpus,
    extend_visibility,
    receive_jobs,
)
from app.worker.handlers import (
    handle_ingest_policy,
    handle_ingest_regulation,
    handle_run_analysis,
    handle_run_portfolio,
    handle_sync_corpus,
)

logger = logging.getLogger("regimpact.worker")

HANDLERS: dict[str, Callable[[dict[str, Any]], None]] = {
    JOB_INGEST_REGULATION: handle_ingest_regulation,
    JOB_INGEST_POLICY: handle_ingest_policy,
    JOB_RUN_ANALYSIS: handle_run_analysis,
    JOB_SYNC_CORPUS: handle_sync_corpus,
    JOB_RUN_PORTFOLIO: handle_run_portfolio,
}

UNHANDLED_VISIBILITY_SECONDS = 12 * 60 * 60


def process_once(wait_seconds: int = 20) -> int:
    messages = receive_jobs(wait_seconds=wait_seconds)
    handled = 0
    for message in messages:
        job_type = message.body.get("job_type")
        handler = HANDLERS.get(job_type)
        if handler is None:
            logger.info("No handler for %s; leaving message on queue", job_type)
            extend_visibility(message.receipt_handle, UNHANDLED_VISIBILITY_SECONDS)
            continue
        try:
            handler(message.body)
            delete_job(message.receipt_handle)
            handled += 1
        except Exception:
            logger.exception("Job failed: %s", job_type)
            # Stop SQS from immediately replaying a throttled Bedrock job.
            extend_visibility(message.receipt_handle, 300)
    return handled


SYNC_EVERY_SECONDS = 6 * 60 * 60


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    logger.info(
        "Worker started. Waiting for jobs (%s, %s, %s, %s, %s).",
        JOB_INGEST_REGULATION,
        JOB_INGEST_POLICY,
        JOB_RUN_ANALYSIS,
        JOB_SYNC_CORPUS,
        JOB_RUN_PORTFOLIO,
    )
    last_sync = 0.0
    while True:
        try:
            now = time.time()
            if now - last_sync >= SYNC_EVERY_SECONDS:
                try:
                    enqueue_sync_corpus()
                    last_sync = now
                    logger.info("Queued background RBI corpus sync")
                except Exception:
                    logger.exception("Could not queue corpus sync")
                    last_sync = now
            process_once()
        except Exception:
            logger.exception("Receive loop failed")
            time.sleep(5)


if __name__ == "__main__":
    run()
