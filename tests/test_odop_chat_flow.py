"""
test_odop_chat_flow.py — Test suite for LLM-scored ODOP 100-point fixed benchmarking and end-to-end chat flow.
"""

import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from backend.app.main import app
from backend.app.routers.onboarding import (
    _generate_odop_synergy,
    clean_for_bhashini_tts,
)
from backend.app.core.machinery_matcher import calculate_intelligent_turnover

client = TestClient(app)


def test_bhashini_cleaner_removes_punctuation_and_symbols():
    """Ensure clean_for_bhashini_tts converts symbols and strips awkward punctuation."""
    raw_hi = "क्या आप जानते हैं? आपको ₹10 लाख पर 35% सब्सिडी मिलेगी: 1. ODOP से जुड़ें / 2. मूल विचार!"
    cleaned = clean_for_bhashini_tts(raw_hi, "hi")
    
    assert "₹" not in cleaned
    assert "%" not in cleaned
    assert ":" not in cleaned
    assert "?" not in cleaned
    assert "/" not in cleaned
    assert "1." not in cleaned
    assert "2." not in cleaned
    assert "रुपये" in cleaned
    assert "प्रतिशत" in cleaned
    assert "पहला विकल्प" in cleaned
    assert "दूसरा विकल्प" in cleaned


def test_odop_synergy_high_alignment():
    """Test agro-processing business matching district ODOP receives high benchmark score (>=65)."""
    synergy = _generate_odop_synergy(
        user_business="Tomato Puree and Ketchup Processing Unit",
        sector="food_processing",
        state="Maharashtra",
        district="Pune",
        language="hi",
    )
    assert synergy is not None
    score = synergy["alignment_score"]
    assert 65 <= score <= 100, f"Expected high score >= 65, got {score}"
    assert synergy["verdict_key"] == "recommended"
    assert "synergy_pillars" in synergy
    assert "product_innovation" in synergy["synergy_pillars"]
    assert "local_sourcing" in synergy["synergy_pillars"]
    assert "financial_incentives" in synergy["synergy_pillars"]


def test_odop_synergy_low_alignment():
    """Test non-overlapping service business receives low benchmark score (<50) and honest recommendation."""
    synergy = _generate_odop_synergy(
        user_business="Smart Phone and Laptop Repair Center",
        sector="repair",
        state="Maharashtra",
        district="Sangli",
        language="hi",
    )
    assert synergy is not None
    score = synergy["alignment_score"]
    assert score < 55, f"Expected low score < 55, got {score}"
    assert synergy["verdict_key"] == "not_recommended"
    assert "PMEGP" in synergy["mira_recommendation"] or "Standard" in synergy["mira_recommendation"] or "Continue" in synergy["mira_recommendation"]


def test_odop_fallback_on_llm_failure():
    """Verify that when LLM call fails or times out, deterministic statutory benchmark runs gracefully."""
    with patch("backend.app.routers.onboarding.chat_service._call_llm_chat_completion", side_effect=TimeoutError("LLM timeout")):
        synergy = _generate_odop_synergy(
            user_business="Tomato Processing Factory",
            sector="food_processing",
            state="Maharashtra",
            district="Pune",
            language="hi",
        )
        assert synergy is not None
        assert synergy["alignment_score"] >= 65
        assert synergy["verdict_key"] == "recommended"
        assert "synergy_pillars" in synergy


def test_odop_decision_action_align():
    """Test clicking 'Align with ODOP' button (action='odop_decision', odop_decision='align')."""
    payload = {
        "messages": [
            {"role": "assistant", "content": "1. ODOP से जुड़ें\n2. अपना मूल विचार रखें"},
            {"role": "user", "content": "1. ODOP से जुड़ें"},
        ],
        "language": "hi",
        "user_name": "Ramesh",
        "collected_fields": {
            "enterprise_name": "Ramesh Tomato Farm",
            "sector": "food_processing",
            "state_name": "Maharashtra",
            "district_name": "Pune",
            "project_cost": 500000.0,
            "promoter_equity": 100000.0,
            "odop_alignment_presented": True,
            "odop_product": "Tomato",
        },
        "conversation_step": 4,
        "current_action": "odop_decision",
        "odop_decision": "align",
    }
    resp = client.post("/api/v2/chat/onboarding", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["all_fields_collected"] is True
    assert data["next_phase"] == "processing"
    assert data["extracted_fields"]["odop_decision"] == "align"
    assert data["extracted_fields"]["odop_synergy_aligned"] is True
    assert "35 प्रतिशत" in data["reply"] or "35%" in data["reply"] or "PMFME" in data["reply"]
    # Verify Bhashini text is clean
    assert "₹" not in data["tts_text"]
    assert "%" not in data["tts_text"]
    assert "?" not in data["tts_text"]


def test_odop_decision_action_keep_original():
    """Test clicking 'Keep My Idea' button (action='odop_decision', odop_decision='keep_original')."""
    payload = {
        "messages": [
            {"role": "assistant", "content": "1. ODOP से जुड़ें\n2. अपना मूल विचार रखें"},
            {"role": "user", "content": "2. अपना मूल विचार रखें"},
        ],
        "language": "hi",
        "user_name": "Suresh",
        "collected_fields": {
            "enterprise_name": "Suresh Electronics",
            "sector": "repair",
            "state_name": "Maharashtra",
            "district_name": "Sangli",
            "project_cost": 200000.0,
            "promoter_equity": 50000.0,
            "odop_alignment_presented": True,
            "odop_product": "Raisins",
        },
        "conversation_step": 4,
        "current_action": "odop_decision",
        "odop_decision": "keep_original",
    }
    resp = client.post("/api/v2/chat/onboarding", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["all_fields_collected"] is True
    assert data["next_phase"] == "processing"
    assert data["extracted_fields"]["odop_decision"] == "keep_original"
    assert data["extracted_fields"]["odop_synergy_aligned"] is False
    assert "मूल विचार" in data["reply"] or "PMEGP" in data["reply"]


def test_odop_decision_chat_text_number_1():
    """Test user simply typing '1' in the chat when ODOP decision is pending."""
    payload = {
        "messages": [
            {"role": "assistant", "content": "अब आप मुझे बताइए, आप क्या चुनना चाहेंगे:\n1. ODOP से जुड़ें\n2. अपना मूल विचार रखें"},
            {"role": "user", "content": "1"},
        ],
        "language": "hi",
        "user_name": "Anita",
        "collected_fields": {
            "enterprise_name": "Anita Agro",
            "sector": "food_processing",
            "state_name": "Maharashtra",
            "district_name": "Pune",
            "project_cost": 600000.0,
            "promoter_equity": 100000.0,
            "odop_alignment_presented": True,
            "odop_product": "Tomato",
        },
        "conversation_step": 5,
    }
    resp = client.post("/api/v2/chat/onboarding", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["all_fields_collected"] is True
    assert data["next_phase"] == "processing"
    assert data["extracted_fields"]["odop_decision"] == "align"
    assert data["extracted_fields"]["odop_synergy_aligned"] is True


def test_odop_decision_chat_text_keep_original():
    """Test user typing natural language 'अपना मूल विचार ही रखेंगे' in the chat."""
    payload = {
        "messages": [
            {"role": "assistant", "content": "अब आप मुझे बताइए, आप क्या चुनना चाहेंगे:\n1. ODOP से जुड़ें\n2. अपना मूल विचार रखें"},
            {"role": "user", "content": "अपना मूल विचार रखेंगे"},
        ],
        "language": "hi",
        "user_name": "Vikas",
        "collected_fields": {
            "enterprise_name": "Vikas Garage",
            "sector": "repair",
            "state_name": "Maharashtra",
            "district_name": "Pune",
            "project_cost": 300000.0,
            "promoter_equity": 60000.0,
            "odop_alignment_presented": True,
            "odop_product": "Tomato",
        },
        "conversation_step": 5,
    }
    resp = client.post("/api/v2/chat/onboarding", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["all_fields_collected"] is True
    assert data["next_phase"] == "processing"
    assert data["extracted_fields"]["odop_decision"] == "keep_original"
    assert data["extracted_fields"]["odop_synergy_aligned"] is False


def test_machinery_matching_and_capacity():
    """Verify profile matching and typical capacity parsing from msme_machinery_dataset.json."""
    from backend.app.core.machinery_matcher import (
        find_matching_machinery_profile,
        parse_monthly_capacity,
    )

    profile = find_matching_machinery_profile("Spice grinding and automatic pouch packing", "food_processing")
    assert profile is not None
    assert "Spice Grinding" in profile["business_name"]
    assert profile["total_machinery_cost_inr"] > 500000

    monthly_units, unit_label = parse_monthly_capacity(profile["typical_capacity"])
    assert monthly_units == 12500.0  # 500 kg/day * 25 days
    assert unit_label == "kg"


def test_owned_machinery_detection():
    """Verify detection and valuation of owned machinery mentioned in natural language."""
    from backend.app.core.machinery_matcher import (
        find_matching_machinery_profile,
        detect_owned_machinery,
    )

    profile = find_matching_machinery_profile("masala grinding", "food_processing")
    user_text = "मेरे पास पहले से pulverizer और ribbon blender है"
    machines, val = detect_owned_machinery(user_text, profile)

    assert len(machines) >= 2
    assert val >= 300000  # Pin mill pulverizer (220k) + Ribbon blender (125k) = 345k
    machine_names = [m["machine_name"] for m in machines]
    assert any("Pulverizer" in name for name in machine_names)
    assert any("Blender" in name for name in machine_names)


def test_tiered_promoter_margin_and_outlay_deduction():
    """Verify tiered promoter equity margin (15% to 28%) and owned machinery valuation credit."""
    from backend.app.core.machinery_matcher import calculate_tiered_capital_outlay

    # Micro tier (equity <= 1.5L -> 15% margin)
    micro = calculate_tiered_capital_outlay(100000.0, owned_machinery_value=0.0)
    assert micro["promoter_margin_pct"] == 15.0
    assert micro["gross_project_cost"] == 666700.0

    # Micro tier with owned machinery deduction of 2.2 Lakhs
    micro_credit = calculate_tiered_capital_outlay(100000.0, owned_machinery_value=220000.0)
    assert micro_credit["gross_project_cost"] == 666700.0
    assert micro_credit["owned_machinery_value"] == 220000.0
    assert micro_credit["net_project_cost"] < micro_credit["gross_project_cost"]
    assert micro_credit["estimated_monthly_emi_saved_inr"] > 0

    # Small tier (equity = 5 Lakhs -> 18% margin)
    small = calculate_tiered_capital_outlay(500000.0, owned_machinery_value=0.0)
    assert small["promoter_margin_pct"] == 18.0

    # Small & Medium tier (equity = 20 Lakhs -> 22% margin)
    medium = calculate_tiered_capital_outlay(2000000.0, owned_machinery_value=0.0)
    assert medium["promoter_margin_pct"] == 22.0


def test_statutory_banking_parameters_allocation():
    """Verify statutory banking parameters (tenure, moratorium, infra score) are assigned dynamically."""
    from backend.app.core.machinery_matcher import (
        compute_statutory_banking_parameters,
        find_matching_machinery_profile,
    )

    profile = find_matching_machinery_profile("Dairy processing unit", "dairy")
    params = compute_statutory_banking_parameters(
        sector="dairy",
        business_category="manufacturing",
        project_cost=1000000.0,
        is_rural=True,
        matched_profile=profile,
    )

    assert params["tenure_years"] == 7.0  # RBI Plant & Machinery standard
    assert params["moratorium_months"] == 6  # Agro/Food gestation standard
    assert params["infrastructure_score"] == 7.8  # Rural agro cluster standard
    assert params["expected_monthly_units"] == 25000.0  # 1000 L/day * 25 days
    assert params["capacity_unit_label"] == "litres"


def test_conversational_onboarding_machinery_deduction_and_banking_fields():
    """Test full conversational onboarding message providing equity and existing machine."""
    payload = {
        "messages": [
            {"role": "assistant", "content": "कृपया मुझे बताइए कि आपके पास कितनी प्रमोटर इक्विटी है?"},
            {"role": "user", "content": "मेरे पास 1 लाख रुपये हैं और मेरे पास पहले से ग्राइंडर (pulverizer) उपलब्ध है"},
        ],
        "language": "hi",
        "user_name": "Radha",
        "collected_fields": {
            "enterprise_name": "Radha Spices",
            "sector": "food_processing",
            "state_name": "Maharashtra",
            "district_name": "Pune",
        },
        "conversation_step": 3,
    }
    resp = client.post("/api/v2/chat/onboarding", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    fields = data["extracted_fields"]
    assert fields["promoter_equity"] == 100000.0
    assert fields["owned_machinery_value"] > 0
    assert fields["project_cost"] < fields["gross_project_cost"]
    assert fields["tenure_years"] == 7.0
    assert fields["moratorium_months"] == 6
    assert fields["infrastructure_score"] > 0

    # Check that Mira spoke about the owned machinery and its EMI savings
    assert "रुपये" in data["reply"] or "मशीन" in data["reply"]
    assert data["banking_parameters"] is not None
    assert data["machinery_analysis"] is not None


def test_applicable_machinery_returned_on_business_idea():
    """Verify that when a user gives their business idea, applicable_machinery dropdown data is returned."""
    payload = {
        "messages": [
            {"role": "assistant", "content": "आप क्या व्यवसाय शुरू करना चाहते हैं?"},
            {"role": "user", "content": "मैं मसाला पीसने और पैकिंग का काम (spice grinding) शुरू करना चाहता हूँ"},
        ],
        "language": "hi",
        "user_name": "Ramesh",
        "collected_fields": {
            "state_name": "Rajasthan",
            "district_name": "Jodhpur",
        },
        "conversation_step": 2,
    }
    resp = client.post("/api/v2/chat/onboarding", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["applicable_machinery"] is not None
    app_mach = data["applicable_machinery"]
    assert "Spice" in app_mach["business_name"]
    assert len(app_mach["machinery_list"]) >= 4
    # Check that each machine has name, cost, specs
    first_m = app_mach["machinery_list"][0]
    assert "machine_name" in first_m
    assert first_m["estimated_cost_inr"] > 0
    assert "technical_specs" in first_m


def test_select_owned_machinery_action_confirms_and_credits_outlay():
    """Verify that selecting machines via current_action='select_owned_machinery' credits valuation."""
    payload = {
        "messages": [
            {"role": "assistant", "content": "कृपया मशीनें चुनें"},
        ],
        "language": "hi",
        "user_name": "Sunita",
        "collected_fields": {
            "enterprise_name": "Sunita Dairy Farm",
            "sector": "dairy",
            "state_name": "Gujarat",
            "district_name": "Anand",
            "promoter_equity": 150000.0,
        },
        "current_action": "select_owned_machinery",
        "selected_machines": [
            {"machine_name": "Cream Separator", "estimated_cost_inr": 60000.0},
            {"machine_name": "Paneer Press & Cheese Vat", "estimated_cost_inr": 80000.0},
        ],
        "conversation_step": 3,
    }
    resp = client.post("/api/v2/chat/onboarding", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    fields = data["extracted_fields"]
    assert fields["machinery_selection_confirmed"] is True
    assert fields["owned_machinery_value"] == 140000.0
    assert len(fields["owned_machines"]) == 2
    # Gross cost minus owned value equals net cost
    assert fields["project_cost"] == fields["gross_project_cost"] - 140000.0
    assert fields["estimated_monthly_emi_saved"] > 0

    # Since equity was already present, it should advance to ODOP alignment
    assert data["next_phase"] == "odop_alignment"
    assert data["odop_alignment"] is not None


def test_calculate_intelligent_turnover_triangulation():
    """Verify intelligent projected sales calculations triangulate machine capacity and velocity."""
    res = calculate_intelligent_turnover(
        project_cost=900000.0,
        sector="dairy",
        business_category="manufacturing",
        expected_monthly_units=5000.0,  # 5,000 litres/month
        annual_tam=3500000.0,
        monthly_emi=8800.0,
    )
    assert res["projected_turnover"] > 0
    # Turnover must clear solvency guardrail for DSCR >= 1.33
    min_solvency = (1.33 * 8800.0 * 12) / 0.30
    assert res["projected_turnover"] >= min_solvency
    assert "derivation_basis" in res
    assert "asset_turnover_ratio" in res
    assert 1.2 <= res["asset_turnover_ratio"] <= 3.5


def test_onboarding_auto_calculates_intelligent_turnover():
    """Verify onboarding extracts intelligent annual turnover estimate."""
    payload = {
        "messages": [
            {"role": "user", "content": "I want to start a spice grinding and packaging business with 1 lakh rupees savings in Bankura West Bengal"},
        ],
        "language": "en",
        "user_name": "Arjun",
        "collected_fields": {
            "state_name": "West Bengal",
            "district_name": "Bankura",
            "village_name": "Bikna",
            "is_rural": True,
        },
        "conversation_step": 1,
    }
    resp = client.post("/api/v2/chat/onboarding", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    fields = data["extracted_fields"]
    assert "annual_turnover_estimate" in fields
    assert fields["annual_turnover_estimate"] > 0
    assert "project_cost" in fields
    # Turnover should be scaled intelligently relative to project cost
    assert fields["annual_turnover_estimate"] >= fields["project_cost"] * 1.5


