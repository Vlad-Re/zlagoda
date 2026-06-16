import { useState } from 'react';
import PrintPreview from '../../components/PrintPreview';
import {
  getChecksInPeriod, getSalesRevenue, getTotalSoldPerProduct,
  getTopCashiers, getTotalSoldPerCategory, getCategoriesAllProductsSold,
  getCustomersServedByAll, getEmployeesServedAll,
} from '../../api/reports';
import { getDropdown } from '../../api/dropdowns';
import { useEffect } from 'react';

const tabs = [
  { id: 'checks',    label: 'Чеки за період' },
  { id: 'revenue',   label: 'Виручка' },
  { id: 'sold',      label: 'Продані товари' },
  { id: 'promo',     label: 'Акційні/неакційні' },
  { id: 'cashiers',  label: 'Топ-касири' },
  { id: 'advanced',  label: 'Розширені' },
];

function DateRange({ value, onChange, showEmployee, cashiers }) {
  return (
    <div className="filters">
      <div className="filter-group">
        <label>З дати</label>
        <input type="date" value={value.start} onChange={(e) => onChange({ ...value, start: e.target.value })} />
      </div>
      <div className="filter-group">
        <label>По дату</label>
        <input type="date" value={value.end} onChange={(e) => onChange({ ...value, end: e.target.value })} />
      </div>
      {showEmployee && (
        <div className="filter-group">
          <label>Касир</label>
          <select value={value.id_employee || ''} onChange={(e) => onChange({ ...value, id_employee: e.target.value })}>
            <option value="">Всі касири</option>
            {cashiers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
      )}
    </div>
  );
}

export default function Reports() {
  const [tab, setTab] = useState('checks');
  const [cashiers, setCashiers] = useState([]);
  const [filters, setFilters] = useState({ start: '', end: '', id_employee: '' });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [printOpen, setPrintOpen] = useState(false);
  const [promoFilter, setPromoFilter] = useState('');
  const [soldSort, setSoldSort] = useState('total_sold');

  useEffect(() => {
    getDropdown('cashiers').then((r) => setCashiers(r.results)).catch(() => {});
  }, []);

  const run = async () => {
    setLoading(true); setError(''); setData(null);
    try {
      const p = {};
      if (filters.start) p.start = filters.start;
      if (filters.end) p.end = filters.end;
      if (filters.id_employee) p.id_employee = filters.id_employee;

      if (tab === 'checks') {
        const r = await getChecksInPeriod(p);
        setData(r.results);
      } else if (tab === 'revenue') {
        const r = await getSalesRevenue(p);
        setData(r);
      } else if (tab === 'sold') {
        const r = await getTotalSoldPerProduct(p);
        setData(r.results);
      } else if (tab === 'cashiers') {
        const r = await getTopCashiers(p);
        setData(r.results);
      } else if (tab === 'advanced') {
        const [cats, cust, emp] = await Promise.all([
          getCategoriesAllProductsSold(), getCustomersServedByAll(), getEmployeesServedAll(),
        ]);
        setData({ cats: cats.results, cust: cust.results, emp: emp.results });
      }
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const runPromo = async () => {
    setLoading(true); setError('');
    try {
      const { apiFetch } = await import('../../api/client');
      const params = new URLSearchParams({ sort: 'p.product_name' });
      if (promoFilter !== '') params.set('promotional', promoFilter);
      const r = await apiFetch('/store-products/?' + params.toString());
      setData(r.results);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const getTitle = () => tabs.find((t) => t.id === tab)?.label || '';
  const getSubtitle = () => filters.start && filters.end ? `${filters.start} — ${filters.end}` : (filters.start || filters.end || '');

  const renderContent = () => {
    if (!data) return null;
    if (tab === 'checks') {
      return (
        <table>
          <thead><tr><th>№ чека</th><th>Дата</th><th>Касир</th><th>Товари</th><th>Сума</th></tr></thead>
          <tbody>
            {data.map((ch) => (
              <tr key={ch.check_number}>
                <td>{ch.check_number}</td>
                <td>{new Date(ch.print_date).toLocaleString('uk-UA')}</td>
                <td>{ch.empl_surname} {ch.empl_name}</td>
                <td>{ch.items?.map((i) => `${i.product_name} ×${i.product_number}`).join(', ')}</td>
                <td>{Number(ch.sum_total).toFixed(2)} грн</td>
              </tr>
            ))}
            {data.length === 0 && <tr><td colSpan={5} className="text-center">Немає даних</td></tr>}
          </tbody>
        </table>
      );
    }
    if (tab === 'revenue') {
      return <p style={{ fontSize: '1.5rem', fontWeight: 700 }}>
        Загальна виручка: {Number(data.total_revenue).toFixed(2)} грн
      </p>;
    }
    if (tab === 'sold') {
      const sorted = [...data].sort((a, b) =>
        soldSort === 'name' ? a.product_name.localeCompare(b.product_name) : b.total_sold - a.total_sold
      );
      return (
        <table>
          <thead><tr><th>Товар</th><th>Продано (шт.)</th></tr></thead>
          <tbody>
            {sorted.map((r, i) => <tr key={i}><td>{r.product_name}</td><td>{r.total_sold}</td></tr>)}
            {sorted.length === 0 && <tr><td colSpan={2} className="text-center">Немає даних</td></tr>}
          </tbody>
        </table>
      );
    }
    if (tab === 'cashiers') {
      return (
        <table>
          <thead><tr><th>Касир</th><th>Чеків</th><th>Виручка</th><th>Середній чек</th></tr></thead>
          <tbody>
            {data.map((r) => (
              <tr key={r.id_employee}>
                <td>{r.empl_surname} {r.empl_name}</td>
                <td>{r.checks_count}</td>
                <td>{Number(r.revenue).toFixed(2)} грн</td>
                <td>{Number(r.avg_check).toFixed(2)} грн</td>
              </tr>
            ))}
            {data.length === 0 && <tr><td colSpan={4} className="text-center">Немає даних</td></tr>}
          </tbody>
        </table>
      );
    }
    if (tab === 'promo') {
      return (
        <table>
          <thead><tr><th>UPC</th><th>Назва</th><th>Категорія</th><th>Ціна</th><th>К-сть</th><th>Акція</th></tr></thead>
          <tbody>
            {data.map((r) => (
              <tr key={r.UPC}>
                <td>{r.UPC}</td>
                <td>{r.product_name}</td>
                <td>{r.category_name}</td>
                <td>{Number(r.selling_price).toFixed(2)} грн</td>
                <td>{r.products_number}</td>
                <td>{r.promotional_product ? 'Так' : 'Ні'}</td>
              </tr>
            ))}
            {data.length === 0 && <tr><td colSpan={6} className="text-center">Немає даних</td></tr>}
          </tbody>
        </table>
      );
    }
    if (tab === 'advanced') {
      return (
        <div>
          <h3>Категорії, де продано кожен товар</h3>
          <table><thead><tr><th>№</th><th>Назва категорії</th></tr></thead>
            <tbody>{data.cats.map((r) => <tr key={r.category_number}><td>{r.category_number}</td><td>{r.category_name}</td></tr>)}
              {data.cats.length === 0 && <tr><td colSpan={2} className="text-center">Немає даних</td></tr>}
            </tbody>
          </table>
          <h3 style={{ marginTop: '1.5rem' }}>Клієнти, яких обслужили всі касири</h3>
          <table><thead><tr><th>Прізвище</th><th>Ім'я</th></tr></thead>
            <tbody>{data.cust.map((r, i) => <tr key={i}><td>{r.cust_surname}</td><td>{r.cust_name}</td></tr>)}
              {data.cust.length === 0 && <tr><td colSpan={2} className="text-center">Немає даних</td></tr>}
            </tbody>
          </table>
          <h3 style={{ marginTop: '1.5rem' }}>Касири, що обслужили кожного клієнта з карткою</h3>
          <table><thead><tr><th>Прізвище</th><th>Ім'я</th></tr></thead>
            <tbody>{data.emp.map((r, i) => <tr key={i}><td>{r.empl_surname}</td><td>{r.empl_name}</td></tr>)}
              {data.emp.length === 0 && <tr><td colSpan={2} className="text-center">Немає даних</td></tr>}
            </tbody>
          </table>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="page">
      <div className="page-header"><h1>Звіти</h1></div>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="tabs">
        {tabs.map((t) => (
          <button key={t.id} className={`tab-btn${tab === t.id ? ' active' : ''}`}
            onClick={() => { setTab(t.id); setData(null); setError(''); }}>
            {t.label}
          </button>
        ))}
      </div>

      {tab !== 'promo' && tab !== 'advanced' && (
        <DateRange value={filters} onChange={setFilters} showEmployee={['checks','revenue'].includes(tab)} cashiers={cashiers} />
      )}

      {tab === 'promo' && (
        <div className="filters">
          <div className="filter-group">
            <label>Тип</label>
            <select value={promoFilter} onChange={(e) => setPromoFilter(e.target.value)}>
              <option value="">Всі</option>
              <option value="true">Акційні</option>
              <option value="false">Звичайні</option>
            </select>
          </div>
        </div>
      )}

      {tab === 'sold' && data && (
        <div className="filters">
          <div className="filter-group">
            <label>Сортування</label>
            <select value={soldSort} onChange={(e) => setSoldSort(e.target.value)}>
              <option value="total_sold">За к-стю</option>
              <option value="name">За назвою</option>
            </select>
          </div>
        </div>
      )}

      <div className="flex gap-sm" style={{ marginBottom: '1rem' }}>
        <button className="btn btn-primary" onClick={tab === 'promo' ? runPromo : run} disabled={loading}>
          {loading ? 'Завантаження...' : 'Сформувати'}
        </button>
        {data && (
          <button className="btn btn-ghost" onClick={() => setPrintOpen(true)}>🖨 Переглянути / Друкувати</button>
        )}
      </div>

      {data && (
        <div className="table-wrap">
          {renderContent()}
        </div>
      )}

      {printOpen && data && (
        <PrintPreview title={getTitle()} subtitle={getSubtitle()} onClose={() => setPrintOpen(false)}>
          <div className="table-wrap">
            {renderContent()}
          </div>
        </PrintPreview>
      )}
    </div>
  );
}
