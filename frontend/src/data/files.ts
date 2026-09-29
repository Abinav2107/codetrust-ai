import type { CodeFile } from '../types';

export const codeFiles: Record<string, CodeFile> = {
  'src/services/auth.ts': {
    path: 'src/services/auth.ts', kind: 'file', lines: [
      { line: 39, code: '// get current session token' },
      { line: 40, code: 'export function getToken() {' },
      { line: 41, code: '  const user = session.current();' },
      { line: 42, code: '  const token = user.token;', error: true, fix: '  const token = user?.token;' },
      { line: 43, code: '  return token;' },
      { line: 44, code: '}' },
      { line: 45, code: '' },
      { line: 46, code: 'export async function login(email, password) {' },
      { line: 47, code: "  const res = await api.post('/login', { email, password });", error: true },
      { line: 48, code: '  return res.data;' },
      { line: 49, code: '}' },
    ],
  },
  'src/services/api.ts': {
    path: 'src/services/api.ts', kind: 'file', lines: [
      { line: 60, code: 'export function findUser(name) {' },
      { line: 61, code: "  const query = `SELECT * FROM users WHERE name = '` + name + `';`;", error: true, fix: "  const query = db.prepare('SELECT * FROM users WHERE name = ?');" },
      { line: 62, code: '  return db.exec(query);' },
      { line: 63, code: '}' },
    ],
  },
  'src/pages/Dashboard.tsx': {
    path: 'src/pages/Dashboard.tsx', kind: 'file', lines: [
      { line: 16, code: 'export function Dashboard() {' },
      { line: 17, code: '  const [projects, setProjects] = useState([]);' },
      { line: 18, code: '  const [isLoading, setIsLoading] = useState(false);', error: true, fix: '  // removed unused state' },
      { line: 19, code: '  return <ProjectList projects={projects} />;' },
      { line: 20, code: '}' },
    ],
  },
  'src/components/Header.tsx': {
    path: 'src/components/Header.tsx', kind: 'file', lines: [
      { line: 5, code: 'export function Header({ user }) {' },
      { line: 6, code: '  if (!user) return null;' },
      { line: 7, code: '  return (' },
      { line: 8, code: '    <header>' },
      { line: 9, code: '      {user.name}', error: true, fix: "      {user?.name ?? 'Guest'}" },
      { line: 10, code: '    </header>' },
      { line: 11, code: '  );' },
      { line: 12, code: '}' },
    ],
  },
  'src/App.tsx': {
    path: 'src/App.tsx', kind: 'file', lines: [
      { line: 1, code: "import { Router } from './router';" },
      { line: 2, code: '' },
      { line: 3, code: 'export default function App() {' },
      { line: 4, code: '  return <Router />;' },
      { line: 5, code: '}' },
    ],
  },
  'package.json': { path: 'package.json', kind: 'file', lines: [{ line: 1, code: '{ "name": "acme-dashboard", "version": "1.2.0" }' }] },
  'README.md': { path: 'README.md', kind: 'file', lines: [{ line: 1, code: '# acme-dashboard' }] },
};

export const fileTree = [
  { type: 'folder', name: 'src', children: [
    { type: 'folder', name: 'components', children: [{ type: 'file', key: 'src/components/Header.tsx', name: 'Header.tsx' }] },
    { type: 'folder', name: 'pages', children: [{ type: 'file', key: 'src/pages/Dashboard.tsx', name: 'Dashboard.tsx' }] },
    { type: 'folder', name: 'services', children: [
      { type: 'file', key: 'src/services/auth.ts', name: 'auth.ts' },
      { type: 'file', key: 'src/services/api.ts', name: 'api.ts' },
    ] },
    { type: 'file', key: 'src/App.tsx', name: 'App.tsx' },
  ] },
  { type: 'file', key: 'package.json', name: 'package.json' },
  { type: 'file', key: 'README.md', name: 'README.md' },
] as const;
