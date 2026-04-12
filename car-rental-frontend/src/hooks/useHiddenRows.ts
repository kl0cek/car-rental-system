import { useState } from 'react';

export function useHiddenRows() {
  const [hiddenIds, setHiddenIds] = useState<Set<string>>(new Set());

  const hide = (id: string) => setHiddenIds((prev) => new Set([...prev, id]));

  const showAll = () => setHiddenIds(new Set());

  const isHidden = (id: string) => hiddenIds.has(id);

  return { hide, showAll, isHidden, hiddenCount: hiddenIds.size };
}
