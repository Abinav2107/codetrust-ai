import { useCallback, useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { AppShell } from './components/layout/AppShell';
import { Toast } from './components/ui/Toast';
import { Modal, ModalActions } from './components/ui/Modal';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import { useAppNavigation } from './app/useAppNavigation';
import { DashboardPage } from './pages/DashboardPage';
import { ProjectsPage } from './pages/ProjectsPage';
import WorkspacePage from './pages/WorkspacePage';
import { IssuesPage } from './pages/IssuesPage';
import { TestsPage } from './pages/TestsPage';
import { ReportPage } from './pages/ReportPage';
import { SettingsPage } from './pages/SettingsPage';
import { IssueDetail } from './components/issues/IssueDetail';
import { TestDetail } from './components/tests/TestDetail';
import { issues as seedIssues } from './data/issues';
import { tests } from './data/tests';
import { projects as seedProjects } from './data/projects';
import { runProjectAnalysis } from './services/projectService';
import type { Issue, Project, ThemeMode } from './types';
import { useHotkeys } from './hooks/useHotkeys';
import { Icon } from './components/ui/Icon';

export default function App() {
  const { view, navigate, detailId, setDetailId } = useAppNavigation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [toast, setToast] = useState('');
  const [newProjectOpen, setNewProjectOpen] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [projectRepo, setProjectRepo] = useState('');
  const [projects, setProjects] = useState<Project[]>(() => seedProjects.map(p => ({ ...p })));
  const [issues, setIssues] = useState<Issue[]>(() => seedIssues.map(i => ({ ...i })));
  const [analyzing, setAnalyzing] = useState(false);
  const [theme, setTheme] = useState<ThemeMode>(() => (localStorage.getItem('debugagent-theme') as ThemeMode) || 'dark');
  const [commandOpen, setCommandOpen] = useState(false);
  const [codeOverrides, setCodeOverrides] = useState<Record<string, Record<number, string>>>({});
  const toastTimer = useRef<number | null>(null);

  const showToast = useCallback((message: string) => {
    setToast(message);
    if (toastTimer.current) window.clearTimeout(toastTimer.current);
    toastTimer.current = window.setTimeout(() => setToast(''), 2600);
  }, []);

  useEffect(() => () => {
    if (toastTimer.current) window.clearTimeout(toastTimer.current);
  }, []);

  useEffect(() => {
    localStorage.setItem('debugagent-theme', theme);
    const applyTheme = (mode: ThemeMode) => { document.documentElement.dataset.theme = mode === 'system' ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : mode; };
    applyTheme(theme);
    if (theme !== 'system') return;
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => applyTheme('system');
    media.addEventListener('change', handleChange);
    return () => media.removeEventListener('change', handleChange);
  }, [theme]);

  const openIssue = useCallback((id: string) => {
    setDetailId(id);
    navigate('issue-detail');
  }, [navigate, setDetailId]);

  const openTest = useCallback((id: string) => {
    setDetailId(id);
    navigate('test-detail');
  }, [navigate, setDetailId]);

  useEffect(() => {
    const handler = (event: Event) => openIssue((event as CustomEvent<string>).detail);
    window.addEventListener('debugagent:open-issue', handler);
    return () => window.removeEventListener('debugagent:open-issue', handler);
  }, [openIssue]);

  const handleRunAnalysis = useCallback(async () => {
    const current = projects[0];
    if (!current || analyzing) return;
    setAnalyzing(true);
    setProjects(prev => prev.map(p => p.id === current.id ? { ...p, status: 'running' } : p));
    try {
      await runProjectAnalysis(current.name);
      setProjects(prev => prev.map(p => p.id === current.id ? { ...p, status: 'complete', lastRun: 'just now' } : p));
      showToast('Analysis completed successfully');
    } catch {
      setProjects(prev => prev.map(p => p.id === current.id ? { ...p, status: 'error' } : p));
      showToast('Analysis failed — try again');
    } finally {
      setAnalyzing(false);
    }
  }, [analyzing, projects, showToast]);

  const handleApplyFix = useCallback((id: string) => {
    const target = issues.find(issue => issue.id === id);
    if (target) setCodeOverrides(prev => ({ ...prev, [target.file]: { ...(prev[target.file] ?? {}), [target.line]: target.suggested.split('\n')[0] } }));
    setIssues(prev => prev.map(issue => issue.id === id ? { ...issue, status: 'fixed' } : issue));
    showToast('Fix marked as applied');
  }, [showToast]);

  const createProject = () => {
    const name = projectName.trim();
    if (!name) return;
    const next: Project = {
      id: `p${Date.now()}`,
      name,
      language: projectRepo.includes('python') ? 'Python' : 'TypeScript',
      branch: 'main',
      lastRun: 'not run yet',
      issues: 0,
      tests: '—',
      status: 'idle',
    };
    setProjects(prev => [next, ...prev]);
    setNewProjectOpen(false);
    setProjectName('');
    setProjectRepo('');
    showToast(`${name} added to projects`);
    navigate('projects');
  };

  const issueCount = useMemo(() => issues.filter(i => i.status === 'open').length, [issues]);
  const selectedIssue = issues.find(i => i.id === detailId) ?? issues[0];
  const selectedTest = tests.find(t => t.id === detailId) ?? tests.find(t => t.status === 'failed')!;
  const currentProject = projects[0];

  useHotkeys({
    'mod+k': (e) => { e.preventDefault(); setCommandOpen(true); },
    'mod+/': (e) => { e.preventDefault(); document.querySelector<HTMLInputElement>('.chat-input input')?.focus(); },
    'mod+enter': (e) => { e.preventDefault(); void handleRunAnalysis(); },
    'escape': () => { setNewProjectOpen(false); setCommandOpen(false); },
  });

  const commands: Array<[string, string, () => void]> = [
    ['Go to Dashboard', 'Overview and recent activity', () => navigate('dashboard')],
    ['Open Projects', 'Manage connected repositories', () => navigate('projects')],
    ['Open Workspace', 'Inspect code and ask AI', () => navigate('workspace')],
    ['Review Issues', 'Find and fix detected problems', () => navigate('issues')],
    ['Run Analysis', 'Scan acme-dashboard now', () => { void handleRunAnalysis(); }],
    ['Open Settings', 'Preferences and appearance', () => navigate('settings')],
  ];

  const page = (() => {
    if (view === 'dashboard') return <DashboardPage projects={projects} issues={issues} tests={tests} onNavigate={navigate} onNewProject={() => setNewProjectOpen(true)} onRun={() => void handleRunAnalysis()} analyzing={analyzing} />;
    if (view === 'projects') return <ProjectsPage projects={projects} onNewProject={() => setNewProjectOpen(true)} onOpen={() => navigate('workspace')} />;
    if (view === 'workspace') return <WorkspacePage onNavigate={navigate} onToast={showToast} onRun={handleRunAnalysis} analyzing={analyzing} projectName={currentProject?.name ?? 'acme-dashboard'} codeOverrides={codeOverrides} initialFile={selectedIssue?.file} />;
    if (view === 'issues') return <IssuesPage issues={issues} onOpen={openIssue} />;
    if (view === 'issue-detail') return <IssueDetail issue={selectedIssue} onBack={() => navigate('issues')} onApply={() => handleApplyFix(selectedIssue.id)} onAsk={() => navigate('workspace')} />;
    if (view === 'tests') return <TestsPage onOpen={openTest} />;
    if (view === 'test-detail') return <TestDetail test={selectedTest} onBack={() => navigate('tests')} onCode={() => navigate('workspace')} onAsk={() => navigate('workspace')} />;
    if (view === 'report') return <ReportPage issues={issues} tests={tests} onToast={showToast} />;
    return <SettingsPage theme={theme} onThemeChange={setTheme} />;
  })();

  return (
    <ErrorBoundary>
      <AppShell activeView={view} sidebarCollapsed={sidebarCollapsed} onNavigate={navigate} onToggleSidebar={() => setSidebarCollapsed(v => !v)} issueCount={issueCount} onSearch={() => {}}>
        {page}
      </AppShell>
      <Toast message={toast} visible={!!toast} />
      {commandOpen && <div className="command-backdrop" role="presentation" onMouseDown={() => setCommandOpen(false)}><div className="command-palette" role="dialog" aria-modal="true" aria-label="Command palette" onMouseDown={event => event.stopPropagation()}><div className="command-search"><Icon name="search" size={16}/><input autoFocus placeholder="Type a command…" onKeyDown={event => { if (event.key === 'Escape') setCommandOpen(false); }} /></div><div className="command-list">{commands.map(([label, hint, action]) => <button key={label} onClick={() => { action(); setCommandOpen(false); }}><span><strong>{label}</strong><small>{hint}</small></span><kbd>Enter</kbd></button>)}</div><div className="command-footer"><span>Navigate</span><span><kbd>Esc</kbd> close</span></div></div></div>}
      <Modal
        open={newProjectOpen}
        title="Add a project"
        subtitle="Import a repository to start an analysis."
        onClose={() => setNewProjectOpen(false)}
        footer={<ModalActions onCancel={() => setNewProjectOpen(false)} submitLabel="Add project" onSubmit={createProject} disabled={!projectName.trim()} />}
      >
        <div className="form-group">
          <label htmlFor="project-name">Project name</label>
          <input id="project-name" value={projectName} onChange={(e: ChangeEvent<HTMLInputElement>) => setProjectName(e.target.value)} autoFocus placeholder="e.g. my-api" />
        </div>
        <div className="form-group">
          <label htmlFor="project-repo">Repository URL</label>
          <input id="project-repo" value={projectRepo} onChange={(e: ChangeEvent<HTMLInputElement>) => setProjectRepo(e.target.value)} placeholder="https://github.com/you/project" />
          <div className="hint">The URL is stored locally in this demo. Connect GitHub from Settings when a backend is added.</div>
        </div>
      </Modal>
    </ErrorBoundary>
  );
}
