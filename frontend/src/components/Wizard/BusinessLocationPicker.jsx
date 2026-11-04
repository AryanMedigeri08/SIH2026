import React, { useEffect, useRef, useState } from 'react';
import { onboardingApi } from '../../services/api';
import { getDevicePosition } from '../../services/deviceLocation';
import { AreaClassificationSummary } from '../AreaClassificationSummary';

const levels = [
  ['states', 'State', 'state_code', 'state_name'],
  ['districts', 'District', 'district_code', 'district_name'],
  ['blocks', 'Development block', 'development_block_code', 'development_block_name'],
  ['villages', 'Village', 'village_code', 'village_name'],
];

export function BusinessLocationPicker({ token, state, onResult, onError, disabled, language }) {
  const [selected, setSelected] = useState(['', '', '', '']);
  const [options, setOptions] = useState([[], [], [], []]);
  const [search, setSearch] = useState('');
  const [retry, setRetry] = useState(0);
  const [loading, setLoading] = useState(false);
  const prefill = useRef(true);
  const hint = state?.physical_location;
  const needsArea = state?.location?.is_rural == null && state?.location;
  const canVerifyExisting = needsArea && !selected.some(Boolean);
  useEffect(() => {
    let active = true;
    const index = selected.findIndex(s => !s);
    if (index < 0) return;
    setLoading(true);
    const timer = setTimeout(() => {
      onboardingApi.locationOptions(token, levels[index][0], index ? Number(selected[index - 1]) : null, index === 3 ? search : '')
        .then(items => { if (active) setOptions(previous => previous.map((items_, i) => i === index ? items : items_)); })
        .catch(error => { if (active) onError(error.message); })
        .finally(() => { if (active) setLoading(false); });
    }, 250);
    return () => { active = false; clearTimeout(timer); };
  }, [token, selected.join(','), search, retry]);
  useEffect(() => {
    if (!prefill.current || !hint) return;
    const index=selected.findIndex(value=>!value);
    if(index<0||!options[index].length)return;
    const normalize=value=>String(value||'').toLowerCase().replace(/\s+(district|division)$/,'').replace(/[^\p{L}\p{N}]/gu,'');
    const code=hint.resolved_codes?.[['state_code','district_code','block_code','village_code'][index]];
    const name=[hint.state_name,hint.district_hint,hint.block_hint,hint.locality_hint][index];
    const matches=options[index].filter(item=>code?item[levels[index][2]]===code:normalize(item[levels[index][3]])===normalize(name));
    if(matches.length===1)setSelected(previous=>previous.map((value,i)=>i===index?String(matches[0][levels[index][2]]):value));
    else if(index===3&&hint.locality_hint&&!search)setSearch(hint.locality_hint);
  },[options,selected.join(','),hint,search]);
  const choose = (index, value) => {
    prefill.current=false;
    setSelected(previous => previous.map((s, i) => i === index ? value : i > index ? '' : s));
    setOptions(previous => previous.map((items, i) => i > index ? [] : items));
  };
  const save = async event => {
    event.preventDefault();
    setLoading(true);
    try {
      const location = selected.every(Boolean) ? {
        state_code: Number(selected[0]), district_code: Number(selected[1]), block_code: Number(selected[2]), village_code: Number(selected[3]),
      } : canVerifyExisting ? { state_code: needsArea.state_code, district_code: needsArea.district_code, block_code: needsArea.block_code, village_code: needsArea.village_code } : null;
      if (!location) throw new Error('Please choose all four location levels.');
      const result = await onboardingApi.chooseLocation(token, { ...location, revision: state.revision, language });
      onResult(result);
    } catch (error) { onError(error.message); }
    finally { setLoading(false); }
  };
  const detect = async () => {
    setLoading(true);
    try {
      const gps=await getDevicePosition();
      prefill.current=true;setSelected(['','','','']);
      onResult(await onboardingApi.detectLocation(token,{revision:state.revision,language,...gps}));
    }catch(error){onError(error.message);}
    finally{setLoading(false);}
  };
  return <form onSubmit={save} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 space-y-4" aria-label="Business location">
    <p className="text-sm text-slate-700">Your business can be in a different place from your current location.</p>
    <button type="button" className="mira-secondary" disabled={disabled || loading} onClick={detect}>Use my current location</button>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {levels.map(([level, label, code, name], index) => <label key={level} className="text-sm font-medium text-slate-700">
        {label}
        <select aria-label={label} value={selected[index]} onChange={e => choose(index, e.target.value)}
          disabled={disabled || loading || (index > 0 && !selected[index - 1])} className="mira-input mt-1">
          <option value="">Choose {label.toLowerCase()}</option>
          {options[index].map(item => <option key={item[code]} value={item[code]}>{item[name]}</option>)}
        </select>
      </label>)}
    </div>
    {selected[2] && <label className="block text-sm">Find village (directory results are limited to 500)
      <input className="mira-input mt-1" value={search} onChange={e => { setSearch(e.target.value); choose(3, ''); }} placeholder="Type village name" />
    </label>}
    {selected.every(Boolean)&&<p className="text-xs text-slate-600">Area classification is calculated automatically from matched official records, population, employment and available village amenities.</p>}
    {needsArea&&<AreaClassificationSummary location={state.location}/>}
    <div className="flex flex-wrap gap-3">
      <button className="mira-primary" disabled={disabled || loading || (!selected.every(Boolean) && !canVerifyExisting)}>{loading ? 'Checking village data…' : canVerifyExisting?'Retry automatic classification':'Check this business location'}</button>
      <button type="button" className="mira-secondary" disabled={loading} onClick={() => setRetry(r => r + 1)}>Retry directory</button>
    </div>
  </form>;
}
