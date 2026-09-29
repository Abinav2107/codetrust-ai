import { Icon } from './Icon';
export function Toast({ message, visible }: { message: string; visible: boolean }) { return <div className={`toast ${visible?'toast-visible':''}`} role="status"><Icon name="check"/><span>{message}</span></div>; }
