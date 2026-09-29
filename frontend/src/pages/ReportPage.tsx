import type { Issue, TestResult } from '../types';
import { ReportPageView } from '../components/report/ReportPageView';
export function ReportPage({ issues, tests, onToast }: { issues: Issue[]; tests: TestResult[]; onToast: (message: string) => void }) {
  return <ReportPageView issues={issues} tests={tests} onToast={onToast} />;
}
