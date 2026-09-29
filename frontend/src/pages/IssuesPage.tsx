import { useMemo, useState, type ChangeEvent } from 'react';
import type { Issue } from '../types';
import { IssueTable } from '../components/issues/IssueTable';
import { SearchInput } from '../components/ui/Input';
import { Icon } from '../components/ui/Icon';

export function IssuesPage({ issues, onOpen }: { issues: Issue[]; onOpen: (id: string) => void }) {
  const [filter, setFilter] = useState('all');
  const [query, setQuery] = useState('');
  const rows = useMemo(() => issues.filter(i => {
    const matchesFilter = filter === 'all' || i.severity === filter || i.status === filter;
    const q = query.toLowerCase().trim();
    const matchesQuery = !q || `${i.title} ${i.file} ${i.description}`.toLowerCase().includes(q);
    return matchesFilter && matchesQuery;
  }), [filter, query, issues]);
  const open = issues.filter(i => i.status === 'open').length;
  const critical = issues.filter(i => i.severity === 'critical' && i.status === 'open').length;
  return <div className="page">
    <div className="row"><div><div className="eyebrow">Code quality</div><h1 className="page-title">Analysis results</h1><p className="page-sub">{open} open findings{critical ? ` · ${critical} critical` : ''} in the current project.</p></div></div>
    <div className="filter-bar">
      {['all','critical','high','medium','low','fixed'].map(item => <button key={item} className={`chip ${filter === item ? 'active' : ''}`} onClick={() => setFilter(item)}>{item[0].toUpperCase() + item.slice(1)}</button>)}
      <div className="search-inline"><SearchInput value={query} onChange={(e: ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)} placeholder="Search title, file, or text…" /></div>
    </div>
    <div className="issues-summary"><span><Icon name="bug" size={13}/> {rows.length} shown</span><span><Icon name="check" size={13}/> {issues.filter(i => i.status === 'fixed').length} fixed</span><span><Icon name="alert" size={13}/> {critical} critical</span></div>
    {rows.length ? <IssueTable rows={rows} onOpen={onOpen} /> : <div className="card"><p className="empty-inline">No issues match this filter or search.</p></div>}
  </div>;
}
