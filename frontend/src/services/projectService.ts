import { projects } from '../data/projects';

export async function runProjectAnalysis(projectName = 'acme-dashboard') {
  await new Promise((resolve) => window.setTimeout(resolve, 1100));
  return { projectName, completedAt: new Date().toISOString() };
}

export function findProject(id: string) { return projects.find((project) => project.id === id); }
