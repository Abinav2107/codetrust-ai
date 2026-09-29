import type { Issue, Project, TestResult, ViewId } from '../types';
import { Button } from '../components/ui/Button';
import { StatCard } from '../components/dashboard/StatCard';
import { ProjectTable } from '../components/dashboard/ProjectTable';
import { ActivityList } from '../components/dashboard/ActivityList';
import { HealthSummary } from '../components/dashboard/HealthSummary';
import { QuickActions } from '../components/dashboard/QuickActions';
import { Icon } from '../components/ui/Icon';

export function DashboardPage({ projects, issues, tests, onNavigate, onNewProject, onRun, analyzing }: {
  projects: Project[];
  issues: Issue[];
  tests: TestResult[];
  onNavigate: (view: ViewId) => void;
  onNewProject: () => void;
  onRun: () => void;
  analyzing: boolean;
}) {
  const current = projects[0];
  const open = issues.filter(i => i.status === 'open').length;
  const passed = tests.filter(t => t.status === 'passed').length;
  const failed = tests.filter(t => t.status === 'failed').length;
  const coverage = Math.round((passed / Math.max(tests.length, 1)) * 100);

  return (
    <div className="page dashboard-page">
      <div className="row dashboard-heading">
        <div>
          <div className="eyebrow">Overview</div>
          <h1 className="page-title">Good afternoon, Ravi.</h1>
          <p className="page-sub">Here’s what changed in your codebase since the last run.</p>
        </div>
        <div className="detail-actions">
          <Button variant="secondary" icon="refresh" onClick={onRun} disabled={analyzing}>{analyzing ? 'Analyzing…' : 'Run analysis'}</Button>
          <Button icon="plus" onClick={onNewProject}>New project</Button>
        </div>
      </div>

      <HealthSummary
        project={current}
        openIssues={open}
        failedTests={failed}
        onOpenIssues={() => onNavigate('issues')}
        onRun={onRun}
        analyzing={analyzing}
      />

      <div className="grid-stats">
        <StatCard label="Projects" value={projects.length} icon={<Icon name="folder" size={14} />} />
        <StatCard label="Open issues" value={open} icon={<Icon name="bug" size={14} />} tone={open > 0 ? 'danger' : 'success'} />
        <StatCard label="Tests passing" value={`${passed}/${tests.length}`} icon={<Icon name="flask" size={14} />} tone="success" />
        <StatCard label="Pass rate" value={`${coverage}%`} icon={<Icon name="activity" size={14} />} />
      </div>

      <div className="dashboard-main-grid">
        <div className="dashboard-stack">
          <ProjectTable projects={projects} onOpen={onNavigate} />
          <QuickActions onRun={onRun} onIssues={() => onNavigate('issues')} onTests={() => onNavigate('tests')} onReport={() => onNavigate('report')} />
        </div>
        <ActivityList />
      </div>
    </div>
  );
}
