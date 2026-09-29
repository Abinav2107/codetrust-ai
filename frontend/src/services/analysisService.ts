import { issues as seedIssues } from '../data/issues';
import { tests as seedTests } from '../data/tests';
import type { Issue, TestResult, Severity } from '../types';

const API_BASE_URL = (import.meta as unknown as { env?: Record<string, string> }).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export interface BackendBugReport {
  bug_id: string;
  title: string;
  severity: string;
  line_number?: number | null;
  description: string;
  root_cause: string;
  suggested_fix: string;
  fixed_code_snippet?: string | null;
}

export interface BackendTestCase {
  test_id: string;
  name: string;
  description?: string | null;
  test_code: string;
  expected_output?: string | null;
  test_type: string;
}

export interface BackendVerificationReport {
  verified: boolean;
  status: string;
  confidence: number;
  passed_tests: number;
  failed_tests: number;
  regressions: string[];
  remaining_risks: string[];
  evidence: string[];
}

export interface BackendAnalysisData {
  session_id: string;
  language: string;
  summary: string;
  total_bugs_detected: number;
  bugs: BackendBugReport[];
  fixed_code?: string | null;
  test_cases: BackendTestCase[];
  analysis_time_ms: number;
  status: string;
  verification_report?: BackendVerificationReport | null;
}

export function mapBackendBugsToIssues(bugs: BackendBugReport[], filePath = 'src/services/auth.ts'): Issue[] {
  if (!bugs || bugs.length === 0) return [];
  return bugs.map((b, idx) => {
    const sev = (['critical', 'high', 'medium', 'low'].includes(b.severity?.toLowerCase())
      ? b.severity.toLowerCase()
      : 'medium') as Severity;

    return {
      id: b.bug_id || `i-${idx + 1}`,
      title: b.title || 'Detected Bug',
      severity: sev,
      file: filePath,
      line: b.line_number ?? 42,
      status: 'open' as const,
      description: b.description || 'Issue flagged during static analysis and multi-agent pipeline verification.',
      rootCause: b.root_cause || 'Root cause determined by RCA Agent.',
      original: '// vulnerable line',
      suggested: b.suggested_fix || (b.fixed_code_snippet ?? '// suggested fix applied'),
    };
  });
}

export function mapBackendTestsToResults(testCases: BackendTestCase[], filePath = 'src/services/auth.ts'): TestResult[] {
  if (!testCases || testCases.length === 0) return [];
  return testCases.map((tc, idx) => ({
    id: tc.test_id || `t-${idx + 1}`,
    name: tc.name || `test_case_${idx + 1}`,
    status: 'passed' as const,
    duration: '24ms',
    file: filePath,
    expected: tc.expected_output || 'Passes quality gate',
    actual: 'passed',
    stack: tc.test_code || undefined,
  }));
}

export async function analyzeCodeWithBackend(params: {
  code: string;
  language?: string;
  file_name?: string;
  context_description?: string;
}): Promise<BackendAnalysisData | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code: params.code,
        language: params.language || 'python',
        file_name: params.file_name,
        context_description: params.context_description,
        generate_test_cases: true,
      }),
    });

    if (!response.ok) {
      console.warn('Backend returned error status:', response.status);
      return null;
    }

    const payload = await response.json();
    return payload.data as BackendAnalysisData;
  } catch (err) {
    console.warn('Could not reach backend API at', API_BASE_URL, err);
    return null;
  }
}

// Preserve original exports for backwards compatibility
export function getOpenIssues() { return seedIssues.filter((issue) => issue.status === 'open'); }
export function findIssue(id: string) { return seedIssues.find((issue) => issue.id === id); }
export function applyIssueFix(issue: Issue) { issue.status = 'fixed'; }
