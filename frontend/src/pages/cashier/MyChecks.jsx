import { useState, useEffect } from 'react';
import { getChecks, getCheck } from '../../api/checks';
import Modal from '../../components/Modal';

export default function MyChecks() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [detail, setDetail] = useState(null);

  const load = () => {
    setLoading(true);
    const params = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    getChecks(params)
      .then((r) => setRows(r.results))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [dateFrom, dateTo]);

  const viewDetail = async (check_number) => {
    try { const r = await getCheck(check_number); setDetail(r); }
    catch (e) { setError(e.message); }
  };

  const todayStr = new Date().toISOString().split('T')[0];

  return (
    <div className="page">
      <div className="page-header"><h1>Мої чеки</h1></div>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="filters">
        <div className="filter-group">
          <label>З дати</label>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        </div>
        <div className="filter-group">
          <label>По дату</label>
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </div>
        <div className="filter-group" style={{ justifyContent: 'flex-end' }}>
          <label>&nbsp;</label>
          <button className="btn btn-ghost btn-sm" onClick={() => { setDateFrom(todayStr); setDateTo(todayStr); }}>Сьогодні</button>
        </div>
        <div className="filter-group">
          <label>&nbsp;</label>
          <button className="btn btn-secondary btn-sm" onClick={() => { setDateFrom(''); setDateTo(''); }}>Всі</button>
        </div>
      </div>

      {loading ? <div className="loading">Завантаження...</div> : (
        <div className="table-wrap">
          <table>
            <thead><tr><th>№ чека</th><th>Дата і час</th><th>Сума</th><th>ПДВ</th><th></th></tr></thead>
            <tbody>
              {rows.length === 0 && <tr><td colSpan={5}><div className="empty-state"><p>Немає чеків</p></div></td></tr>}
              {rows.map((row) => (
                <tr key={row.check_number}>
                  <td><span className="text-muted">{row.check_number}</span></td>
                  <td className="nowrap">{new Date(row.print_date).toLocaleString('uk-UA')}</td>
                  <td className="nowrap">{Number(row.sum_total).toFixed(2)} грн</td>
                  <td className="nowrap">{Number(row.vat).toFixed(2)} грн</td>
                  <td className="td-actions">
                    <button className="btn btn-ghost btn-sm" onClick={() => viewDetail(row.check_number)}>Деталі</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {detail && (
        <Modal title={`Чек №${detail.check.check_number}`} onClose={() => setDetail(null)} wide>
          <p><strong>Дата:</strong> {new Date(detail.check.print_date).toLocaleString('uk-UA')}</p>
          <p><strong>Сума:</strong> {Number(detail.check.sum_total).toFixed(2)} грн &nbsp;|&nbsp;
             <strong>ПДВ:</strong> {Number(detail.check.vat).toFixed(2)} грн</p>
          <div className="table-wrap" style={{ marginTop: '1rem' }}>
            <table>
              <thead><tr><th>Товар</th><th>К-сть</th><th>Ціна</th><th>Сума</th></tr></thead>
              <tbody>
                {detail.items.map((item, i) => (
                  <tr key={i}>
                    <td>{item.product_name}</td>
                    <td>{item.product_number}</td>
                    <td>{Number(item.selling_price).toFixed(2)} грн</td>
                    <td>{(item.product_number * item.selling_price).toFixed(2)} грн</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Modal>
      )}
    </div>
  );
}
