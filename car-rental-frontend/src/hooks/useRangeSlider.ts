import { useState, useEffect } from 'react';

export function useRangeSlider(committed: [number, number]) {
  const [local, setLocal] = useState<[number, number]>(committed);

  useEffect(() => {
    setLocal(committed);
  }, [committed]);

  return [local, setLocal] as const;
}
