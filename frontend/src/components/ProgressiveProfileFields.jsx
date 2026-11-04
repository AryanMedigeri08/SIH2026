import React, { useEffect,useRef } from 'react';
import { PROFILE_ORDER } from '../services/profilePrompts';
import { miraCopy } from '../services/miraCopy';

export function ProgressiveProfileFields({values,activeField,visibleCount,onChange,onAnswer,disabled,errors={},language,focusCurrent=false}) {
  const copy=miraCopy(language),inputs=useRef({});
  useEffect(()=>{if(focusCurrent)inputs.current[activeField]?.focus();},[activeField,focusCurrent]);
  const gender=[['Male',copy.male],['Female',copy.female],['Other',copy.other],['Unspecified',copy.unspecified]];
  const categories=[['general',copy.general],...['obc','sc','st','minority','ph','artisan','women','women_shg'].map(value=>[value,value.replaceAll('_',' ').toUpperCase()])];
  return <div className="progressive-fields" aria-label={copy.create}>{PROFILE_ORDER.slice(0,visibleCount).map(key=><section key={key}
    className={`registration-field ${key===activeField?'registration-field--active':''}`} aria-label={copy[key]}>
    <label htmlFor={`profile-${key}`} className="registration-field-label">{copy[key]}</label>
    {key==='gender'||key==='promoter_category'?<div className="registration-choices" role="group" aria-label={copy[key]}>
      {(key==='gender'?gender:categories).map(([value,label])=><button type="button" key={value} aria-pressed={values[key]===value}
        className={`registration-choice ${values[key]===value?'is-selected':''}`} disabled={disabled}
        onClick={()=>onAnswer(key,value)}>{label}</button>)}
    </div>:<input ref={node=>{inputs.current[key]=node;}} id={`profile-${key}`} aria-label={copy[key]} value={values[key]||''}
      type={key==='email'?'email':key==='phone'?'tel':'text'} inputMode={key==='phone'?'tel':undefined}
      autoComplete={{name:'name',phone:'tel',email:'email'}[key]} className="registration-input" disabled={disabled}
      maxLength={key==='name'?120:key==='phone'?22:254} onChange={event=>onChange(key,event.target.value)}
      onKeyDown={event=>{if(event.key==='Enter'&&!event.nativeEvent.isComposing){event.preventDefault();onAnswer(key,values[key]||'');}}}/>}
    {key==='email'&&<button type="button" disabled={disabled} className="registration-skip" onClick={()=>onAnswer('email','skip')}>{copy.skip}</button>}
    {errors[key]&&<p role="alert" className="registration-field-error">{errors[key]}</p>}
    {key===activeField&&!['gender','promoter_category'].includes(key)&&<p className="registration-hint">{copy.enter}</p>}
  </section>)}</div>;
}
