import { activity } from '../../data/activity';
import { Icon } from '../ui/Icon';
import { Card } from '../ui/Card';
export function ActivityList() { return <Card className="activity-card"><div className="section-head"><div className="section-title">Recent Activity</div></div><div className="activity-list">{activity.map((item,index)=><div className="activity-item" key={`${item.time}-${index}`}><Icon name={item.icon} size={15}/><span>{item.text}</span><small>{item.time}</small></div>)}</div></Card>; }
