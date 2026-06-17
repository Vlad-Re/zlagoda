import { useState, useEffect } from 'react';
import { getCategories, createCategory, updateCategory, deleteCategory } from '../../api/categories';
import Modal from '../../components/Modal';
import ConfirmDialog from '../../components/ConfirmDialog';
import { useSort, SortTh } from '../../hooks/useSort.jsx';

const EMPTY = { category_number: '', category_name: '' };

export default function Categories() {
  const sort = useSort();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modal, setModal] = useState(null); // null | { mode:'create'|'edit', data }
  const [delTarget, setDelTarget] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [formError, setFormError] = useState('');

  const load = () => {
    setLoading(true);
    getCategories()
      .then((r) => setRows(r.results))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const openCreate = () => { setForm(EMPTY); setFormError(''); setModal({ mode: 'create' }); };
  const openEdit = (row) => { setForm({ ...row }); setFormError(''); setModal({ mode: 'edit', id: row.category_number }); };

  const handleSave = async () => {
    if (!form.category_number || !form.category_name) {
      setFormError('Заповніть усі поля');
      return;
    }
    setSaving(true);
    setFormError('');
    try {
      if (modal.mode === 'create') {
        await createCategory(form);
      } else {
        await updateCategory(modal.id, form);
      }
      setModal(null);
      load();
    } catch (e) {
      setFormError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setSaving(true);
    try {
      await deleteCategory(delTarget.category_number);
      setDelTarget(null);
      load();
    } catch (e) {
      setError(e.message);
      setDelTarget(null);
    } finally {
      setSaving(false);
    }
  };

  const f = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <div className="page">
      <div className="page-header">
        <h1>Категорії</h1>
        <button className="btn btn-primary" onClick={openCreate}>+ Додати</button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? <div className="loading">Завантаження...</div> : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <SortTh sort={sort} field="category_number">№</SortTh>
                <SortTh sort={sort} field="category_name">Назва</SortTh>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && (
                <tr><td colSpan={3}><div className="empty-state"><p>Немає категорій</p></div></td></tr>
              )}
              {sort.apply(rows).map((row) => (
                <tr key={row.category_number}>
                  <td>{row.category_number}</td>
                  <td>{row.category_name}</td>
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
        <Modal
          title={modal.mode === 'create' ? 'Нова категорія' : 'Редагувати категорію'}
          onClose={() => setModal(null)}
          onSubmit={handleSave}
          loading={saving}
        >
          {formError && <div className="alert alert-error">{formError}</div>}
          <div className="form-group">
            <label>Номер категорії<span className="req"> *</span></label>
            <input type="number" value={form.category_number} onChange={f('category_number')} disabled={modal.mode === 'edit'} />
          </div>
          <div className="form-group">
            <label>Назва<span className="req"> *</span></label>
            <input type="text" value={form.category_name} onChange={f('category_name')} />
          </div>
        </Modal>
      )}

      {delTarget && (
        <ConfirmDialog
          message={`Видалити категорію "${delTarget.category_name}"? Це незворотна дія.`}
          onConfirm={handleDelete}
          onCancel={() => setDelTarget(null)}
          loading={saving}
        />
      )}
    </div>
  );
}
