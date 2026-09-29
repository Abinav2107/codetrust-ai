import { tests } from '../data/tests';
export function getTestSummary() {
  return {
    passed: tests.filter((test) => test.status === 'passed').length,
    failed: tests.filter((test) => test.status === 'failed').length,
    skipped: tests.filter((test) => test.status === 'skipped').length,
  };
}
export function findTest(id: string) { return tests.find((test) => test.id === id); }
