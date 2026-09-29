import type { ReactNode } from 'react';
import { Card } from '../ui/Card';
export function StatCard({ label, value, tone, icon }: { label:string; value:string|number; tone?:'success'|'danger'; icon?:ReactNode }) { return <Card className="stat-card"><div className="stat-label">{icon}{label}</div><div className={`stat-value ${tone?`stat-${tone}`:''}`}>{value}</div></Card>; }
