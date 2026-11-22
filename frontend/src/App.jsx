import { BrowserRouter as Router, Routes, Route, Outlet } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
import Products from './pages/Products';
import ProductDetail from './pages/ProductDetail';
import Profile from './pages/Profile';
import Notifications from './pages/Notifications';
import Layout from './component/Layout';
import ProtectedRoute, { HomeRedirect } from './component/ProtectedRoute';
import NotificationProvider from './context/NotificationProvider';
import Orders from './pages/Orders';
import CustomerDashboard from './pages/CustomerDashboard';
import Customers from './pages/Customers';
import CustomerProducts from './pages/CustomerProducts';
import Cart from './pages/Cart';
import CustomerOrders from './pages/CustomerOrders';
import Reports from './pages/Reports';
import Settings from './pages/Settings';

// Rol kontrollü, menülü sayfa iskeleti. allowedRole verilmezse giriş yapmış herkes erişebilir.
function ProtectedLayout({ allowedRole }) {
  return (
    <ProtectedRoute allowedRole={allowedRole}>
      <Layout>
        <Outlet />
      </Layout>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <Router>
      <NotificationProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* ADMIN ROTALARI */}
          <Route element={<ProtectedLayout allowedRole="admin" />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/products" element={<Products />} />
            <Route path="/products/:id" element={<ProductDetail />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/customers" element={<Customers />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<Settings />} />
          </Route>

          {/* MÜŞTERİ ROTALARI */}
          <Route element={<ProtectedLayout allowedRole="customer" />}>
            <Route path="/portal/anasayfa" element={<CustomerDashboard />} />
            <Route path="/portal/urunler" element={<CustomerProducts />} />
            <Route path="/portal/sepet" element={<Cart />} />
            <Route path="/portal/siparisler" element={<CustomerOrders />} />
          </Route>

          {/* ORTAK ROTALAR (giriş yapmış her kullanıcı) */}
          <Route element={<ProtectedLayout />}>
            <Route path="/profile" element={<Profile />} />
            <Route path="/notifications" element={<Notifications />} />
          </Route>

          {/* ROL BAZLI JOKER YÖNLENDİRME */}
          <Route path="*" element={<HomeRedirect />} />
        </Routes>
      </NotificationProvider>
    </Router>
  );
}
