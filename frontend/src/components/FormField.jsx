export default function FormField({ label, required, error, children }) {
  return (
    <div className="form-group">
      <label>
        {label}{required && <span className="req"> *</span>}
      </label>
      {children}
      {error && <div className="form-error">{error}</div>}
    </div>
  );
}
