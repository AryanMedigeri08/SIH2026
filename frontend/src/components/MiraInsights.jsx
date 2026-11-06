import React, { useState } from 'react';
import { MapPin, CheckCircle2, AlertTriangle, HelpCircle, ArrowRight } from 'lucide-react';
import { TranslatedText as T } from './TranslatedText';
import './miraInsights.css';

const money = value => value == null ? '—' : `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
const number = value => value == null ? '—' : Number(value).toLocaleString('en-IN');
const verdicts = { HIGH_OPPORTUNITY: 'Strong regional opportunity', MODERATE_OPPORTUNITY: 'Regional opportunity to explore', SATURATED_MARKET: 'Strong competition needs attention', CONSTRAINED_MARKET: 'Regional operating challenges', NOT_RECOMMENDED: 'Changes needed for this region', INSUFFICIENT_DATA: 'More local evidence needed' };
const isNumber = value => typeof value === 'number' && Number.isFinite(value);

function EvidenceList({ title, items = [], tone, icon: Icon }) {
  if (!items.length) return null;
  return <section className={`mira-evidence-list ${tone}`}><h3><Icon size={17} /><T text={title} /></h3><ul>{items.map((text, i) => <li key={i}><T text={text} /></li>)}</ul></section>;
}

export function CatchmentMap({ region }) {
  const market = region.market || {}, target = market.target_location || region.location || {};
  const lat = target.latitude ?? target.lat, lon = target.longitude ?? target.lon;
  const competitors = (market.classified_competitors || []).filter(item => isNumber(item.latitude) && isNumber(item.longitude) && isNumber(lat) && isNumber(lon));
  const dots = competitors.map((item, i) => {
    const x = (item.longitude - lon) * 111.32 * Math.cos(lat * Math.PI / 180), y = (item.latitude - lat) * 111.32;
    return { ...item, x, y, i };
  }).filter(item => Math.hypot(item.x, item.y) <= 10);
  const scenarios = (market.sensitivity_analysis || []).filter(item => item.radius_km === 5 || item.radius_km === 10);
  return <div className="mira-catchment"><svg viewBox="0 0 300 230" role="img" aria-label="Schematic business catchment within five and ten kilometres">
    <defs><pattern id="catchment-grid" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e9e2ef" strokeWidth=".6" /></pattern></defs>
    <rect width="300" height="230" fill="url(#catchment-grid)" /><circle cx="150" cy="115" r="100" fill="#ede1f329" stroke="#bfa7d2" strokeDasharray="4 4" /><circle cx="150" cy="115" r="50" fill="#e5d5f34d" stroke="#ac8bc5" />
    <text x="206" y="110" fill="#8d729f" fontSize="11">5 km</text><text x="251" y="110" fill="#8d729f" fontSize="11">10 km</text>
    {dots.map(item => <circle key={item.i} cx={150 + item.x * 10} cy={115 - item.y * 10} r="4" fill="#ba8056"><title>{item.enterprise_name || 'Registered business'} · {item.distance_km == null ? 'Distance approximate' : `${item.distance_km} km`}</title></circle>)}
    <circle cx="150" cy="115" r="8" fill="#744598" stroke="white" strokeWidth="3" /><text x="12" y="220" fontSize="10" fill="#8b7893">Schematic · north up · straight-line distance</text>
  </svg><div><h3><MapPin size={16} /><T text="Your local catchment" /></h3><p><T text={dots.length ? 'Dots show mapped registered businesses from the available records.' : 'No reliable mapped competitor coordinates are available for this view. An empty map does not mean no competition.'} /></p>
    {scenarios.map(item => <p key={item.radius_km}><strong>{item.radius_km} km · {number(item.competitors_count)}</strong> <T text="registered competitors in the available sample" /></p>)}
    <small><T text="Directory coverage, coordinate accuracy and travel routes affect this picture. Purchasing power and raw-material supply still need local checks." /></small></div></div>;
}

export function RegionalEvidenceCard({ region, accepted }) {
  if (!region) return null;
  const evidence = region.evidence || {}, market = region.market || {}, demand = market.demand_features || {}, supply = market.supply_metrics || {};
  const confidence = region.confidence || evidence.confidence || 'INSUFFICIENT_DATA';
  const scores = market.opportunity_indicators || {};
  return <section className="mira-insight-card" aria-label="Regional suitability assessment"><div className="mira-insight-heading"><span className="mira-kicker"><T text="Regional suitability" /></span><span className="mira-estimate-tag"><T text={`Evidence: ${confidence.replaceAll('_', ' ').toLowerCase()}`} /></span></div>
    <h2><T text={verdicts[region.recommendation] || 'Regional evidence for your idea'} /></h2><p><T text={evidence.plain_language_summary || 'The available data does not establish local suitability yet.'} /></p>
    <div className="mira-number-grid"><Metric label="Population in available records" value={demand.sources?.length && demand.population > 0 ? number(demand.population) : '—'} /><Metric label="Registered direct competitors" value={isNumber(supply.direct_competitors_count) ? number(supply.direct_competitors_count) : '—'} /><Metric label="Nearest mapped direct competitor" value={isNumber(supply.nearest_direct_competitor_km) ? `${supply.nearest_direct_competitor_km.toFixed(1)} km` : '—'} /></div>
    {Object.keys(scores).length > 0 && <div className="mira-evidence-bars">{[['supply_gap_score', 'Room in the market'], ['demand_support_score', 'Demand indicators'], ['accessibility_gap_score', 'Access opportunity']].filter(([key]) => isNumber(scores[key])).map(([key, label]) => <div key={key}><span><T text={label} /></span><meter min="0" max="100" value={scores[key]} /><strong>{Math.round(scores[key])}/100</strong></div>)}<small><T text="Model indicators from the available data; these scores are not a probability of business success." /></small></div>}
    <div className="mira-evidence-columns"><EvidenceList title="What supports the idea" items={evidence.top_positive_drivers} tone="positive" icon={CheckCircle2} /><EvidenceList title="What needs care" items={evidence.top_risk_factors} tone="risk" icon={AlertTriangle} /><EvidenceList title="What we still need to check" items={[...(evidence.missing_evidence || []), ...(evidence.data_quality_limitations || [])]} tone="unknown" icon={HelpCircle} /></div>
    <CatchmentMap region={region} />{accepted && <p className="mira-risk-acceptance"><T text="You explicitly chose to continue with these regional concerns." /></p>}
    {region.data_lineage?.length > 0 && <details><summary><T text="Sources and coverage" /></summary>{region.data_lineage.map((source, index) => <p key={index}><T text={source.name || source.source || source.description || 'Regional data source'} /></p>)}</details>}
  </section>;
}

function Metric({ label, value }) { return <div className="mira-metric"><span><T text={label} /></span><strong>{value}</strong></div>; }

export function FundingCard({ finance, projection, preview = false, compact = false }) {
  if (!finance) return null;
  const capital = finance.capital_structure || {}, costs = finance.cost_items || {};
  return <section className={`mira-insight-card mira-funding-card ${compact ? 'compact' : ''}`} aria-label="Financial planning breakdown">
    <div className="mira-insight-heading"><span className="mira-kicker"><T text={preview ? 'Reference planning scenario' : 'Your reviewed financial plan'} /></span><span className="mira-estimate-tag"><T text="Estimate" /></span></div>
    <h2>{money(finance.project_outlay)} <small><T text="total setup" /></small></h2>
    <div className="mira-cost-chart" role="img" aria-label="Setup cost allocation">{Object.entries(costs).filter(([, value]) => value > 0).map(([key, value], index) => <div key={key} style={{ flex: value, background: ['#79509f', '#ab8dc4', '#d1b8dd', '#61998d', '#c09a68'][index % 5] }} title={`${key.replaceAll('_', ' ')}: ${money(value)}`} />)}</div>
    <ul className="mira-cost-legend">{Object.entries(costs).filter(([, value]) => value > 0).map(([key, value]) => <li key={key}><T text={key.replaceAll('_', ' ')} /><strong>{money(value)}</strong></li>)}</ul>
    <div className="mira-number-grid"><Metric label="Required promoter equity" value={money(capital.required_promoter_equity)} /><Metric label={finance.own_funds_known === false ? 'Own cash assumed for this scenario' : 'Your available own funds'} value={money(finance.personal_contribution)} /><Metric label="Potential normal borrowing" value={money(finance.capital_deficit)} /><Metric label="Promoter margin shortfall" value={money(capital.equity_gap)} /></div>
    <p className="mira-finance-note"><T text="Potential borrowing is the funding gap, subject to lender approval. Subsidies and SCA are conditional; they are not cash in hand." /></p>
    {!compact && <details><summary><T text="Loan and SCA terms" /></summary><p>{finance.normal_loan.rate_pct}% · {finance.normal_loan.tenure_years} <T text="years" /> · {finance.normal_loan.moratorium_months} <T text="months grace" /> · <T text="Normal EMI" /> {money(finance.normal_loan.monthly_emi)}</p><p><T text="SCA terms" />: {capital.sca_interest_rate_pct}% · {capital.sca_tenure_years} <T text="years" /> · {capital.sca_moratorium_months} <T text="months grace" /></p></details>}
    {projection && <OperatingCard projection={projection} compact={compact} />}
  </section>;
}

function OperatingCard({ projection: p, compact }) {
  const maximum = Math.max(p.monthly_sales, p.monthly_expenses, Math.abs(p.monthly_after_debt), 1);
  return <div className="mira-operating"><h3><T text={p.basis === 'user_estimate' ? 'Your monthly operating estimates' : 'Illustrative monthly operating scenario'} /></h3>
    <div className="mira-operating-bars">{[['Monthly sales', p.monthly_sales], ['Running expenses', p.monthly_expenses], ['Cash after expenses and normal EMI', p.monthly_after_debt]].map(([label, amount], index) => <div key={label}><span><T text={label} /></span><div><i style={{ width: `${Math.abs(amount) / maximum * 100}%`, background: amount < 0 ? '#c86b61' : ['#7c539f', '#baa2cd', '#629c88'][index] }} /></div><strong>{money(amount)}</strong></div>)}</div>
    <div className="mira-number-grid"><Metric label="Operating margin before EMI" value={p.operating_margin_pct == null ? '—' : `${p.operating_margin_pct}%`} /><Metric label="Simple project payback (months)" value={p.simple_project_payback_months == null ? '—' : number(p.simple_project_payback_months)} /><Metric label="Break-even monthly sales" value={money(p.break_even_monthly_sales)} /></div>
    <p className="mira-finance-note"><T text={p.notice} /></p>{!compact && <details><summary><T text="Details to refine this estimate" /></summary><ul>{p.missing_details.map(item => <li key={item}><T text={item} /></li>)}</ul></details>}
  </div>;
}

export function OperatingPlanForm({ onSubmit, disabled, values = {} }) {
  const [draft, setDraft] = useState(() => Object.fromEntries(['monthly_sales', 'monthly_expenses', 'monthly_fixed_costs', 'variable_cost_pct'].map(key => [key, values[key]?.value ?? ''])));
  return <form className="mira-insight-card" onSubmit={event => { event.preventDefault(); onSubmit({ ...Object.fromEntries(Object.entries(draft).filter(([, value]) => value !== '').map(([key, value]) => [key, Number(value)])), operating_basis: 'user_estimate' }); }}>
    <h3><T text="Refine your operating plan" /></h3><p><T text="Use your own estimates if you know them. Running expenses include rent and exclude loan EMI." /></p>
    <div className="mira-operating-fields">{[['monthly_sales', 'Expected monthly sales'], ['monthly_expenses', 'Monthly running expenses']].map(([key, label]) => <label key={key}><T text={label} /><input type="number" min="0" max="10000000000" required step="0.01" value={draft[key]} onChange={event => setDraft(previous => ({ ...previous, [key]: event.target.value }))} /></label>)}</div>
    <details><summary><T text="Optional break-even inputs" /></summary><div className="mira-operating-fields">{[['monthly_fixed_costs', 'Fixed monthly costs', 10000000000], ['variable_cost_pct', 'Variable costs as % of sales', 100]].map(([key, label, max]) => <label key={key}><T text={label} /><input type="number" min="0" max={max} step="0.01" value={draft[key]} onChange={event => setDraft(previous => ({ ...previous, [key]: event.target.value }))} /></label>)}</div></details>
    <button className="mira-primary" disabled={disabled}><T text="Use my operating estimates" /></button>
  </form>;
}

export function RecommendationCards({ items = [], state, disabled, onChoose, onDiscuss, onCompare, onAlternatives }) {
  return <section className="mira-recommendations" aria-label="Business recommendations"><div className="mira-recommendation-heading"><div><span className="mira-kicker"><T text="Your regional shortlist" /></span><h2><T text="Businesses to explore" /></h2></div>{items.length > 1 && <button className="mira-secondary" onClick={onCompare} disabled={disabled}><T text="Compare businesses" /></button>}</div>
    {state.alternative_budget_basis && <p className="mira-finance-note"><T text={state.alternative_budget_basis} /></p>}
    {items.length < 3 && <p><T text="The current evidence supports fewer than three options. Mira will not invent extra feasible businesses." /></p>}
    {state.comparison_requested && <div className="mira-comparison"><table><caption><T text="Compare the same planning assumptions" /></caption><thead><tr><th><T text="Planning measure" /></th>{items.map(item => <th key={item.id}>{item.idea}</th>)}</tr></thead><tbody>{[['Setup cost', item => money(item.finance_preview?.project_outlay ?? item.outlay_range[0])], ['Required own equity', item => money(item.finance_preview?.capital_structure.required_promoter_equity)], ['Potential borrowing', item => money(item.finance_preview?.capital_deficit)], ['Monthly sales estimate', item => money(item.finance_preview?.operating_projection.monthly_sales)], ['Cash after expenses and EMI', item => money(item.finance_preview?.operating_projection.monthly_after_debt)], ['Regional evidence', item => item.confidence || 'INSUFFICIENT_DATA']].map(([label, get]) => <tr key={label}><th><T text={label} /></th>{items.map(item => <td key={item.id}>{get(item)}</td>)}</tr>)}</tbody></table></div>}
    <div className="mira-recommendation-grid">{items.map((item, index) => <article className="mira-recommendation" key={item.id}><span className="mira-option-number">0{index + 1}</span><h3>{item.idea}</h3><p><T text={item.description} /></p><p className="mira-why"><CheckCircle2 size={16} /><T text={item.why_region} /></p>
      <span className="mira-estimate-tag"><T text={item.provisional ? 'Provisional · local checks needed' : 'Screened against available regional evidence'} /></span>
      <p><strong>ODOP · </strong><T text={item.odop?.aligned ? `Sector connection to ${item.odop.product}; product eligibility still needs checking.` : item.odop?.product ? `District product: ${item.odop.product}. No sector alignment established.` : 'No verified district ODOP record available.'} /></p>
      <FundingCard finance={item.finance_preview} projection={item.finance_preview?.operating_projection} preview compact />
      <details open={state.discussed_recommendation_id === item.id}><summary><T text="Why this business, how to start, and risks" /></summary><p><T text={item.requirements} /></p><p><T text={item.market_evidence} /></p><RegionalEvidenceCard region={item.regional_assessment} /></details>
      <div className="mira-recommendation-actions"><button className="mira-primary" disabled={disabled} onClick={() => onChoose(item.id)}><T text="Explore this business" /><ArrowRight size={16} /></button><button className="mira-secondary" disabled={disabled} onClick={() => onDiscuss(item.id)}><T text="Discuss this option" /></button></div>
    </article>)}</div><button className="mira-secondary" disabled={disabled} onClick={onAlternatives}><T text="None of these · Find other options" /></button>
  </section>;
}
