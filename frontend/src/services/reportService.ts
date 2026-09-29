import type { Issue, TestResult } from '../types';
import { issues as seedIssues } from '../data/issues';
import { tests as seedTests } from '../data/tests';

export function buildReport(issueData: Issue[] = seedIssues, testData: TestResult[] = seedTests) {
  const critical = issueData.filter(i => i.severity === 'critical' && i.status === 'open').length;
  const fixed = issueData.filter(i => i.status === 'fixed').length;
  const passed = testData.filter(t => t.status === 'passed').length;
  const failed = testData.filter(t => t.status === 'failed').length;
  const skipped = testData.filter(t => t.status === 'skipped').length;
  return {
    totalIssues: issueData.length,
    openIssues: issueData.filter(i => i.status === 'open').length,
    critical,
    fixed,
    passed,
    failed,
    skipped,
    totalTests: testData.length,
  };
}
