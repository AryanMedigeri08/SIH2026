import assert from 'node:assert/strict';
import test from 'node:test';
import { roleHome, isStaffRole } from '../src/services/roleRoutes.js';
import { firebaseStaffEmail } from '../src/services/staffIdentity.js';

test('only server-assigned staff roles route to staff dashboards', () => {
  assert.equal(roleHome('entrepreneur'), '/dashboard');
  assert.equal(roleHome('banker'), '/banker');
  assert.equal(roleHome('government'), '/government');
  assert.equal(roleHome('superadmin'), '/admin');
  assert.equal(roleHome('unknown'), '/login');
  assert.equal(isStaffRole('entrepreneur'), false);
  assert.equal(isStaffRole('banker'), true);
});

test('@udyam IDs map to Firebase-valid internal emails without changing ordinary emails', () => {
  assert.equal(firebaseStaffEmail('Alandi@udyam'), 'alandi@udyam.example.com');
  assert.equal(firebaseStaffEmail('Gov@udyam'), 'gov@udyam.example.com');
  assert.equal(firebaseStaffEmail('clerk@example.com'), 'clerk@example.com');
});
