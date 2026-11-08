// Only business/location inputs invalidate this advisory check; finance fields do not.
export function hybridInput(form) {
  return {
    state_name: form.state_name || '', district_name: form.district_name || '',
    block_name: form.block_name || '', village_name: form.village_name || '',
    enterprise_name: form.enterprise_name || '', business_category: form.business_category,
    sector: form.sector, idea_description: form.enterprise_idea ?? form.additional_business_details ?? '',
  };
}

export const hybridInputKey = form => JSON.stringify(hybridInput(form));
export const validHybridReview = (review, form) => !!review
  && [review.input_key, review.adopted_key].includes(hybridInputKey(form));
export const hybridStepReady = (review, form) => validHybridReview(review, form)
  && (review.choice === 'no' || (!!review.result && ['original', 'hybrid'].includes(review.selection)));

export function selectHybridPlan(form, review, selection) {
  if (!validHybridReview(review, form) || !review.result) throw new Error('This assessment is out of date. Evaluate again or keep your own idea.');
  const original = review.original_form;
  const next = {
    ...form,
    enterprise_name: selection === 'hybrid' ? review.result.hybrid_name : original.enterprise_name,
    enterprise_idea: selection === 'hybrid' ? review.result.hybrid_description : original.enterprise_idea,
  };
  return { form: next, review: { ...review, selection, adopted_key: selection === 'hybrid' ? hybridInputKey(next) : null } };
}

export function combinedBusinessContext(form) {
  return [...new Set([form.enterprise_idea?.trim(), form.additional_business_details?.trim()].filter(Boolean))].join('\n');
}
