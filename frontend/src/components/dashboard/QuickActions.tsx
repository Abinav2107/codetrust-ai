import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Icon } from '../ui/Icon';

export function QuickActions({ onRun, onIssues, onTests, onReport }: {
  onRun: () => void;
  onIssues: () => void;
  onTests: () => void;
  onReport: () => void;
}) {
  const actions = [
    { icon: 'play' as const, title: 'Run analysis', text: 'Scan the current branch', action: onRun },
    { icon: 'bug' as const, title: 'Review issues', text: 'Open findings and fixes', action: onIssues },
    { icon: 'flask' as const, title: 'View tests', text: 'Inspect failing test cases', action: onTests },
    { icon: 'file' as const, title: 'Open report', text: 'Share the latest summary', action: onReport },
  ];

  return (
    <Card className="quick-actions">
      <div className="section-head"><div><div className="eyebrow">Shortcuts</div><div className="section-title">Common actions</div></div></div>
      <div className="quick-grid">
        {actions.map(action => (
          <button key={action.title} className="quick-action" onClick={action.action}>
            <span className="quick-icon"><Icon name={action.icon} size={15} /></span>
            <span><strong>{action.title}</strong><small>{action.text}</small></span>
            <Icon name="chevron-right" size={14} className="quick-arrow" />
          </button>
        ))}
      </div>
    </Card>
  );
}
