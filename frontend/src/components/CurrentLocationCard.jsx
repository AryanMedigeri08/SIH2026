import React, { useEffect, useRef, useState } from 'react';
import { MapPin, RefreshCw } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { onboardingApi } from '../services/api';
import { getDevicePosition } from '../services/deviceLocation';
import { TranslatedText as T } from './TranslatedText';
import { AreaClassificationSummary } from './AreaClassificationSummary';

export function CurrentLocationCard({onOpenWizard}) {
  const {token}=useAuth();
  const [result,setResult]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const alive=useRef(true),generation=useRef(0);
  const detect=async()=>{
    const id=++generation.current;setBusy(true);setError('');
    try {
      const gps=await getDevicePosition();
      if(!alive.current||id!==generation.current)return;
      const data=await onboardingApi.currentLocation(token,gps);
      if(alive.current&&id===generation.current)setResult(data);
    }catch(err){if(alive.current&&id===generation.current)setError(err.message);}
    finally{if(alive.current&&id===generation.current)setBusy(false);}
  };
  useEffect(()=>{alive.current=true;if(token)detect();return()=>{alive.current=false;generation.current++;};},[token]);
  const address=result?.location,physical=result?.physical_location;
  return <section className="mx-2 sm:mx-6 rounded-2xl border border-sky-100 bg-sky-50/70 p-4 space-y-2" aria-label="Your current location">
    <div className="flex items-start justify-between gap-4"><div className="flex gap-2"><MapPin className="text-sky-700 shrink-0" size={20}/><div>
      <h2 className="font-semibold"><T text="Your current location"/></h2>
      <p role="status" className="text-sm text-slate-700">{busy?<T text="Finding your location…"/>:address?
        [address.village_name,address.block_name,address.district_name,address.state_name].filter(Boolean).join(', '):physical?
        [physical.locality_hint,physical.district_hint,physical.state_name].filter(Boolean).join(', '):<T text="Location has not been detected yet."/>}</p>
    </div></div><button className="mira-secondary shrink-0" onClick={detect} disabled={busy} aria-label="Retry current location"><RefreshCw size={16}/><T text="Retry"/></button></div>
    {error&&<p role="alert" className="text-sm text-amber-900">{error}</p>}
    {address&&<AreaClassificationSummary location={address}/>}
    {physical&&!address&&<p className="text-xs text-slate-600"><T text="Choose the business village to calculate its area classification automatically."/></p>}
    {physical?.approximate&&<p className="text-xs text-slate-600"><T text="This is an approximate device location. Confirm where the business will operate."/></p>}
    {result?.odop?.product&&<p className="text-sm"><strong>ODOP: </strong>{result.odop.product}<span className="block text-xs text-slate-600"><T text="Mira will help you explore alignment while planning your business."/></span></p>}
    <button className="text-sm font-semibold text-violet-800 underline" onClick={onOpenWizard}><T text="Choose or confirm the business location with Mira"/></button>
  </section>;
}
