import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function NavSection({ label, links }) {
  return (
    <div className="sidebar-section">
      <div className="sidebar-section-label">{label}</div>
      {links.map(({ to, label }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) => 'sidebar-link' + (isActive ? ' active' : '')}
        >
          {label}
        </NavLink>
      ))}
    </div>
  );
}

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const managerLinks = [
    { to: '/manager/employees',       label: 'Працівники' },
    { to: '/manager/categories',      label: 'Категорії' },
    { to: '/manager/products',        label: 'Товари' },
    { to: '/manager/store-products',  label: 'Товари в магазині' },
    { to: '/manager/customer-cards',  label: 'Картки клієнтів' },
    { to: '/manager/checks',          label: 'Чеки' },
    { to: '/manager/reports',         label: 'Звіти' },
  ];

  const cashierLinks = [
    { to: '/cashier/products',        label: 'Товари' },
    { to: '/cashier/customer-cards',  label: 'Картки клієнтів' },
    { to: '/cashier/new-check',       label: 'Новий чек' },
    { to: '/cashier/my-checks',       label: 'Мої чеки' },
    { to: '/cashier/profile',         label: 'Мій профіль' },
  ];

  return (
    <div className="app-layout">
      <nav className="sidebar">
        <div className="sidebar-brand">
          Злагода
          <span>{user?.role === 'Manager' ? 'Менеджер' : 'Касир'}</span>
        </div>

        {user?.role === 'Manager' && (
          <NavSection label="Менеджер" links={managerLinks} />
        )}
        {user?.role === 'Cashier' && (
          <NavSection label="Касир" links={cashierLinks} />
        )}
        {user?.role === 'Manager' && (
          <NavSection label="Каса" links={cashierLinks} />
        )}

        <div className="sidebar-footer">
          <strong>{user?.name}</strong>
          <button
            className="btn btn-ghost btn-sm"
            style={{ width: '100%', justifyContent: 'center', marginTop: '.5rem' }}
            onClick={handleLogout}
          >
            Вийти
          </button>
        </div>
      </nav>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
