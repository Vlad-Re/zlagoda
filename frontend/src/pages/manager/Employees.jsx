import { useState, useEffect } from 'react';
import { getEmployees, createEmployee, updateEmployee, deleteEmployee, searchEmployees } from '../../api/employees';
import Modal from '../../components/Modal';
import ConfirmDialog from '../../components/ConfirmDialog';

const EMPTY = {
  id_employee: '', empl_surname: '', empl_name: '', empl_patronymic: '',
  empl_role: 'Cashier', salary: '', date_of_birth: '', date_of_start: '',
  phone_number: '', city: '', street: '', zip_code: '', password: '',
};

export default function Employees() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sort, setSort] = useState('empl_surname');
  const [roleFilter, setRoleFilter] = useState('');
  const [modal, setModal] = useState(null);
  const [delTarget, setDelTarget] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [formError, setFormError] = useState('');
  const [searchSurname, setSearchSurname] = useState('');
  const [searchResults, setSearchResults] = useState(null);

  const load = () => {
    setLoading(true);
    const params = { sort };
    if (roleFilter) params.role = roleFilter;
    getEmployees(params)
      .then((r) => setRows(r.results))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [sort, roleFilter]);

  const openCreate = () => { setForm(EMPTY); setFormError(''); setModal({ mode: 'create' }); };
  const openEdit = (row) => { setForm({ ...row, password: '' }); setFormError(''); setModal({ mode: 'edit', id: row.id_employee }); };

  const validateAge = (dob) => {
    if (!dob) return false;
    const age = (new Date() - new Date(dob)) / (365.25 * 24 * 3600 * 1000);
    return age >= 18;
  };

  const handleSave = async () => {
    if (!form.id_employee || !form.empl_surname || !form.empl_name || !form.empl_role ||
        !form.salary || !form.date_of_birth || !form.date_of_start || !form.phone_number ||
        !form.city || !form.street || !form.zip_code) {
      setFormError("Заповніть усі обов'язкові поля");
      return;
    }
    if (!validateAge(form.date_of_birth)) {
      setFormError('Вік працівника повинен бути не менше 18 років');
      return;
    }
    if (!form.phone_number.startsWith('+') || form.phone_number.length > 13) {
      setFormError('Телефон повинен починатися з "+" і мати не більше 13 символів');
      return;
    }
    setSaving(true); setFormError('');
    try {
      const payload = { ...form };
      if (!payload.password) delete payload.password;
      if (modal.mode === 'create') {
        await createEmployee(payload);
      } else {
        await updateEmployee(modal.id, payload);
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
      await deleteEmployee(delTarget.id_employee);
      setDelTarget(null); load();
    } catch (e) {
      setError(e.message); setDelTarget(null);
    } finally { setSaving(false); }
  };

  const handleSearch = async () => {
    if (!searchSurname.trim()) { setSearchResults(null); return; }
    try {
      const r = await searchEmployees(searchSurname);
      setSearchResults(r.results);
    } catch (e) { setError(e.message); }
  };

  const f = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <div className="page">
      <div className="page-header">
        <h1>Працівники</h1>
        <button className="btn btn-primary" onClick={openCreate}>+ Додати</button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="filters">
        <div className="filter-group">
          <label>Роль</label>
          <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
            <option value="">Всі</option>
            <option value="Manager">Менеджер</option>
            <option value="Cashier">Касир</option>
          </select>
        </div>
        <div className="filter-group">
          <label>Сортування</label>
          <select value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="empl_surname">Прізвище</option>
            <option value="empl_role">Роль</option>
            <option value="salary">Зарплата</option>
            <option value="date_of_start">Дата прийому</option>
          </select>
        </div>
        <div className="filter-group">
          <label>Пошук за прізвищем (телефон+адреса)</label>
          <div className="flex gap-sm">
            <input type="text" value={searchSurname} onChange={(e) => setSearchSurname(e.target.value)}
              placeholder="Введіть прізвище" onKeyDown={(e) => e.key === 'Enter' && handleSearch()} />
            <button className="btn btn-ghost btn-sm" onClick={handleSearch}>Знайти</button>
            {searchResults && <button className="btn btn-secondary btn-sm" onClick={() => setSearchResults(null)}>✕</button>}
          </div>
        </div>
      </div>

      {searchResults && (
        <div style={{ marginBottom: '1rem' }}>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Прізвище</th><th>Ім'я</th><th>Телефон</th><th>Місто</th><th>Вулиця</th><th>Індекс</th></tr>
              </thead>
              <tbody>
                {searchResults.length === 0 && <tr><td colSpan={6} className="text-center">Нічого не знайдено</td></tr>}
                {searchResults.map((r, i) => (
                  <tr key={i}>
                    <td>{r.empl_surname}</td><td>{r.empl_name}</td>
                    <td>{r.phone_number}</td><td>{r.city}</td>
                    <td>{r.street}</td><td>{r.zip_code}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {loading ? <div className="loading">Завантаження...</div> : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th><th>Прізвище</th><th>Ім'я</th><th>Роль</th>
                <th>Зарплата</th><th>Телефон</th><th>Дата прийому</th><th></th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && <tr><td colSpan={8}><div className="empty-state"><p>Немає працівників</p></div></td></tr>}
              {rows.map((row) => (
                <tr key={row.id_employee}>
                  <td><span className="text-muted">{row.id_employee}</span></td>
                  <td>{row.empl_surname}</td>
                  <td>{row.empl_name} {row.empl_patronymic || ''}</td>
                  <td>
                    <span className={`badge ${row.empl_role === 'Manager' ? 'badge-purple' : 'badge-gray'}`}>
                      {row.empl_role === 'Manager' ? 'Менеджер' : 'Касир'}
                    </span>
                  </td>
                  <td className="nowrap">{Number(row.salary).toLocaleString('uk-UA')} грн</td>
                  <td>{row.phone_number}</td>
                  <td>{row.date_of_start}</td>
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
        <Modal title={modal.mode === 'create' ? 'Новий працівник' : 'Редагувати працівника'}
          onClose={() => setModal(null)} onSubmit={handleSave} loading={saving} wide>
          {formError && <div className="alert alert-error">{formError}</div>}
          <div className="form-row">
            <div className="form-group">
              <label>ID<span className="req"> *</span></label>
              <input type="text" value={form.id_employee} onChange={f('id_employee')} disabled={modal.mode === 'edit'} />
            </div>
            <div className="form-group">
              <label>Роль<span className="req"> *</span></label>
              <select value={form.empl_role} onChange={f('empl_role')}>
                <option value="Cashier">Касир</option>
                <option value="Manager">Менеджер</option>
              </select>
            </div>
          </div>
          <div className="form-row">
            <div className="form-group"><label>Прізвище<span className="req"> *</span></label><input type="text" value={form.empl_surname} onChange={f('empl_surname')} /></div>
            <div className="form-group"><label>Ім'я<span className="req"> *</span></label><input type="text" value={form.empl_name} onChange={f('empl_name')} /></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label>По батькові</label><input type="text" value={form.empl_patronymic} onChange={f('empl_patronymic')} /></div>
            <div className="form-group"><label>Зарплата<span className="req"> *</span></label><input type="number" min="0" value={form.salary} onChange={f('salary')} /></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label>Дата народження<span className="req"> *</span></label><input type="date" value={form.date_of_birth} onChange={f('date_of_birth')} /></div>
            <div className="form-group"><label>Дата прийому<span className="req"> *</span></label><input type="date" value={form.date_of_start} onChange={f('date_of_start')} /></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label>Телефон<span className="req"> *</span></label><input type="text" placeholder="+380XXXXXXXXX" value={form.phone_number} onChange={f('phone_number')} maxLength={13} /></div>
            <div className="form-group"><label>Місто<span className="req"> *</span></label><input type="text" value={form.city} onChange={f('city')} /></div>
          </div>
          <div className="form-row">
            <div className="form-group"><label>Вулиця<span className="req"> *</span></label><input type="text" value={form.street} onChange={f('street')} /></div>
            <div className="form-group"><label>Індекс<span className="req"> *</span></label><input type="text" value={form.zip_code} onChange={f('zip_code')} /></div>
          </div>
          <div className="form-group">
            <label>{modal.mode === 'create' ? 'Пароль (за замовчуванням = ID)' : 'Новий пароль (залиште порожнім, щоб не змінювати)'}</label>
            <input type="password" value={form.password} onChange={f('password')} autoComplete="new-password" />
          </div>
        </Modal>
      )}

      {delTarget && (
        <ConfirmDialog
          message={`Видалити працівника "${delTarget.empl_surname} ${delTarget.empl_name}"?`}
          onConfirm={handleDelete} onCancel={() => setDelTarget(null)} loading={saving}
        />
      )}
    </div>
  );
}
