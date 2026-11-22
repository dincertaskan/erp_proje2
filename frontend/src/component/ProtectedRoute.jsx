import { Navigate } from 'react-router-dom';
import { getHomePath } from '../utils/routes';

// Oturum yoksa giriş sayfasına, rol uyuşmuyorsa kullanıcının kendi ana sayfasına yönlendirir.
// allowedRole verilmezse giriş yapmış her kullanıcı erişebilir.
export default function ProtectedRoute({ children, allowedRole }) {
  const token = localStorage.getItem('token');
  const userRole = localStorage.getItem('user_role') || 'customer';

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRole && userRole !== allowedRole) {
    return <Navigate to={getHomePath(userRole)} replace />;
  }

  return children;
}

// Bilinmeyen adresleri oturum durumuna göre doğru sayfaya yönlendirir.
// Rol, App ilk açıldığında değil yönlendirme anında okunur (giriş/çıkış sonrası da doğru çalışır).
export function HomeRedirect() {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/login" replace />;
  return <Navigate to={getHomePath(localStorage.getItem('user_role'))} replace />;
}
