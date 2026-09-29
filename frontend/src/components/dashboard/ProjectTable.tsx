import type { Project, ViewId } from '../../types';
import { Card } from '../ui/Card';
import { StatusBadge } from '../ui/Badge';
import { Icon } from '../ui/Icon';

export function ProjectTable({ projects, onOpen }: { projects: Project[]; onOpen: (view: ViewId) => void }) {
  return <Card className="table-card">
    <div className="section-head">
      <div><div className="eyebrow">Repositories</div><div className="section-title">Recent projects</div></div>
      <button className="text-button" onClick={() => onOpen('projects')}>View all <Icon name="arrow-right" size={12}/></button>
    </div>
    <div className="table-scroll"><table className="tbl">
      <thead><tr><th>Project</th><th>Language</th><th>Last run</th><th>Issues</th><th>Tests</th><th>Status</th></tr></thead>
      <tbody>{projects.map(p => <tr key={p.id} className="clickable" onClick={() => onOpen('workspace')}>
        <td><div className="project-cell"><span className="project-glyph"><Icon name="folder" size={14}/></span><span><strong className="cell-primary">{p.name}</strong><small className="cell-sub mono">{p.branch}</small></span></div></td>
        <td>{p.language}</td><td className="cell-sub">{p.lastRun}</td>
        <td>{p.status === 'error' ? '—' : p.issues}</td><td>{p.status === 'error' ? '—' : p.tests}</td><td><StatusBadge status={p.status}/></td>
      </tr>)}</tbody>
    </table></div>
  </Card>;
}
