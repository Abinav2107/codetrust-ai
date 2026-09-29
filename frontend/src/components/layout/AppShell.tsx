import type { ReactNode } from 'react';
import type { ViewId } from '../../types';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export function AppShell({ children, activeView, sidebarCollapsed, onNavigate, onToggleSidebar, issueCount, onSearch }: { children:ReactNode; activeView:ViewId; sidebarCollapsed:boolean; onNavigate:(view:ViewId)=>void; onToggleSidebar:()=>void; issueCount:number; onSearch:(value:string)=>void }) {
 return <div className="app-shell"><Sidebar activeView={activeView} collapsed={sidebarCollapsed} onNavigate={onNavigate} onToggle={onToggleSidebar} issueCount={issueCount}/><div className="main"><Header activeView={activeView} collapsed={sidebarCollapsed} onToggle={onToggleSidebar} onSearch={onSearch} onNavigate={onNavigate}/><main className="content">{children}</main></div></div>;
}
