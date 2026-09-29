import { useEffect, useRef } from 'react';

type Binding = (event: KeyboardEvent) => void;

export function useHotkeys(bindings: Record<string, Binding>) {
  const latest = useRef(bindings);
  useEffect(() => { latest.current = bindings; }, [bindings]);
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const modifier = event.metaKey || event.ctrlKey;
      const key = modifier ? `mod+${event.key.toLowerCase()}` : event.key.toLowerCase();
      latest.current[key]?.(event);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);
}
