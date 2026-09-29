import type { InputHTMLAttributes } from 'react';
import { Icon } from './Icon';
export function SearchInput({ value, onChange, placeholder='Search…', ...props }: InputHTMLAttributes<HTMLInputElement>) { return <label className="search-input"><Icon name="search" size={15}/><input value={value} onChange={onChange} placeholder={placeholder} autoComplete="off" {...props}/></label>; }
