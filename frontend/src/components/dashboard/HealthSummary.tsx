import type { Project } from '../../types';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';
import { Icon } from '../ui/Icon';

export function HealthSummary({ project, openIssues, failedTests, onOpenIssues, onRun, analyzing }: {
  project: Project;
  openIssues: number;
  failedTests: number;
  onOpenIssues: () => void;
  onRun: () => void;
  analyzing: boolean;
}) {
  const health = openIssues === 0 && failedTests === 0 ? 'Healthy' : openIssues >= 5 || failedTests >= 2 ? 'Needs attention' : 'Watch';
  const healthTone = health === 'Healthy' ? 'success' : health === 'Watch' ? 'warning' : 'error';

  return (
    <Card className="health-card">
      <div className="health-main">
        <div className="health-icon"><Icon name="activity" size={19} /></div>
        <div>
          <div className="eyebrow">Current project</div>
          <h2>{project.name}</h2>
          <p>{project.language} · <span className="mono">{project.branch}</span> · {analyzing ? 'analysis in progress' : `last analysis ${project.lastRun}`}</p>
        </div>
      </div>
      <div className="health-side">
        <Badge tone={healthTone}>{health}</Badge>
        <div className="health-metrics">
          <button onClick={onOpenIssues}><strong>{openIssues}</strong><span>open issues</span></button>
          <div><strong>{failedTests}</strong><span>failed tests</span></div>
        </div>
        <button className="text-button health-run" onClick={onRun} disabled={analyzing}><Icon name="refresh" size={13} /> {analyzing ? 'Analyzing…' : 'Run again'}</button>
      </div>
    </Card>
  );
}
