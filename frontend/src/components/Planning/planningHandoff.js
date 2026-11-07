// Planner previews already contain the final engine's sizing. Preserve it on
// mount; an explicit cost/sector/capacity edit resumes the existing wizard sizing.
export function usesPlanningSnapshot(form, snapshot, capacityFactor = 0.8) {
  const initial = snapshot?.initial_data;
  return !!initial && capacityFactor === 0.8
    && Number(form.project_cost) === Number(initial.project_cost)
    && form.sector === initial.sector
    && form.business_category === initial.business_category;
}

export function planningRent(form) {
  if (form.premise_type !== 'rented') return 0;
  return form.monthly_rent !== '' && form.monthly_rent != null
    ? Number(form.monthly_rent) : 2500;
}
