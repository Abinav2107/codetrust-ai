import { useMemo, useState, type ChangeEvent } from 'react';
import type { Project } from '../types';
import { Button } from '../components/ui/Button';
import { SearchInput } from '../components/ui/Input';
import { StatusBadge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { Icon } from '../components/ui/Icon';

export function ProjectsPage({ projects, onNewProject, onOpen }: { projects: Project[]; onNewProject: () => void; onOpen: (id?: string) => void }) {
  const [filter, setFilter] = useState('all');
  const [query, setQuery] = useState('');
  const rows = useMemo(() => projects.filter(p => (filter === 'all' || p.status === filter) && p.name.toLowerCase().includes(query.toLowerCase())), [filter, query, projects]);
  return <div className="page">
    <div className="row"><div><div className="eyebrow">Workspace</div><h1 className="page-title">Projects</h1><p className="page-sub">Repositories connected to DebugAgent and their latest analysis state.</p></div><Button icon="plus" onClick={onNewProject}>New project</Button></div>
    <div className="toolbar-card card"><div className="filter-bar">{['all','complete','running','idle','error'].map(item => <button key={item} className={`chip ${filter === item ? 'active' : ''}`} onClick={() => setFilter(item)}>{item[0].toUpperCase() + item.slice(1)}</button>)}<div className="search-inline"><SearchInput value={query} onChange={(e: ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)} placeholder="Search projects…"/></div></div></div>
    <Card className="table-card"><div className="table-scroll"><table className="tbl"><thead><tr><th>Project</th><th>Language</th><th>Branch</th><th>Last run</th><th>Issues</th><th>Tests</th><th>Status</th></tr></thead><tbody>
      {rows.length ? rows.map(p => <tr className="clickable" key={p.id} onClick={() => onOpen(p.id)}><td><div className="project-cell"><span className="project-glyph"><Icon name="folder" size={14}/></span><span><strong>{p.name}</strong><small className="cell-sub">Repository</small></span></div></td><td>{p.language}</td><td className="mono cell-sub">{p.branch}</td><td className="cell-sub">{p.lastRun}</td><td>{p.status === 'error' ? '—' : p.issues}</td><td>{p.tests}</td><td><StatusBadge status={p.status}/></td></tr>) : <tr><td colSpan={7}><EmptyState title="No projects match" description="Try a different search term or status filter." /></td></tr>}
    </tbody></table></div></Card>
  </div>;
}
