export async function askAssistant(question: string, file: string) {
  await new Promise((resolve) => window.setTimeout(resolve, 750));
  const lower = question.toLowerCase();
  if (lower.includes('why') || lower.includes('fail')) {
    return 'The payment test is failing because a response parser reads an undefined id field. Check that the API response shape matches the test fixture before changing the assertion.';
  }
  if (file.includes('auth')) return 'The main risk in this file is around lines 42 and 47: null-safety and missing request error handling.';
  if (file.includes('api')) return 'Line 61 builds SQL with concatenation. Parameter binding keeps the input separate from the query text.';
  return `I would start by reviewing ${file} and checking the highlighted lines before making a change.`;
}
