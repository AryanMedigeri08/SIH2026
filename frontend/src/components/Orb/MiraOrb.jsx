import React from 'react';
import Orb from './Orb';

const states={
  idle:{speed:.45,wobble:.6,glow:.9,highlight:.7},
  thinking:{speed:1.8,wobble:1.5,glow:1.25,highlight:1.6},
  speaking:{speed:1.1,wobble:1.25,glow:1.7,highlight:1.5},
  listening:{speed:.65,wobble:1,glow:1.2,highlight:1.1},
  paused:{speed:.15,wobble:.25,glow:.65,highlight:.4},
};

export function MiraOrb({state='idle',volume=0}) {
  const config=states[state]||states.idle;
  const level=state==='listening'?Math.min(1,Math.max(0,volume))*2:0;
  return <div className="mira-orb" data-state={state} aria-hidden="true">
    <Orb colors={['#9c43fe','#4cc2e9','#101499']} backgroundColor="#06040d" {...config}
      glow={config.glow+level} wobble={config.wobble+level} size={.88} trail={state==='thinking'?1.8:1}
      forceHoverState={state==='speaking'||state==='listening'} rotateOnHover followCursor hoverIntensity={1}/>
  </div>;
}
