"""Mira extracts user statements; she cannot set derived geography or financial results."""
from __future__ import annotations

import asyncio
import json
import re

from app.models.onboarding import Facts

NUMBER_WORDS = {word: index for index, word in enumerate(("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"))}
NUMBER_WORDS.update({word: index * 10 for index, word in enumerate(("twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"), start=2)})
NUMBER_WORDS.update(dict(zip(("शून्य", "एक", "दो", "तीन", "चार", "पाँच", "छह", "सात", "आठ", "नौ", "दस"), range(11))))
NUMBER_WORDS.update({"पाच": 5, "दोन": 2, "सहा": 6, "नऊ": 9, "दहा": 10})
NUMBER_PATTERN = re.compile(r"(?<!\w)(?:(?:" + "|".join(NUMBER_WORDS) + r"|hundred)(?:[ -]+(?=\w)|\b))+(?=\s|$|[^\w])", re.I)
MONEY_PATTERN = re.compile(r"(?:₹|rs\.?|inr|rupees?)?\s*([-+]?\d[\d,]*(?:\.\d+)?)\s*(crores?|cr\b|lakhs?|lacs?|thousand|k\b)?", re.I)


def normalize_money_words(text: str) -> str:
    for word, unit in (("लाख", "lakh"), ("करोड़", "crore"), ("कोटी", "crore"), ("हज़ार", "thousand"), ("हजार", "thousand"),
                       ("லட்சம்", "lakh"), ("లక్షలు", "lakh"), ("ಲಕ್ಷ", "lakh")):
        text = text.replace(word, unit)

    def to_digits(match):
        tokens = match[0].strip().lower().replace("-", " ").split()
        total = 0
        for token in tokens:
            total = max(1, total) * 100 if token == "hundred" else total + NUMBER_WORDS.get(token, 0)
        return str(total) + (" " if match[0].endswith(" ") else "")

    return NUMBER_PATTERN.sub(to_digits, text)


def money(text: str):
    match = MONEY_PATTERN.search(normalize_money_words(text))
    if not match:
        return None
    amount = float(match[1].replace(",", ""))
    unit = (match[2] or "").lower()
    if unit.startswith(("lakh", "lac")):
        amount *= 100000
    elif unit.startswith(("crore", "cr")):
        amount *= 10000000
    elif unit in ("thousand", "k"):
        amount *= 1000
    return amount


def fallback_extract(text: str, question: str | None) -> dict:
    """Conservative offline comprehension. Unclear values stay missing."""
    lower = normalize_money_words(text.lower().strip())
    updates = {}
    if re.search(r"no (?:business )?idea|(?:don.t know|not sure) (?:what|which).*business|suggest.*business|explore businesses", lower):
        updates["idea_status"] = "explore"
    if re.search(r"\b(start|establish|open|want|plan|switch|instead)\b", lower) and re.search(
        r"dairy|milk|paneer|ghee|tailor|garment|repair|shop|store|mill|processing|salon|fabricat|poultry|business|unit", lower
    ) and updates.get("idea_status") != "explore":
        updates.update(idea=text, idea_status="known")
    if re.search(r"\b(manufactur\w*|mak(?:e|ing)|produc(?:e|ing))\b", lower):
        updates["activity"] = "manufacture"
    if re.search(r"\bprocess(?:ing)?\b", lower):
        updates["activity"] = "process"
    if re.search(r"\b(retail|sell|selling|shop|store)\b", lower) and "activity" not in updates:
        updates["activity"] = "retail"
    if re.search(r"\b(repair|repairing|service|services|salon)\b", lower) and "activity" not in updates:
        updates["activity"] = "service"
    if re.search(r"\bdistribut\w*\b", lower):
        updates["activity"] = "distribute"
    if re.search(r"(?:already )?(?:own|have my own|owns)\b.*\b(land|premises|building|shop|space)\b", lower):
        updates["premises"] = "owned"
    if re.search(r"\b(?:need to |will |want to )?rent\b", lower):
        updates["premises"] = "rented"
    if re.search(r"\bshared (?:facility|space|premises)\b", lower):
        updates["premises"] = "shared"
    if re.search(r"\b(?:buy|purchase)\b.*\b(?:land|premises|space|shop)\b", lower):
        updates["premises"] = "purchase"
    if re.search(r"\b(?:no fixed|without fixed) premises\b", lower):
        updates["premises"] = "mobile"
    rent = re.search(r"(?:rent(?: is| of| will be| costs)?|pay)\s*(?:₹|rs\.?|inr)?\s*(\d[\d,.]*\s*(?:thousand|lakhs?|k)?)", lower)
    if rent:
        updates["rent_amount"] = money(rent[1])
        if re.search(r"per (?:month|monthly)|a month|monthly|/month", lower):
            updates["rent_period"] = "monthly"
        elif re.search(r"per (?:year|annum)|annual|a year|/year", lower):
            updates["rent_period"] = "annual"
    budget = re.search(r"(?:invest(?:ment)?|budget|(?<!working )capital|savings|contribut\w*|borrow(?:ing capacity)?)\s*(?:is|of|up to|about|around|have|can be|will be)?\s*(?:₹|rs\.?|inr)?\s*(\d[\d,.]*\s*(?:lakhs?|lacs?|crores?|thousand|k)?)", lower)
    if not budget and (question == "idea" or updates.get("idea_status") == "explore"):
        budget = re.search(r"\b(?:i have|i saved|i can spend)\s*(?:₹|rs\.?|inr)?\s*(\d[\d,.]*\s*(?:lakhs?|lacs?|crores?|thousand))\b", lower)
    if budget:
        updates["budget"] = money(budget[1])
        if re.search(r"personal|my (?:own|savings)|own (?:money|capital|contribution)|savings", lower):
            updates.update(budget_kind="personal", personal_contribution=updates["budget"])
        elif re.search(r"total (?:project |available )?(?:budget|investment)|entire project", lower):
            updates["budget_kind"] = "total"
        elif re.search(r"borrowing|borrow|loan capacity", lower):
            updates["budget_kind"] = "borrowing"
    capacity = re.search(r"\d[\d,.]*\s*(?:litres?|liters?|kg|kilograms?|units?|customers?|orders?|pieces?).*?(?:per day|daily|a day|/day|per month|monthly|a month|/month)", lower)
    if capacity:
        updates["scale"] = capacity[0]
    products = [p for p in ("paneer", "ghee", "curd", "ice cream", "milk", "flour", "garments", "uniforms", "phone repair") if p in lower]
    if products and ("idea" in updates or question in ("idea", "products")):
        updates["products"] = ", ".join(products)
    unresolved = lower.strip(" .!?।") in ("not sure", "i don't know", "don't know", "no idea", "maybe", "anything")
    if question in ("name", "enterprise_name", "products", "operations", "scale", "skills", "constraints", "space", "cost_basis", "funding_source") and "idea" not in updates and not unresolved:
        updates[question] = text.strip()
    if "idea" not in updates and question not in ("activity", "idea"):
        updates.pop("activity", None)
    if question == "idea" and "idea" not in updates and updates.get("idea_status") != "explore" and not unresolved and len(text.strip()) >= 5 and ("activity" in updates or "products" in updates or (not updates and not MONEY_PATTERN.search(lower))):
        updates.update(idea=text.strip(), idea_status="known")
    if question in ("budget", "personal_contribution", "rent_amount", "project_cost") and not updates:
        amount = money(text)
        monetary_answer = re.search(r"₹|\brupees?\b|\binr\b|\brs\b|\b(?:lakh|lac|thousand|crore)s?\b", lower) or MONEY_PATTERN.fullmatch(lower.strip(" ."))
        if amount is not None and monetary_answer:
            updates[question] = amount
        if question == "budget" and re.search(r"don.t know|not sure|no budget|estimate first", lower):
            updates["budget_kind"] = "unknown_budget"
    if "rent_amount" in updates and "rent_period" not in updates:
        if re.search(r"per month|a month|monthly|/month", lower):
            updates["rent_period"] = "monthly"
        elif re.search(r"per year|per annum|annual|a year|/year", lower):
            updates["rent_period"] = "annual"
    if "budget" in updates and "budget_kind" not in updates:
        if re.search(r"\b(personal|my own|savings)\b", lower):
            updates["budget_kind"] = "personal"
        elif re.search(r"\b(total|entire project)\b", lower):
            updates["budget_kind"] = "total"
        elif re.search(r"\b(borrow|borrowing)\b", lower):
            updates["budget_kind"] = "borrowing"
    if question == "personal_contribution" and "budget" in updates and "budget" not in lower and updates.get("budget_kind") not in ("total", "borrowing", "other"):
        updates["personal_contribution"] = updates.pop("budget")
        updates.pop("budget_kind", None)
    if question == "budget_kind":
        if "personal" in lower or "savings" in lower or "own" in lower:
            updates["budget_kind"] = "personal"
        elif "total" in lower:
            updates["budget_kind"] = "total"
        elif "borrow" in lower or "loan" in lower:
            updates["budget_kind"] = "borrowing"
        elif "other" in lower:
            updates["budget_kind"] = "other"
    if question == "rent_period":
        if "month" in lower:
            updates["rent_period"] = "monthly"
        elif "year" in lower or "annual" in lower:
            updates["rent_period"] = "annual"
    if question == "premises_suitable" and lower in ("yes", "suitable", "no", "not suitable"):
        updates["premises_suitable"] = lower in ("yes", "suitable")
    if question == "odop_preference":
        if re.search(r"no|reject|not interested", lower):
            updates["odop_preference"] = "reject"
        elif re.search(r"keep|original|continue", lower):
            updates["odop_preference"] = "keep"
        elif re.search(r"yes|explore|interested", lower):
            updates["odop_preference"] = "explore"
    if question == "gender":
        updates["gender"] = {"male": "Male", "female": "Female", "other": "Other", "prefer not to say": "Unspecified"}.get(lower)
    if question == "promoter_category" and lower in ("general", "sc", "st", "obc", "minority", "ph", "artisan", "women", "women_shg"):
        updates["promoter_category"] = lower
    costs = {}
    for key, pattern in (("equipment", r"equipment|machinery|tools"), ("premises_setup", r"premises setup|building setup|civil works|renovation"),
                         ("inventory", r"inventory|initial stock|raw materials"), ("working_capital", r"working capital"), ("other", r"other setup costs|other costs")):
        match = re.search(rf"(?:{pattern})\s*(?:is|of|costs|cost)?\s*(?:₹|rs\.?|inr)?\s*(\d[\d,.]*\s*(?:lakhs?|lacs?|crores?|thousand|k)?)", lower)
        if match:
            costs[key] = money(match[1])
    if costs:
        updates["cost_items"] = costs
    if question == "financing_choice":
        for word, choice in (("normal", "normal"), ("sca", "sca"), ("increase", "increase"), ("self", "self")):
            if word in lower:
                updates["financing_choice"] = choice
    return {key: value for key, value in updates.items() if value is not None}


async def understand(text: str, state: dict) -> tuple[dict, list[str], str]:
    question = (state.get("next") or {}).get("field")
    if state.get('experience') == 'adaptive':
        from app.core.profile_conversation import parse_correction
        corrected = parse_correction(text)
        if corrected:
            return corrected, [], 'validated_profile_correction'
    if state.get('experience') == 'adaptive' and question in ('name','gender','promoter_category','phone','email'):
        from app.core.profile_conversation import parse_answer
        return parse_answer(question, text) or {}, [], 'validated_profile_answer'
    fallback = fallback_extract(text, question)
    # Profile fields never go to a general-purpose model.
    if question in ("name", "gender", "promoter_category") or re.search(r"\bmy (?:caste|gender|name)\b", text, re.I):
        return fallback, [], "local"
    from app.core.chat_service import ChatService
    service = ChatService.get_instance()
    if not service._get_api_key():
        return fallback, [], "offline"
    full_schema = Facts.model_json_schema()
    schema = full_schema["properties"]
    schema = {k: v for k, v in schema.items() if k not in ("name", "gender", "promoter_category", "phone", "email", "email_status")}
    tool = {"type": "function", "function": {"name": "record_user_facts", "description": "Extract only explicit facts in the latest user statement.", "parameters": {
        "type": "object", "$defs": full_schema.get("$defs", {}), "properties": {"updates": {"type": "object", "properties": schema, "additionalProperties": False},
            "evidence": {"type": "object", "additionalProperties": {"type": "string"}},
            "ambiguities": {"type": "array", "items": {"type": "string"}}}, "required": ["updates", "evidence", "ambiguities"]}}}
    known = {k: v["value"] for k, v in state["fields"].items() if k not in ("name", "gender", "promoter_category", "phone", "email", "email_status")}
    prompt = ("You are Mira's language understanding layer for rural Indian entrepreneurs. Use record_user_facts. "
              "Extract ALL explicitly stated facts, including multiple answers and corrections, in any supported Indian language. "
              "Each update MUST include a verbatim evidence substring from the latest user message. No guesses. "
              "Never calculate estimates, infer personal contribution from an unqualified budget, or invent scheme/geography/category decisions. "
              "Normalize lakh/crore and rupees only when stated, and monthly/annual rent only when explicit. "
              "Separate products, operations (equipment, supply, staffing), and scale/capacity. A land statement is not site suitability. "
              "A bare answer may answer the current question. Return ambiguities as short English clarification questions, one issue each. "
              f"Known facts: {json.dumps(known, ensure_ascii=False)}. Current question: {json.dumps(state.get('next'), ensure_ascii=False)}")
    try:
        _, result, model = await asyncio.to_thread(service._call_llm_chat_completion,
            [{"role": "system", "content": prompt}, {"role": "user", "content": text}],
            tools=[tool], temperature=0, max_tokens=1300, timeout_s=15)
        if not result or result.get("name") != "record_user_facts":
            return fallback, [], "offline"
        args = result.get("arguments", {})
        evidence = args.get("evidence", {})
        grounded = {k: v for k, v in args.get("updates", {}).items()
                    if k in schema and isinstance(evidence.get(k), str) and evidence[k].strip()
                    and evidence[k].casefold() in text.casefold() and v is not None}
        for key in list(grounded):
            if key in ("budget", "personal_contribution", "rent_amount", "project_cost", "cost_items"):
                amounts = [money(match[0]) for match in MONEY_PATTERN.finditer(normalize_money_words(evidence[key]))]
                values = grounded[key].values() if isinstance(grounded[key], dict) else [grounded[key]]
                if any(not isinstance(v, (float, int)) or not any(abs(v - a) < 0.01 for a in amounts) for v in values):
                    grounded.pop(key)
        validated = Facts(**grounded).model_dump(exclude_none=True)
        ambiguities = [str(a)[:300] for a in args.get("ambiguities", [])[:3]]
        return {**fallback, **validated}, ambiguities, model
    except Exception:
        # No user input is discarded; it is retained in history and stays editable in the UI.
        return fallback, [], "offline"
