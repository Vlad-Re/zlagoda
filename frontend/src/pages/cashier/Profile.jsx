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
        <div className="card profile-card">
          <div className="profile-details">
            {Object.entries(labels).map(([key, label]) => (
                user[key] !== undefined && user[key] !== null && user[key] !== '' ? (
                    <div className="profile-row" key={key}>
                      <span className="profile-label">{label}</span>
                      <span className="profile-value">
                  {key === 'salary'
                      ? `${Number(user[key]).toLocaleString('uk-UA')} грн`
                      : key === 'empl_role'
                          ? (user[key] === 'Manager' ? 'Менеджер' : 'Касир')
                          : String(user[key])}
                </span>
                    </div>
                ) : null
            ))}
          </div>
        </div>
      </div>
  );
}
