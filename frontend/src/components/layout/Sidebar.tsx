import { navigation } from '../../data/navigation';
import type { ViewId } from '../../types';
import { Icon } from '../ui/Icon';

export function Sidebar({ activeView, collapsed, onNavigate, onToggle, issueCount }: { activeView: ViewId; collapsed: boolean; onNavigate: (view: ViewId) => void; onToggle: () => void; issueCount: number }) {
  return <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''}`}>
    <div className="brand"><div className="brand-mark">D</div><span>DebugAgent</span><span className="brand-dot" /></div>
    <nav className="nav" aria-label="Primary">
      {navigation.map(section => <div key={section.section}>
        <div className="nav-section">{section.section}</div>
        {section.items.map(item => {
          const active = activeView === item.id || (item.id === 'issues' && activeView === 'issue-detail') || (item.id === 'tests' && activeView === 'test-detail');
          return <button key={item.id} className={`nav-item ${active ? 'active' : ''}`} onClick={() => onNavigate(item.id)} title={collapsed ? item.label : undefined} aria-current={active ? 'page' : undefined}>
            <Icon name={item.icon}/><span>{item.label}</span>{item.id === 'issues' && <span className="nav-count">{issueCount}</span>}{item.id === 'tests' && <span className="nav-count nav-count-warning">2</span>}
          </button>;
        })}
      </div>)}
    </nav>
    <div className="sidebar-bottom">
      <button className={`nav-item ${activeView === 'settings' ? 'active' : ''}`} onClick={() => onNavigate('settings')} title={collapsed ? 'Settings' : undefined}><Icon name="settings"/><span>Settings</span></button>
      <div className="user"><div className="avatar">RK</div><div className="user-info"><div>Ravi K.</div><small>Free plan</small></div></div>
      <button className="sidebar-collapse" onClick={onToggle} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}><Icon name={collapsed ? 'chevron-right' : 'menu'} size={15}/></button>
    </div>
  </aside>;
}
