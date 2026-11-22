import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api, { getErrorMessage } from '../api/axios';
import { validatePassword } from '../utils/validation';
import { UserPlus } from 'lucide-react';

export default function Register() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [registrationOpen, setRegistrationOpen] = useState(true);
  const navigate = useNavigate();

  // Yönetici Ayarlar sayfasından yeni kayıtları kapatmış olabilir
  useEffect(() => {
    api.get('/settings/public')
      .then((res) => setRegistrationOpen(res.data.allow_registration))
      .catch(() => {});
  }, []);

  const validateEmail = (emailStr) => {
    // İzin verilen e-posta uzantıları
    const allowedDomains = [
      'gmail.com', 
      'hotmail.com', 
      'outlook.com', 
      'yahoo.com', 
      'yandex.com',
      'icloud.com'
    ];

    // Genel e-posta formatı kontrolü
    const basicEmailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!basicEmailRegex.test(emailStr)) {
      return "Lütfen geçerli bir e-posta adresi giriniz.";
    }

    // E-posta uzantısını (domain) ayıklama
    const domain = emailStr.split('@')[1]?.toLowerCase();

    // Uzantı kontrolü
    if (!allowedDomains.includes(domain)) {
      return `Lütfen geçerli bir e-posta adresi giriniz.`;
    }

    return null;
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');

    const emailError = validateEmail(email);
    if (emailError) {
      setError(emailError);
      return;
    }

    const passwordError = validatePassword(password);
    if (passwordError) {
      setError(passwordError);
      return;
    }

    if (password !== confirmPassword) {
      setError("Girdiğiniz şifreler birbiriyle eşleşmiyor!");
      return;
    }
    
    try {
      await api.post('/auth/register', {
        full_name: fullName,
        email,
        password
        // Kayıt sayfasından yalnızca müşteri hesabı açılır; yöneticileri mevcut bir yönetici ekler
      });

      alert('Kayıt başarılı! Lütfen giriş yapınız.');
      navigate('/login');
    } catch (err) {
      console.error("Kayıt Detaylı Hata Yanıtı:", err.response);
      setError(getErrorMessage(err, 'Form verileri geçersiz.'));
    }
  };

  if (!registrationOpen) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
        <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md flex flex-col gap-4 text-center">
          <div className="flex items-center gap-2 justify-center text-indigo-600 font-bold text-2xl">
            <UserPlus size={28} /> Kayıt Ol
          </div>
          <div className="bg-amber-50 text-amber-700 p-3 rounded-lg text-sm font-medium border border-amber-200">
            Yeni müşteri kaydı şu anda kapalı. Lütfen daha sonra tekrar deneyin.
          </div>
          <p className="text-xs text-gray-500">
            Zaten hesabın var mı? <Link to="/login" className="text-indigo-600 font-semibold hover:underline">Giriş Yap</Link>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
      <form onSubmit={handleRegister} className="bg-white p-8 rounded-xl shadow-md w-full max-w-md flex flex-col gap-4">
        <div className="flex items-center gap-2 justify-center text-indigo-600 font-bold text-2xl mb-2">
          <UserPlus size={28} /> Kayıt Ol
        </div>

        {error && (
          <div className="bg-red-100 text-red-600 p-2.5 rounded-lg text-sm text-center font-medium border border-red-200 break-words">
            {error}
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Ad Soyad</label>
          <input 
            type="text" 
            placeholder="Örn: Ahmet Yılmaz" 
            value={fullName} 
            onChange={(e) => setFullName(e.target.value)} 
            required 
            className="w-full border p-2.5 rounded-lg focus:outline-indigo-500 text-sm" 
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">E-posta Adresi</label>
          <input 
            type="email" 
            placeholder="ornek@gmail.com" 
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
            required 
            className="w-full border p-2.5 rounded-lg focus:outline-indigo-500 text-sm" 
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Şifre</label>
          <input 
            type="password" 
            placeholder="••••••••" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            required 
            className="w-full border p-2.5 rounded-lg focus:outline-indigo-500 text-sm" 
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Şifre Tekrarı</label>
          <input 
            type="password" 
            placeholder="Şifrenizi tekrar giriniz" 
            value={confirmPassword} 
            onChange={(e) => setConfirmPassword(e.target.value)} 
            required 
            className="w-full border p-2.5 rounded-lg focus:outline-indigo-500 text-sm" 
          />
        </div>

        <button 
          type="submit" 
          className="bg-indigo-600 text-white py-2.5 rounded-lg font-semibold hover:bg-indigo-700 transition shadow-sm cursor-pointer mt-2"
        >
          Hesap Oluştur
        </button>

        <p className="text-xs text-center text-gray-500 mt-2">
          Zaten hesabın var mı? <Link to="/login" className="text-indigo-600 font-semibold hover:underline">Giriş Yap</Link>
        </p>
      </form>
    </div>
  );
}