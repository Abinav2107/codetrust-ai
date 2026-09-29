import type { ReactNode } from 'react';
import type { Severity, Status } from '../../types';
import { severityLabel, statusLabel } from '../../utils/labels';
export function Badge({ tone, children }: { tone: 'success'|'error'|'warning'|'info'|'neutral'; children: ReactNode }) { return <span className={`badge badge-${tone}`}>{children}</span>; }
export function StatusBadge({ status }: { status: Status }) { const tone = status==='complete'||status==='fixed'||status==='passed' ? 'success' : status==='error'||status==='failed' ? 'error' : status==='open' ? 'warning' : status==='running' ? 'info' : 'neutral'; return <Badge tone={tone}>{statusLabel[status]}</Badge>; }
export function SeverityBadge({ severity }: { severity: Severity }) { const tone = severity==='critical'||severity==='high' ? 'error' : severity==='medium' ? 'warning' : 'info'; return <Badge tone={tone}>{severityLabel[severity]}</Badge>; }
