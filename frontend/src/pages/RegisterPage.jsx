import React, { useEffect, useRef, useState } from 'react';
import { Link,useNavigate } from 'react-router-dom';
import { Chrome,Pause,Play,RefreshCw,Zap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { auth,RecaptchaVerifier } from '../services/firebaseClient';
import { authApi } from '../services/api';
import { authErrorMessage } from '../services/authErrorMessage';
import { useMiraConversation } from '../hooks/useMiraConversation';
import { PROFILE_ORDER,profilePrompt } from '../services/profilePrompts';
import { LanguageSelector } from '../components/LanguageSelector';
import { ProfileDetailsForm } from '../components/ProfileDetailsForm';

export function RegisterPage(){
  const {language}=useLanguage();
  const {sendPhoneCode,completePhoneSignIn,loginWithGoogle,loginAsDemo}=useAuth();
  const navigate=useNavigate();
  const [field,setField]=useState('name'),[reply,setReply]=useState(()=>profilePrompt(language,'name'));
  const [phase,setPhase]=useState('profile'),[draft,setDraft]=useState({});
  const [form,setForm]=useState({name:'',gender:'',promoter_category:'',phone:'',email:''});
  const [fieldErrors,setFieldErrors]=useState({});
  const [sequence,setSequence]=useState(0),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const [confirmation,setConfirmation]=useState(null),[code,setCode]=useState('');
  const verifier=useRef(null),flight=useRef(false),attemptedCode=useRef(''),alive=useRef(true);
  useEffect(()=>{alive.current=true;return()=>{alive.current=false;verifier.current?.clear();};},[]);
  useEffect(()=>{if(field)setReply(profilePrompt(language,field));},[language]);
  const sendCode=async values=>{
    setPhase('verification');setBusy(true);setError('');
    try{
      if(!verifier.current)verifier.current=new RecaptchaVerifier(auth,'phone-recaptcha',{size:'invisible'});
      const result=await sendPhoneCode(values.phone,verifier.current);
      if(alive.current)setConfirmation(result);
    }catch(err){if(alive.current){setError(authErrorMessage(err,'The SMS code could not be sent. Retry or use Google sign-in.',language));verifier.current?.clear();verifier.current=null;}}
    finally{if(alive.current)setBusy(false);}
  };
  const submit=async text=>{
    if(flight.current)return {valid:false};
    flight.current=true;setBusy(true);setError('');
    try{
      const result=await authApi.registrationAnswer({field,text,language});
      if(!alive.current)return {valid:false};
      setSequence(value=>value+1);
      if(!result.valid){setReply(result.reply);return {valid:false};}
      const updated={...form,...Object.fromEntries(Object.entries(result.values||{}).filter(([key])=>key in form)),...(result.values?.email_status==='skipped'?{email:''}:{})};
      setForm(updated);
      setFieldErrors(previous=>({...previous,[field]:null}));
      if(result.next_field){setField(result.next_field);setReply(result.reply);}
      else {
        const checked=await authApi.validateRegistration({...updated,language});
        if(!checked.valid){setFieldErrors(checked.errors);setField(checked.next_field);setReply(checked.reply);return {valid:false};}
        setDraft(checked.values);await sendCode(checked.values);
      }
      return {valid:true};
    }catch(err){if(alive.current)setError('Your answer could not be processed. Please retry when connected.');throw err;}
    finally{flight.current=false;if(alive.current)setBusy(false);}
  };
  const conversation=useMiraConversation({language,prompt:reply,questionKey:`${field}:${sequence}:${language}`,field,
    enabled:phase==='profile',busy,onAnswer:submit});
  const change=(key,value)=>{
    conversation.pause();setForm(previous=>({...previous,[key]:value}));setFieldErrors(previous=>({...previous,[key]:null}));
  };
  const submitForm=async event=>{
    event.preventDefault();if(flight.current)return;
    conversation.pause();flight.current=true;setBusy(true);setError('');
    try{
      const result=await authApi.validateRegistration({...form,language});
      if(!alive.current)return;
      setFieldErrors(result.errors||{});
      if(!result.valid){setField(result.next_field);setReply(result.reply);setSequence(value=>value+1);return;}
      setDraft(result.values);await sendCode(result.values);
    }catch(err){setError('Your details could not be checked. Please retry when connected.');}
    finally{flight.current=false;if(alive.current)setBusy(false);}
  };
  const verify=async value=>{
    if(flight.current||!confirmation||value.length!==6||attemptedCode.current===value)return;
    flight.current=true;attemptedCode.current=value;setBusy(true);setError('');
    try{
      await completePhoneSignIn(confirmation,value,{name:draft.name,gender:draft.gender,promoter_category:draft.promoter_category,
        phone:draft.phone,email_status:draft.email_status,...(draft.email?{email:draft.email}:{})});
      setDraft({});navigate('/onboarding',{replace:true});
    }catch(err){setError(authErrorMessage(err,'The code could not be verified. Check it and try again.',language));}
    finally{flight.current=false;if(alive.current)setBusy(false);}
  };
  const enter=async method=>{
    conversation.pause();setBusy(true);setError('');
    try{await method();setDraft({});navigate('/onboarding',{replace:true});}
    catch(err){setError(authErrorMessage(err,'Sign-in could not finish. Please try again.',language));}
    finally{if(alive.current)setBusy(false);}
  };
  return <main className="min-h-screen bg-gradient-to-br from-rose-50 via-white to-sky-50 px-4 py-6 text-slate-900">
    <div className="max-w-2xl mx-auto space-y-6">
      <header className="flex justify-between items-center gap-3"><Link to="/" className="font-bold text-lg">उ Udyam Saathi</Link><LanguageSelector/></header>
      <section className="rounded-3xl border border-violet-100 bg-white p-5 sm:p-8 shadow-sm space-y-5" aria-label="Automatic voice registration">
        <div className="flex items-center gap-3"><img src="/mira-avatar.png" alt="Mira" className="w-16 h-16 rounded-full object-cover"/><div><h1 className="text-xl font-bold">Mira · Create your account</h1><p className="text-sm text-slate-500">{phase==='profile'?`${PROFILE_ORDER.indexOf(field)+1} / ${PROFILE_ORDER.length}`:'Secure phone verification'}</p></div></div>
        <p className="text-xl leading-relaxed" aria-live="polite">{phase==='profile'?reply:confirmation?'Enter the SMS code sent to your phone. It will be verified automatically.':'Sending your verification code…'}</p>
        {phase==='profile'&&<>
          <p role="status" className="text-sm text-violet-700">{busy?'Saving your answer…':conversation.status==='speaking'?'Mira is speaking…':conversation.status==='listening'?'Listening — answer naturally':conversation.status==='processing'?'Understanding your answer…':'Conversation paused'}</p>
          <div className="flex flex-wrap gap-3"><button type="button" className="mira-secondary" onClick={conversation.paused?conversation.resume:conversation.pause}>{conversation.paused?<Play size={17}/>:<Pause size={17}/>} {conversation.paused?'Resume conversation':'Pause'}</button><button type="button" className="mira-secondary" onClick={conversation.repeat}><RefreshCw size={17}/>Repeat question</button></div>
          <p className="text-xs text-slate-500">The microphone starts automatically after each question. Allow microphone access once. Say repeat to hear the question again. Email is optional.</p>
        </>}
        <ProfileDetailsForm values={form} onChange={change} onSubmit={submitForm} errors={fieldErrors} activeField={phase==='profile'?field:null} disabled={busy||phase!=='profile'} showSubmit={phase==='profile'} submitLabel={busy?'Checking details…':'Verify mobile and create account'}/>
        <div id="phone-recaptcha"/>
        {phase==='verification'&&confirmation&&<label className="block font-semibold">SMS verification code<input aria-label="SMS verification code" type="text" inputMode="numeric" autoComplete="one-time-code" maxLength={6} className="mira-input mt-2" value={code} disabled={busy} onChange={event=>{const value=event.target.value.replace(/\D/g,'').slice(0,6);setCode(value);if(value.length===6)verify(value);}}/></label>}
        {phase==='verification'&&!busy&&<button type="button" className="mira-secondary" onClick={()=>{setCode('');attemptedCode.current='';setConfirmation(null);verifier.current?.clear();verifier.current=null;sendCode(draft);}}>Send a new SMS code</button>}
        {phase==='verification'&&!busy&&<button type="button" className="mira-secondary" onClick={()=>{conversation.pause();setConfirmation(null);setCode('');setDraft({});attemptedCode.current='';verifier.current?.clear();verifier.current=null;setPhase('profile');setField('phone');setReply(profilePrompt(language,'phone'));setError('');}}>Edit registration details</button>}
        {(error||conversation.error)&&<p role="alert" className="rounded-xl bg-rose-50 border border-rose-200 p-3 text-sm text-rose-800">{error||conversation.error}</p>}
      </section>
      <div className="grid gap-3 sm:grid-cols-2"><button disabled={busy} className="mira-secondary justify-center" onClick={()=>enter(loginWithGoogle)}><Chrome size={18}/>Continue with Google</button><button disabled={busy} className="mira-secondary justify-center" onClick={()=>enter(loginAsDemo)}><Zap size={18}/>One-click evaluator access</button></div>
      <p className="text-center text-sm text-slate-500">Already registered? <Link to="/login" className="text-violet-800 underline">Sign in</Link></p>
    </div>
  </main>;
}
export default RegisterPage;
