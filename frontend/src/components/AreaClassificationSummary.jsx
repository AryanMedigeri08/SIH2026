import React from 'react';
import { TranslatedText as T } from './TranslatedText';

export function AreaClassificationSummary({location}) {
  if(!location)return null;
  const area=location.area_classification;
  const profile=area?.development_profile;
  const indicators=area?.amenities?.indicators||{};
  const official=location.is_rural==null?null:location.is_rural?'Rural':'Urban';
  return <section className="rounded-xl bg-slate-50 border border-slate-200 p-3 text-sm space-y-2" aria-label="Automatic area classification">
    <p className="font-semibold"><T text="Automatic area classification"/>: <T text={official||'Official status unavailable'}/></p>
    {profile&&profile.label!=='Insufficient data'&&<p><T text="Development profile"/>: <T text={profile.label}/><span className="text-xs text-slate-500"> · <T text="estimated from village indicators"/></span></p>}
    {!official&&<p className="text-xs text-amber-900"><T text="Official records are incomplete. Retry the data check; no Rural/Urban choice is needed."/></p>}
    {area&&<details><summary className="cursor-pointer text-xs font-medium text-slate-600"><T text="Why this classification?"/></summary><div className="text-xs text-slate-600 space-y-1 mt-2">
      <p>{area.local_body_type||<T text={official?'Matched official village/town record':'Official village/town record unavailable'}/>}</p>
      {profile.population!=null&&<p><T text="Census population"/> ({profile.population_year}): {profile.population.toLocaleString('en-IN')}</p>}
      {profile.density_per_sq_km!=null&&<p><T text="Population per square kilometre"/>: {profile.density_per_sq_km.toLocaleString('en-IN')}</p>}
      {profile.non_agricultural_main_workers_percent!=null&&<p><T text="Non-agricultural share of all main workers"/>: {profile.non_agricultural_main_workers_percent}%</p>}
      {area.amenities.available?<p><T text="Observed amenities"/>: {[
        ['road','All-weather road'],['banking','Bank or ATM'],['internet','Internet'],['market_or_storage','Market / storage'],
      ].filter(([key])=>indicators[key]===true).map(([,label])=><span className="inline-block mr-2" key={label}><T text={label}/></span>)}{indicators.power_hours!=null&&<span> · <T text="Power hours per day"/>: {indicators.power_hours}</span>}</p>:<p><T text="Exact village amenities are unavailable; regional averages are not used for classification."/></p>}
      <p><T text="Development indicators do not change the official area category used for scheme calculations."/></p>
    </div></details>}
  </section>;
}
