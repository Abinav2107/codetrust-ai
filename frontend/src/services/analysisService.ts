import { issues } from '../data/issues';
import type { Issue } from '../types';

export function getOpenIssues() { return issues.filter((issue) => issue.status === 'open'); }
export function findIssue(id: string) { return issues.find((issue) => issue.id === id); }
export function applyIssueFix(issue: Issue) { issue.status = 'fixed'; }
