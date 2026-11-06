"""Answer common follow-up questions from saved evidence without selecting an idea."""
import re
from app.core import onboarding as base


def discuss(text, state):
    lower = text.lower().strip()
    if not (re.search(r'\b(compare|details|explain|why|how|what|profit|risk|demand|competition|loan|equity|odop|cost)\b', lower) and
            (state.get('recommendations') or state.get('regional') or state.get('assessment'))):
        return None
    items = state.get('recommendations') or []
    match = re.search(r'(?:option|idea|business|recommendation)\s*([123])\b|\b(first|second|third)\b', lower)
    index = int(match[1])-1 if match and match[1] else {'first': 0, 'second': 1, 'third': 2}.get(match[2] if match else '', -1)
    named = next((item for item in items if item['idea'].lower() in lower), None)
    if index >= len(items) and match:
        return 'That option is not in the current shortlist. Choose one of the displayed businesses.'
    candidates = [named or items[index]] if named or index >= 0 else items
    if candidates:
        state['comparison_requested'] = len(candidates) > 1
        if len(candidates) == 1:
            state['discussed_recommendation_id'] = candidates[0]['id']
    else:
        from app.core.onboarding_insights import insights
        data = insights(state)
        candidates = [{'idea': base.value(state, 'idea', 'Your business'), 'regional_assessment': state.get('regional'),
            'finance_preview': state.get('assessment') or data.get('finance_preview'), 'odop': state.get('odop'),
            'market_evidence': (state.get('regional') or {}).get('evidence', {}).get('plain_language_summary', '')}]
        if candidates[0]['finance_preview'] and not candidates[0]['finance_preview'].get('operating_projection'):
            candidates[0] = {**candidates[0], 'finance_preview': {**candidates[0]['finance_preview'], 'operating_projection': data.get('operating_projection')}}
    replies = []
    for item in candidates:
        finance = item.get('finance_preview') or {}
        projection = finance.get('operating_projection') or {}
        evidence = (item.get('regional_assessment') or {}).get('evidence') or {}
        parts = [item['idea'] + '.']
        if re.search(r'profit|revenue|expense|break.?even|earn|income', lower):
            if projection:
                parts.append(f"The planning scenario has monthly sales of ₹{projection['monthly_sales']:,.0f}, expenses of ₹{projection['monthly_expenses']:,.0f}, and ₹{projection['monthly_after_debt']:,.0f} left after the normal-loan EMI. This is an estimate, not verified demand or guaranteed profit.")
                if 'break' in lower:
                    parts.append(f"Break-even monthly sales are ₹{projection['break_even_monthly_sales']:,.0f}." if projection.get('break_even_monthly_sales') is not None else 'A break-even sales figure needs fixed expenses and variable costs. A break-even date also needs monthly sales ramp-up; simple payback is a different measure.')
            else:
                parts.append('Profitability needs setup costs, expected monthly sales, operating expenses and financing terms first.')
        elif re.search(r'loan|equity|cost|invest|budget', lower) and finance:
            parts.append(f"Reference project cost: ₹{finance['project_outlay']:,.0f}. Required promoter equity: ₹{finance['capital_structure']['required_promoter_equity']:,.0f}. Potential normal borrowing: ₹{finance['capital_deficit']:,.0f}. Loan and subsidy approval remain conditional.")
        elif 'odop' in lower:
            odop = item.get('odop') or {}
            parts.append(f"The district product is {odop['product']}. " + ('The sector overlaps; product-level alignment still needs checking.' if odop.get('aligned') else 'A product or value-chain connection has not been established.') if odop.get('product') else 'No verified district ODOP record is available for this option.')
        else:
            parts += [item.get('why_region', ''), item.get('market_evidence', '')]
            parts += evidence.get('top_risk_factors', []) + evidence.get('missing_evidence', [])
            if not any(parts[1:]):
                parts.append('Local demand, competition, raw-material access and infrastructure have not been established with the available evidence.')
        replies.append(' '.join(part for part in parts if part))
    return '\n\n'.join(replies) + '\n\nYour selection and confirmed answers have not changed. You can explore an option, compare them, request alternatives or describe a change.'
