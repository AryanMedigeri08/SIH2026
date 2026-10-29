"""Read-only forecast appendix. Escape all user/model text in exported HTML."""
from html import escape
import json


def forecast_html(forecast):
    if not forecast:
        return ""
    e = lambda value: escape(str(value), quote=True)
    annual = forecast.get("annual_sales", {})
    result = ['<section style="margin-top:24px;page-break-inside:auto"><h2>Estimated Year-1 Gross Sales</h2>',
              '<p>Provisional forecast. Demand and prices are assumptions unless independently verified. Existing DSCR and expense formulas are unchanged.</p>']
    if forecast.get("status") == "manual_fallback":
        result.append('<p>Entered estimate retained; automatic demand/capacity validation was unavailable.</p>')
    result.append('<table><tr><th>Scenario</th><th>Year-1 sales (INR)</th></tr>')
    for scenario, revenue in annual.items():
        result.append(f'<tr><td>{e(scenario)}</td><td>{float(revenue):,.2f}</td></tr>')
    result.append('</table><table><tr><th>Month</th><th>Product/channel</th><th>Demand</th><th>Units sold</th><th>Price INR/unit</th><th>Revenue INR</th></tr>')
    for month in forecast.get("monthly_scenarios", {}).get("base", []):
        for product in month["products"]:
            result.append(f'<tr><td>{e(month["month"])}</td><td>{e(product["name"])} / {e(product["channel"])} ({e(product["unit"])})</td>'
                          f'<td>{product["obtainable_demand"]:,.2f}</td><td>{product["units_sold"]:,.2f}</td>'
                          f'<td>{product["average_selling_price"]:,.2f}</td><td>{product["revenue"]:,.2f}</td></tr>')
    result.append('</table><h3>Indicative machinery</h3>')
    for item in forecast.get("selected_equipment", []):
        result.append(f'<p>{e(item["business_name"])}: {e(item["typical_capacity"])}; INR {item["total_machinery_cost_inr"]:,.0f}. Supplier confirmation required.</p>')
    plan = forecast.get("accepted_plan", {})
    result.append('<h3>Assumptions and provenance</h3>')
    for p in plan.get("products", []):
        result.append(f'<h4>{e(p["name"])} — {e(p["channel"])}</h4><p>{e(p["method_reason"])}</p>')
        for name, source in {**p["assumptions"], "conversion": p["output_per_input"], "capacity": p["capacity_basis"]}.items():
            result.append(f'<p><b>{e(name)}</b> ({e(source["unit"])}): {e(source["source_kind"])}, {e(source["confidence"])} confidence. {e(source["reasoning"])}</p>')
        result.append(f'<p>Accepted monthly drivers and prices: {e(json.dumps(p["scenarios"], ensure_ascii=False))}</p>')
    for warning in forecast.get("warnings", []) + forecast.get("limitations", []):
        result.append(f'<p>{e(warning)}</p>')
    result.append(f'<p>Calculation version: {e(forecast.get("version", ""))}; evidence hash: {e(forecast.get("input_hash", ""))}</p></section>')
    return "".join(result)


def forecast_markdown(forecast):
    if not forecast:
        return ""
    lines = ["\n## Estimated Year-1 Gross Sales", "Provisional forecast; existing DSCR/expense formulas remain unchanged."]
    for key, value in forecast.get("annual_sales", {}).items():
        lines.append(f"{key}: INR {value:,.2f}")
    # JSON code block is an auditable snapshot without interpreting model text as Markdown.
    safe = json.dumps(forecast, indent=2, ensure_ascii=False).replace("`", "\\u0060")
    lines.extend(["Accepted forecast, assumptions and source snapshot:", "```json", safe, "```"])
    return "\n".join(lines)
