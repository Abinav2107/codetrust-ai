import type { Project } from '../types';

export const projects: Project[] = [
  { id: 'p1', name: 'acme-dashboard', language: 'TypeScript', branch: 'main', lastRun: '12 min ago', issues: 5, tests: '21', status: 'complete' },
  { id: 'p2', name: 'my-react-app', language: 'JavaScript', branch: 'main', lastRun: '2 hours ago', issues: 3, tests: '24', status: 'complete' },
  { id: 'p3', name: 'payments-service', language: 'Python', branch: 'feature/refund', lastRun: '3 hours ago', issues: 0, tests: '—', status: 'error' },
  { id: 'p4', name: 'internal-cli', language: 'Go', branch: 'main', lastRun: '3 days ago', issues: 0, tests: '12', status: 'idle' },
];
