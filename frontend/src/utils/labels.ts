import type { Severity, Status, ViewId } from '../types';

export const viewLabels: Record<ViewId, string> = {
  dashboard: 'Dashboard', projects: 'Projects', workspace: 'acme-dashboard / Workspace', issues: 'Analysis Results',
  'issue-detail': 'Analysis / Issues', tests: 'Test Results', 'test-detail': 'acme-dashboard / Tests', report: 'Analysis Report', settings: 'Settings',
};

export const severityLabel: Record<Severity, string> = { critical: 'Critical', high: 'High', medium: 'Medium', low: 'Low' };
export const statusLabel: Record<Status, string> = {
  complete:'Complete', running:'Running', idle:'Idle', error:'Failed', open:'Open', fixed:'Fixed', passed:'Passed', failed:'Failed', skipped:'Skipped'
};

export function formatCount(value: number, singular: string, plural = `${singular}s`) { return `${value} ${value === 1 ? singular : plural}`; }
