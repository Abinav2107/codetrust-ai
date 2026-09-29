import type { TestResult } from '../types';

export const tests: TestResult[] = [
  { id: 't1', name: 'Login flow', status: 'passed', duration: '120ms', file: 'auth.test.ts' },
  { id: 't2', name: 'Dashboard rendering', status: 'passed', duration: '85ms', file: 'Dashboard.test.tsx' },
  {
    id: 't3', name: 'Payment flow', status: 'failed', duration: '340ms', file: 'payment.test.ts',
    expected: 'status: 200, body: { success: true }',
    actual: 'status: 500, body: { error: "Cannot read properties of undefined (reading id)" }',
    stack: 'at processPayment (src/services/payments.ts:34:18)\nat Object.<anonymous> (payment.test.ts:22:5)',
  },
  { id: 't4', name: 'Logout', status: 'passed', duration: '40ms', file: 'auth.test.ts' },
  {
    id: 't5', name: 'Refund calculation', status: 'failed', duration: '210ms', file: 'payment.test.ts',
    expected: 'refundAmount: 42.50', actual: 'refundAmount: NaN',
    stack: 'at calculateRefund (src/services/payments.ts:58:11)\nat Object.<anonymous> (payment.test.ts:40:5)',
  },
  { id: 't6', name: 'API request retries', status: 'skipped', duration: '—', file: 'api.test.ts' },
];
