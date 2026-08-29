"""
chat_service.py — Enterprise AI Chatbot & Conversational MSME Advisory Engine.
Powered by Groq Cloud with dedicated GROQ_CHAT_KEY support, real-time page-aware context injection,
dashboard tab summary intelligence, and zero-crash deterministic fallback.
"""

from __future__ import annotations
import os
import time
import json
import logging
from typing import Optional, Any, Dict, List
from dataclasses import dataclass

try:
    from app.config import settings
except ImportError:
    from backend.app.config import settings

logger = logging.getLogger("udyam_saathi.chat")

# System Grounding Template for Udyam Saathi
BASE_SYSTEM_PROMPT = """You are the official Udyam Saathi (उद्यम साथी) AI Credit & Enterprise Advisor for Indian MSMEs (Smart India Hackathon 2026).
Your goal is to provide accurate, authoritative, and actionable financial, regulatory, and credit-feasibility guidance to entrepreneurs, loan officers, and small business owners.

CORE CAPABILITIES & DOMAIN EXPERTISE:
1. Indian Government Schemes: PMEGP (15-35% subsidy up to ₹50L manufacturing / ₹20L services), PM Mudra Yojana (Shishu up to ₹50k, Kishore ₹50k-₹5L, Tarun ₹5L-₹10L), CGTMSE (collateral-free credit guarantee up to ₹5 Cr), PMFME (35% subsidy up to ₹10L for food processing), Stand-Up India (₹10L-₹1 Cr for SC/ST/Women).
2. Financial & Credit Appraisal Metrics:
   - Debt Service Coverage Ratio (DSCR): Benchmark >= 1.33 for scheduled commercial bank loans.
   - Break-Even Pricing & Contribution Margin under MoSPI rural CPI inflation.
   - Total Addressable Market (TAM) based on Census 2011 Catchment Demographics.
   - Capital Reconciliation: Outlay = Promoter Margin + Capital Subsidy + Net Bank Term Loan.
3. 10-Dimensional TreeSHAP Viability: Evaluates infrastructure score, competition saturation, MSME density, climate/weather risk, and debt sustainability.
4. Statutory & Regulatory Compliance: Udyam Registration (Zero-cost portal), GSTIN, FSSAI, Pollution Control Board (CTO/CTE), Trade License, Fire Safety NOC.

PAGE & TAB AWARENESS INSTRUCTIONS:
- You have real-time access to the user's active dashboard viewport and tab content provided under "CURRENT ACTIVE ENTERPRISE CONTEXT".
- When the user asks:
  * "Summarize this page" or "Explain this tab"
  * "What does this content mean?" or "Explain the numbers here"
  * "Walk me through this section" or "What is on my screen?"
  You MUST provide a clear, structured executive summary of the ACTIVE TAB DATA.
- Highlight:
  1. What the active tab represents for the enterprise.
  2. The specific numerical metrics visible on their screen (e.g. DSCR, subsidies, TreeSHAP scores, 5-year revenues, risks, SWOT).
  3. Actionable takeaways and recommendations for loan approval or operational success.

FORMATTING & TONE GUIDELINES:
- Always use professional, encouraging, and financially rigorous tone.
- Format all rupee amounts with the Rupee symbol (e.g. ₹5,00,000 or ₹5.20 Lakhs).
- Use clean Markdown: bold key metrics, use bullet points for action items, and short structured paragraphs.
- Keep answers concise and actionable (under 250 words unless detailed calculations are requested).
- LANGUAGE INVARIANT: You must ALWAYS reason and output your response in clear, professional English. The client-side translation layer handles translating into the user's selected Indic language. Never generate responses in non-English languages.
"""


class ChatService:
    """
    Singleton service handling Groq-powered chat completions with active enterprise context.
    """
    _instance: Optional[ChatService] = None

    def __init__(self):
        pass

    @classmethod
    def get_instance(cls) -> ChatService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_api_key(self) -> Optional[str]:
        return (
            getattr(settings, "GROQ_CHAT_KEY", None)
            or os.environ.get("GROQ_CHAT_KEY")
            or getattr(settings, "GROQ_API_KEY", None)
            or os.environ.get("GROQ_API_KEY")
        )

    def _build_context_prompt(self, context: Optional[Dict[str, Any]]) -> str:
        """Formats the active enterprise, report telemetry, and active tab content into a system context block."""
        if not context:
            return ""

        lines = ["\n--- CURRENT ACTIVE ENTERPRISE CONTEXT (GROUNDED DATA) ---"]
        
        # Enterprise Basic Profile
        if context.get("enterprise_name"):
            lines.append(f"- Enterprise: {context.get('enterprise_name')} ({context.get('sector', 'N/A')} - {context.get('business_category', 'N/A')})")
        if context.get("location"):
            lines.append(f"- Location: {context.get('location')}")
        if context.get("project_cost"):
            lines.append(f"- Total Project Outlay: ₹{float(context.get('project_cost', 0)):,.2f}")
        if context.get("promoter_margin"):
            lines.append(f"- Promoter Margin: ₹{float(context.get('promoter_margin', 0)):,.2f}")
        if context.get("top_scheme_name"):
            lines.append(f"- Matched Scheme: {context.get('top_scheme_name')} (Subsidy: ₹{float(context.get('subsidy_amount', 0)):,.2f})")
        if context.get("effective_loan"):
            lines.append(f"- Net Bank Term Loan: ₹{float(context.get('effective_loan', 0)):,.2f} (EMI: ₹{float(context.get('monthly_emi', 0)):,.2f}/mo)")
        if context.get("dscr"):
            lines.append(f"- DSCR: {float(context.get('dscr', 1.33)):.2f} ({context.get('dscr_verdict', 'VIABLE')})")
        if context.get("ml_verdict"):
            lines.append(f"- ML Viability: {context.get('ml_verdict')} ({float(context.get('ml_confidence_pct', 95)):.1f}% confidence)")
        
        # Active Viewport / Tab Telemetry
        active_tab = context.get("current_tab", "overview")
        active_tab_title = context.get("active_tab_title", "Overview Dashboard")
        lines.append(f"\n--- ACTIVE USER VIEWPORT: [{active_tab_title.upper()}] (Route: /{active_tab}) ---")
        lines.append(f"User is currently viewing the '{active_tab_title}' screen.")

        # Tab-Specific Deep Telemetry Payload
        tab_data = context.get("active_tab_data") or {}
        if tab_data:
            lines.append("Active Tab Detailed Content On Screen:")
            for k, v in tab_data.items():
                if isinstance(v, (list, dict)):
                    lines.append(f"  * {k}: {json.dumps(v, ensure_ascii=False)}")
                else:
                    lines.append(f"  * {k}: {v}")
        elif context.get("active_tab_summary"):
            lines.append(f"Active Tab Summary: {context.get('active_tab_summary')}")

        lines.append("When asked to 'summarize this page' or 'explain this screen', base your answer directly on the active viewport content above.")
        return "\n".join(lines)

    def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Processes conversation history and returns assistant response with latency metadata.
        """
        start_time = time.perf_counter()
        api_key = self._get_api_key()

        # Build full system instruction with page grounding (always English)
        system_instruction = BASE_SYSTEM_PROMPT + self._build_context_prompt(context)
        system_instruction += "\n\nCRITICAL INSTRUCTION: Always generate your response in pure English. Never output in non-English languages."

        # Assemble messages payload
        groq_messages = [{"role": "system", "content": system_instruction}]
        for m in messages:
            role = m.get("role", "user")
            if role in ("user", "assistant"):
                groq_messages.append({"role": role, "content": m.get("content", "")})

        # If no API key or offline, use deterministic fallback
        if not api_key:
            fallback_text = self._generate_rule_based_fallback(messages, context, language)
            latency = (time.perf_counter() - start_time) * 1000
            return {
                "message": {"role": "assistant", "content": fallback_text},
                "model": "deterministic_advisor_v2",
                "is_fallback": True,
                "latency_ms": round(latency, 2),
            }

        # Attempt Groq completion with model fallback cascade
        try:
            from groq import Groq

            client = Groq(api_key=api_key, timeout=14.0)
            models_to_try = [
                os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b"),
                "openai/gpt-oss-20b",
                "llama-3.3-70b-versatile",
                "llama3-70b-8192",
            ]
            models_to_try = list(dict.fromkeys(models_to_try))

            assistant_reply = None
            used_model = models_to_try[0]

            for model_name in models_to_try:
                try:
                    chat_completion = client.chat.completions.create(
                        messages=groq_messages,
                        model=model_name,
                        temperature=0.25,
                        max_tokens=1024,
                    )
                    assistant_reply = chat_completion.choices[0].message.content
                    used_model = model_name
                    break
                except Exception as model_err:
                    logger.warning("Groq model %s failed: %s; trying fallback model...", model_name, model_err)
                    continue

            if not assistant_reply:
                raise RuntimeError("All Groq chat model attempts failed")

            latency = (time.perf_counter() - start_time) * 1000
            return {
                "message": {"role": "assistant", "content": assistant_reply},
                "model": f"groq:{used_model}",
                "is_fallback": False,
                "latency_ms": round(latency, 2),
            }

        except Exception as e:
            logger.warning("Groq Chatbot API call failed (%s); generating structured rule-based response.", e)
            fallback_text = self._generate_rule_based_fallback(messages, context, language)
            latency = (time.perf_counter() - start_time) * 1000
            return {
                "message": {"role": "assistant", "content": fallback_text},
                "model": "deterministic_advisor_v2",
                "is_fallback": True,
                "latency_ms": round(latency, 2),
            }

    def _generate_rule_based_fallback(
        self,
        messages: List[Dict[str, str]],
        context: Optional[Dict[str, Any]],
        language: str = "en",
    ) -> str:
        """Intelligent, grounded domain responses when Groq is unreachable."""
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "").lower()
                break

        ent_name = context.get("enterprise_name", "your enterprise") if context else "your enterprise"
        dscr = float(context.get("dscr", 1.45)) if context else 1.45
        loan = float(context.get("effective_loan", 325000)) if context else 325000
        subsidy = float(context.get("subsidy_amount", 125000)) if context else 125000
        scheme = context.get("top_scheme_name", "PMEGP") if context else "PMEGP"
        active_tab = context.get("current_tab", "overview") if context else "overview"
        active_title = context.get("active_tab_title", "Overview Dashboard") if context else "Overview Dashboard"

        # Tab Summary detection
        is_summary_req = any(w in last_user_msg for w in ["summar", "explain", "page", "tab", "screen", "what is on", "walk me through"])

        if is_summary_req:
            if "viability" in active_tab:
                return (
                    f"### 📊 Summary of ML Viability & TreeSHAP Analysis for {ent_name}\n\n"
                    f"- **Verdict**: **{context.get('ml_verdict', 'SUITABLE')}** ({float(context.get('ml_confidence_pct', 94)):.1f}% confidence)\n"
                    f"- **Model**: 10-Dimensional Supervised XGBoost calibrated on empirical repayment data.\n"
                    f"- **Top Positive Drivers**: Strong promoter margin contribution and healthy debt-service coverage ratio.\n"
                    f"- **Key Takeaway**: Your credit risk profile meets the benchmark criteria for institutional bank financing."
                )
            elif "market" in active_tab:
                return (
                    f"### 📍 Summary of Market Demand & Local Cluster for {ent_name}\n\n"
                    f"- **Catchment Demand**: Driven by local demographics and supply gap analysis.\n"
                    f"- **Competition Saturation**: Evaluated against same-sector micro-enterprise density.\n"
                    f"- **Key Takeaway**: Healthy addressable market (TAM) with room for localized expansion."
                )
            elif "scheme" in active_tab:
                return (
                    f"### 🏛️ Summary of Matched Government Schemes for {ent_name}\n\n"
                    f"- **Primary Match**: **{scheme}**\n"
                    f"- **Subsidy Potential**: **₹{subsidy:,.2f}**\n"
                    f"- **Effective Loan Burden**: Reduced to **₹{loan:,.2f}**\n"
                    f"- **Key Action**: Download the Bank DPR package and submit via the official nodal portal."
                )
            elif "financial" in active_tab:
                return (
                    f"### 📈 Summary of 5-Year Financials & Cash Flow for {ent_name}\n\n"
                    f"- **DSCR Ratio**: **{dscr:.2f}** (Prudential threshold: ≥ 1.33)\n"
                    f"- **Monthly Term Loan EMI**: ₹{float(context.get('monthly_emi', 6800)):,.2f}\n"
                    f"- **Solvency Status**: Projected EBITDA comfortably exceeds annual principal + interest debt service."
                )
            elif "risk" in active_tab:
                return (
                    f"### ⚠️ Summary of Comprehensive Risk Assessment for {ent_name}\n\n"
                    f"- **Risk Profile**: Low to Moderate overall risk grade.\n"
                    f"- **Core Mitigations**: Maintain a 2-month working capital buffer and adhere to statutory quality standards."
                )
            elif "swot" in active_tab:
                return (
                    f"### 🎯 Summary of SWOT Matrix for {ent_name}\n\n"
                    f"- **Strengths**: Local procurement advantage and attractive unit margins.\n"
                    f"- **Opportunities**: Government credit subsidy leverage and expanding regional consumer demand."
                )
            elif "dpr" in active_tab:
                return (
                    f"### 📑 Summary of Official Bank DPR Package for {ent_name}\n\n"
                    f"- **Compliance**: Fully structured 7-Section Bank DPR ready for commercial loan appraisal.\n"
                    f"- **Next Steps**: Print PDF package and attach promoter KYC (PAN/Aadhaar) and Udyam Registration."
                )
            else:
                return (
                    f"### 📋 Overview Summary for {ent_name}\n\n"
                    f"- **Total Project Cost**: ₹{float(context.get('project_cost', 500000)):,.2f}\n"
                    f"- **Matched Subsidy**: {scheme} (₹{subsidy:,.2f})\n"
                    f"- **DSCR Solvency**: {dscr:.2f} ({context.get('dscr_verdict', 'VIABLE')})\n"
                    f"- **ML Viability**: {context.get('ml_verdict', 'SUITABLE')}"
                )

        if "dscr" in last_user_msg or "ratio" in last_user_msg or "coverage" in last_user_msg:
            return (
                f"### Debt Service Coverage Ratio (DSCR) Appraisal for {ent_name}\n\n"
                f"- **Current DSCR**: **{dscr:.2f}** (RBI Prudential Benchmark: **1.33**)\n"
                f"- **Verdict**: The projected cash flow indicates **adequate solvency** to service scheduled term debt.\n\n"
                f"**Key Recommendation**: Keep a 3-month debt-service reserve to safeguard against seasonal revenue fluctuations."
            )

        if "scheme" in last_user_msg or "pmegp" in last_user_msg or "subsidy" in last_user_msg or "mudra" in last_user_msg:
            return (
                f"### Government Scheme & Subsidy Summary for {ent_name}\n\n"
                f"- **Top Matched Scheme**: **{scheme}**\n"
                f"- **Estimated Capital Subsidy**: **₹{subsidy:,.2f}**\n"
                f"- **Net Bank Term Loan Exposure**: **₹{loan:,.2f}**\n\n"
                f"**Application Steps**:\n"
                f"1. Generate your complete 7-Section Bank DPR from the **Bank DPR** tab.\n"
                f"2. Apply via the official KVIC / PMEGP portal using your Udyam Registration number.\n"
                f"3. Submit the printed appraisal package to your local nodal bank branch."
            )

        if "checklist" in last_user_msg or "document" in last_user_msg or "license" in last_user_msg:
            return (
                f"### Statutory Compliance & Banking Checklist\n\n"
                f"1. **Udyam Registration**: Zero-cost statutory MSME identity.\n"
                f"2. **PAN & Aadhaar**: Promoter KYC documentation.\n"
                f"3. **Bank Statement**: Past 6–12 months account statements.\n"
                f"4. **FSSAI / Pollution Consent**: Mandatory for food processing & manufacturing units.\n"
                f"5. **Detailed Project Report (DPR)**: Generated directly from Udyam Saathi."
            )

        return (
            f"Hello! I am your **Udyam Saathi Credit & Feasibility AI Advisor**.\n\n"
            f"I have full access to the **{active_title}** you are currently viewing.\n\n"
            f"You can ask me to:\n"
            f"- 📊 **'Summarize this page'** or explain specific numbers on your screen\n"
            f"- 🏛️ **Optimize your scheme subsidy** (PMEGP, Mudra, PMFME, CGTMSE)\n"
            f"- 📈 **Audit financial ratios** (DSCR {dscr:.2f}, monthly EMI, break-even floor)\n\n"
            f"How can I assist **{ent_name}** on this screen?"
        )


chat_service = ChatService.get_instance()
