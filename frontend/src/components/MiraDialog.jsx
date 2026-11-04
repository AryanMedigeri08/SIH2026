import React, { useEffect,useRef } from 'react';
import { X } from 'lucide-react';

export function MiraDialog({open,onClose,title,closeLabel,children}) {
  const dialog=useRef(null);
  useEffect(()=>{const node=dialog.current;if(open&&!node.open)node.showModal();if(!open&&node.open)node.close();
    return()=>{if(node.open)node.close();};},[open]);
  return <dialog ref={dialog} className="mira-dialog" aria-label={title} onCancel={event=>{event.preventDefault();onClose();}}>
    <div className="mira-dialog-heading"><h2>{title}</h2><button type="button" aria-label={closeLabel} onClick={onClose}><X size={22}/></button></div>
    <div className="mira-dialog-body">{open&&children}</div>
  </dialog>;
}
