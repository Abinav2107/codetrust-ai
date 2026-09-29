import { TestTable } from '../components/tests/TestTable';
import { StatCard } from '../components/dashboard/StatCard';
import { tests } from '../data/tests';
import { Icon } from '../components/ui/Icon';

export function TestsPage({ onOpen }: { onOpen: (id: string) => void }) {
  const passed = tests.filter(t => t.status === 'passed').length;
  const failed = tests.filter(t => t.status === 'failed').length;
  const skipped = tests.filter(t => t.status === 'skipped').length;
  const rate = Math.round((passed / Math.max(passed + failed, 1)) * 100);
  return <div className="page">
    <div className="row"><div><div className="eyebrow">Quality</div><h1 className="page-title">Test results</h1><p className="page-sub">Last run 12 minutes ago across the current project.</p></div></div>
    <div className="grid-stats">
      <StatCard label="Passed" value={passed} tone="success" icon={<Icon name="check" size={14} />} />
      <StatCard label="Failed" value={failed} tone="danger" icon={<Icon name="x" size={14} />} />
      <StatCard label="Skipped" value={skipped} icon={<Icon name="flask" size={14} />} />
      <StatCard label="Pass rate" value={`${rate}%`} icon={<Icon name="activity" size={14} />} />
    </div>
    <TestTable rows={tests} onOpen={onOpen}/>
  </div>;
}
