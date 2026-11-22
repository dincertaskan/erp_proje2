import { useState } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import api, { clearSession, getErrorMessage } from '../api/axios';
import { getHomePath } from '../utils/routes';
import { LogIn } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionExpired = searchParams.get('oturum') === 'sona-erdi';

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const res = await api.post('/auth/login', { email, password });

      // Önceki oturumdan kalan bilgiler (ör. başka kullanıcının sepeti) temizlenir
      clearSession();

      // Token ve Kullanıcı Bilgilerini Kaydetme
      localStorage.setItem('token', res.data.access_token);
      
      if (res.data.full_name) {
        localStorage.setItem('user_name', res.data.full_name);
      }
      
      // Rol bilgisini kaydediyoruz ('admin' veya 'customer')
      const userRole = res.data.role || 'customer';
      localStorage.setItem('user_role', userRole);

      // Role göre dinamik yönlendirme
      navigate(getHomePath(userRole), { replace: true });

    } catch (err) {
      console.error("Giriş Hatası:", err.response);
      setError(getErrorMessage(err, 'E-posta veya şifre hatalı.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form onSubmit={handleLogin} className="bg-white p-8 rounded-xl shadow-md w-96 flex flex-col gap-4">
        <div className="flex items-center gap-2 justify-center text-indigo-600 font-bold text-2xl mb-2">
          <LogIn size={28} /> Giriş Yap
        </div>
        
        {sessionExpired && !error && (
          <div className="bg-amber-50 text-amber-700 p-2.5 rounded-lg text-sm text-center font-medium border border-amber-200">
            Oturumunuzun süresi doldu. Lütfen tekrar giriş yapın.
          </div>
        )}

        {error && (
          <div className="bg-red-100 text-red-600 p-2.5 rounded-lg text-sm text-center font-medium border border-red-200">
            {error}
          </div>
        )}

        <input 
          type="email" 
          placeholder="E-posta Adresi" 
          value={email} 
          onChange={(e) => setEmail(e.target.value)} 
          required 
          className="border p-2.5 rounded-lg focus:outline-indigo-500 text-sm" 
        />
        <input 
          type="password" 
          placeholder="Şifre" 
          value={password} 
          onChange={(e) => setPassword(e.target.value)} 
          required 
          className="border p-2.5 rounded-lg focus:outline-indigo-500 text-sm" 
        />
        <button 
          type="submit" 
          disabled={submitting}
          className="bg-indigo-600 text-white py-2.5 rounded-lg font-semibold hover:bg-indigo-700 transition shadow-sm cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {submitting ? 'Giriş Yapılıyor...' : 'Giriş Yap'}
        </button>
        <p className="text-xs text-center text-gray-500 mt-2">
          Hesabın yok mu? <Link to="/register" className="text-indigo-600 font-semibold hover:underline">Kayıt Ol</Link>
        </p>
      </form>
    </div>
  );
}