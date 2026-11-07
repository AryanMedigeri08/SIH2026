import assert from 'node:assert/strict';
import { test } from 'node:test';
import { usesPlanningSnapshot, planningRent } from './planningHandoff.js';

const initial_data = { project_cost: 300000, sector: 'dairy', business_category: 'manufacturing', annual_turnover_estimate: 475000 };
const snapshot = { initial_data, machinery_schedule: { total_machinery_cost_inr: 165000 } };

test('planner sizing survives mount and numeric form serialization', () => {
  assert.equal(usesPlanningSnapshot({ ...initial_data, project_cost: '300000' }, snapshot), true);
});

test('legacy path and explicit sizing edits use the existing sizing flow', () => {
  assert.equal(usesPlanningSnapshot(initial_data, null), false);
  assert.equal(usesPlanningSnapshot({ ...initial_data, project_cost: 400000 }, snapshot), false);
  assert.equal(usesPlanningSnapshot({ ...initial_data, sector: 'repair' }, snapshot), false);
  assert.equal(usesPlanningSnapshot(initial_data, snapshot, 0.6), false);
});

test('planned rented premises retain explicit zero and positive rent', () => {
  assert.equal(planningRent({ premise_type: 'rented', monthly_rent: 0 }), 0);
  assert.equal(planningRent({ premise_type: 'rented', monthly_rent: '4000' }), 4000);
  assert.equal(planningRent({ premise_type: 'owned', monthly_rent: 4000 }), 0);
  assert.equal(planningRent({ premise_type: 'rented', monthly_rent: '' }), 2500);
});
