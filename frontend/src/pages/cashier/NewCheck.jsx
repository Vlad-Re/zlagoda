import { useState, useEffect } from 'react';
import { getDropdown } from '../../api/dropdowns';
import { createCheck } from '../../api/checks';

export default function NewCheck() {
  const [storeProds, setStoreProds] = useState([]);
  const [cards, setCards] = useState([]);
  const [cardNumber, setCardNumber] = useState('');
  const [items, setItems] = useState([{ UPC: '', product_number: 1 }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    getDropdown('store-products').then((r) => setStoreProds(r.results)).catch(() => {});
    getDropdown('customer-cards').then((r) => setCards(r.results)).catch(() => {});
  }, []);

  const getProdInfo = (upc) => storeProds.find((p) => p.id === upc);

  const addItem = () => setItems([...items, { UPC: '', product_number: 1 }]);
  const removeItem = (i) => setItems(items.filter((_, idx) => idx !== i));
  const updateItem = (i, k, v) => setItems(items.map((it, idx) => {
    if (idx !== i) return it;

    if (k === 'product_number') {
      if (v === '') return { ...it, [k]: '' };

      let val = parseInt(v, 10);
      if (isNaN(val) || val < 1) val = 1;

      return { ...it, [k]: val };
    }

    return { ...it, [k]: v };
  }));
  const total = items.reduce((sum, it) => {
    const prod = getProdInfo(it.UPC);
    return sum + (prod ? Number(prod.selling_price) * Number(it.product_number || 0) : 0);
  }, 0);

  const vat = total * 0.2;

  const handleSubmit = async () => {
    setError(''); setSuccess('');
    const validItems = items.filter((it) => it.UPC && Number(it.product_number) > 0);
    if (validItems.length === 0) {
      setError('Додайте хоча б один товар'); return;
    }
    for (const it of validItems) {
      const prod = getProdInfo(it.UPC);
      if (prod && Number(it.product_number) > prod.products_number) {
        setError(`Недостатньо товару "${prod.product_name}" (є ${prod.products_number} шт.)`);
        return;
      }
    }
    setLoading(true);
    try {
      const r = await createCheck({
        card_number: cardNumber || null,
        products: validItems.map((it) => ({ UPC: it.UPC, product_number: Number(it.product_number) })),
      });
      setSuccess(`Чек №${r.check_number} успішно створено!`);
      setItems([{ UPC: '', product_number: 1 }]);
      setCardNumber('');
      getDropdown('store-products').then((r) => setStoreProds(r.results)).catch(() => {});
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="page">
      <div className="page-header"><h1>Новий чек</h1></div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div style={{ maxWidth: 640 }}>
        <div className="form-group">
          <label>Картка клієнта (необов'язково)</label>
          <select value={cardNumber} onChange={(e) => setCardNumber(e.target.value)}>
            <option value="">— Без картки —</option>
            {cards.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>

        <h3 style={{ marginTop: '1rem' }}>Товари</h3>

        {items.map((item, i) => {
          const prod = getProdInfo(item.UPC);
          return (
            <div key={i} className="check-item-row">
              <select value={item.UPC} onChange={(e) => updateItem(i, 'UPC', e.target.value)} style={{ flex: '1 1 250px' }}>
                <option value="">— Оберіть товар —</option>
                {storeProds.map((p) => (
                  <option key={p.id} value={p.id} disabled={p.products_number === 0}>
                    {p.name} {p.products_number === 0 ? '(немає)' : ''}
                  </option>
                ))}
              </select>
              <input
                type="number" min="1" value={item.product_number}
                max={prod?.products_number || 9999}
                onChange={(e) => updateItem(i, 'product_number', e.target.value)}
                style={{ width: 80 }}
              />
              {prod && <span className="text-muted nowrap">{Number(prod.selling_price).toFixed(2)} грн/шт.</span>}
              {items.length > 1 && (
                <button className="btn btn-danger btn-sm" onClick={() => removeItem(i)}>✕</button>
              )}
            </div>
          );
        })}

        <button className="btn btn-ghost btn-sm" onClick={addItem} style={{ marginTop: '.5rem' }}>
          + Додати товар
        </button>

        <div className="check-total" style={{ marginTop: '1rem' }}>
          <div>До сплати: <strong>{total.toFixed(2)} грн</strong></div>
          <div className="text-muted" style={{ fontSize: '.85rem' }}>ПДВ (20%): {vat.toFixed(2)} грн</div>
        </div>

        <div style={{ marginTop: '1rem', display: 'flex', gap: '.75rem' }}>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={loading}>
            {loading ? 'Оформлення...' : 'Оформити чек'}
          </button>
          <button className="btn btn-secondary" onClick={() => { setItems([{ UPC: '', product_number: 1 }]); setCardNumber(''); setError(''); setSuccess(''); }}>
            Скинути
          </button>
        </div>
      </div>
    </div>
  );
}
