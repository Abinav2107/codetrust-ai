import type { Issue } from '../types';

export const issues: Issue[] = [
  {
    id: 'i1', severity: 'high', title: 'Authentication token may be undefined', file: 'src/services/auth.ts', line: 42, status: 'open',
    description: 'The token is accessed without checking whether the session exists.',
    rootCause: 'The authentication state can be undefined during initial render, before the session has loaded from storage.',
    original: 'const token = user.token;', suggested: 'const token = user?.token;',
  },
  {
    id: 'i2', severity: 'medium', title: 'Missing error handling in login()', file: 'src/services/auth.ts', line: 47, status: 'open',
    description: 'The login request has no try/catch, so network failures surface as unhandled promise rejections.',
    rootCause: 'api.post() rejects on non-2xx responses and nothing in login() catches that rejection.',
    original: "const res = await api.post('/login', { email, password });",
    suggested: "try {\n  const res = await api.post('/login', { email, password });\n  return res.data;\n} catch (e) {\n  throw new AuthError(e);\n}",
  },
  {
    id: 'i3', severity: 'medium', title: 'Unused variable "isLoading"', file: 'src/pages/Dashboard.tsx', line: 18, status: 'open',
    description: 'isLoading is declared but never read or set outside its initializer.',
    rootCause: 'Left over from an earlier loading-state implementation that was replaced by a suspense boundary.',
    original: 'const [isLoading, setIsLoading] = useState(false);', suggested: '// removed unused state',
  },
  {
    id: 'i4', severity: 'low', title: 'Potential null reference', file: 'src/components/Header.tsx', line: 9, status: 'open',
    description: 'user.name is read after an early-return null check, but user can still be an empty object.',
    rootCause: 'The null check only guards against user being falsy, not against a partially-loaded user object.',
    original: '{user.name}', suggested: "{user?.name ?? 'Guest'}",
  },
  {
    id: 'i5', severity: 'critical', title: 'SQL string built via concatenation', file: 'src/services/api.ts', line: 61, status: 'open',
    description: 'The query is built with string concatenation instead of parameter binding, exposing a SQL injection risk.',
    rootCause: 'findUser() interpolates the raw name argument directly into the query string.',
    original: "const query = `SELECT * FROM users WHERE name = '` + name + `';`",
    suggested: "const query = db.prepare('SELECT * FROM users WHERE name = ?');",
  },
];
