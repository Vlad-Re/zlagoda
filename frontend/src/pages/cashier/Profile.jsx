import { useAuth } from '../../context/AuthContext';

const labels = {
  id_employee: 'ID',
  empl_surname: 'Прізвище',
  empl_name: "Ім'я",
  empl_patronymic: 'По батькові',
  empl_role: 'Роль',
  salary: 'Зарплата',
  date_of_birth: 'Дата народження',
  date_of_start: 'Дата прийому',
  phone_number: 'Телефон',
  city: 'Місто',
  street: 'Вулиця',
  zip_code: 'Поштовий індекс',
};

export default function Profile() {
  const { user } = useAuth();

  if (!user) return <div className="loading">Завантаження...</div>;

  return (
    <div className="page">
      <div className="page-header"><h1>Мій профіль</h1></div>
      <div className="card" style={{ maxWidth: 500 }}>
        <table>
          <tbody>
            {Object.entries(labels).map(([key, label]) => (
              user[key] !== undefined && user[key] !== null ? (
                <tr key={key}>
                  <td style={{ fontWeight: 600, width: '45%', paddingLeft: 0 }}>{label}</td>
                  <td style={{ paddingLeft: '1rem' }}>
                    {key === 'salary'
                      ? `${Number(user[key]).toLocaleString('uk-UA')} грн`
                      : key === 'empl_role'
                      ? (user[key] === 'Manager' ? 'Менеджер' : 'Касир')
                      : String(user[key])}
                  </td>
                </tr>
              ) : null
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
