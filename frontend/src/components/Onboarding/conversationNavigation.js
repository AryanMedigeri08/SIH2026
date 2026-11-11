export function previousQuestion(sequence, question, answers) {
  const index = question === 'ready' ? sequence.length : sequence.indexOf(question);
  return sequence.slice(0, Math.max(0, index)).reverse().find(field => Object.hasOwn(answers, field));
}

export function nextSavedQuestion(sequence, question, answers, frontier) {
  const next = sequence[sequence.indexOf(question) + 1];
  return next && (Object.hasOwn(answers, next) || next === frontier) ? next : frontier;
}

export function matchesSavedAnswer(field, value, answers, extras = {}) {
  if (!Object.hasOwn(answers, field)) return false;
  if (field === 'odop_choice' && value === 'hybrid' && extras.hybrid_description) {
    return answers.odop_choice === value && answers.idea === extras.hybrid_description && answers.enterprise_name === extras.hybrid_name;
  }
  const saved = answers[field];
  if (saved == null) return value == null || value === 'unknown';
  if (typeof saved === 'number') return String(value).trim() !== '' && Number(value) === saved;
  return saved === value;
}
