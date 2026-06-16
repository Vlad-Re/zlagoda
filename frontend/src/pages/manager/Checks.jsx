import { useState, useEffect } from 'react';
import { getChecks, getCheck, deleteCheck } from '../../api/checks';
import { getDropdown } from '../../api/dropdowns';
import Modal from '../../components/Modal';
import ConfirmDialog from '../../components/ConfirmDialog';

export default function Checks() {
  const [rows, setRows] = useState([]);
  const [cashiers, setCashiers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ id_employee: '', date_from: '', date_to: '' });
  const [detail, setDetail] = useState(null);
  const [delTarget, setDelTarget] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    const params = {};
    if (filters.id_employee) params.id_employee = filters.id_employee;
    if (filters.date_from) params.date_from = filters.date_from;
    if (filters.date_to) params.date_to = filters.date_to;
    getChecks(params)
      .then((r) => setRows(r.results))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    getDropdown('cashiers').then((r) => setCashiers(r.results)).catch(() => {});
  }, []);

  useEffect(load, [filters]);

  const handleViewDetail = async (check_number) => {
    try { const r = await getCheck(check_number); setDetail(r); }
    catch (e) { setError(e.message); }
  };

  const handleDelete = async () => {
    setSaving(true);
    try { await deleteCheck(delTarget.check_number); setDelTarget(null); load(); }
    catch (e) { setError(e.message); setDelTarget(null); }
    finally { setSaving(false); }
  };

  const totalRevenue = rows.reduce((s, r) => s + Number(r.sum_total), 0);

  return (
    <div className="page">
      <div className="page-header"><h1>Чеки</h1></div>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="filters">
        <div className="filter-group">
          <label>Касир</label>
          <select value={filters.id_employee} onChange={(e) => setFilters({ ...filters, id_employee: e.target.value })}>
            <option value="">Всі касири</option>
            {cashiers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div className="filter-group">
          <label>З дати</label>
          <input type="date" value={filters.date_from} onChange={(e) => setFilters({ ...filters, date_from: e.target.value })} />
        </div>
        <div className="filter-group">
          <label>По дату</label>
          <input type="date" value={filters.date_to} onChange={(e) => setFilters({ ...filters, date_to: e.target.value })} />
        </div>
        <div className="filter-group" style={{ justifyContent: 'flex-end' }}>
          <label>&nbsp;</label>
          <button className="btn btn-secondary btn-sm" onClick={() => setFilters({ id_employee: '', date_from: '', date_to: '' })}>Скинути</button>
        </div>
      </div>

      {rows.length > 0 && (
        <div style={{ marginBottom: '1rem', fontWeight: 600 }}>
          Підсумок: {rows.length} чеків, загальна сума: {totalRevenue.toLocaleString('uk-UA', { minimumFractionDigits: 2 })} грн
        </div>
      )}

      {loading ? <div className="loading">Завантаження...</div> : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>№ чека</th><th>Дата</th><th>Касир</th><th>Сума</th><th>ПДВ</th><th></th></tr>
            </thead>
            <tbody>
              {rows.length === 0 && <tr><td colSpan={6}><div className="empty-state"><p>Немає чеків</p></div></td></tr>}
              {rows.map((row) => (
                <tr key={row.check_number}>
                  <td><span className="text-muted">{row.check_number}</span></td>
                  <td className="nowrap">{new Date(row.print_date).toLocaleString('uk-UA')}</td>
                  <td>{row.empl_surname} {row.empl_name}</td>
                  <td className="nowrap">{Number(row.sum_total).toFixed(2)} грн</td>
                  <td className="nowrap">{Number(row.vat).toFixed(2)} грн</td>
                  <td className="td-actions">
                    <button className="btn btn-ghost btn-sm" onClick={() => handleViewDetail(row.check_number)}>Деталі</button>
                    {' '}
                    <button className="btn btn-danger btn-sm" onClick={() => setDelTarget(row)}>Видалити</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {detail && (
        <Modal title={`Чек ${detail.check.check_number}`} onClose={() => setDetail(null)} wide>
          <p><strong>Касир:</strong> {detail.check.empl_surname} {detail.check.empl_name}</p>
          <p><strong>Дата:</strong> {new Date(detail.check.print_date).toLocaleString('uk-UA')}</p>
          <p><strong>Сума:</strong> {Number(detail.check.sum_total).toFixed(2)} грн &nbsp;|&nbsp; <strong>ПДВ:</strong> {Number(detail.check.vat).toFixed(2)} грн</p>
          <div className="table-wrap" style={{ marginTop: '1rem' }}>
            <table>
              <thead><tr><th>Товар</th><th>UPC</th><th>К-сть</th><th>Ціна</th><th>Сума</th></tr></thead>
              <tbody>
                {detail.items.map((item, i) => (
                  <tr key={i}>
                    <td>{item.product_name}</td>
                    <td><span className="text-muted">{item.UPC}</span></td>
                    <td>{item.product_number}</td>
                    <td className="nowrap">{Number(item.selling_price).toFixed(2)} грн</td>
                    <td className="nowrap">{(item.product_number * item.selling_price).toFixed(2)} грн</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Modal>
      )}

      {delTarget && (
        <ConfirmDialog message={`Видалити чек №${delTarget.check_number}?`}
          onConfirm={handleDelete} onCancel={() => setDelTarget(null)} loading={saving} />
      )}
    </div>
  );
}
