import { useState, useEffect } from 'react';
import { getStoreProducts, createStoreProduct, updateStoreProduct, deleteStoreProduct, getStoreProduct } from '../../api/storeProducts';
import { getDropdown } from '../../api/dropdowns';
import Modal from '../../components/Modal';
import ConfirmDialog from '../../components/ConfirmDialog';

const EMPTY = { UPC: '', UPC_prom: '', id_product: '', selling_price: '', products_number: '', promotional_product: false };

export default function StoreProducts() {
  const [rows, setRows] = useState([]);
  const [products, setProducts] = useState([]);
  const [storeProds, setStoreProds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [promoFilter, setPromoFilter] = useState('');
  const [sort, setSort] = useState('products_number');
  const [searchUpc, setSearchUpc] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [modal, setModal] = useState(null);
  const [delTarget, setDelTarget] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [formError, setFormError] = useState('');

  const loadDropdowns = () => {
    getDropdown('products').then((r) => setProducts(r.results)).catch(() => {});
    getStoreProducts().then((r) => setStoreProds(r.results)).catch(() => {});
  };

  const load = () => {
    setLoading(true);
    const params = { sort };
    if (promoFilter !== '') params.promotional = promoFilter;
    getStoreProducts(params)
      .then((r) => setRows(r.results))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadDropdowns(); }, []);
  useEffect(load, [promoFilter, sort]);

  const openCreate = () => { setForm(EMPTY); setFormError(''); setModal({ mode: 'create' }); };
  const openEdit = (row) => {
    setForm({ UPC: row.UPC, UPC_prom: row.UPC_prom || '', id_product: row.id_product, selling_price: row.selling_price, products_number: row.products_number, promotional_product: row.promotional_product });
    setFormError(''); setModal({ mode: 'edit', id: row.UPC });
  };

  const handleSave = async () => {
    if (!form.UPC || !form.id_product || form.selling_price === '' || form.products_number === '') {
      setFormError("Заповніть усі поля"); return;
    }
    if (Number(form.selling_price) < 0 || Number(form.products_number) < 0) {
      setFormError('Ціна та кількість не можуть бути від\'ємними'); return;
    }
    setSaving(true); setFormError('');
    try {
      const payload = { ...form, UPC_prom: form.UPC_prom || null };
      if (modal.mode === 'create') await createStoreProduct(payload);
      else await updateStoreProduct(modal.id, payload);
      setModal(null); load();
    } catch (e) { setFormError(e.message); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    setSaving(true);
    try { await deleteStoreProduct(delTarget.UPC); setDelTarget(null); load(); }
    catch (e) { setError(e.message); setDelTarget(null); }
    finally { setSaving(false); }
  };

  const handleUpcSearch = async () => {
    if (!searchUpc.trim()) { setSearchResult(null); return; }
    try { const r = await getStoreProduct(searchUpc.trim()); setSearchResult(r); }
    catch (e) { setError(e.message); }
  };

  const f = (k) => (e) => setForm({ ...form, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value });

  return (
    <div className="page">
      <div className="page-header">
        <h1>Товари в магазині</h1>
        <button className="btn btn-primary" onClick={openCreate}>+ Додати</button>
      </div>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="filters">
        <div className="filter-group">
          <label>Акційні</label>
          <select value={promoFilter} onChange={(e) => setPromoFilter(e.target.value)}>
            <option value="">Всі</option>
            <option value="true">Акційні</option>
            <option value="false">Звичайні</option>
          </select>
        </div>
        <div className="filter-group">
          <label>Сортування</label>
          <select value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="products_number">К-сть</option>
            <option value="selling_price">Ціна</option>
            <option value="p.product_name">Назва</option>
          </select>
        </div>
        <div className="filter-group">
          <label>Пошук за UPC</label>
          <div className="flex gap-sm">
            <input type="text" value={searchUpc} onChange={(e) => setSearchUpc(e.target.value)}
              placeholder="000000000001" onKeyDown={(e) => e.key === 'Enter' && handleUpcSearch()} />
            <button className="btn btn-ghost btn-sm" onClick={handleUpcSearch}>Знайти</button>
            {searchResult && <button className="btn btn-secondary btn-sm" onClick={() => setSearchResult(null)}>✕</button>}
          </div>
        </div>
      </div>

      {searchResult && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <h3>Результат пошуку за UPC: {searchResult.UPC}</h3>
          <p><strong>Назва:</strong> {searchResult.product_name}</p>
          <p><strong>Характеристики:</strong> {searchResult.characteristics}</p>
          <p><strong>Ціна:</strong> {Number(searchResult.selling_price).toFixed(2)} грн</p>
          <p><strong>К-сть на складі:</strong> {searchResult.products_number}</p>
          <p><strong>Акційний:</strong> {searchResult.promotional_product ? 'Так' : 'Ні'}</p>
        </div>
      )}

      {loading ? <div className="loading">Завантаження...</div> : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>UPC</th><th>Назва</th><th>Категорія</th><th>Ціна</th><th>К-сть</th><th>Акція</th><th></th></tr>
            </thead>
            <tbody>
              {rows.length === 0 && <tr><td colSpan={7}><div className="empty-state"><p>Немає товарів</p></div></td></tr>}
              {rows.map((row) => (
                <tr key={row.UPC}>
                  <td><span className="text-muted">{row.UPC}</span></td>
                  <td>{row.product_name}</td>
                  <td>{row.category_name}</td>
                  <td className="nowrap">{Number(row.selling_price).toFixed(2)} грн</td>
                  <td className={row.products_number === 0 ? 'badge-red' : ''}>{row.products_number}</td>
                  <td>
                    {row.promotional_product
                      ? <span className="badge badge-green">Акція</span>
                      : <span className="badge badge-gray">Звичайний</span>}
                  </td>
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
        <Modal title={modal.mode === 'create' ? 'Новий товар в магазині' : 'Редагувати товар'}
          onClose={() => setModal(null)} onSubmit={handleSave} loading={saving}>
          {formError && <div className="alert alert-error">{formError}</div>}
          <div className="form-row">
            <div className="form-group"><label>UPC<span className="req"> *</span></label><input type="text" value={form.UPC} onChange={f('UPC')} disabled={modal.mode === 'edit'} maxLength={12} /></div>
            <div className="form-group">
              <label>Товар<span className="req"> *</span></label>
              <select value={form.id_product} onChange={f('id_product')}>
                <option value="">— Оберіть —</option>
                {products.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
          </div>
          <div className="form-row">
            <div className="form-group"><label>Ціна<span className="req"> *</span></label><input type="number" min="0" step="0.01" value={form.selling_price} onChange={f('selling_price')} /></div>
            <div className="form-group"><label>К-сть<span className="req"> *</span></label><input type="number" min="0" value={form.products_number} onChange={f('products_number')} /></div>
          </div>
          <div className="form-group">
            <label>UPC базового товару (для акційних)</label>
            <select value={form.UPC_prom} onChange={f('UPC_prom')}>
              <option value="">— Не акційний —</option>
              {storeProds.filter((s) => !s.promotional_product && s.UPC !== form.UPC).map((s) => (
                <option key={s.UPC} value={s.UPC}>{s.product_name} [{s.UPC}]</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '.5rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={!!form.promotional_product} onChange={f('promotional_product')} style={{ width: 'auto' }} />
              Акційний товар
            </label>
          </div>
        </Modal>
      )}

      {delTarget && (
        <ConfirmDialog message={`Видалити товар "${delTarget.product_name}" (${delTarget.UPC})?`}
          onConfirm={handleDelete} onCancel={() => setDelTarget(null)} loading={saving} />
      )}
    </div>
  );
}
