import React, { useEffect, useState } from 'react';
import { onboardingApi } from '../../services/api';

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
  const [verification, setVerification] = useState('');
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
  const choose = (index, value) => {
    setSelected(previous => previous.map((s, i) => i === index ? value : i > index ? '' : s));
    setOptions(previous => previous.map((items, i) => i > index ? [] : items));
    setVerification('');
  };
  const save = async event => {
    event.preventDefault();
    setLoading(true);
    try {
      const location = selected.every(Boolean) ? {
        state_code: Number(selected[0]), district_code: Number(selected[1]), block_code: Number(selected[2]), village_code: Number(selected[3]),
      } : canVerifyExisting ? { state_code: needsArea.state_code, district_code: needsArea.district_code, block_code: needsArea.block_code, village_code: needsArea.village_code } : null;
      if (!location) throw new Error('Please choose all four location levels.');
      const result = await onboardingApi.chooseLocation(token, { ...location, revision: state.revision, language,
        verified_is_rural: verification === '' ? null : verification === 'rural' });
      onResult(result);
    } catch (error) { onError(error.message); }
    finally { setLoading(false); }
  };
  const detect = () => {
    if (!navigator.geolocation) { onError('Location is unavailable on this device. Choose the business location below.'); return; }
    setLoading(true);
    navigator.geolocation.getCurrentPosition(async position => {
      try {
        onResult(await onboardingApi.detectLocation(token, { revision: state.revision, language,
          latitude: position.coords.latitude, longitude: position.coords.longitude, accuracy: position.coords.accuracy }));
      } catch (error) { onError(error.message); }
      finally { setLoading(false); }
    }, () => { setLoading(false); onError('Location permission was denied or GPS is unavailable. Choose where you will establish the business below.'); },
    { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 });
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
    {canVerifyExisting && <label className="block text-sm text-slate-700">The official row has no rural/urban flag. Verify the area status for {needsArea.village_name}.
      <select className="mira-input mt-1" aria-label="Verify area classification" value={verification} onChange={e => setVerification(e.target.value)} required>
        <option value="">Choose verified status</option><option value="rural">Rural</option><option value="urban">Urban / semi-urban</option>
      </select>
      <span className="text-xs block mt-1">This uses the original application’s manual verification fallback. GPS does not establish subsidy eligibility.</span>
    </label>}
    <div className="flex flex-wrap gap-3">
      <button className="mira-primary" disabled={disabled || loading || (!selected.every(Boolean) && !canVerifyExisting)}>{loading ? 'Checking directory…' : 'Check this business location'}</button>
      <button type="button" className="mira-secondary" disabled={loading} onClick={() => setRetry(r => r + 1)}>Retry directory</button>
    </div>
  </form>;
}
