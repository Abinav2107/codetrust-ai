export type ViewId =
  | 'dashboard'
  | 'projects'
  | 'workspace'
  | 'issues'
  | 'issue-detail'
  | 'tests'
  | 'test-detail'
  | 'report'
  | 'settings';

export type ThemeMode = 'light' | 'dark' | 'system';

export type Status = 'complete' | 'running' | 'idle' | 'error' | 'open' | 'fixed' | 'passed' | 'failed' | 'skipped';
export type Severity = 'critical' | 'high' | 'medium' | 'low';

export interface Project {
  id: string;
  name: string;
  language: string;
  branch: string;
  lastRun: string;
  issues: number;
  tests: string;
  status: Extract<Status, 'complete' | 'running' | 'idle' | 'error'>;
}

export interface Issue {
  id: string;
  severity: Severity;
  title: string;
  file: string;
  line: number;
  status: Extract<Status, 'open' | 'fixed'>;
  description: string;
  rootCause: string;
  original: string;
  suggested: string;
}

export interface TestResult {
  id: string;
  name: string;
  status: Extract<Status, 'passed' | 'failed' | 'skipped'>;
  duration: string;
  file: string;
  expected?: string;
  actual?: string;
  stack?: string;
}

export interface CodeLine {
  line: number;
  code: string;
  error?: boolean;
  fix?: string;
}

export interface CodeFile {
  path: string;
  kind: 'folder' | 'file';
  lines?: CodeLine[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

export interface Activity {
  icon: 'check' | 'bug' | 'flask' | 'x';
  text: string;
  time: string;
}
