import type { Issue, TestResult } from '../../types';
import { buildReport } from '../../services/reportService';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { StatCard } from '../dashboard/StatCard';
import { Icon } from '../ui/Icon';
import { copyText } from '../../utils/clipboard';

export function ReportPageView({ issues, tests, onToast }: { issues: Issue[]; tests: TestResult[]; onToast: (message: string) => void }) {
  const r = buildReport(issues, tests);
  const exportReport = () => {
    const payload = JSON.stringify({ generatedAt: new Date().toISOString(), project: 'acme-dashboard', summary: r }, null, 2);
    const blob = new Blob([payload], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'debugagent-report.json'; a.click(); URL.revokeObjectURL(url);
    onToast('Report exported');
  };
  const share = async () => {
    const ok = await copyText(`${location.origin}${location.pathname}#/report`);
    onToast(ok ? 'Report link copied' : 'Could not copy the report link');
  };

  return <div className="page">
    <div className="row">
      <div><div className="eyebrow">Project summary</div><h1 className="page-title">Analysis report</h1><p className="page-sub">acme-dashboard · generated from the latest local run</p></div>
      <div className="detail-actions"><Button variant="secondary" icon="copy" onClick={share}>Share</Button><Button icon="download" onClick={exportReport}>Download</Button></div>
    </div>
    <div className="grid-stats">
      <StatCard label="Open issues" value={r.openIssues} tone={r.openIssues ? 'danger' : 'success'} icon={<Icon name="bug" size={14} />} />
      <StatCard label="Critical" value={r.critical} tone={r.critical ? 'danger' : 'success'} icon={<Icon name="alert" size={14} />} />
      <StatCard label="Fixed" value={r.fixed} tone="success" icon={<Icon name="check" size={14} />} />
      <StatCard label="Tests" value={`${r.passed}/${r.totalTests}`} icon={<Icon name="flask" size={14} />} />
    </div>
    <Card className="report-card">
      <section className="report-lead"><div className="report-kicker"><Icon name="activity" size={14}/> Executive summary</div><h2>{r.critical ? 'One critical finding needs attention.' : 'No critical findings remain.'}</h2><p>The current project has {r.openIssues} open issue{r.openIssues === 1 ? '' : 's'} and {r.failed} failing test{r.failed === 1 ? '' : 's'}. Review the highest-severity findings first, then rerun the test suite before merging.</p></section>
      <section><div className="section-title">Issues found</div><p>{r.totalIssues} findings total. {r.fixed} fixed, {r.openIssues} still open.</p></section>
      <section><div className="section-title">Test results</div><p>{r.passed} passed, {r.failed} failed, {r.skipped} skipped. Coverage remains at the project’s latest reported 87% baseline.</p></section>
      <section><div className="section-title">Recommended next steps</div><div className="report-steps"><span><b>01</b> Review the critical API finding</span><span><b>02</b> Apply safe null checks</span><span><b>03</b> Rerun the payment suite</span></div></section>
    </Card>
  </div>;
}
