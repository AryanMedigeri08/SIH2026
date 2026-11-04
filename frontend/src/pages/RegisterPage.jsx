import React, { useEffect,useRef,useState } from 'react';
import { Link,useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { auth,RecaptchaVerifier } from '../services/firebaseClient';
import { authApi } from '../services/api';
import { authErrorMessage } from '../services/authErrorMessage';
import { useMiraConversation } from '../hooks/useMiraConversation';
import { PROFILE_ORDER,profilePrompt } from '../services/profilePrompts';
import { registrationAnswerState } from '../services/progressiveRegistration';
import { miraCopy } from '../services/miraCopy';
import { LanguageSelector } from '../components/LanguageSelector';
import { GuidedRegistrationPanel } from '../components/GuidedRegistrationPanel';
import { ProgressiveProfileFields } from '../components/ProgressiveProfileFields';

export function RegisterPage(){
  const {language}=useLanguage(),copy=miraCopy(language);
  const {sendPhoneCode,completePhoneSignIn,loginWithGoogle,loginAsDemo}=useAuth();
  const navigate=useNavigate();
  const [field,setField]=useState('name'),[reply,setReply]=useState(()=>profilePrompt(language,'name'));
  const [phase,setPhase]=useState('profile'),[draft,setDraft]=useState({});
  const [form,setForm]=useState({name:'',gender:'',promoter_category:'',phone:'',email:''});
  const [visibleCount,setVisibleCount]=useState(1),[fieldErrors,setFieldErrors]=useState({});
  const [sequence,setSequence]=useState(0),[busy,setBusy]=useState(false),[error,setError]=useState(''),[mode,setMode]=useState('voice');
  const [confirmation,setConfirmation]=useState(null),[code,setCode]=useState('');
  const verifier=useRef(null),flight=useRef(false),attemptedCode=useRef(''),alive=useRef(true),confirmed=useRef(new Set()),codeInput=useRef(null);
  const announcedStep=useRef(null);
  useEffect(()=>{alive.current=true;return()=>{alive.current=false;verifier.current?.clear();};},[]);
  useEffect(()=>{if(field)setReply(profilePrompt(language,field));},[language]);
  useEffect(()=>{if(confirmation)codeInput.current?.focus();},[confirmation]);
  const prompt=phase==='profile'?reply:confirmation?copy.otp:copy.sendingCode;
  const sendCode=async values=>{
    setPhase('verification');setBusy(true);setError('');
    try{
      if(!verifier.current)verifier.current=new RecaptchaVerifier(auth,'phone-recaptcha',{size:'invisible'});
      const result=await sendPhoneCode(values.phone,verifier.current);
      if(alive.current)setConfirmation(result);
    }catch(err){if(alive.current){setError(authErrorMessage(err,copy.connection,language));verifier.current?.clear();verifier.current=null;}}
    finally{if(alive.current)setBusy(false);}
  };
  const submitField=async(key,text,source='text')=>{
    if(flight.current||phase!=='profile')return {valid:false};
    if(source!=='voice'){setMode('text');conversation.pause();}
    flight.current=true;setBusy(true);setError('');
    try{
      const result=await authApi.registrationAnswer({field:key,text:key==='email'&&!text.trim()?'skip':text,language});
      if(!alive.current)return {valid:false};
      setSequence(value=>value+1);
      if(!result.valid){setField(key);setReply(result.reply);setFieldErrors(previous=>({...previous,[key]:result.reply}));return {valid:false};}
      if(!Object.keys(result.values||{}).length){setReply(result.reply);return {valid:true};}
      const updated=registrationAnswerState(form,confirmed.current,result);
      confirmed.current=updated.confirmed;setForm(updated.form);setFieldErrors(previous=>({...previous,[key]:null}));
      if(updated.next){setField(updated.next);setReply(profilePrompt(language,updated.next));setVisibleCount(count=>Math.max(count,PROFILE_ORDER.indexOf(updated.next)+1));}
      else{
        const checked=await authApi.validateRegistration({...updated.form,language});
        if(!checked.valid){setFieldErrors(checked.errors);setField(checked.next_field);setReply(checked.reply);return {valid:false};}
        setDraft(checked.values);await sendCode(checked.values);
      }
      return {valid:true};
    }catch(err){if(alive.current)setError(copy.connection);throw err;}
    finally{flight.current=false;if(alive.current)setBusy(false);}
  };
  const conversation=useMiraConversation({language,prompt,questionKey:`${phase}:${field}:${sequence}:${language}:${!!confirmation}`,field,
    enabled:phase==='profile'||!!confirmation,autoListen:phase==='profile'&&mode==='voice',busy,
    onAnswer:text=>submitField(field,text,'voice')});
  useEffect(()=>{
    const key=`${phase}:${field}:${sequence}:${language}:${!!confirmation}`;
    if(mode==='voice'){announcedStep.current=key;return;}
    if(!busy&&(phase==='profile'||confirmation)&&announcedStep.current!==key){announcedStep.current=key;conversation.resume();}
  },[phase,field,sequence,language,confirmation,busy]);
  const type=()=>{setMode('text');conversation.pause();};
  const microphone=()=>{if(mode==='voice'&&!conversation.paused){type();}else{setMode('voice');conversation.resume();}};
  const change=(key,value)=>{
    type();confirmed.current.delete(key);setForm(previous=>({...previous,[key]:value}));setFieldErrors(previous=>({...previous,[key]:null}));
    setField(key);setReply(profilePrompt(language,key));
  };
  const verify=async value=>{
    if(flight.current||!confirmation||value.length!==6||attemptedCode.current===value)return;
    flight.current=true;attemptedCode.current=value;setBusy(true);setError('');
    try{
      await completePhoneSignIn(confirmation,value,{name:draft.name,gender:draft.gender,promoter_category:draft.promoter_category,
        phone:draft.phone,email_status:draft.email_status,...(draft.email?{email:draft.email}:{})});
      setDraft({});navigate('/onboarding',{replace:true});
    }catch(err){setError(authErrorMessage(err,copy.connection,language));}
    finally{flight.current=false;if(alive.current)setBusy(false);}
  };
  const enter=async method=>{
    type();setBusy(true);setError('');
    try{await method();setDraft({});navigate('/onboarding',{replace:true});}
    catch(err){setError(authErrorMessage(err,copy.connection,language));}
    finally{if(alive.current)setBusy(false);}
  };
  const edit=()=>{type();setConfirmation(null);setCode('');setDraft({});attemptedCode.current='';verifier.current?.clear();verifier.current=null;
    confirmed.current.delete('phone');confirmed.current.delete('email');setPhase('profile');setField('phone');setReply(profilePrompt(language,'phone'));setError('');};
  return <main className="registration-page">
    <header className="registration-page-header"><Link to="/">उ Udyam Saathi</Link><LanguageSelector/></header>
    <h1 className="registration-page-title">{copy.create}</h1>
    <GuidedRegistrationPanel language={language} prompt={prompt} speech={conversation} mode={mode} onMicrophone={microphone} onTyping={type}>
      {phase==='profile'?<ProgressiveProfileFields language={language} values={form} activeField={field} visibleCount={visibleCount} disabled={busy}
        errors={fieldErrors} onChange={change} onAnswer={(key,value)=>submitField(key,value).catch(()=>{})} focusCurrent={mode==='text'}/>:<section className="registration-field registration-field--active">
        <label className="registration-code-label" htmlFor="registration-code">{copy.code}</label>
        <input ref={codeInput} id="registration-code" aria-label={copy.code} className="registration-input registration-code-input" inputMode="numeric" autoComplete="one-time-code" maxLength={6}
          value={code} disabled={busy||!confirmation} onChange={event=>{const value=event.target.value.replace(/\D/g,'').slice(0,6);setCode(value);if(value.length===6)verify(value);}}/>
        <div className="registration-secondary-actions"><button type="button" disabled={busy} onClick={()=>{setCode('');attemptedCode.current='';setConfirmation(null);verifier.current?.clear();verifier.current=null;sendCode(draft);}}>{copy.resend}</button><button type="button" disabled={busy} onClick={edit}>{copy.edit}</button></div>
      </section>}
      <div id="phone-recaptcha"/>
      {(error||(mode==='voice'&&conversation.error))&&<p role="alert" className="registration-error">{error||copy.voiceRecovery}</p>}
      <div className="registration-secondary-actions"><button disabled={busy} onClick={()=>enter(loginWithGoogle)}>{copy.google}</button><button disabled={busy} onClick={()=>enter(loginAsDemo)}>{copy.evaluator}</button></div>
      <Link to="/login" className="registration-back-link">{copy.signIn}</Link>
    </GuidedRegistrationPanel>
  </main>;
}
export default RegisterPage;
