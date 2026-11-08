import assert from 'node:assert/strict';
import { test } from 'node:test';
import { planningHybridForm, planningPayload } from './planningOdop.js';
import { hybridInputKey } from '../Wizard/odopHybridState.js';

const form = { business_id: 'dairy_aggregation', idea_description: 'Make curd for local shops',
  state_name: 'West Bengal', district_name: 'Bankura', block_name: 'Test block', village_name: 'Test village',
  own_cash: '', premise_type: 'rented', monthly_rent: '2500', promoter_category: 'sc', gender: 'Female',
  custom_sector: 'general', custom_category: 'manufacturing' };
const choices = [{ id: 'dairy_aggregation', name: 'Dairy', sector: 'dairy', business_category: 'manufacturing' }];
const original = planningHybridForm(form, choices);
const review = { choice: 'yes', input_key: hybridInputKey(original), original_form: original,
  result: { hybrid_name: 'Curd in local clay pots', hybrid_description: 'Make curd in food-safe pots from local artisans.' } };

test('Idea-only planning requires an ODOP choice before any calculation payload', () => {
  assert.throws(() => planningPayload(form, 'idea_only', choices, null));
  assert.throws(() => planningPayload(form, 'idea_only', choices, review));
  assert.throws(() => planningPayload({ ...form, district_name: 'Other' }, 'idea_only', choices, { ...review, selection: 'hybrid' }));
  assert.throws(() => planningPayload({ ...form, idea_description: 'Another idea' }, 'idea_only', choices, { ...review, selection: 'original' }));
});

test('Adoption sends the hybrid to appraisal without changing catalogue cost tiers or financial inputs', () => {
  const payload = planningPayload(form, 'idea_only', choices, { ...review, selection: 'hybrid' });
  assert.equal(payload.enterprise_name, review.result.hybrid_name);
  assert.equal(payload.idea_description, review.result.hybrid_description);
  assert.equal(payload.business_id, form.business_id);
  assert.equal(payload.own_cash, null);
  assert.equal(payload.monthly_rent, 2500);
  assert.equal(payload.promoter_category, form.promoter_category);
  assert.equal(payload.gender, form.gender);
  assert.equal(original.sector, 'dairy');
  assert.equal(form.idea_description, 'Make curd for local shops');
});

test('No and keeping the original after evaluation preserve the original idea', () => {
  for (const chosen of [{ ...review, choice: 'no', result: null }, { ...review, selection: 'original' }]) {
    const payload = planningPayload(form, 'idea_only', choices, chosen);
    assert.equal(payload.idea_description, form.idea_description);
    assert.equal(payload.enterprise_name, undefined);
  }
});

test('Financial edits preserve advice and budget-only never requires ODOP consent', () => {
  const payload = planningPayload({ ...form, own_cash: '70000' }, 'idea_only', choices, { ...review, selection: 'hybrid' });
  assert.equal(payload.own_cash, 70000);
  const budget = planningPayload({ ...form, own_cash: '70000' }, 'budget_only', choices, null);
  assert.equal(budget.business_id, null);
  assert.equal(budget.enterprise_name, undefined);
});

test('Custom idea uses its own description and selected sector/type', () => {
  const custom = planningHybridForm({ ...form, business_id: 'custom', custom_sector: 'repair', custom_category: 'service' }, choices);
  assert.equal(custom.enterprise_name, form.idea_description);
  assert.equal(custom.sector, 'repair');
  assert.equal(custom.business_category, 'service');
});
