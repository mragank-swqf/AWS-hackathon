from uuid import uuid4

from app.agents.contracts import ActionPlanOutput, GapOutput, RequirementsOutput
from app.agents.prompts import fence
from app.enums import GapStatus
from app.services.local_ai import local_json
from demo.documents import GRIEVANCE_PAGES, KYC_PAGES, REGULATION_PAGES


def test_local_extract_splits_payflow_shall_clauses():
    chunk_id = uuid4()
    prompt = fence(f"[chunk_id={chunk_id} pages=1-3 clause=3.1]\n" + "\n".join(REGULATION_PAGES))
    payload = local_json(prompt, RequirementsOutput)
    output = RequirementsOutput.model_validate(payload)
    clauses = [item.clause_number for item in output.requirements]
    assert clauses == ["3.1", "3.2", "3.3", "4.1", "5.1", "6.1"]
    assert any("48-hour" in item.requirement_text for item in output.requirements)


def test_local_gap_maps_payflow_policies():
    policy_id = uuid4()
    grievance = fence(f"[chunk_id={policy_id} pages=1-2 clause=2]\n" + "\n".join(GRIEVANCE_PAGES))
    kyc_id = uuid4()
    kyc = fence(f"[chunk_id={kyc_id} pages=1-1 clause=1]\n" + "\n".join(KYC_PAGES))

    officer = local_json(
        "Requirement: 3.1 Every payment aggregator shall appoint a grievance officer. compliant or partial\n"
        + grievance,
        GapOutput,
    )
    assert officer["gap_status"] == GapStatus.COMPLIANT.value

    missing_48h = local_json(
        "Requirement: 3.3 The grievance redressal process shall include a "
        "48-hour escalation path. compliant or partial\n" + grievance,
        GapOutput,
    )
    assert missing_48h["gap_status"] == GapStatus.NON_COMPLIANT.value
    assert "48-hour" in missing_48h["explanation"]

    kyc_gap = local_json(
        "Requirement: 4.1 Every payment aggregator shall maintain a documented KYC policy. compliant or partial\n"
        + kyc,
        GapOutput,
    )
    assert kyc_gap["gap_status"] == GapStatus.PARTIAL.value

    complaints = local_json(
        "Requirement: 5.1 Every payment aggregator shall publish quarterly "
        "complaint data on its website. compliant or partial\n" + grievance,
        GapOutput,
    )
    assert complaints["gap_status"] == GapStatus.INSUFFICIENT_EVIDENCE.value

    action = local_json(
        "Requirement: 3.3 The grievance redressal process shall include a 48-hour escalation path.",
        ActionPlanOutput,
    )
    assert "48-hour" in action["actions"][0]["title"]
