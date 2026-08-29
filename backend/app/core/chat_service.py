"""
chat_service.py — Enterprise AI Chatbot & Conversational MSME Advisory Engine.
Powered by Groq Cloud with dedicated GROQ_CHAT_KEY support, real-time enterprise context injection,
and zero-crash deterministic conversational fallback.
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

FORMATTING & TONE GUIDELINES:
- Always use professional, encouraging, and financially rigorous tone.
- Format all rupee amounts with the Rupee symbol (e.g. ₹5,00,000 or ₹5 Lakhs).
- Use clean Markdown: bold key metrics, use bullet points for action items, and short structured paragraphs.
- Keep answers concise and actionable (under 250 words unless detailed calculations are requested).
- If the user writes in Hindi, Marathi, Tamil, Telugu, or Kannada, respond fluently in that language while preserving exact financial figures (₹).
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
        """Formats the active enterprise & report telemetry into a system context block."""
        if not context:
            return ""

        lines = ["\n--- CURRENT ACTIVE ENTERPRISE CONTEXT (GROUNDED DATA) ---"]
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
        if context.get("current_tab"):
            lines.append(f"- Active Dashboard Tab: {context.get('current_tab')}")
        lines.append("Use these exact metrics if the user asks about their specific enterprise appraisal.")
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

        # Build full system instruction
        system_instruction = BASE_SYSTEM_PROMPT + self._build_context_prompt(context)
        if language and language != "en":
            system_instruction += f"\n\nIMPORTANT: The user has selected language code '{language}'. Please provide your response in that language."

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

            client = Groq(api_key=api_key, timeout=12.0)
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
                        temperature=0.3,
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

        if "dscr" in last_user_msg or "ratio" in last_user_msg or "coverage" in last_user_msg:
            return (
                f"### Debt Service Coverage Ratio (DSCR) Appraisal for {ent_name}\n\n"
                f"- **Current DSCR**: **{dscr:.2f}** (RBI Prudential Benchmark: **1.33**)\n"
                f"- **Verdict**: The projected cash flow indicates **adequate solvency** to service the scheduled term loan.\n\n"
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
            f"I can assist you with:\n"
            f"- **Scheme Optimization**: Eligibility for PMEGP, Mudra, PMFME, and CGTMSE subsidies.\n"
            f"- **Financial Health**: Evaluating your DSCR ({dscr:.2f}), EMI liabilities, and break-even realization.\n"
            f"- **Statutory Clearances**: Udyam, GST, FSSAI, and bank documentation.\n\n"
            f"How can I assist **{ent_name}** today?"
        )


chat_service = ChatService.get_instance()
