import React from 'react';

export function ProfileDetailsForm({values,onChange,onSubmit,errors={},activeField,disabled=false,buttonDisabled=false,submitLabel='Save details and continue',showSubmit=true}) {
  return <form onSubmit={onSubmit} className="grid sm:grid-cols-2 gap-4" aria-label="Registration details">
    {[
      ['name','Full name','text'],['gender','Gender','select'],['promoter_category','Caste / category','select'],['phone','Mobile number','tel'],['email','Email (optional)','email'],
    ].map(([key,label,type])=><label key={key} className={`block text-sm font-semibold rounded-xl p-2 ${activeField===key?'bg-violet-50 ring-1 ring-violet-200':''} ${key==='name'?'sm:col-span-2':''}`}>
      {label}
      {type==='select'?<select aria-label={label} className="mira-input mt-1" value={values[key]||''} disabled={disabled} onChange={event=>onChange(key,event.target.value)}>
        <option value="">Choose {key==='gender'?'gender':'category'}</option>
        {(key==='gender'?['Male','Female','Other','Unspecified']:['general','obc','sc','st','minority','ph','artisan','women','women_shg']).map(value=><option key={value} value={value}>{value==='Unspecified'?'Prefer not to say':value==='general'?'General':value.replaceAll('_',' ').toUpperCase()}</option>)}
      </select>:<input aria-label={label} type={type} className="mira-input mt-1" autoComplete={{name:'name',phone:'tel',email:'email'}[key]} inputMode={key==='phone'?'tel':undefined} maxLength={key==='name'?120:key==='phone'?22:254} value={values[key]||''} disabled={disabled} onChange={event=>onChange(key,event.target.value)} placeholder={key==='phone'?'10 digit mobile number':key==='email'?'You can leave this blank':undefined}/>}
      {errors[key]&&<span role="alert" className="block text-xs text-rose-700 mt-1">{errors[key]}</span>}
    </label>)}
    {showSubmit&&<button className="mira-primary justify-center sm:col-span-2" disabled={disabled||buttonDisabled}>{submitLabel}</button>}
  </form>;
}
