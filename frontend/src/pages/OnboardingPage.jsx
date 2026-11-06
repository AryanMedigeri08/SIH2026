import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Pencil, Check } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage, LANGUAGES } from '../context/LanguageContext';
import { onboardingApi,authApi } from '../services/api';
import { useMiraConversation } from '../hooks/useMiraConversation';
import { TranslatedText as T } from '../components/TranslatedText';
import { BusinessLocationPicker } from '../components/Wizard/BusinessLocationPicker';
import { getDevicePosition } from '../services/deviceLocation';
import { ProgressiveProfileFields } from '../components/ProgressiveProfileFields';
import { GuidedRegistrationPanel } from '../components/GuidedRegistrationPanel';
import { MiraChatShell } from '../components/MiraChatShell';
import { MiraDialog } from '../components/MiraDialog';
import { miraCopy } from '../services/miraCopy';
import { PROFILE_ORDER } from '../services/profilePrompts';
import { AreaClassificationSummary } from '../components/AreaClassificationSummary';
import { RegionalEvidenceCard, FundingSummary, RecommendationCards, OperatingPlanForm } from '../components/MiraInsights';
import { readableChatPrompt } from '../services/chatPresentation';

const money = value => `₹${Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
const labels = { personal: 'My own savings', total: 'Total setup budget', borrowing: 'Money I expect to borrow',
  manufacture: 'Make products', process: 'Process raw materials', retail: 'Sell ready-made products', distribute: 'Distribute products', service: 'Provide a service',
  explore: 'Explore ODOP', keep: 'Keep my idea', reject: 'Skip ODOP', owned: 'Own / family space', rented: 'Rent a space', shared: 'Shared space', mobile: 'No fixed premises',
  increase: 'Increase my investment', normal: 'Normal bank loan', sca: 'Explore SCA assistance', self: 'Use my own funds', monthly: 'Per month', annual: 'Per year', Unspecified: 'Prefer not to say' };
const numeric = new Set(['budget', 'personal_contribution', 'rent_amount','monthly_sales','monthly_expenses','monthly_fixed_costs','variable_cost_pct']);
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
  const [audioEnabled,setAudioEnabled]=useState(true);
  const [inputMode,setInputMode]=useState('text');
  const [speechAllowed, setSpeechAllowed] = useState(true);
  const [profileForm,setProfileForm]=useState(()=>profileValues(userProfile));
  const [profileErrors,setProfileErrors]=useState({});
  const [manualLocation, setManualLocation] = useState(false);
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
  const announcedQuestion = useRef(null);
  const caption=readableChatPrompt(reply,state,language);
  const speech = useMiraConversation({ language, token, prompt:caption, questionKey:`${state?.revision}:${messageSequence}:${language}`, field:state?.next?.field,
    enabled:started && audioEnabled && speechAllowed && !!state && !state.paused && state.next?.field !== 'complete' && !manualLocation,
    autoListen:inputMode==='voice',
    busy:busy || isLoading, onAnswer:transcript => sendRef.current?.({text:transcript,source:'voice'}) });
  useEffect(()=>{
    const key=`${state?.revision}:${messageSequence}:${language}`;
    if(!busy&&!isLoading&&audioEnabled&&speechAllowed&&state&&!manualLocation&&announcedQuestion.current!==key){
      announcedQuestion.current=key;if(speech.paused)speech.resume();
    }
  },[state?.revision,messageSequence,language,busy,isLoading,audioEnabled,speechAllowed,manualLocation]);
  useEffect(()=>{if(speech.paused&&!speech.isRecording&&!busy&&inputMode==='voice')setInputMode('text');},[speech.paused,speech.isRecording,busy,inputMode]);
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
    if(options.source==='voice')setInputMode('text');
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
  const typeAnswer=()=>{speech.pause();setInputMode('text');};
  const useMicrophone=async()=>{
    if(inputMode==='voice'){typeAnswer();return;}
    setInputMode('voice');setAudioEnabled(true);
    if(stateRef.current?.paused)await send({action:'resume',text:''});
    speech.resume();
  };
  const toggleAudio=()=>{if(audioEnabled){speech.pause();setInputMode('text');setAudioEnabled(false);}else{setAudioEnabled(true);speech.resume();}};
  const changeLocation=()=>{speech.pause();setInputMode('text');setManualLocation(true);send({action:'change_location',text:''});};
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
  const assessment = state?.assessment;
  const insights=state?.insights||{};
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
      {!speechAllowed && <button className="mira-secondary" disabled={locked} onClick={reload}><T text="Retry spoken translation" /></button>}
      {current?.field==='regional_review'&&state.regional?.evidence?.top_risk_factors?.length>0&&<section className="mira-plan-concerns"><h3><T text="What needs attention"/></h3><ul>{state.regional.evidence.top_risk_factors.map(reason=><li key={reason}><T text={reason}/></li>)}</ul></section>}
      {current?.field==='financial_review'&&insights.financial_concerns?.length>0&&<section className="mira-plan-concerns"><h3><T text="What needs attention"/></h3><ul>{insights.financial_concerns.map(reason=><li key={reason}><T text={reason}/></li>)}</ul></section>}
      {!state?.paused && current && <>
        {['location_confirmation','business_confirmation','pending_changes'].includes(current.field) && <div className="mira-quick-actions">
          <button className="mira-primary" disabled={locked} onClick={() => send({action:current.action,text:''})}><Check size={18} /><T text={current.field==='location_confirmation'?'Yes, use this location':'Yes, continue'} /></button>
          {current.field === 'location_confirmation' && <button className="mira-secondary" disabled={locked} onClick={changeLocation}><T text="Change location" /></button>}
          {current.field === 'pending_changes' && <button className="mira-secondary" disabled={locked} onClick={() => send({action:'discard_change',text:''})}>Keep previous answer</button>}
        </div>}
        {!profileStep && current.choices?.length > 0 && <div className="mira-quick-actions">{current.choices.map(choice => <button key={String(choice)} disabled={locked} className="mira-secondary" onClick={() => send({text:'',updates:{[current.field]:choice}})}><T text={labels[choice] || String(choice).toUpperCase()} /></button>)}</div>}
        {current.field === 'regional_review' && <div className="mira-quick-actions"><button disabled={locked} className="mira-primary" onClick={() => send({action:'explore_alternatives',text:''})}><T text="Explore other ideas" /></button><button disabled={locked} className="mira-secondary" onClick={() => send({action:'accept_regional_risk',text:''})}><T text="Continue with these risks" /></button></div>}
        {current.field === 'financial_review' && <div className="mira-quick-actions"><button disabled={locked} className="mira-primary" onClick={()=>send({action:'explore_alternatives',text:''})}><T text="Find ideas within my funds"/></button><button disabled={locked} className="mira-secondary" onClick={()=>send({text:'',correction:true,updates:{financing_choice:'increase'}})}><T text="Increase my contribution"/></button><button disabled={locked} className="mira-secondary" onClick={()=>send({action:'accept_financial_risk',text:''})}><T text="Accept these risks and continue"/></button></div>}
        {current.field === 'operating_plan'&&<><OperatingPlanForm onSubmit={updates=>send({text:'',updates})} disabled={locked} values={state.fields}/><button disabled={locked} className="mira-secondary" onClick={()=>send({action:'use_operating_estimate',text:''})}><T text="I am not sure · Show an estimate"/></button></>}
        {current.field==='odop_explore'&&<button disabled={locked} className="mira-primary" onClick={()=>send({action:'align_odop',text:''})}><T text="Use this product for my business"/></button>}
        {current.field === 'rent_amount' && state.rent_proposal != null && <button className="mira-secondary" disabled={locked} onClick={() => send({action:'confirm_rent',text:''})}>Use {money(state.rent_proposal)} per month for planning</button>}
        {current.field === 'cost_proposal' && state.cost_proposal && <section className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 space-y-3">
          <h2 className="font-bold">Setup planning estimate · {money(state.cost_proposal.total)}</h2>
          <details className="text-sm"><summary className="cursor-pointer"><T text="See how this estimate was made"/></summary><p>{state.cost_proposal.basis}</p><ul className="mt-2 space-y-1">{state.cost_proposal.equipment.items.map(item => <li key={item.item_name}>{item.item_name} · {money(item.total_cost_inr)}</li>)}</ul></details>
          <div className="mira-quick-actions"><button className="mira-primary" disabled={locked} onClick={() => send({action:'confirm_estimate',text:''})}><T text="Use this estimate" /></button><button className="mira-secondary" disabled={locked} onClick={() => setCosts(state.cost_proposal.items)}><T text="Change the costs" /></button></div>
        </section>}
        {(costs || current.field === 'cost_items') && <form className="rounded-2xl border p-4 bg-white space-y-3" onSubmit={event => {event.preventDefault();send({text:'',correction:!!state.fields.cost_items,updates:{cost_items:costs || {},cost_basis:'User-reviewed setup estimates; verify supplier quotes and actual capacity before borrowing.'}});}}>
          <p className="text-sm">Enter only applicable setup costs. Rent is separate; include stock only once.</p>
          {['equipment','premises_setup','inventory','working_capital','other'].map(key => <label className="block text-sm" key={key}>{key.replaceAll('_',' ')}<input className="mira-input mt-1" type="number" min="0" step="0.01" value={costs?.[key] ?? ''} onChange={e => setCosts(prev => ({...prev,[key]:Number(e.target.value)}))} /></label>)}
          <button className="mira-primary" disabled={locked}><T text="Use these costs" /></button>
        </form>}
        {current.field === 'recommendations' && <RecommendationCards items={state.recommendations} state={state} disabled={locked}
          onChoose={id=>send({recommendation_id:id,text:''})} onDiscuss={id=>send({action:'recommendation_details',recommendation_id:id,text:''})}
          onCompare={()=>send({action:'compare_recommendations',text:''})} onAlternatives={()=>send({action:'alternatives',text:''})}/>}
      </>}
      {['cost_proposal','personal_contribution','operating_plan','financing_choice','financial_review','ready'].includes(current?.field)&&<FundingSummary finance={assessment||insights.finance_preview} projection={insights.operating_projection} preview={!assessment}/>}
      {caption!==reply&&<details className="mira-context-details"><summary><T text="Read Mira’s full explanation"/></summary><p className="whitespace-pre-wrap">{reply}</p></details>}
      {state?.regional&&<details className="mira-context-details"><summary><T text="Why this business may work here"/></summary><RegionalEvidenceCard region={state.regional} accepted={insights.regional_risk_accepted}/></details>}
      {state?.location&&<details className="mira-context-details"><summary><T text="Location details"/></summary><div className="mira-location-brief"><div><strong>{state.location.village_name}</strong><p>{state.location.block_name}, {state.location.district_name}, {state.location.state_name}</p></div><button disabled={locked} onClick={changeLocation}><T text="Change"/></button></div><AreaClassificationSummary location={state.location}/></details>}
      {assessment&&current?.field!=='operating_plan'&&<details className="mira-insight-card"><summary><T text="Change my monthly sales and expenses"/></summary><OperatingPlanForm key={state.revision} disabled={locked} values={state.fields} onSubmit={updates=>send({text:'',correction:true,updates})}/></details>}
      {state && <section className="space-y-3"><button className="mira-secondary" onClick={() => setShowSummary(!showSummary)}><T text={showSummary ? 'Hide my answers' : 'Check or change my answers'}/></button>
        {showSummary && <div className="rounded-2xl border bg-white p-4 space-y-3">{Object.entries(state.fields).filter(([key]) => reviewLabels[key]).map(([key, field]) => <div key={key} className="text-sm flex justify-between items-start gap-3"><div><span className="text-slate-500">{reviewLabels[key]}: </span><span>{['budget','personal_contribution','project_cost','rent_amount'].includes(key) ? money(field.value) : key === 'promoter_category' ? String(field.value).toUpperCase() : labels[field.value] || String(field.value)}</span></div>{(choices[key] || numeric.has(key) || ['idea','products','scale','enterprise_name','name'].includes(key)) && <button aria-label={`Correct ${key}`} disabled={locked} onClick={() => openEdit(key)}><Pencil size={15} /></button>}</div>)}
          {edit && <form onSubmit={event => {event.preventDefault();send({text:'',correction:true,updates:{[edit]:numeric.has(edit)?Number(editValue):editValue}});}} className="space-y-2"><label className="text-sm">Correct {edit.replaceAll('_',' ')}{choices[edit] ? <select className="mira-input" value={editValue} onChange={e=>setEditValue(e.target.value)}>{choices[edit].map(value=><option key={value} value={value}>{labels[value]||value}</option>)}</select> : <input className="mira-input" type={numeric.has(edit)?'number':'text'} min="0" required value={editValue} onChange={e=>setEditValue(e.target.value)} />}</label><button className="mira-primary" disabled={locked}>Save correction</button></form>}
        </div>}
      </section>}
      {current?.field === 'ready' && <button type="button" className="mira-secondary" disabled={locked} onClick={() => setCosts({...state.fields.cost_items?.value})}>Change setup cost estimates</button>}
      {current?.field === 'ready' && insights.can_finish && <button className="mira-primary w-full justify-center py-4" disabled={locked} onClick={finish}><T text="Save and open my business plan" /></button>}
      {current?.field === 'complete' && <div className="mira-quick-actions"><Link to="/dashboard" className="mira-primary">Open my saved business report</Link><button className="mira-secondary" disabled={locked} onClick={async () => {gpsAttempted.current=false;setManualLocation(false);setBusy(true);try {accept(await onboardingApi.newSession(token,state.revision));}catch(err){setError(err.message);}finally{setBusy(false);}}}>Start another business plan</button></div>}
      {speech.speechError && <p role="status" className="text-sm text-amber-800">{speech.speechError}</p>}</div>;
  return <MiraChatShell language={language} prompt={caption||copy.locating} speech={speech} busy={busy||isLoading} inputMode={inputMode} input={input}
    onInput={setInput} onTyping={typeAnswer} onMicrophone={useMicrophone} onSend={()=>send()} audioEnabled={audioEnabled} onAudioToggle={toggleAudio}
    history={state?.history||[]} error={error} onRetry={()=>requestRef.current?send({},true):reload()} dialogs={<>
    <MiraDialog open={manualLocation} onClose={closeLocation} title={copy.location} closeLabel={copy.close}>
      <p className="chat-location-help">{copy.locationHelp}</p>
      {state&&<BusinessLocationPicker token={token} state={state} language={language} disabled={locked} onError={setError} onResult={locationResult}/>}
    </MiraDialog>
    </>}>
      {details}
  </MiraChatShell>;
}
export default OnboardingPage;
