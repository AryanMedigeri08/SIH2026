import { PROFILE_ORDER } from './profilePrompts.js';

export function registrationAnswerState(form,confirmed,answer) {
  const values=answer.values||{};
  const nextForm={...form,...Object.fromEntries(Object.entries(values).filter(([key])=>PROFILE_ORDER.includes(key)))};
  if(values.email_status==='skipped')nextForm.email='';
  const nextConfirmed=new Set(confirmed);
  for(const key of PROFILE_ORDER)if(Object.hasOwn(values,key)||(key==='email'&&values.email_status))nextConfirmed.add(key);
  return {form:nextForm,confirmed:nextConfirmed,next:PROFILE_ORDER.find(key=>!nextConfirmed.has(key))||null};
}
