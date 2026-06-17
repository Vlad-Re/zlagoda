/* eslint-disable react-refresh/only-export-components */
import { useState, useMemo } from 'react';

// Client-side column sorting for already-loaded table rows.
// Usage:
//   const sort = useSort();
//   const view = sort.apply(rows);
//   <SortTh sort={sort} field="name">Назва</SortTh>
//   {view.map(...)}
export function useSort(initialField = null, initialDir = 'asc') {
  const [field, setField] = useState(initialField);
  const [dir, setDir] = useState(initialDir);

  const toggle = (f) => {
    if (field === f) setDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setField(f); setDir('asc'); }
  };

  const apply = useMemo(() => (rows) => {
    if (!field || !Array.isArray(rows)) return rows;
    const sign = dir === 'asc' ? 1 : -1;
    return [...rows].sort((a, b) => {
      const av = a[field];
      const bv = b[field];
      // Nulls/empties always sort to the bottom regardless of direction.
      const aEmpty = av === null || av === undefined || av === '';
      const bEmpty = bv === null || bv === undefined || bv === '';
      if (aEmpty && bEmpty) return 0;
      if (aEmpty) return 1;
      if (bEmpty) return -1;
      const an = Number(av);
      const bn = Number(bv);
      const numeric = !Number.isNaN(an) && !Number.isNaN(bn);
      const cmp = numeric ? an - bn : String(av).localeCompare(String(bv), 'uk');
      return cmp * sign;
    });
  }, [field, dir]);

  const arrow = (f) => (field === f ? (dir === 'asc' ? ' ▲' : ' ▼') : '');
  const thClass = (f) => 'sortable' + (field === f ? ' sorted' : '');

  return { field, dir, toggle, apply, arrow, thClass };
}

// Clickable sortable table header cell.
export function SortTh({ sort, field, children }) {
  return (
    <th className={sort.thClass(field)} onClick={() => sort.toggle(field)}>
      {children}{sort.arrow(field)}
    </th>
  );
}
