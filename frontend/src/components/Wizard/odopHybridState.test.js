import assert from 'node:assert/strict';
import { test } from 'node:test';
import { hybridInputKey, validHybridReview, hybridStepReady, selectHybridPlan, combinedBusinessContext } from './odopHybridState.js';

const form = { state_name: 'West Bengal', district_name: 'Bankura', enterprise_name: 'Dairy',
  sector: 'dairy', business_category: 'manufacturing', enterprise_idea: 'Make curd', additional_business_details: 'Existing cooperative tie-up',
  project_cost: 600000, margin_capital: 60000, tenure_years: 7, monthly_rent: 2500 };
const review = { choice: 'yes', input_key: hybridInputKey(form), original_form: { ...form },
  result: { hybrid_name: 'Curd in local food-safe clay pots', hybrid_description: 'Source pots from local artisans.' } };

test('No is ready without a score; Yes requires an explicit plan choice', () => {
  assert.equal(hybridStepReady({ ...review, result: null, choice: 'no' }, form), true);
  assert.equal(hybridStepReady(review, form), false);
  assert.equal(hybridStepReady({ ...review, selection: 'original' }, form), true);
});

test('Adoption is explicit, reversible, and preserves all financial fields', () => {
  const chosen = selectHybridPlan(form, review, 'hybrid');
  assert.equal(chosen.form.enterprise_name, review.result.hybrid_name);
  for (const key of ['project_cost','margin_capital','tenure_years','monthly_rent','sector','business_category']) {
    assert.equal(chosen.form[key], form[key]);
  }
  assert.equal(hybridStepReady(chosen.review, chosen.form), true);
  const restored = selectHybridPlan(chosen.form, chosen.review, 'original');
  assert.deepEqual(restored.form, form);
});

test('Business or location edits invalidate old scores; finance edits do not', () => {
  assert.equal(validHybridReview(review, { ...form, district_name: 'Another district' }), false);
  assert.equal(validHybridReview(review, { ...form, sector: 'repair' }), false);
  assert.equal(validHybridReview(review, { ...form, enterprise_idea: 'Another product' }), false);
  assert.equal(validHybridReview(review, { ...form, additional_business_details: 'More background' }), true);
  assert.equal(validHybridReview(review, { ...form, project_cost: 900000 }), true);
  assert.throws(() => selectHybridPlan({ ...form, enterprise_name: 'New idea' }, review, 'hybrid'));
});

test('The final context preserves the chosen idea and supplementary background', () => {
  const chosen = selectHybridPlan(form, review, 'hybrid');
  assert.equal(combinedBusinessContext(chosen.form), `${review.result.hybrid_description}\n${form.additional_business_details}`);
  assert.equal(chosen.form.additional_business_details, form.additional_business_details);
});
