import type { HTMLAttributes, ReactNode } from 'react';
export function Card({ className='', children, ...props }: HTMLAttributes<HTMLDivElement> & { children: ReactNode }) { return <div className={`card ${className}`} {...props}>{children}</div>; }
