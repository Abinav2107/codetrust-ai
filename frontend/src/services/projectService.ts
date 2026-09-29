import { projects } from '../data/projects';
import { issues as seedIssues } from '../data/issues';
import { tests as seedTests } from '../data/tests';
import { codeFiles } from '../data/files';
import {
  analyzeCodeWithBackend,
  mapBackendBugsToIssues,
  mapBackendTestsToResults,
  type BackendAnalysisData,
} from './analysisService';
import type { Issue, TestResult } from '../types';

export interface ProjectAnalysisResult {
  projectName: string;
  completedAt: string;
  issues: Issue[];
  tests: TestResult[];
  backendData?: BackendAnalysisData | null;
}

export async function runProjectAnalysis(
  projectName = 'acme-dashboard',
  targetFile = 'src/services/auth.ts',
  sourceCode?: string
): Promise<ProjectAnalysisResult> {
  const code = sourceCode || codeFiles[targetFile]?.lines?.map(l => l.code).join('\n') || 'def main():\n    pass\n';
  const lang = targetFile.endsWith('.py') ? 'python' : 'typescript';

  const backendData = await analyzeCodeWithBackend({
    code,
    language: lang,
    file_name: targetFile,
    context_description: `Analysis for ${projectName} on file ${targetFile}`,
  });

  if (backendData) {
    const issues = backendData.bugs?.length > 0
      ? mapBackendBugsToIssues(backendData.bugs, targetFile)
      : seedIssues;
    const tests = backendData.test_cases?.length > 0
      ? mapBackendTestsToResults(backendData.test_cases, targetFile)
      : seedTests;

    return {
      projectName,
      completedAt: new Date().toISOString(),
      issues,
      tests,
      backendData,
    };
  }

  // Fallback to local simulation if offline
  await new Promise((resolve) => window.setTimeout(resolve, 800));
  return {
    projectName,
    completedAt: new Date().toISOString(),
    issues: seedIssues,
    tests: seedTests,
    backendData: null,
  };
}

export function findProject(id: string) {
  return projects.find((project) => project.id === id);
}
