import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Mic, Square, Send, Volume2, VolumeX, Pause, Play, RefreshCw, Pencil, Check } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage, LANGUAGES } from '../context/LanguageContext';
import { onboardingApi,authApi } from '../services/api';
import { useMiraConversation } from '../hooks/useMiraConversation';
import { TranslatedText as T } from '../components/TranslatedText';
import { BusinessLocationPicker } from '../components/Wizard/BusinessLocationPicker';
import { getDevicePosition } from '../services/deviceLocation';
import { ProgressiveProfileFields } from '../components/ProgressiveProfileFields';
import { GuidedRegistrationPanel } from '../components/GuidedRegistrationPanel';
import { OrbOnboardingShell } from '../components/OrbOnboardingShell';
import { MiraDialog } from '../components/MiraDialog';
import { miraCopy } from '../services/miraCopy';
import { PROFILE_ORDER } from '../services/profilePrompts';
import { AreaClassificationSummary } from '../components/AreaClassificationSummary';

const money = value => `₹${Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
const labels = { personal: 'My own savings', total: 'Total setup budget', borrowing: 'Money I expect to borrow',
  manufacture: 'Make products', process: 'Process raw materials', retail: 'Sell ready-made products', distribute: 'Distribute products', service: 'Provide a service',
  explore: 'Explore ODOP', keep: 'Keep my idea', reject: 'Skip ODOP', owned: 'Own / family space', rented: 'Rent a space', shared: 'Shared space', mobile: 'No fixed premises',
  increase: 'Increase my investment', normal: 'Normal bank loan', sca: 'Explore SCA assistance', self: 'Use my own funds', monthly: 'Per month', annual: 'Per year', Unspecified: 'Prefer not to say' };
const numeric = new Set(['budget', 'personal_contribution', 'rent_amount']);
const personalFields=['name','gender','promoter_category','phone','email'];
const profileValues=profile=>Object.fromEntries(personalFields.map(key=>[key,key==='gender'&&profile?.gender==='Unspecified'&&!profile?.promoter_category?'':profile?.[key]||'']));
const reviewLabels = { idea: 'Business idea', products: 'Products or services',
  activity: 'Business activity', scale: 'Planned capacity', premises: 'Work premises', rent_amount: 'Rent or shared-space fee', rent_period: 'Rent period',
  budget: 'Stated budget', budget_kind: 'Budget means', personal_contribution: 'Your own funds', project_cost: 'Setup estimate', enterprise_name: 'Enterprise name', financing_choice: 'Funding choice' };
const reportCommand = text => /^(?:please\s+)?(?:generate|create|prepare|make)(?:\s+my|\s+the)?(?:\s+feasibility|\s+business|\s+project)?\s+report[.! ]*$/i.test(text.trim()) || /^(?:मेरी\s+)?रिपोर्ट\s+(?:बनाओ|बना दो|बनाइए)[।.! ]*$|^अहवाल तयार करा[।.! ]*$|^నివేదిక తయారు చేయండి[.! ]*$|^அறிக்கை உருவாக்கவும்[.! ]*$|^ವರದಿ ತಯಾರಿಸಿ[.! ]*$/.test(text.trim());

const choices = { gender: ['Male', 'Female', 'Other', 'Unspecified'], promoter_category: ['general', 'sc', 'st', 'obc', 'minority', 'ph', 'artisan', 'women', 'women_shg'],
  activity: ['manufacture', 'process', 'retail', 'distribute', 'service'], budget_kind: ['personal', 'total', 'borrowing'], premises: ['owned', 'rented', 'shared', 'mobile'], rent_period: ['monthly', 'annual'] };

export function OnboardingPage({ onWizardSubmit, isLoading }) {
  const { token, firebaseUser, userProfile, refreshProfile } = useAuth();
  const { language, setLanguage } = useLanguage();
  const copy=miraCopy(language);
  const [started, setStarted] = useState(() => !!sessionStorage.getItem('udyam_mira_language_selected'));
  const [state, setState] = useState(null);
  const [reply, setReply] = useState('');
  const [messageSequence, setMessageSequence] = useState(0);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [voice, setVoice] = useState(true);
  const [inputMode,setInputMode]=useState('voice');
  const [detailsOpen,setDetailsOpen]=useState(false);
  const [speechAllowed, setSpeechAllowed] = useState(true);
  const [profileForm,setProfileForm]=useState(()=>profileValues(userProfile));
  const [profileErrors,setProfileErrors]=useState({});
  const [manualLocation, setManualLocation] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [edit, setEdit] = useState('');
  const [editValue, setEditValue] = useState('');
  const [costs, setCosts] = useState(null);
  const stateRef = useRef(null);
  const flight = useRef(false);
  const requestRef = useRef(null);
  const sendRef = useRef(null);
  const gpsAttempted = useRef(false);
  const alive = useRef(true);
  const speech = useMiraConversation({ language, token, prompt:reply, questionKey:`${state?.revision}:${messageSequence}:${language}`, field:state?.next?.field,
    enabled:started && voice && inputMode==='voice' && speechAllowed && !!state && !state.paused && state.next?.field !== 'complete' && !manualLocation && !detailsOpen,
    busy:busy || isLoading, onAnswer:transcript => sendRef.current?.({text:transcript,source:'voice'}) });
  const accept = result => {
    if(result.state.next?.field==='area_verification'||(stateRef.current?.next?.field==='location_confirmation'&&result.state.next?.field==='location'))setManualLocation(true);
    stateRef.current = result.state; setState(result.state); setReply(result.reply); setMessageSequence(value => value + 1); setSpeechAllowed(result.speech_allowed !== false); setError('');
  };
  const reload = async () => {
    setBusy(true);
    try { const result = await onboardingApi.session(token, language, 'adaptive'); if (alive.current) accept(result); }
    catch (err) { if (alive.current) setError(err.message); }
    finally { if (alive.current) setBusy(false); }
  };
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  useEffect(() => { if (started && token) reload(); }, [started, token, language]);
  const send = async (options = {}, retry = false) => {
    if (!stateRef.current || flight.current || isLoading) return;
    if (stateRef.current.next?.field === 'ready' && reportCommand(options.text || input)) return finish();
    flight.current = true; setBusy(true); setError(''); speech.stopSpeaking();
    const payload = retry ? requestRef.current : { revision: stateRef.current.revision, request_id: crypto.randomUUID(),
      text: input, source: 'text', language, ...options };
    requestRef.current = payload;
    try {
      const result = await onboardingApi.turn(token,payload); accept(result); requestRef.current = null;
      if(personalFields.includes(stateRef.current?.next?.field)||personalFields.some(key=>Object.hasOwn(options.updates||{},key))||personalFields.includes(state?.next?.field)){
        try {const profile=await refreshProfile();if(alive.current)setProfileForm(previous=>({...previous,...Object.fromEntries(Object.entries(profileValues(profile)).filter(([,value])=>value)),...(profile.gender==='Unspecified'&&result.state.fields.gender?.provided?{gender:'Unspecified'}:{})}));}catch(_){}
      }
      setInput(''); setEdit(''); setCosts(null);
      return {valid:result.accepted !== false};
    } catch (err) { setError(err.message); if(options.source === 'voice') throw err; return {valid:false}; }
    finally { flight.current = false; setBusy(false); }
  };
  sendRef.current = send;
  const typeAnswer=()=>{speech.pause();setInputMode('text');setVoice(false);};
  const useMicrophone=async()=>{
    if(inputMode==='voice'&&!speech.paused){typeAnswer();return;}
    setInputMode('voice');setVoice(true);
    if(stateRef.current?.paused)await send({action:'resume',text:''});
    speech.resume();
  };
  const openDetails=()=>{speech.pause();setDetailsOpen(true);};
  const closeDetails=()=>{setDetailsOpen(false);if(inputMode==='voice')speech.resume();};
  const changeLocation=()=>{speech.pause();setDetailsOpen(false);setManualLocation(true);send({action:'change_location',text:''});};
  const closeLocation=()=>{setManualLocation(false);if(inputMode==='voice')speech.resume();};
  const locationResult=result=>{accept(result);setManualLocation(result.state.next?.field==='area_verification');if(inputMode==='voice')speech.resume();};
  const answerProfile=async(key,text)=>{
    if(flight.current)return;typeAnswer();flight.current=true;setBusy(true);setError('');
    let checked;
    try {
      checked=await authApi.registrationAnswer({field:key,text:key==='email'&&!text.trim()?'skip':text,language});
      if(!checked.valid){setProfileErrors(previous=>({...previous,[key]:checked.reply}));setReply(checked.reply);}
    }catch(err){setError(err.message);}
    finally{flight.current=false;setBusy(false);}
    if(checked?.valid)await send({text:'',updates:checked.values,source:'control'});
  };
  const detect = async () => {
    if (gpsAttempted.current || !stateRef.current || flight.current) return;
    gpsAttempted.current = true;
    const usePosition = async gps => {
      if (!alive.current) return;
      setBusy(true); flight.current = true;
      try {
        const result = await onboardingApi.detectLocation(token, { revision: stateRef.current.revision, language,
          latitude: gps.latitude, longitude: gps.longitude, accuracy: gps.accuracy });
        if (!alive.current) return;
        accept(result); setManualLocation(!result.state.location||result.state.next?.field==='area_verification');
      } catch (err) { if (alive.current) { setError(err.message); setManualLocation(true); } }
      finally { flight.current = false; if (alive.current) setBusy(false); }
    };
    try {
      const captured = JSON.parse(sessionStorage.getItem('mira-registration-gps') || 'null');
      sessionStorage.removeItem('mira-registration-gps');
      if (captured && Date.now() - captured.captured_at < 180000) return usePosition(captured);
    } catch (_) {}
    setBusy(true);
    try { await usePosition(await getDevicePosition()); }
    catch(err) { if(alive.current){setBusy(false);setManualLocation(true);setError(err.message);} }
  };
  useEffect(() => { if (state?.next?.field === 'location' && !manualLocation && !busy && !isLoading) detect(); }, [state?.next?.field,manualLocation,busy,isLoading]);
  const finish = async () => {
    if (flight.current || !state || isLoading) return;
    flight.current = true; setBusy(true); setError(''); speech.stopSpeaking();
    try { await onWizardSubmit({ onboarding_revision: state.revision, language,
      enterprise_name: state.fields.enterprise_name?.value, district_name: state.location?.district_name, sector: state.classification?.sector }); }
    catch (err) { setError(err.message); }
    finally { flight.current = false; setBusy(false); }
  };
  const current = state?.next;
  const profileStep=personalFields.includes(current?.field);
  const locked = busy || isLoading || speech.transcribing;
  const locationStep = current && ['location', 'area_verification'].includes(current.field);
  const assessment = state?.assessment;
  const openEdit = key => { setEdit(key); setEditValue(String(state.fields[key]?.value ?? '')); };
  if (!started) return <main className="min-h-screen flex items-center bg-gradient-to-br from-rose-50 via-white to-sky-50 px-5 py-12">
    <div className="max-w-3xl mx-auto text-center space-y-6">
      <img src="/mira-avatar.png" alt="Mira" className="w-24 h-24 object-cover rounded-full mx-auto ring-4 ring-white shadow-xl" />
      <h1 className="text-3xl font-bold text-slate-900">Let’s plan your business with Mira</h1>
      <p className="text-slate-600">Choose your language. Speak naturally, or type whenever you prefer. Your progress is saved.</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">{LANGUAGES.map(item => <button key={item.code} onClick={() => { setLanguage(item.code); setStarted(true); }} className="rounded-2xl border border-violet-200 bg-white py-5 px-4 shadow-sm hover:bg-violet-50">
        <strong className="block text-lg">{item.native}</strong><span className="text-sm text-slate-500">{item.label}</span>
      </button>)}</div>
      <Link to="/dashboard" className="text-sm text-slate-600 underline"><T text="Back to my businesses" /></Link>
    </div>
  </main>;
  if(profileStep)return <main className="registration-page">
    <header className="registration-page-header"><Link to="/">उ Udyam Saathi</Link><span>{copy.create}</span></header>
    <GuidedRegistrationPanel language={language} prompt={reply} speech={speech} mode={inputMode} onMicrophone={useMicrophone} onTyping={typeAnswer}>
      <ProgressiveProfileFields language={language} values={profileForm} activeField={current.field} visibleCount={Math.max(1,PROFILE_ORDER.indexOf(current.field)+1)} disabled={locked} errors={profileErrors}
        focusCurrent={inputMode==='text'} onChange={(key,value)=>{typeAnswer();setProfileForm(previous=>({...previous,[key]:value}));setProfileErrors(previous=>({...previous,[key]:null}));}} onAnswer={answerProfile}/>
      {error&&<p role="alert" className="registration-error">{error}</p>}
    </GuidedRegistrationPanel>
  </main>;
  const details=<div className="mira-review-content">
      {error && <div role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}<div className="flex gap-4 mt-2">
        <button onClick={reload} disabled={locked} className="underline">Reload saved progress</button>{requestRef.current && <button onClick={() => send({}, true)} disabled={locked} className="underline">Retry answer</button>}
      </div></div>}
      <section className="rounded-3xl border border-violet-100 bg-white p-5 sm:p-7 shadow-sm" aria-live="polite">
        <p className="text-xs uppercase tracking-widest text-violet-700 mb-3"><T text="One question at a time" /></p>
        <p className="text-lg leading-relaxed font-medium whitespace-pre-line">{reply || 'Connecting to Mira…'}</p>
        {!speechAllowed && <button className="mira-secondary mt-3" disabled={locked} onClick={reload}><T text="Reload saved progress" /></button>}
        <div className="mt-4 flex gap-4 text-xs text-slate-500"><button onClick={() => speech.speak(reply)} disabled={!reply}><T text="Listen again" /></button><button disabled={locked || !state} onClick={() => send({action:'explain', text:''})}><T text="Explain this" /></button></div>
      </section>
      {state?.location && <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm flex items-start justify-between gap-3"><div><strong>{state.location.village_name}</strong><p className="text-slate-500">{state.location.block_name}, {state.location.district_name}, {state.location.state_name}</p></div>
        <button className="text-violet-800 font-semibold" disabled={locked} onClick={changeLocation}>Change</button></div>}
      {state?.location&&current?.field!=='area_verification'&&<AreaClassificationSummary location={state.location}/>}
      {state?.physical_location && !state?.location && <div className="rounded-2xl border border-sky-100 bg-sky-50 p-4 text-sm"><strong><T text="Device location found"/></strong><p>{[state.physical_location.locality_hint,state.physical_location.district_hint,state.physical_location.state_name].filter(Boolean).join(', ')}</p><p className="text-xs text-slate-600 mt-1"><T text="Confirm the business address using the selections above."/></p></div>}
      {state?.odop?.product && <section className="rounded-2xl border border-amber-200 bg-amber-50 p-4 space-y-2" aria-label="District ODOP alignment"><strong>One District One Product (ODOP)</strong><p className="font-medium">{state.odop.product}</p><p className="text-sm"><T text={state.odop.aligned?'Your business sector matches the district product. Product and scheme eligibility still need checking.':'You can explore a business connection to this district product, or keep your original idea.'}/></p>
        {current?.field==='odop_explore'&&<button disabled={locked} className="mira-primary" onClick={()=>send({action:'align_odop',text:''})}><T text="Plan a business using this ODOP product"/></button>}
      </section>}
      {!state?.paused && current && <>
        {['location_confirmation','business_confirmation','pending_changes'].includes(current.field) && <div className="flex flex-wrap gap-3">
          <button className="mira-primary" disabled={locked} onClick={() => send({action:current.action,text:''})}><Check size={18} /><T text="Yes, that’s right" /></button>
          {current.field === 'location_confirmation' && <button className="mira-secondary" disabled={locked} onClick={changeLocation}><T text="Choose a different place" /></button>}
          {current.field === 'pending_changes' && <button className="mira-secondary" disabled={locked} onClick={() => send({action:'discard_change',text:''})}>Keep previous answer</button>}
        </div>}
        {!profileStep && current.choices?.length > 0 && <div className="flex flex-wrap gap-3">{current.choices.map(choice => <button key={String(choice)} disabled={locked} className="mira-secondary" onClick={() => send({text:'',updates:{[current.field]:choice}})}><T text={labels[choice] || String(choice).toUpperCase()} /></button>)}</div>}
        {current.field === 'regional_review' && <div className="flex flex-wrap gap-3"><button disabled={locked} className="mira-primary" onClick={() => send({action:'explore_alternatives',text:''})}><T text="Explore other ideas" /></button><button disabled={locked} className="mira-secondary" onClick={() => send({action:'accept_regional_risk',text:''})}><T text="Continue with these risks" /></button></div>}
        {current.field === 'rent_amount' && state.rent_proposal != null && <button className="mira-secondary" disabled={locked} onClick={() => send({action:'confirm_rent',text:''})}>Use {money(state.rent_proposal)} per month for planning</button>}
        {current.field === 'cost_proposal' && state.cost_proposal && <section className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 space-y-3">
          <h2 className="font-bold">Setup planning estimate · {money(state.cost_proposal.total)}</h2><p className="text-sm text-slate-600">{state.cost_proposal.basis}</p>
          <details className="text-sm"><summary className="cursor-pointer">Equipment and cost details</summary><ul className="mt-2 space-y-1">{state.cost_proposal.equipment.items.map(item => <li key={item.item_name}>{item.item_name} · {money(item.total_cost_inr)}</li>)}</ul></details>
          <div className="flex flex-wrap gap-3"><button className="mira-primary" disabled={locked} onClick={() => send({action:'confirm_estimate',text:''})}><T text="Use this planning estimate" /></button><button className="mira-secondary" disabled={locked} onClick={() => setCosts(state.cost_proposal.items)}><T text="Change cost estimates" /></button></div>
        </section>}
        {(costs || current.field === 'cost_items') && <form className="rounded-2xl border p-4 bg-white space-y-3" onSubmit={event => {event.preventDefault();send({text:'',correction:!!state.fields.cost_items,updates:{cost_items:costs || {},cost_basis:'User-reviewed setup estimates; verify supplier quotes and actual capacity before borrowing.'}});}}>
          <p className="text-sm">Enter only applicable setup costs. Rent is separate; include stock only once.</p>
          {['equipment','premises_setup','inventory','working_capital','other'].map(key => <label className="block text-sm" key={key}>{key.replaceAll('_',' ')}<input className="mira-input mt-1" type="number" min="0" step="0.01" value={costs?.[key] ?? ''} onChange={e => setCosts(prev => ({...prev,[key]:Number(e.target.value)}))} /></label>)}
          <button className="mira-primary" disabled={locked}><T text="Use these costs" /></button>
        </form>}
        {current.field === 'recommendations' && <div className="space-y-3">{state.recommendations.map(item => <article key={item.id} className="rounded-2xl border border-emerald-200 bg-white p-5 space-y-2"><h2 className="font-bold">{item.idea}</h2><p className="text-sm">{item.description}</p><p className="text-sm text-slate-500">{item.market_evidence}</p><p className="font-semibold">Setup range: {money(item.outlay_range[0])}–{money(item.outlay_range[1])}</p><p className="text-xs">Evidence confidence: {item.confidence}. Scheme approval is not guaranteed.</p><button disabled={locked} className="mira-primary" onClick={() => send({recommendation_id:item.id,text:''})}>Explore this business</button></article>)}<button disabled={locked} className="mira-secondary" onClick={() => send({action:'alternatives',text:''})}><T text="Other options" /></button></div>}
      </>}
      {state?.regional && <details className="rounded-2xl border bg-white p-4 text-sm" open={current?.field === 'odop_preference'}><summary className="font-semibold cursor-pointer">Regional assessment · {state.regional.recommendation || 'Evidence available'}</summary><p className="mt-2">{state.regional.evidence?.plain_language_summary || 'The available evidence is insufficient for a definite suitability conclusion.'}</p><p className="text-xs text-slate-500 mt-1">Confidence: {state.regional.confidence || state.regional.evidence?.confidence || 'INSUFFICIENT_DATA'}</p></details>}
      {assessment && <section className="rounded-2xl border bg-white p-5 space-y-2 text-sm"><h2 className="font-bold"><T text="Your funding draft" /></h2><dl className="grid grid-cols-2 gap-2"><dt>Setup estimate</dt><dd>{money(assessment.project_outlay)}</dd><dt>Your own funds</dt><dd>{money(assessment.personal_contribution)}</dd><dt>Remaining funding need</dt><dd>{money(assessment.capital_deficit)}</dd><dt>Candidate subsidy</dt><dd>{money(assessment.subsidy_candidate)}</dd></dl>
        <p className="text-xs text-slate-500">Subsidies are conditional and separate from cash available today. Final appraisal uses the existing normal loan and SCA rules.</p>
        <details><summary className="cursor-pointer">Loan terms and margin shortfall</summary><p className="mt-2">Normal loan exploration: {assessment.normal_loan.rate_pct}% · {assessment.normal_loan.tenure_years} years · {assessment.normal_loan.moratorium_months} months grace. EMI {money(assessment.normal_loan.monthly_emi)}.</p><p>SCA margin shortfall: {money(assessment.capital_structure.equity_gap)}. Existing SCA terms: {assessment.capital_structure.sca_interest_rate_pct}% · {assessment.capital_structure.sca_tenure_years} years.</p></details>
      </section>}
      {state && <section className="space-y-3"><button className="text-sm font-semibold text-violet-800" onClick={() => setShowSummary(!showSummary)}>{showSummary ? 'Hide' : 'Review or correct'} saved answers</button>
        {(showSummary || current?.field === 'ready') && <div className="rounded-2xl border bg-white p-4 space-y-3">{Object.entries(state.fields).filter(([key]) => reviewLabels[key]).map(([key, field]) => <div key={key} className="text-sm flex justify-between items-start gap-3"><div><span className="text-slate-500">{reviewLabels[key]}: </span><span>{['budget','personal_contribution','project_cost','rent_amount'].includes(key) ? money(field.value) : key === 'promoter_category' ? String(field.value).toUpperCase() : labels[field.value] || String(field.value)}</span></div>{(choices[key] || numeric.has(key) || ['idea','products','scale','enterprise_name','name'].includes(key)) && <button aria-label={`Correct ${key}`} disabled={locked} onClick={() => openEdit(key)}><Pencil size={15} /></button>}</div>)}
          {edit && <form onSubmit={event => {event.preventDefault();send({text:'',correction:true,updates:{[edit]:numeric.has(edit)?Number(editValue):editValue}});}} className="space-y-2"><label className="text-sm">Correct {edit.replaceAll('_',' ')}{choices[edit] ? <select className="mira-input" value={editValue} onChange={e=>setEditValue(e.target.value)}>{choices[edit].map(value=><option key={value} value={value}>{labels[value]||value}</option>)}</select> : <input className="mira-input" type={numeric.has(edit)?'number':'text'} min="0" required value={editValue} onChange={e=>setEditValue(e.target.value)} />}</label><button className="mira-primary" disabled={locked}>Save correction</button></form>}
        </div>}
        <button className="block text-xs text-slate-500" onClick={()=>setShowHistory(!showHistory)}>{showHistory ? 'Hide conversation' : 'Show conversation'}</button>
        {showHistory && <div className="space-y-2">{state.history.map((message,index)=><p key={index} className={`rounded-xl p-3 text-sm ${message.role==='user'?'bg-violet-100':'bg-white border'}`}>{message.text}</p>)}</div>}
      </section>}
      {current?.field === 'ready' && <button type="button" className="mira-secondary" disabled={locked} onClick={() => setCosts({...state.fields.cost_items?.value})}>Change setup cost estimates</button>}
      {current?.field === 'ready' && <button className="mira-primary w-full justify-center py-4" disabled={locked} onClick={finish}><T text="Generate my feasibility report" /></button>}
      {current?.field === 'complete' && <div className="flex flex-wrap gap-3"><Link to="/dashboard" className="mira-primary">Open my saved business report</Link><button className="mira-secondary" disabled={locked} onClick={async () => {gpsAttempted.current=false;setManualLocation(false);setBusy(true);try {accept(await onboardingApi.newSession(token,state.revision));}catch(err){setError(err.message);}finally{setBusy(false);}}}>Start another business plan</button></div>}
      {speech.speechError && <p role="status" className="text-sm text-amber-800">{speech.speechError}</p>}</div>;
  const locationActions=current?.field==='location_confirmation'?<div className="orb-onboarding-actions">
    <button type="button" disabled={locked} onClick={()=>send({action:'confirm_location',text:''})}>{copy.yes}</button>
    <button type="button" disabled={locked} onClick={changeLocation}>{copy.changeLocation}</button>
  </div>:null;
  return <OrbOnboardingShell language={language} prompt={reply||copy.locating} speech={speech} busy={busy||isLoading} inputMode={inputMode} input={input}
    onInput={setInput} onTyping={typeAnswer} onMicrophone={useMicrophone} onSend={()=>send()} onDetails={openDetails} onLocation={()=>{speech.pause();setManualLocation(true);}}
    locationStep={locationStep||current?.field==='location_confirmation'} error={error} onRetry={reload} actions={locationActions}>
    <MiraDialog open={manualLocation} onClose={closeLocation} title={copy.location} closeLabel={copy.close}>
      <p className="orb-location-help">{copy.locationHelp}</p>
      {state&&<BusinessLocationPicker token={token} state={state} language={language} disabled={locked} onError={setError} onResult={locationResult}/>}
    </MiraDialog>
    <MiraDialog open={detailsOpen} onClose={closeDetails} title={copy.details} closeLabel={copy.close}>{details}</MiraDialog>
  </OrbOnboardingShell>;
}
export default OnboardingPage;
