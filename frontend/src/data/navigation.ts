import type { ViewId } from '../types';

export interface NavItem { id: ViewId; label: string; icon: 'grid'|'folder'|'code'|'bug'|'flask'|'file'|'settings'; count?: number; }
export const navigation: { section: string; items: NavItem[] }[] = [
  { section: 'Overview', items: [
    { id: 'dashboard', label: 'Dashboard', icon: 'grid' },
    { id: 'projects', label: 'Projects', icon: 'folder' },
  ] },
  { section: 'Current Project', items: [
    { id: 'workspace', label: 'Workspace', icon: 'code' },
    { id: 'issues', label: 'Issues', icon: 'bug', count: 5 },
    { id: 'tests', label: 'Tests', icon: 'flask', count: 2 },
    { id: 'report', label: 'Report', icon: 'file' },
  ] },
];
