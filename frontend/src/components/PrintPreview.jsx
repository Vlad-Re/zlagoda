import Modal from './Modal';

export default function PrintPreview({ title, subtitle, children, onClose }) {
  const handlePrint = () => window.print();

  return (
    <Modal title={title} onClose={onClose} wide>
      <div className="no-print" style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <button className="btn btn-primary" onClick={handlePrint}>🖨 Друкувати</button>
      </div>
      <div className="print-area">
        <div className="print-header">
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {children}
        <div className="print-footer">
          Сформовано: {new Date().toLocaleString('uk-UA')}
        </div>
      </div>
    </Modal>
  );
}
