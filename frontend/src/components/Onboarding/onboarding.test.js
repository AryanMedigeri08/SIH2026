import assert from 'node:assert/strict';
import { test } from 'node:test';
import { copyRows, languages, copy, registrationSteps } from './copy.js';
import { conversationForm, conversationExistingPayload, conversationPlanningPayload } from './payloads.js';
import { SECTOR_CAPITAL_MULTIPLIERS } from '../Wizard/wizardSizing.js';
import { questionCopyRows } from './questionCopy.js';

const profile = { name: 'Test promoter', promoter_category: 'sc', gender: 'Female' };
const choices = [{ id: 'dairy_aggregation', name: 'Dairy', sector: 'dairy', business_category: 'manufacturing' }];
const draft = { journey: 'idea_only', language: 'hi', location: { confirmed: true, state_name: 'West Bengal', district_name: 'Bankura', block_name: 'Test block', village_name: 'Test village' },
  answers: { business_id: 'dairy_aggregation', idea: 'Make curd for local shops', enterprise_name: 'Test curd', own_cash: null, premise_type: 'rented', monthly_rent: 0, review_confirmed: true } };

test('Registration asks one field in the requested order, with six complete catalogues', () => {
  assert.deepEqual(registrationSteps, ['name','gender','category','phone','otp']);
  for (const [key, row] of Object.entries({ ...copyRows, ...questionCopyRows })) {
    assert.equal(row.length, languages.length, key);
    for (const value of row) assert.ok(value.trim().length > 0);
  }
});

test('Idea-only unknown money stays unknown; zero cash and zero rent are retained', () => {
  const payload = conversationPlanningPayload(draft, profile, choices);
  assert.equal(payload.own_cash, null);
  assert.equal(payload.monthly_rent, 0);
  assert.equal(payload.language, 'hi');
  assert.equal(payload.business_id, 'dairy_aggregation');
  assert.equal(payload.promoter_category, 'sc');
  assert.equal(conversationPlanningPayload({ ...draft, answers: { ...draft.answers, own_cash: 0 } }, profile, choices).own_cash, 0);
});

test('Budget-only has no invented original business and uses context as notes', () => {
  const current = { ...draft, journey: 'budget_only', answers: { ...draft.answers, business_id: undefined, idea: undefined, own_cash: 50000, skills: 'Tailoring' } };
  const payload = conversationPlanningPayload(current, profile, choices);
  assert.equal(payload.business_id, null);
  assert.equal(payload.enterprise_name, '');
  assert.match(payload.idea_description, /Tailoring/);
});

test('Explicitly selected ODOP idea reaches planning without changing catalogue cost tiers', () => {
  const current = { ...draft, answers: { ...draft.answers, enterprise_name: 'Curd in local clay pots', idea: 'Make curd in food-safe artisan pots.' } };
  const payload = conversationPlanningPayload(current, profile, choices);
  assert.equal(payload.enterprise_name, 'Curd in local clay pots');
  assert.match(payload.idea_description, /artisan pots/);
  assert.equal(payload.business_id, draft.answers.business_id);
  assert.equal(draft.answers.idea, 'Make curd for local shops');
});

test('Known-investment payload matches existing wizard sizing, sales and loan terms', () => {
  const current = { ...draft, journey: 'existing', answers: { ...draft.answers, own_cash: 60000 } };
  const payload = conversationExistingPayload(current, profile, choices, { total_machinery_cost_inr: 330000 });
  assert.equal(payload.project_cost, 600000);
  assert.equal(payload.available_margin_capital, 60000);
  assert.equal(payload.annual_turnover_estimate, 670000);
  assert.equal(payload.tenure_years, 7);
  assert.equal(payload.moratorium_months, 6);
  assert.equal(payload.monthly_rent, 0);
  assert.equal(payload.language, 'hi');
  assert.equal(SECTOR_CAPITAL_MULTIPLIERS.dairy, 1.40);
});

test('Known-investment micro boundary and explicit annual sales remain unchanged', () => {
  const current = { ...draft, journey: 'existing', answers: { ...draft.answers, own_cash: 0, project_cost: 140000, annual_sales: 180000 } };
  const payload = conversationExistingPayload(current, profile, choices, null);
  assert.equal(payload.tenure_years, 3); assert.equal(payload.moratorium_months, 3);
  assert.equal(payload.available_margin_capital, 0); assert.equal(payload.annual_turnover_estimate, 180000);
});

test('Unconfirmed location or answers cannot form an appraisal payload', () => {
  assert.throws(() => conversationPlanningPayload({ ...draft, location: { ...draft.location, confirmed: false } }, profile, choices));
  assert.throws(() => conversationExistingPayload(draft, profile, choices, null));
});

test('Long descriptions fail visibly instead of silently truncating business context', () => {
  assert.throws(() => conversationPlanningPayload({ ...draft, answers: { ...draft.answers, idea: 'x'.repeat(801) } }, profile, choices));
});
