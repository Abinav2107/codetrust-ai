import { useCallback, useEffect, useState } from 'react';
import type { ViewId } from '../types';

const validViews: ViewId[] = ['dashboard','projects','workspace','issues','issue-detail','tests','test-detail','report','settings'];
function readHash(): ViewId {
  const raw = window.location.hash.replace(/^#\/?/, '') as ViewId;
  return validViews.includes(raw) ? raw : 'dashboard';
}

export function useAppNavigation() {
  const [view, setView] = useState<ViewId>(readHash);
  const [detailId, setDetailId] = useState<string | null>(null);
  useEffect(() => {
    const handler = () => setView(readHash());
    window.addEventListener('hashchange', handler);
    return () => window.removeEventListener('hashchange', handler);
  }, []);
  useEffect(() => {
    document.title = view === 'dashboard' ? 'DebugAgent · Dashboard' : `DebugAgent · ${view.replace('-', ' ')}`;
  }, [view]);
  const navigate = useCallback((next: ViewId) => {
    window.location.hash = `/${next}`;
    setView(next);
    if (!next.includes('detail')) setDetailId(null);
  }, []);
  return { view, navigate, detailId, setDetailId };
}
