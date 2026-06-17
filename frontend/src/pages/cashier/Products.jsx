import { useState, useEffect } from 'react';
import { getStoreProducts } from '../../api/storeProducts';
import { getDropdown } from '../../api/dropdowns';
import { useSort, SortTh } from '../../hooks/useSort.jsx';

export default function CashierProducts() {
  const sort = useSort();
  const [rows, setRows] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [catFilter, setCatFilter] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    getDropdown('categories').then((r) => setCategories(r.results)).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = { sort: 'p.product_name' };
    if (search) params.search = search;
    getStoreProducts(params)
      .then((r) => {
        let filtered = r.results;
        if (catFilter) filtered = filtered.filter((row) => String(row.category_name) === catFilter);
        setRows(filtered);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [search, catFilter]);

  return (
    <div className="page">
      <div className="page-header"><h1>Товари в магазині</h1></div>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="filters">
        <div className="filter-group">
          <label>Пошук за назвою</label>
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Назва товару..." />
        </div>
        <div className="filter-group">
          <label>Категорія</label>
          <select value={catFilter} onChange={(e) => setCatFilter(e.target.value)}>
            <option value="">Всі</option>
            {categories.map((c) => <option key={c.id} value={c.name}>{c.name}</option>)}
          </select>
        </div>
      </div>

      {loading ? <div className="loading">Завантаження...</div> : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <SortTh sort={sort} field="product_name">Назва</SortTh>
                <SortTh sort={sort} field="category_name">Категорія</SortTh>
                <SortTh sort={sort} field="UPC">UPC</SortTh>
                <SortTh sort={sort} field="selling_price">Ціна</SortTh>
                <SortTh sort={sort} field="products_number">На складі</SortTh>
                <SortTh sort={sort} field="promotional_product">Акція</SortTh>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && <tr><td colSpan={6}><div className="empty-state"><p>Немає товарів</p></div></td></tr>}
              {sort.apply(rows).map((row) => (
                <tr key={row.UPC}>
                  <td>{row.product_name}</td>
                  <td>{row.category_name}</td>
                  <td><span className="text-muted">{row.UPC}</span></td>
                  <td className="nowrap">{Number(row.selling_price).toFixed(2)} грн</td>
                  <td>{row.products_number === 0
                    ? <span className="badge badge-red">Немає</span>
                    : <span className="badge badge-green">{row.products_number}</span>}
                  </td>
                  <td>{row.promotional_product ? <span className="badge badge-yellow">Акція</span> : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
