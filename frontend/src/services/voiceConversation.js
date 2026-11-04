export class VoiceConversation {
  constructor(io) { this.io=io; this.generation=0; this.enabled=false; this.busy=false; this.processing=false; this.failures=0; this.status='paused'; }
  update({key,field,prompt,enabled,busy=false,autoListen=true}) {
    if (field!==this.field) this.failures=0;
    this.field=field; this.question={key,prompt}; this.enabled=enabled; this.busy=busy;this.autoListen=autoListen;
    if (!enabled||busy) { this.cancel(); return; }
    if (!this.processing&&this.activeKey!==key) this.run();
  }
  state(value) { this.status=value; this.io.status?.(value); }
  cancel() { this.generation++; this.activeKey=null; this.io.stop(); if(!this.processing)this.state('paused'); }
  async run() {
    if(!this.enabled||this.busy||this.processing||!this.question?.prompt)return;
    const id=++this.generation; this.activeKey=this.question.key; this.state('speaking');
    let spoken;
    try { spoken=await this.io.speak(this.question.prompt); } catch (_) { if(id===this.generation)this.pause('Audio could not play. Resume or type your answer.'); return; }
    if(id!==this.generation||!this.enabled||this.busy)return;
    if(!spoken){this.pause('Audio could not play. Resume the conversation or type your answer.');return;}
    if(!this.autoListen){this.state('paused');return;}
    this.state('listening');
    let listening;
    try { listening=await this.io.listen(); } catch (_) { listening=false; }
    if(id!==this.generation)return;
    if(!listening)this.pause('Microphone access is unavailable. Allow it once, then resume, or type your answer.');
  }
  async answer(text) {
    if(!this.enabled||this.processing||!text?.trim())return;
    const answeredKey=this.question?.key;
    let invalid=false;
    this.processing=true; this.generation++; this.io.stop(); this.state('processing');
    try {
      const result=await this.io.answer(text.trim());
      invalid=result?.valid===false;
      this.failures=result?.valid===false?this.failures+1:0;
      if(this.failures>=3)this.pause('I could not validate that answer after three tries. Type it or resume when ready.');
    }catch(_){this.pause('The answer could not be saved. Retry or resume when connected.');}
    finally{this.processing=false;this.activeKey=null;if(this.enabled&&!this.busy&&(invalid||this.question?.key!==answeredKey))this.run();}
  }
  failure() {
    if(!this.enabled||this.processing)return;
    this.failures++;this.cancel();
    if(this.failures>=3)this.pause('I could not hear a valid answer. Type it or resume when ready.');
    else this.run();
  }
  pause(message){this.enabled=false;this.cancel();this.io.error?.(message);this.io.paused?.();}
  dispose(){this.enabled=false;this.cancel();}
}
