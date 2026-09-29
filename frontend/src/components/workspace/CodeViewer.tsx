import { codeFiles } from '../../data/files';
import { Icon } from '../ui/Icon';

export function CodeViewer({ file, codeOverrides = {} }: { file: string; codeOverrides?: Record<string, Record<number, string>> }) {
  const source = codeFiles[file];
  const data = source && codeOverrides[file] ? { ...source, lines: source.lines?.map(line => ({ ...line, code: codeOverrides[file][line.line] ?? line.code, error: codeOverrides[file][line.line] ? false : line.error })) } : source;
  if (!data) {
    return <div className="code-panel"><div className="code-header"><span className="mono">{file}</span></div><div className="code-empty"><Icon name="file" size={22}/><strong>Preview unavailable</strong><span>This file is not included in the demo code map.</span></div></div>;
  }
  const errors = data.lines?.filter(l => l.error).length ?? 0;
  return <div className="code-panel"><div className="code-header"><span className="mono">{file}</span>{errors > 0 && <span className="err-marker"><Icon name="alert" size={13}/>{errors} {errors === 1 ? 'issue' : 'issues'}</span>}</div><div className="code-area"><div className="code-lines">{data.lines?.map(line => <div className={`code-line ${line.error ? 'code-line-error' : ''}`} key={line.line}><span className="ln">{line.line}</span><code>{line.code || ' '}</code></div>)}</div></div></div>;
}
