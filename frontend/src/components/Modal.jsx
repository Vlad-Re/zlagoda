import { useEffect } from 'react';

export default function Modal({ title, onClose, onSubmit, children, wide, submitLabel = 'Зберегти', loading }) {
    useEffect(() => {
        document.body.style.overflow = 'hidden';
        
        return () => {
            document.body.style.overflow = '';
        };
    }, []);
  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`modal${wide ? ' modal-wide' : ''}`}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">{children}</div>
        {onSubmit && (
          <div className="modal-footer">
            <button className="btn btn-secondary" onClick={onClose} disabled={loading}>Скасувати</button>
            <button className="btn btn-primary" onClick={onSubmit} disabled={loading}>
              {loading ? 'Збереження...' : submitLabel}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
