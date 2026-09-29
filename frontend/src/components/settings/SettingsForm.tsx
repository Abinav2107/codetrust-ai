import { useMemo, useState } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Icon } from '../ui/Icon';
import type { ThemeMode } from '../../types';

const tabs = [
  ['general', 'General', 'Project identity and defaults'],
  ['editor', 'Editor', 'Code workspace preferences'],
  ['analysis', 'Analysis', 'Scan depth and behavior'],
  ['notifications', 'Notifications', 'What should reach you'],
] as const;

export function SettingsForm({ theme, onThemeChange }: { theme: ThemeMode; onThemeChange: (theme: ThemeMode) => void }) {
  const [tab, setTab] = useState<(typeof tabs)[number][0]>('general');
  const [saved, setSaved] = useState(false);
  const current = useMemo(() => tabs.find(([id]) => id === tab)!, [tab]);
  return <div className="page">
    <div className="eyebrow">Preferences</div><h1 className="page-title">Settings</h1><p className="page-sub">Tune DebugAgent for the way you review and ship code.</p>
    <div className="settings-layout">
      <div className="settings-tabs">{tabs.map(([id, label, desc]) => <button key={id} className={tab === id ? 'active' : ''} onClick={() => { setTab(id); setSaved(false); }}><strong>{label}</strong><small>{desc}</small></button>)}</div>
      <Card className="settings-card">
        <div className="settings-heading"><div><div className="section-title">{current[1]}</div><p>{current[2]}</p></div><span className="settings-mark"><Icon name="settings" size={15}/></span></div>
        {tab === 'general' && <><div className="form-group"><label htmlFor="project-name-settings">Project name</label><input id="project-name-settings" defaultValue="acme-dashboard"/></div><div className="form-group"><label htmlFor="branch-settings">Default branch</label><input id="branch-settings" defaultValue="main"/></div></>}
        {tab === 'editor' && <><div className="form-group"><label htmlFor="theme-setting">Theme</label><select id="theme-setting" value={theme} onChange={event => onThemeChange(event.target.value as ThemeMode)}><option value="light">Light</option><option value="dark">Dark</option><option value="system">System</option></select></div><div className="form-group"><label>Font size</label><select defaultValue="13"><option value="12">12 px</option><option value="13">13 px</option><option value="14">14 px</option></select></div></>}
        {tab === 'analysis' && <><div className="form-group"><label>Analysis depth</label><select defaultValue="balanced"><option value="fast">Fast</option><option value="balanced">Balanced</option><option value="deep">Deep</option></select></div><label className="toggle-row"><span><strong>Auto-analyze on import</strong><small>Start a scan when a project is added.</small></span><input type="checkbox" defaultChecked/><span className="toggle"/></label></>}
        {tab === 'notifications' && <><label className="toggle-row"><span><strong>Desktop notifications</strong><small>Show important analysis changes.</small></span><input type="checkbox" defaultChecked/><span className="toggle"/></label><label className="toggle-row"><span><strong>Failed test alerts</strong><small>Notify when a fresh run adds failures.</small></span><input type="checkbox" defaultChecked/><span className="toggle"/></label></>}
        <div className="settings-footer"><span>{saved ? 'Changes saved locally' : 'Changes are local to this demo'}</span><Button icon="check" onClick={() => setSaved(true)}>{saved ? 'Saved' : 'Save changes'}</Button></div>
      </Card>
    </div>
  </div>;
}
