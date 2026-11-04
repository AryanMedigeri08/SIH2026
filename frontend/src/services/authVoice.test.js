import test from 'node:test';
import assert from 'node:assert/strict';
import { VoiceConversation } from './voiceConversation.js';
import { authenticatedSession } from './authenticatedSession.js';
import { destinationAfterSignIn } from './authNavigation.js';
import { canonicalAuthOrigin } from '../../vite.config.js';
import { getDevicePosition } from './deviceLocation.js';

const tick=()=>new Promise(resolve=>setImmediate(resolve));
test('device location retries a timed-out GPS reading with balanced accuracy',async()=>{
  let calls=0;const value=await getDevicePosition({getCurrentPosition(success,error,options){calls++;if(calls===1){assert.equal(options.enableHighAccuracy,true);error({code:3});}else{assert.equal(options.enableHighAccuracy,false);success({coords:{latitude:18.5,longitude:73.9,accuracy:5000}});}}});
  assert.equal(calls,2);assert.equal(value.accuracy,5000);
});
test('denied location permissions do not cause repeated permission requests',async()=>{
  let calls=0;await assert.rejects(()=>getDevicePosition({getCurrentPosition(_,error){calls++;error({code:1});}}),/blocked/);assert.equal(calls,1);
});
function fixture(answer=async()=>({valid:true}),extra={}){
  const events=[];
  const loop=new VoiceConversation({speak:async text=>{events.push(['speak',text]);return true;},listen:async()=>{events.push(['listen']);return true;},stop:()=>events.push(['stop']),status:value=>events.push(['state',value]),answer,error:message=>events.push(['error',message]),...extra});
  const update=(field='name',key=field)=>loop.update({field,key,prompt:field+' question',enabled:true});
  return {loop,events,update};
}
test('voice starts by speaking then opens microphone without a field button',async()=>{
  const {loop,events,update}=fixture();update();await tick();
  assert.equal(loop.status,'listening');assert.deepEqual(events.filter(e=>['speak','listen'].includes(e[0])),[['speak','name question'],['listen']]);loop.dispose();
});
test('a validated response automatically asks the next question exactly once',async()=>{
  let f;f=fixture(async()=>{f.update('gender');return {valid:true};});f.update();await tick();await f.loop.answer('Asha');await tick();
  assert.deepEqual(f.events.filter(e=>e[0]==='speak').map(e=>e[1]),['name question','gender question']);assert.equal(f.loop.status,'listening');f.loop.dispose();
});
test('invalid answers stay on the same field and pause after three tries',async()=>{
  const f=fixture(async()=>({valid:false}));f.update('phone');await tick();
  for(let n=0;n<3;n++){await f.loop.answer('invalid');await tick();}
  assert.equal(f.loop.field,'phone');assert.equal(f.loop.enabled,false);assert.equal(f.events.filter(e=>e[0]==='listen').length,3);
});
test('a repeat response replays the same field using a new presentation key',async()=>{
  let f;f=fixture(async()=>{f.update('name','name:repeat');return {valid:true};});f.update('name','name:first');await tick();await f.loop.answer('repeat');await tick();
  assert.equal(f.loop.field,'name');assert.equal(f.events.filter(e=>e[0]==='listen').length,2);f.loop.dispose();
});
test('silence recovery is bounded and cannot loop forever',async()=>{
  const f=fixture();f.update();await tick();
  for(let n=0;n<3;n++){f.loop.failure();await tick();}
  assert.equal(f.loop.enabled,false);assert.equal(f.events.filter(e=>e[0]==='listen').length,3);
});
test('permission rejection pauses after one attempt',async()=>{
  const f=fixture(undefined,{listen:async()=>false});f.update();await tick();assert.equal(f.loop.enabled,false);assert.equal(f.loop.status,'paused');
});
test('interruption while speech is pending never starts an obsolete microphone',async()=>{
  let finish;const f=fixture(undefined,{speak:()=>new Promise(resolve=>{finish=resolve;})});f.update();f.loop.update({field:'name',key:'name',prompt:'name',enabled:false});finish(true);await tick();
  assert.equal(f.events.some(e=>e[0]==='listen'),false);
});
test('duplicate recognition callbacks cannot save the same field twice',async()=>{
  let resolve,calls=0;const f=fixture(()=>{calls++;return new Promise(done=>{resolve=done;});});f.update();await tick();
  const first=f.loop.answer('Asha');await f.loop.answer('Asha');assert.equal(calls,1);resolve({valid:true});await first;f.loop.dispose();
});
test('Google token survives backend acceptance and destination resolution',async()=>{
  const user={uid:'google-user'};
  const session=await authenticatedSession(user,async()=> 'verified-firebase-id-token',async token=>{assert.equal(token,'verified-firebase-id-token');return {firebase_uid:'google-user'};});
  const destination=await destinationAfterSignIn(session,async token=>{assert.equal(token,'verified-firebase-id-token');return {hasBusinesses:false};});
  assert.equal(destination,'/onboarding');
});
test('backend rejection or identity mismatch never produces an accepted session',async()=>{
  await assert.rejects(()=>authenticatedSession({uid:'one'},async()=>'token',async()=>{throw new Error('rejected');}));
  await assert.rejects(()=>authenticatedSession({uid:'one'},async()=>'token',async()=>({firebase_uid:'two'})));
});
test('development documents use the Firebase-authorized localhost origin; APIs do not redirect',()=>{
  let headers,next=false;const response={writeHead:(status,value)=>{assert.equal(status,307);headers=value;},end:()=>{}};
  canonicalAuthOrigin({method:'GET',headers:{host:'127.0.0.1:3000',accept:'text/html'},url:'/login?next=plan'},response,()=>{next=true;});
  assert.equal(headers.Location,'http://localhost:3000/login?next=plan');assert.equal(next,false);
  canonicalAuthOrigin({method:'GET',headers:{host:'127.0.0.1:3000',accept:'application/json'},url:'/api/v2/auth/me'},response,()=>{next=true;});assert.equal(next,true);
});
