import { useState, useEffect } from 'react';
import { getProducts, createProduct, updateProduct, deleteProduct } from '../../api/products';
import { getDropdown } from '../../api/dropdowns';
import Modal from '../../components/Modal';
import ConfirmDialog from '../../components/ConfirmDialog';
import { useSort, SortTh } from '../../hooks/useSort.jsx';

const EMPTY = { id_product: '', category_number: '', product_name: '', characteristics: '' };

export default function Products() {
  const sort = useSort();
  const [rows, setRows] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [catFilter, setCatFilter] = useState('');
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(null);
  const [delTarget, setDelTarget] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [formError, setFormError] = useState('');

  const loadCats = () => getDropdown('categories').then((r) => setCategories(r.results)).catch(() => {});

  const load = () => {
    setLoading(true);
    const params = {};
    if (catFilter) params.category = catFilter;
    if (search) params.search = search;
    getProducts(params)
      .then((r) => setRows(r.results))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadCats(); }, []);
  useEffect(load, [catFilter, search]);

  const openCreate = () => { setForm(EMPTY); setFormError(''); setModal({ mode: 'create' }); };
  const openEdit = (row) => { setForm({ ...row }); setFormError(''); setModal({ mode: 'edit', id: row.id_product }); };

  const handleSave = async () => {
    if (!form.id_product || !form.category_number || !form.product_name || !form.characteristics) {
      setFormError("Заповніть усі поля"); return;
    }
    setSaving(true); setFormError('');
    try {
      if (modal.mode === 'create') await createProduct(form);
      else await updateProduct(modal.id, form);
      setModal(null); load();
    } catch (e) { setFormError(e.message); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    setSaving(true);
    try { await deleteProduct(delTarget.id_product); setDelTarget(null); load(); }
    catch (e) { setError(e.message); setDelTarget(null); }
    finally { setSaving(false); }
  };

  const f = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <div className="page">
      <div className="page-header">
        <h1>Товари</h1>
        <button className="btn btn-primary" onClick={openCreate}>+ Додати</button>
      </div>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="filters">
        <div className="filter-group">
          <label>Категорія</label>
          <select value={catFilter} onChange={(e) => setCatFilter(e.target.value)}>
            <option value="">Всі</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div className="filter-group">
          <label>Пошук за назвою</label>
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Назва товару..." />
        </div>
      </div>

      {loading ? <div className="loading">Завантаження...</div> : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <SortTh sort={sort} field="id_product">ID</SortTh>
                <SortTh sort={sort} field="product_name">Назва</SortTh>
                <SortTh sort={sort} field="category_name">Категорія</SortTh>
                <SortTh sort={sort} field="characteristics">Характеристики</SortTh>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && <tr><td colSpan={5}><div className="empty-state"><p>Немає товарів</p></div></td></tr>}
              {sort.apply(rows).map((row) => (
                <tr key={row.id_product}>
                  <td><span className="text-muted">{row.id_product}</span></td>
                  <td>{row.product_name}</td>
                  <td>{row.category_name}</td>
                  <td className="text-muted">{row.characteristics}</td>
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
        <Modal title={modal.mode === 'create' ? 'Новий товар' : 'Редагувати товар'}
          onClose={() => setModal(null)} onSubmit={handleSave} loading={saving}>
          {formError && <div className="alert alert-error">{formError}</div>}
          <div className="form-row">
            <div className="form-group"><label>ID<span className="req"> *</span></label><input type="number" value={form.id_product} onChange={f('id_product')} disabled={modal.mode === 'edit'} /></div>
            <div className="form-group">
              <label>Категорія<span className="req"> *</span></label>
              <select value={form.category_number} onChange={f('category_number')}>
                <option value="">— Оберіть —</option>
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
          </div>
          <div className="form-group"><label>Назва<span className="req"> *</span></label><input type="text" value={form.product_name} onChange={f('product_name')} /></div>
          <div className="form-group"><label>Характеристики<span className="req"> *</span></label><input type="text" value={form.characteristics} onChange={f('characteristics')} /></div>
        </Modal>
      )}

      {delTarget && (
        <ConfirmDialog message={`Видалити товар "${delTarget.product_name}"?`}
          onConfirm={handleDelete} onCancel={() => setDelTarget(null)} loading={saving} />
      )}
    </div>
  );
}
