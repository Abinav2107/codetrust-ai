import type { TestResult } from '../../types';
import { Card } from '../ui/Card';
import { StatusBadge } from '../ui/Badge';
export function TestTable({ rows, onOpen }: { rows:TestResult[]; onOpen:(id:string)=>void }) { return <Card className="table-card"><div className="table-scroll"><table className="tbl"><thead><tr><th>Test</th><th>Status</th><th>Duration</th><th>File</th></tr></thead><tbody>{rows.map(test=><tr key={test.id} className={test.status==='failed'?'clickable':''} onClick={()=>test.status==='failed'&&onOpen(test.id)}><td className="cell-primary">{test.name}</td><td><StatusBadge status={test.status}/></td><td className="mono cell-sub">{test.duration}</td><td className="mono cell-sub">{test.file}</td></tr>)}</tbody></table></div></Card>; }
