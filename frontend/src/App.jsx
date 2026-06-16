import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';

// Manager pages
import Employees    from './pages/manager/Employees';
import Categories   from './pages/manager/Categories';
import Products     from './pages/manager/Products';
import StoreProducts from './pages/manager/StoreProducts';
import CustomerCardsManager from './pages/manager/CustomerCards';
import Checks       from './pages/manager/Checks';
import Reports      from './pages/manager/Reports';

// Cashier pages
import CashierProducts      from './pages/cashier/Products';
import CashierCustomerCards from './pages/cashier/CustomerCards';
import NewCheck     from './pages/cashier/NewCheck';
import MyChecks     from './pages/cashier/MyChecks';
import Profile      from './pages/cashier/Profile';

function ProtectedRoute({ children, requiredRole }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading">Завантаження...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (requiredRole && user.role !== requiredRole) return <Navigate to="/" replace />;
  return children;
}

function RootRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading">Завантаження...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === 'Manager') return <Navigate to="/manager/employees" replace />;
  return <Navigate to="/cashier/products" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<RootRedirect />} />

          {/* Manager routes */}
          <Route path="/manager" element={
            <ProtectedRoute requiredRole="Manager"><Layout /></ProtectedRoute>
          }>
            <Route path="employees"      element={<Employees />} />
            <Route path="categories"     element={<Categories />} />
            <Route path="products"       element={<Products />} />
            <Route path="store-products" element={<StoreProducts />} />
            <Route path="customer-cards" element={<CustomerCardsManager />} />
            <Route path="checks"         element={<Checks />} />
            <Route path="reports"        element={<Reports />} />
            <Route index element={<Navigate to="employees" replace />} />
          </Route>

          {/* Cashier routes (also accessible by Manager) */}
          <Route path="/cashier" element={
            <ProtectedRoute><Layout /></ProtectedRoute>
          }>
            <Route path="products"       element={<CashierProducts />} />
            <Route path="customer-cards" element={<CashierCustomerCards />} />
            <Route path="new-check"      element={<NewCheck />} />
            <Route path="my-checks"      element={<MyChecks />} />
            <Route path="profile"        element={<Profile />} />
            <Route index element={<Navigate to="products" replace />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
