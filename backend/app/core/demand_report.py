"""Render persisted demand scenarios without altering financial calculations."""
from html import escape
import math


def _number(value):
    if value is None:
        return "—"
    if value == 0:
        return "0"
    rounded = round(value, 1-int(math.floor(math.log10(abs(value)))))
    return f"{rounded:,.0f}" if abs(rounded) >= 10 else f"{rounded:g}"


def _sections(f):
    yield "text", "Business-specific demand forecast"
    for key in ('industry', 'business_model', 'product_service', 'target_customer', 'buyer_base', 'location',
                'maturity', 'sales_channel', 'buying_cycle', 'method', 'method_reason', 'equation_with_units'):
        yield "text", key.replace('_', ' ') + ": " + str(f[key])
    yield "text", "Provisional scenario range; inputs are hypotheses, not verified sales." if f['provisional'] else "Forecast based on supplied business evidence."
    yield "text", f"Effective monthly capacity: approximately {_number(f['effective_monthly_capacity'])} {f['output_unit']}; period: {f['period']}."
    keys = ('monthly_demand_units', 'realized_monthly_units', 'monthly_active_buyers', 'monthly_transactions',
            'daily_unit_sales', 'monthly_revenue_inr', 'capacity_utilization_pct')
    rows = [['Scenario', 'Monthly demand', 'Monthly realized units', 'Demand active buyers', 'Demand transactions', 'Daily units', 'Monthly revenue (INR)', 'Effective capacity used (%)']]
    groups = []
    for name, scenario in f['scenarios'].items():
        rows.append([name] + [_number(scenario[key]) for key in keys])
        groups.append((name, scenario['inputs']))
    yield "table", rows
    yield "text", "Buyer and transaction counts describe obtainable demand before the capacity limit; realized sales and revenue apply that limit."
    for key in ('category_demand', 'independent_cross_check'):
        item = f.get(key)
        if item:
            yield "text", f"{key.replace('_', ' ')}: approximately {_number(item['monthly_demand_units'])} {f['output_unit']}/month. {item['equation_with_units']}. {item['basis']}"
            groups.append((key, item['inputs']))
    for name, inputs in groups:
        yield "text", name.replace('_', ' ') + " assumption table"
        table = [['Input', 'Value', 'Units', 'Period', 'Source and evidence', 'Confidence', 'Justification']]
        for i in inputs:
            source = i['source_kind'] + ": " + i['source'] + (" ("+i['evidence_path']+")" if i.get('evidence_path') else "")
            table.append([i['role'], str(i['value']), i['units'], i['reference_period'], source, i['confidence'], i['reasoning']])
        yield "table", table
    for key in ('acquisition_constraints', 'reality_review', 'reconciliation', 'warnings', 'uncertainty_drivers', 'limitations', 'missing_data'):
        item = f.get(key)
        if item:
            yield "text", key.replace('_', ' ') + ": " + ("; ".join(item) if isinstance(item, list) else str(item))
    if f.get('review_status') == 'review_required':
        yield "text", "Demand assumptions still require review; report figures are provisional."


def demand_markdown(forecast):
    if not forecast:
        return ""
    clean = lambda s: escape(str(s)).replace('|', '\\|').replace('\n', ' ')
    lines = []
    for kind, section in _sections(forecast):
        if kind == 'text':
            lines.append("\n" + clean(section) + "\n")
        else:
            lines.append("| " + " | ".join(clean(v) for v in section[0]) + " |")
            lines.append("| " + " | ".join('---' for _ in section[0]) + " |")
            lines.extend("| " + " | ".join(clean(v) for v in row) + " |" for row in section[1:])
    return "\n".join(lines)


def demand_html(forecast):
    if not forecast:
        return ""
    parts = ["<section>"]
    for kind, section in _sections(forecast):
        if kind == 'text':
            parts.append("<p>"+escape(section)+"</p>")
        else:
            parts.append("<table><thead><tr>"+"".join("<th>"+escape(str(v))+"</th>" for v in section[0])+"</tr></thead><tbody>")
            parts.extend("<tr>"+"".join("<td>"+escape(str(v))+"</td>" for v in row)+"</tr>" for row in section[1:])
            parts.append("</tbody></table>")
    return "".join(parts)+"</section>"
