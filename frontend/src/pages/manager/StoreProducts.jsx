import { useState, useEffect } from 'react';
import { getStoreProducts, createStoreProduct, updateStoreProduct, deleteStoreProduct, getStoreProduct, receiveStoreProduct } from '../../api/storeProducts';
import { getDropdown } from '../../api/dropdowns';
import Modal from '../../components/Modal';
import ConfirmDialog from '../../components/ConfirmDialog';

const EMPTY = { UPC: '', UPC_prom: '', id_product: '', selling_price: '', products_number: '', promotional_product: false, expire_date: '' };

export default function StoreProducts() {
  const [rows, setRows] = useState([]);
  const [products, setProducts] = useState([]);
  const [storeProds, setStoreProds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [promoFilter, setPromoFilter] = useState('');
  const [sort, setSort] = useState('products_number');
  const [dir, setDir] = useState('asc');
  const [searchUpc, setSearchUpc] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [modal, setModal] = useState(null);
  const [delTarget, setDelTarget] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [formError, setFormError] = useState('');
  const [receipt, setReceipt] = useState(null); // { UPC, quantity, selling_price }
  const [receiptError, setReceiptError] = useState('');

  const loadDropdowns = () => {
    getDropdown('products').then((r) => setProducts(r.results)).catch(() => {});
    getStoreProducts().then((r) => setStoreProds(r.results)).catch(() => {});
  };

  const load = () => {
    setLoading(true);
    const params = { sort, dir };
    if (promoFilter !== '') params.promotional = promoFilter;
    getStoreProducts(params)
      .then((r) => setRows(r.results))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadDropdowns(); }, []);
  useEffect(load, [promoFilter, sort, dir]);

  // Clicking a column header sorts by it; clicking the active column flips direction.
  const toggleSort = (col) => {
    if (sort === col) setDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSort(col); setDir('asc'); }
  };
  const sortArrow = (col) => (sort === col ? (dir === 'asc' ? ' ▲' : ' ▼') : '');
  const thClass = (col) => 'sortable' + (sort === col ? ' sorted' : '');

  const openCreate = () => { setForm(EMPTY); setFormError(''); setModal({ mode: 'create' }); };
  const openEdit = (row) => {
    setForm({ UPC: row.UPC, UPC_prom: row.UPC_prom || '', id_product: row.id_product, selling_price: row.selling_price, products_number: row.products_number, promotional_product: row.promotional_product, expire_date: row.expire_date || '' });
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

  // Goods receipt (Надходження): top up an existing product with a new batch.
  // If a new price is entered, the whole product is revalued to that price.
  const openReceipt = (row) => {
    setReceiptError('');
    setReceipt({ UPC: row ? row.UPC : '', quantity: '', selling_price: row ? row.selling_price : '' });
  };
  const receiptProd = receipt && (rows.find((r) => r.UPC === receipt.UPC) || storeProds.find((s) => s.UPC === receipt.UPC));

  const handleReceive = async () => {
    if (!receipt.UPC) { setReceiptError('Оберіть товар'); return; }
    if (receipt.quantity === '' || Number(receipt.quantity) <= 0) {
      setReceiptError('Вкажіть кількість, що надійшла (більше нуля)'); return;
    }
    if (receipt.selling_price !== '' && Number(receipt.selling_price) < 0) {
      setReceiptError('Ціна не може бути від\'ємною'); return;
    }
    setSaving(true); setReceiptError('');
    try {
      await receiveStoreProduct(receipt.UPC, {
        quantity: Number(receipt.quantity),
        selling_price: receipt.selling_price === '' ? null : Number(receipt.selling_price),
      });
      setReceipt(null); load(); loadDropdowns();
    } catch (e) { setReceiptError(e.message); }
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
        <div className="flex gap-sm">
          <button className="btn btn-secondary" onClick={() => openReceipt(null)}>📦 Надходження</button>
          <button className="btn btn-primary" onClick={openCreate}>+ Додати</button>
        </div>
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
          <p><strong>Ціна:</strong> {Number(searchResult.selling_price).toFixed(2)} грн
            {searchResult.on_sale && <> → <strong>{(Number(searchResult.selling_price) * 0.8).toFixed(2)} грн (Акція −20%)</strong></>}
          </p>
          <p><strong>К-сть на складі:</strong> {searchResult.products_number}</p>
          <p><strong>Термін придатності:</strong> {searchResult.expire_date || '—'}</p>
          <p><strong>Акційний:</strong> {searchResult.promotional_product ? 'Так' : 'Ні'}</p>
        </div>
      )}

      {loading ? <div className="loading">Завантаження...</div> : !searchResult && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th className={thClass('"UPC"')} onClick={() => toggleSort('"UPC"')}>UPC{sortArrow('"UPC"')}</th>
                <th className={thClass('p.product_name')} onClick={() => toggleSort('p.product_name')}>Назва{sortArrow('p.product_name')}</th>
                <th className={thClass('c.category_name')} onClick={() => toggleSort('c.category_name')}>Категорія{sortArrow('c.category_name')}</th>
                <th className={thClass('selling_price')} onClick={() => toggleSort('selling_price')}>Ціна{sortArrow('selling_price')}</th>
                <th className={thClass('products_number')} onClick={() => toggleSort('products_number')}>К-сть{sortArrow('products_number')}</th>
                <th className={thClass('expire_date')} onClick={() => toggleSort('expire_date')}>Термін придатності{sortArrow('expire_date')}</th>
                <th className={thClass('promotional_product')} onClick={() => toggleSort('promotional_product')}>Акція{sortArrow('promotional_product')}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && <tr><td colSpan={8}><div className="empty-state"><p>Немає товарів</p></div></td></tr>}
              {rows.map((row) => (
                <tr key={row.UPC}>
                  <td><span className="text-muted">{row.UPC}</span></td>
                  <td>{row.product_name}</td>
                  <td>{row.category_name}</td>
                  <td className="nowrap">
                    {row.on_sale ? (
                      <>
                        <span className="text-muted" style={{ textDecoration: 'line-through' }}>
                          {Number(row.selling_price).toFixed(2)}
                        </span>{' '}
                        <strong>{(Number(row.selling_price) * 0.8).toFixed(2)} грн</strong>
                      </>
                    ) : (
                      `${Number(row.selling_price).toFixed(2)} грн`
                    )}
                  </td>
                  <td className={row.products_number === 0 ? 'badge-red' : ''}>{row.products_number}</td>
                  <td className="nowrap">{row.expire_date || '—'}</td>
                  <td>
                    {row.promotional_product
                      ? <span className="badge badge-green">{row.on_sale ? 'Акція −20%' : 'Акція'}</span>
                      : <span className="badge badge-gray">Звичайний</span>}
                  </td>
                  <td className="td-actions">
                    <button className="btn btn-secondary btn-sm" onClick={() => openReceipt(row)}>Надходження</button>
                    {' '}
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
            <label>Термін придатності</label>
            <input type="date" value={form.expire_date} onChange={f('expire_date')} />
            <small className="text-muted">Товар автоматично стає акційним, якщо до кінця терміну ≤ 3 дні та на складі більше 10 одиниць.</small>
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

      {receipt && (
        <Modal title="Надходження товару" onClose={() => setReceipt(null)} onSubmit={handleReceive} loading={saving}>
          {receiptError && <div className="alert alert-error">{receiptError}</div>}
          <div className="form-group">
            <label>Товар<span className="req"> *</span></label>
            <select
              value={receipt.UPC}
              onChange={(e) => {
                const sp = storeProds.find((s) => s.UPC === e.target.value);
                setReceipt({ ...receipt, UPC: e.target.value, selling_price: sp ? sp.selling_price : '' });
              }}
            >
              <option value="">— Оберіть товар —</option>
              {storeProds.map((s) => (
                <option key={s.UPC} value={s.UPC}>{s.product_name} [{s.UPC}]</option>
              ))}
            </select>
          </div>
          {receiptProd && (
            <p className="text-muted" style={{ fontSize: '.85rem' }}>
              Зараз на складі: <strong>{receiptProd.products_number}</strong> шт.
              за ціною <strong>{Number(receiptProd.selling_price).toFixed(2)} грн</strong>
            </p>
          )}
          <div className="form-row">
            <div className="form-group">
              <label>К-сть, що надійшла<span className="req"> *</span></label>
              <input type="number" min="1" value={receipt.quantity}
                onChange={(e) => setReceipt({ ...receipt, quantity: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Нова ціна продажу</label>
              <input type="number" min="0" step="0.01" value={receipt.selling_price}
                onChange={(e) => setReceipt({ ...receipt, selling_price: e.target.value })} />
            </div>
          </div>
          {receiptProd && receipt.selling_price !== '' && Number(receipt.selling_price) !== Number(receiptProd.selling_price) && (
            <div className="alert alert-warning" style={{ fontSize: '.85rem' }}>
              Буде виконано переоцінку: усі {Number(receiptProd.products_number) + Number(receipt.quantity || 0)} шт.
              (стара та нова партії) матимуть нову ціну {Number(receipt.selling_price || 0).toFixed(2)} грн.
            </div>
          )}
          <small className="text-muted">
            Кількість додається до наявної. Якщо вказати нову ціну продажу — увесь товар (стара і нова
            партії) переоцінюється за новою ціною. Залиште ціну без змін, щоб лише поповнити запас.
          </small>
        </Modal>
      )}

      {delTarget && (
        <ConfirmDialog message={`Видалити товар "${delTarget.product_name}" (${delTarget.UPC})?`}
          onConfirm={handleDelete} onCancel={() => setDelTarget(null)} loading={saving} />
      )}
    </div>
  );
}
