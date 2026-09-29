import { useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';
import type { ViewId } from '../../types';
import { viewLabels } from '../../utils/labels';
import { Icon } from '../ui/Icon';
import { SearchInput } from '../ui/Input';

export function Header({ activeView, onToggle, onSearch, onNavigate }: { activeView: ViewId; collapsed?: boolean; onToggle: () => void; onSearch: (value: string) => void; onNavigate: (view: ViewId) => void }) {
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const commands = useMemo(() => [
    ['dashboard', 'Dashboard', 'Overview of your projects'],
    ['projects', 'Projects', 'Browse connected repositories'],
    ['workspace', 'Workspace', 'Inspect files and ask AI'],
    ['issues', 'Issues', 'Review code findings'],
    ['tests', 'Tests', 'Inspect test failures'],
    ['report', 'Report', 'Latest analysis summary'],
  ] as const, []);

  const matches = useMemo(() => {
    const q = search.trim().toLowerCase();
    return q ? commands.filter(([, label, sub]) => `${label} ${sub}`.toLowerCase().includes(q)).slice(0, 4) : commands.slice(0, 4);
  }, [search, commands]);

  useEffect(() => {
    const handler = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const submit = (value: string) => {
    setSearch(value);
    onSearch(value);
    setOpen(true);
  };

  const choose = (view: ViewId) => {
    setOpen(false);
    setSearch('');
    onNavigate(view);
  };

  return <header className="header">
    <div className="header-left">
      <button className="icon-btn" onClick={onToggle} aria-label="Toggle sidebar"><Icon name="menu"/></button>
      <div className="crumb">
        {activeView === 'workspace' || activeView === 'issue-detail' || activeView === 'test-detail' ? <><span>acme-dashboard</span><b>/</b><strong>{viewLabels[activeView].split('/').pop()?.trim()}</strong></> : <strong>{viewLabels[activeView]}</strong>}
      </div>
    </div>
    <div className="header-search" ref={ref}>
      <SearchInput value={search} onChange={(e: ChangeEvent<HTMLInputElement>) => submit(e.target.value)} onFocus={() => setOpen(true)} placeholder="Search anything…" aria-label="Search navigation" />
      <span className="shortcut">Ctrl K</span>
      {open && <div className="search-popover">
        <div className="search-pop-head">{search ? 'Matches' : 'Jump to'}<span>Esc to close</span></div>
        {matches.length ? matches.map(([id, label, sub]) => <button key={id} className="search-result" onClick={() => choose(id)}><span className="search-result-icon"><Icon name={id === 'projects' ? 'folder' : id === 'issues' ? 'bug' : id === 'tests' ? 'flask' : id === 'workspace' ? 'code' : id === 'report' ? 'file' : 'grid'} size={14}/></span><span><strong>{label}</strong><small>{sub}</small></span><Icon name="chevron-right" size={13}/></button>) : <div className="search-no-results">No matching destination.</div>}
      </div>}
    </div>
    <div className="header-right">
      <button className="icon-btn notification-button" onClick={() => setNotificationsOpen(v => !v)} aria-label="Notifications" title="Notifications"><Icon name="bell"/><span className="notification-dot"/></button>
      {notificationsOpen && <div className="notification-pop compact"><div className="np-head"><span>Notifications</span><span>2 new</span></div><div className="np-item"><strong>Analysis complete</strong><p>acme-dashboard finished with 5 open issues.</p><small>12 minutes ago</small></div><div className="np-item"><strong>2 tests failed</strong><p>Payment flow and refund calculation need attention.</p><small>13 minutes ago</small></div></div>}
      <div className="avatar avatar-header" title="Ravi K.">RK</div>
    </div>
  </header>;
}
