import { SECTOR_CAPITAL_MULTIPLIERS } from '../Wizard/wizardSizing.js';
// Map confirmed conversation values to existing API contracts, not new formulas.
export function businessContext(draft) {
  const a = draft.answers;
  const known = value => value && !['unknown', 'none'].includes(String(value).trim().toLowerCase());
  return [a.idea, known(a.skills) && `Skills: ${a.skills}`, known(a.resources) && `Resources: ${a.resources}`,
    known(a.preferences) && `Preferences: ${a.preferences}`, a.equipment_quote != null && `Equipment quote: INR ${a.equipment_quote}`]
    .filter(Boolean).join('\n');
}

export function conversationForm(draft, profile, choices) {
  const a = draft.answers;
  const item = choices.find(choice => choice.id === a.business_id);
  return {
    ...Object.fromEntries(['state_name','district_name','block_name','village_name'].map(key => [key, draft.location[key]])),
    promoter_name: profile.name, promoter_category: profile.promoter_category || 'general', gender: profile.gender || 'Unspecified',
    is_rural: draft.location.is_rural ?? true, premise_type: a.premise_type,
    monthly_rent: a.premise_type === 'rented' ? (a.monthly_rent ?? 2500) : 0,
    enterprise_name: a.enterprise_name || item?.name || a.idea?.slice(0, 160) || 'Enterprise',
    enterprise_idea: a.idea || '', sector: item?.sector || a.sector || 'general',
    business_category: item?.business_category || a.business_category || 'manufacturing',
    language: draft.language,
  };
}

export function conversationPlanningPayload(draft, profile, choices) {
  if (!['idea_only', 'budget_only'].includes(draft.journey)) throw new Error('Choose a planning journey.');
  if (!draft.location?.confirmed || !draft.answers.review_confirmed) throw new Error('Confirm the location and your answers first.');
  const form = conversationForm(draft, profile, choices);
  const a = draft.answers;
  const description = businessContext(draft);
  if (description.length > 800) throw new Error('Please shorten the business details to 800 characters.');
  return {
    path: draft.journey, language: draft.language,
    business_id: draft.journey === 'idea_only' ? a.business_id : null,
    idea_description: description, enterprise_name: draft.journey === 'idea_only' ? form.enterprise_name : '',
    own_cash: a.own_cash ?? null, machinery_quote: a.equipment_quote ?? null,
    custom_sector: a.sector || 'general', custom_category: a.business_category || 'manufacturing',
    ...Object.fromEntries(['state_name','district_name','block_name','village_name','promoter_name','promoter_category','gender','is_rural','premise_type','monthly_rent'].map(key => [key, form[key]])),
  };
}

// Same asset-driven sizing, turnover defaults and term boundary as the wizard.
// The machinery schedule is supplied by the existing backend endpoint.
export function conversationExistingPayload(draft, profile, choices, schedule) {
  const form = conversationForm(draft, profile, choices);
  const a = draft.answers;
  if (!draft.location?.confirmed || !a.review_confirmed || a.own_cash == null) throw new Error('Confirm your location, own money and answers first.');
  const machinery = schedule?.total_machinery_cost_inr;
  const projectCost = machinery > 0 ? Math.round((machinery / 0.55) / 1000) * 1000 : a.project_cost || 900000;
  const context = businessContext(draft);
  if (context.length > 1000) throw new Error('Please shorten the business details to 1000 characters.');
  return { ...form, project_cost: projectCost, available_margin_capital: a.own_cash,
    margin_capital: a.own_cash, annual_turnover_estimate: a.annual_sales ?? Math.round(projectCost * (SECTOR_CAPITAL_MULTIPLIERS[form.sector] || 1.30) * .80 / 5000) * 5000,
    tenure_years: projectCost <= 140000 ? 3 : 7, moratorium_months: projectCost <= 140000 ? 3 : 6,
    additional_business_details: context,
  };
}
