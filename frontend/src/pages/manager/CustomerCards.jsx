import { useState, useEffect } from 'react';
import { getCustomerCards, createCustomerCard, updateCustomerCard, deleteCustomerCard } from '../../api/customerCards';
import Modal from '../../components/Modal';
import ConfirmDialog from '../../components/ConfirmDialog';
import { useSort, SortTh } from '../../hooks/useSort.jsx';

const EMPTY = { card_number: '', cust_surname: '', cust_name: '', cust_patronymic: '', phone_number: '', city: '', street: '', zip_code: '', percent: 0 };

export default function CustomerCards() {
  const sort = useSort();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [surnameFilter, setSurnameFilter] = useState('');
  const [modal, setModal] = useState(null);
  const [delTarget, setDelTarget] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [formError, setFormError] = useState('');

  const load = () => {
    setLoading(true);
    const params = {};
    if (surnameFilter) params.surname = surnameFilter;
    getCustomerCards(params)
      .then((r) => setRows(r.results))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [surnameFilter]);

  const openCreate = () => { setForm(EMPTY); setFormError(''); setModal({ mode: 'create' }); };
  const openEdit = (row) => { setForm({ ...row }); setFormError(''); setModal({ mode: 'edit', id: row.card_number }); };

  const handleSave = async () => {
    if (!form.card_number || !form.cust_surname || !form.cust_name || !form.phone_number) {
      setFormError("Заповніть обов'язкові поля"); return;
    }
    if (!form.phone_number.startsWith('+') || form.phone_number.length > 13) {
      setFormError('Телефон повинен починатися з "+" і мати не більше 13 символів'); return;
    }
    if (Number(form.percent) < 0) { setFormError('Відсоток знижки не може бути від\'ємним'); return; }
    setSaving(true); setFormError('');
    try {
      if (modal.mode === 'create') await createCustomerCard(form);
      else await updateCustomerCard(modal.id, form);
      setModal(null); load();
    } catch (e) { setFormError(e.message); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    setSaving(true);
    try { await deleteCustomerCard(delTarget.card_number); setDelTarget(null); load(); }
    catch (e) { setError(e.message); setDelTarget(null); }
    finally { setSaving(false); }
  };

  const f = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <div className="page">
      <div className="page-header">
        <h1>Картки клієнтів</h1>
        <button className="btn btn-primary" onClick={openCreate}>+ Додати</button>
      </div>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="filters">
        <div className="filter-group">
          <label>Пошук за прізвищем</label>
          <input type="text" value={surnameFilter} onChange={(e) => setSurnameFilter(e.target.value)} placeholder="Прізвище клієнта..." />
        </div>
      </div>

      {loading ? <div className="loading">Завантаження...</div> : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <SortTh sort={sort} field="card_number">№ картки</SortTh>
                <SortTh sort={sort} field="cust_surname">Прізвище</SortTh>
                <SortTh sort={sort} field="cust_name">Ім'я</SortTh>
                <SortTh sort={sort} field="phone_number">Телефон</SortTh>
                <SortTh sort={sort} field="percent">Знижка</SortTh>
                <SortTh sort={sort} field="city">Місто</SortTh>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && <tr><td colSpan={7}><div className="empty-state"><p>Немає карток</p></div></td></tr>}
              {sort.apply(rows).map((row) => (
                <tr key={row.card_number}>
                  <td><span className="text-muted">{row.card_number}</span></td>
                  <td>{row.cust_surname}</td>
                  <td>{row.cust_name} {row.cust_patronymic || ''}</td>
                  <td>{row.phone_number}</td>
                  <td><span className="badge badge-yellow">{row.percent}%</span></td>
                  <td>{row.city || '—'}</td>
                  <td className="td-actions">
                    <button className="btn btn-ghost btn-sm" onClick={() => openEdit(row)}>Редагувати</button>
                    {' '}
                    <button className="btn btn-danger btn-sm" onClick={() => setDelTarget(row)}>Видалити</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modal && (
        <Modal title={modal.mode === 'create' ? 'Нова картка клієнта' : 'Редагувати картку'}
          onClose={() => setModal(null)} onSubmit={handleSave} loading={saving}>
          {formError && <div className="alert alert-error">{formError}</div>}
          <div className="form-row">
            <div className="form-group"><label>№ картки<span className="req"> *</span></label><input type="text" value={form.card_number} onChange={f('card_number')} disabled={modal.mode === 'edit'} maxLength={13} /></div>
            <div className="form-group"><label>Знижка, %<span className="req"> *</span></label><input type="number" min="0" max="100" value={form.percent} onChange={f('percent')} /></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label>Прізвище<span className="req"> *</span></label><input type="text" value={form.cust_surname} onChange={f('cust_surname')} /></div>
            <div className="form-group"><label>Ім'я<span className="req"> *</span></label><input type="text" value={form.cust_name} onChange={f('cust_name')} /></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label>По батькові</label><input type="text" value={form.cust_patronymic || ''} onChange={f('cust_patronymic')} /></div>
            <div className="form-group"><label>Телефон<span className="req"> *</span></label><input type="text" placeholder="+380XXXXXXXXX" value={form.phone_number} onChange={f('phone_number')} maxLength={13} /></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label>Місто</label><input type="text" value={form.city || ''} onChange={f('city')} /></div>
            <div className="form-group"><label>Вулиця</label><input type="text" value={form.street || ''} onChange={f('street')} /></div>
          </div>
          <div className="form-group"><label>Індекс</label><input type="text" value={form.zip_code || ''} onChange={f('zip_code')} /></div>
        </Modal>
      )}

      {delTarget && (
        <ConfirmDialog message={`Видалити картку клієнта "${delTarget.cust_surname} ${delTarget.cust_name}"?`}
          onConfirm={handleDelete} onCancel={() => setDelTarget(null)} loading={saving} />
      )}
    </div>
  );
}
