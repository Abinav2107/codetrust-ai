import type { ButtonHTMLAttributes, ComponentProps, ReactNode } from 'react';
import { Icon } from './Icon';

type Variant = 'primary'|'secondary'|'ghost'|'danger';
export function Button({ variant='primary', size='md', icon, children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: 'sm'|'md'; icon?: ComponentProps<typeof Icon>['name']; children?: ReactNode }) {
  return <button className={`btn btn-${variant} btn-${size}`} {...props}>{icon && <Icon name={icon} size={size==='sm'?14:16}/>} {children}</button>;
}
