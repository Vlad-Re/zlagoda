import { useState, useEffect } from 'react';
import { getDropdown } from '../../api/dropdowns';
import { createCheck } from '../../api/checks';

// Typeable product picker: filter by UPC or name, pick from a styled list,
// or type/scan a full UPC to select it directly.
function ProductPicker({ products, value, onChange }) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const selected = products.find((p) => p.id === value);

  const q = query.trim().toLowerCase();
  const filtered = products
    .filter((p) =>
      !q ||
      p.id.toLowerCase().includes(q) ||
      p.product_name.toLowerCase().includes(q),
    )
    .slice(0, 50);

  const handleType = (v) => {
    setQuery(v);
    setOpen(true);
    const exact = products.find((p) => p.id === v.trim());
    onChange(exact ? exact.id : '');
  };

  const pick = (p) => {
    onChange(p.id);
    setQuery('');
    setOpen(false);
  };

  const display = open ? query : (selected ? `${selected.product_name} [${selected.id}]` : query);

  return (
    <div className="combo" style={{ flex: '1 1 250px' }}>
      <input
        value={display}
        onChange={(e) => handleType(e.target.value)}
        onFocus={() => { setQuery(''); setOpen(true); }}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        placeholder="Введіть UPC або назву товару"
      />
      {open && filtered.length > 0 && (
        <ul className="combo-list">
          {filtered.map((p) => (
            <li key={p.id} className="combo-item" onMouseDown={() => pick(p)}>
              {p.product_name} <small>[{p.id}] · {Number(p.selling_price).toFixed(2)} грн</small>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

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
  // On-sale (near-expiry) products are charged 20% off their list price.
  const EXPIRY_SALE_DISCOUNT = 0.2;
  const unitPrice = (prod) =>
    Number(prod.selling_price) * (prod.on_sale ? 1 - EXPIRY_SALE_DISCOUNT : 1);

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
  const selectedCard = cards.find((c) => c.id === cardNumber);
  const cardPercent = selectedCard ? Number(selectedCard.percent) || 0 : 0;

  const subtotal = items.reduce((sum, it) => {
    const prod = getProdInfo(it.UPC);
    return sum + (prod ? unitPrice(prod) * Number(it.product_number || 0) : 0);
  }, 0);
  const discount = subtotal * cardPercent / 100;
  const total = subtotal - discount;
  const vat = total * 0.2;

  // Items on the expiry sale (20% off) — collected to explain the discount on the UI.
  const saleItems = items
    .map((it) => getProdInfo(it.UPC))
    .filter((p) => p && p.on_sale);

  const handleSubmit = async () => {
    setError(''); setSuccess('');
    const validItems = items.filter((it) => it.UPC && Number(it.product_number) > 0);
    if (validItems.length === 0) {
      setError('Додайте хоча б один товар'); return;
    }
    for (const it of validItems) {
      const prod = getProdInfo(it.UPC);
      if (!prod) {
        setError(`Товар з UPC "${it.UPC}" не знайдено`);
        return;
      }
      if (Number(it.product_number) > prod.products_number) {
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
      const discountNote = r.card_percent > 0
        ? ` Застосовано знижку ${r.card_percent}% (−${Number(r.discount_amount).toFixed(2)} грн).`
        : '';
      setSuccess(`Чек №${r.check_number} успішно створено! До сплати: ${Number(r.sum_total).toFixed(2)} грн.${discountNote}`);
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
              <ProductPicker
                products={storeProds}
                value={item.UPC}
                onChange={(upc) => updateItem(i, 'UPC', upc)}
              />
              <input
                type="number" min="1" value={item.product_number}
                max={prod?.products_number || 9999}
                onChange={(e) => updateItem(i, 'product_number', e.target.value)}
                style={{ width: 80 }}
              />
              {prod && <span className="nowrap"><strong>{prod.product_name}</strong></span>}
              {item.UPC && !prod && <span className="nowrap" style={{ color: 'var(--danger)' }}>Товар не знайдено</span>}
              {prod && (
                prod.on_sale ? (
                  <span className="nowrap">
                    <span className="text-muted" style={{ textDecoration: 'line-through' }}>
                      {Number(prod.selling_price).toFixed(2)}
                    </span>{' '}
                    <strong>{unitPrice(prod).toFixed(2)} грн/шт.</strong>
                  </span>
                ) : (
                  <span className="text-muted nowrap">{Number(prod.selling_price).toFixed(2)} грн/шт.</span>
                )
              )}
              {prod?.on_sale && <span className="badge badge-green">Акція −20%</span>}
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
          <div className="text-muted" style={{ fontSize: '.9rem' }}>Проміжна сума: {subtotal.toFixed(2)} грн</div>
          {saleItems.length > 0 && (
            <div style={{ fontSize: '.85rem', color: 'var(--success)' }}>
              Акція за терміном придатності −20% застосована до товарів: {saleItems.map((p) => p.product_name).join(', ')}
            </div>
          )}
          {cardPercent > 0 ? (
            <div style={{ fontSize: '.9rem', color: 'var(--success)' }}>
              Знижка за карткою «{selectedCard?.name}»: −{discount.toFixed(2)} грн ({cardPercent}%)
            </div>
          ) : cardNumber ? (
            <div className="text-muted" style={{ fontSize: '.85rem' }}>Картка без знижки (0%)</div>
          ) : (
            <div className="text-muted" style={{ fontSize: '.85rem' }}>Без картки — знижка не застосовується</div>
          )}
          <div style={{ marginTop: '.35rem' }}>До сплати: <strong>{total.toFixed(2)} грн</strong></div>
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
