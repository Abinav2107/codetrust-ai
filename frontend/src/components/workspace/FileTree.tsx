import { useState, type ReactNode } from 'react';
import { fileTree } from '../../data/files';
import { codeFiles } from '../../data/files';
import { Icon } from '../ui/Icon';
export function FileTree({ selected, onSelect }: { selected:string; onSelect:(file:string)=>void }) {
 const [closed,setClosed]=useState<string[]>([]);
 const toggle=(path:string)=>setClosed(prev=>prev.includes(path)?prev.filter(x=>x!==path):[...prev,path]);
 const render=(nodes:readonly any[],depth=0):ReactNode=>nodes.map((node:any)=>node.type==='folder'?<div key={`${depth}-${node.name}`}><button className="tree-folder" style={{paddingLeft:8+depth*14}} onClick={()=>toggle(`${depth}-${node.name}`)}><Icon name="chevron-down" size={13} className={closed.includes(`${depth}-${node.name}`)?'tree-closed':''}/><Icon name="folder" size={14}/><span>{node.name}</span></button>{!closed.includes(`${depth}-${node.name}`) && render(node.children,depth+1)}</div>:<button key={node.key} className={`tree-file ${selected===node.key?'active':''}`} style={{paddingLeft:24+depth*14}} onClick={()=>onSelect(node.key)}><Icon name="file" size={14}/><span>{node.name}</span>{codeFiles[node.key]?.lines?.some(l=>l.error)?<span className="dot-err"/>:null}</button>);
 return <div className="file-tree">{render(fileTree)}</div>;
}
