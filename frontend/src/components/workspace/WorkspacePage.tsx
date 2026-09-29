import { useState } from 'react';
import type { ViewId } from '../../types';
import { FileTree } from './FileTree';
import { CodeViewer } from './CodeViewer';
import { AIAssistant } from './AIAssistant';
import { Button } from '../ui/Button';
import { Icon } from '../ui/Icon';

export function WorkspacePage({ onNavigate, onToast, onRun, analyzing, projectName, codeOverrides = {}, initialFile }: { onNavigate: (view: ViewId) => void; onToast: (message: string) => void; onRun: () => Promise<void>; analyzing: boolean; projectName: string; codeOverrides?: Record<string, Record<number, string>>; initialFile?: string }) {
  const [file, setFile] = useState(initialFile ?? 'src/services/auth.ts');
  const [running, setRunning] = useState(false);
  const run = async () => { if (running || analyzing) return; setRunning(true); try { await onRun(); } finally { setRunning(false); } };
  return <div className="page workspace-page">
    <div className="workspace-toolbar">
      <div className="workspace-meta"><span className="badge badge-neutral"><Icon name="gitbranch" size={13}/> main</span><span className={`workspace-status ${running || analyzing ? 'is-running' : ''}`}><i />{running || analyzing ? 'Analyzing project…' : 'Ready to analyze'}</span></div>
      <Button size="sm" icon="play" onClick={run} disabled={running || analyzing}>{running || analyzing ? 'Analyzing…' : 'Run analysis'}</Button>
    </div>
    <div className="workspace-projectbar"><div><strong>{projectName}</strong><span> · working tree</span></div><span className="mono">local preview</span></div>
    <div className="workspace-grid"><FileTree selected={file} onSelect={setFile}/><CodeViewer file={file} codeOverrides={codeOverrides}/><AIAssistant file={file} onOpenIssue={(id) => { onNavigate('issue-detail'); window.dispatchEvent(new CustomEvent('debugagent:open-issue', { detail: id })); }} /></div>
  </div>;
}

export default WorkspacePage;
