import { hybridStepReady, selectHybridPlan } from '../Wizard/odopHybridState.js';

// Adapt the planner's original inputs to the shared, optional advisory step.
// Keep the original catalogue ID: adopting a hybrid must not change cost tiers.
export function planningHybridForm(form, choices) {
  const business = choices.find(item => item.id === form.business_id);
  return {
    state_name: form.state_name, district_name: form.district_name,
    block_name: form.block_name, village_name: form.village_name,
    enterprise_name: business?.name || form.idea_description.trim().slice(0, 160),
    enterprise_idea: form.idea_description,
    sector: business?.sector || form.custom_sector,
    business_category: business?.business_category || form.custom_category,
  };
}

export function planningPayload(form, path, choices, review) {
  const payload = {
    ...form, path, business_id: path === 'idea_only' ? form.business_id : null,
    own_cash: form.own_cash === '' ? null : Number(form.own_cash),
    monthly_rent: form.premise_type === 'rented' ? Number(form.monthly_rent) : 0,
  };
  if (path !== 'idea_only') return payload;
  const original = planningHybridForm(form, choices);
  if (!hybridStepReady(review, original)) throw new Error('Choose whether to check ODOP alignment before comparing plans.');
  if (review.choice === 'yes' && review.selection === 'hybrid') {
    const chosen = selectHybridPlan(original, review, 'hybrid').form;
    payload.enterprise_name = chosen.enterprise_name;
    payload.idea_description = chosen.enterprise_idea;
  }
  return payload;
}
