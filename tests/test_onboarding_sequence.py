"""Regression checks for Mira's location → idea → ODOP → investment → review flow."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.business_interpreter import interpret_business_idea


client = TestClient(app)
API = "/api/v2/chat/onboarding"


def _turn(text, fields=None, action=None, language="en", **extra):
    payload = {
        "messages": [{"role": "user", "content": text}],
        "language": language,
        "user_name": "Asha",
        "collected_fields": fields or {},
        "current_action": action,
        **extra,
    }
    response = client.post(API, json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_catalogue_interpretation_distinguishes_paneer_production_and_ghee_retail():
    paneer = interpret_business_idea("Mujhe paneer banana hai")
    assert paneer["sector"] == "dairy"
    assert paneer["business_category"] == "manufacturing"
    names = {m["machine_name"] for m in paneer["machinery_plan"]["machinery_list"]}
    assert "Paneer Press & Cheese Vat" in names
    assert "Ghee Boiler / Kettle" not in names
    assert paneer["machinery_plan"]["total_machinery_cost_inr"] > 0

    ghee_unit = interpret_business_idea("I want to manufacture ghee")
    ghee_machines = {m["machine_name"] for m in ghee_unit["machinery_plan"]["machinery_list"]}
    assert "Ghee Boiler / Kettle" in ghee_machines
    assert "Paneer Press & Cheese Vat" not in ghee_machines

    shop = interpret_business_idea("Mujhe gaon ghee ki dukan kholni he")
    assert shop["sector"] == "dairy"
    assert shop["business_category"] == "service"
    assert shop["machinery_plan"]["machinery_list"] == []


def test_llm_receives_retrieved_candidates_but_cannot_invent_machine_prices():
    captured = {}

    def fake_llm(**kwargs):
        captured["messages"] = kwargs["messages"]
        return ('{"sector":"dairy","business_category":"manufacturing",'
                '"profile_name":"Dairy Processing Unit (Milk Pasteurization, Paneer, Curd & Ghee)",'
                '"machine_names":["Paneer Press & Cheese Vat","Invented Machine"]}', None, "stub")

    result = interpret_business_idea("paneer manufacturing unit", fake_llm)
    assert "catalogue_candidates" in captured["messages"][1]["content"]
    machines = result["machinery_plan"]["machinery_list"]
    assert [m["machine_name"] for m in machines] == ["Paneer Press & Cheese Vat"]
    assert machines[0]["estimated_cost_inr"] == 130000


def test_full_paneer_onboarding_order_and_server_valued_equipment():
    with patch("backend.app.routers.onboarding.chat_service._call_llm_chat_completion", side_effect=RuntimeError("offline")):
        fields = {"state_name": "Maharashtra", "district_name": "Pune", "is_rural": True}
        location = _turn("Continue", fields, "confirm_location")
        assert location["next_phase"] == "business_idea"

        idea = _turn("Mujhe paneer banana hai", fields, "business_idea")
        assert idea["next_phase"] == "odop_check_prompt"
        assert idea["applicable_machinery"] is None  # Equipment is revealed later.
        fields.update(idea["extracted_fields"])
        assert fields["sector"] == "dairy"
        assert fields["business_category"] == "manufacturing"

        verdict = _turn("Let's check", fields, "check_odop_alignment")
        assert verdict["next_phase"] == "odop_alignment"
        assert verdict["odop_alignment"] is not None
        fields.update(verdict["extracted_fields"])

        decision = _turn("Align", fields, "odop_decision", odop_decision="align")
        assert decision["next_phase"] == "enterprise_info"
        fields.update(decision["extracted_fields"])
        assert fields["sector"] == "dairy"
        assert fields["business_category"] == "manufacturing"

        fields.update({"enterprise_name": "Asha Paneer", "promoter_category": "obc"})
        enterprise = _turn("Asha Paneer, OBC", fields, "submit_enterprise_info")
        assert enterprise["next_phase"] == "promoter_equity"
        fields.update(enterprise["extracted_fields"])

        investment = _turn("I can invest 1 lakh", fields, "promoter_equity")
        assert investment["next_phase"] == "machinery_selection"
        machine_names = {m["machine_name"] for m in investment["applicable_machinery"]["machinery_list"]}
        assert "Paneer Press & Cheese Vat" in machine_names
        assert "Ghee Boiler / Kettle" not in machine_names
        fields.update(investment["extracted_fields"])

        review = _turn("I own a paneer press", fields, "select_owned_machinery",
                       selected_machines=[{"machine_name": "Paneer Press & Cheese Vat", "estimated_cost_inr": 99999999},
                                          {"machine_name": "Invented Machine", "estimated_cost_inr": 99999999}])
        assert review["next_phase"] == "split_screen"
        assert review["extracted_fields"]["owned_machinery_value"] == 130000
        assert [m["machine_name"] for m in review["extracted_fields"]["owned_machines"]] == ["Paneer Press & Cheese Vat"]


def test_ghee_shop_has_no_manufacturing_equipment_and_can_finish():
    with patch("backend.app.routers.onboarding.chat_service._call_llm_chat_completion", side_effect=RuntimeError("offline")):
        fields = {"state_name": "Maharashtra", "district_name": "Pune"}
        idea = _turn("Mujhe gaon ghee ki dukan kholni he", fields, "business_idea")
        fields.update(idea["extracted_fields"])
        assert fields["business_category"] == "service"
        assert fields["machinery_plan"]["machinery_list"] == []

        skip = _turn("I will go with my idea", fields, "skip_odop_alignment")
        fields.update(skip["extracted_fields"])
        fields.update({"enterprise_name": "Gaon Ghee Shop", "promoter_category": "general"})
        _turn("Gaon Ghee Shop, general", fields, "submit_enterprise_info")
        investment = _turn("I have 1 lakh", fields, "promoter_equity")
        assert investment["next_phase"] == "machinery_selection"
        assert investment["applicable_machinery"]["machinery_list"] == []
        fields.update(investment["extracted_fields"])
        review = _turn("No machines", fields, "select_owned_machinery", selected_machines=[])
        assert review["next_phase"] == "split_screen"
        assert review["extracted_fields"]["owned_machinery_value"] == 0


def test_location_change_and_review_chat_do_not_mutate_business_fields():
    with patch("backend.app.routers.onboarding.chat_service._call_llm_chat_completion", side_effect=RuntimeError("offline")):
        change = _turn("Change location", {"state_name": "Maharashtra", "district_name": "Pune"}, "request_change_location")
        assert change["next_phase"] == "location_menu"
        selected = _turn("Use Bankura", {}, "submit_new_location", user_location={
            "state_name": "West Bengal", "district_name": "Bankura", "block_name": "Joypur", "village_name": "Joypur", "is_rural": True,
        })
        assert selected["next_phase"] == "business_idea"
        assert selected["extracted_fields"]["district_name"] == "Bankura"

        fields = {"enterprise_name": "Asha Paneer", "business_idea": "paneer manufacturing", "sector": "dairy",
                  "business_category": "manufacturing", "state_name": "West Bengal", "district_name": "Bankura",
                  "promoter_category": "general", "project_cost": 500000}
        answer = _turn("Can I ask about my report?", fields, "chat_only")
        assert answer["next_phase"] == "split_screen"
        assert answer["extracted_fields"] == {}
