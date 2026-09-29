import type { MouseEvent, ReactNode } from 'react';
import { Icon } from './Icon';
import { Button } from './Button';
export function Modal({ open, title, subtitle, onClose, children, footer }: { open: boolean; title: string; subtitle?: string; onClose: () => void; children: ReactNode; footer?: ReactNode }) {
  if (!open) return null;
  return <div className="modal-backdrop" role="presentation" onMouseDown={(e: MouseEvent<HTMLDivElement>)=>{ if(e.currentTarget===e.target) onClose(); }}><div className="modal" role="dialog" aria-modal="true"><div className="modal-head"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div><button className="icon-btn" onClick={onClose} aria-label="Close"><Icon name="x"/></button></div><div className="modal-body">{children}</div>{footer && <div className="modal-actions">{footer}</div>}</div></div>;
}

export function ModalActions({ onCancel, submitLabel, onSubmit, disabled }: { onCancel:()=>void; submitLabel:string; onSubmit:()=>void; disabled?:boolean }) {
  return <><Button variant="secondary" onClick={onCancel}>Cancel</Button><Button icon="plus" onClick={onSubmit} disabled={disabled}>{submitLabel}</Button></>;
}
