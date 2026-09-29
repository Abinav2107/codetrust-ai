import { Icon } from './Icon';
export function EmptyState({ title, description }: { title:string; description:string }) { return <div className="state-box"><Icon name="inbox" size={22}/><h3>{title}</h3><p>{description}</p></div>; }
