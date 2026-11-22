import { useEffect, useState } from 'react';
import { ShieldCheck, UserPlus, Loader2, X } from 'lucide-react';
import api, { getErrorMessage, getImageUrl } from '../api/axios';
import { validatePassword } from '../utils/validation';

const EMPTY_FORM = { full_name: '', email: '', password: '', confirmPassword: '' };

// Yönetici hesaplarını listeler ve yeni yönetici eklenmesini sağlar.
// Kayıt sayfası yalnızca müşteri hesabı açtığı için yeni yöneticiler buradan eklenir.
export default function AdminManagement() {
  const [admins, setAdmins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const fetchAdmins = async () => {
    try {
      const res = await api.get('/auth/admins');
      setAdmins(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error('Yönetici listesi alınamadı:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdmins();
  }, []);

  const closeForm = () => {
    setShowForm(false);
    setForm(EMPTY_FORM);
    setFormError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setSuccessMsg('');

    const passwordError = validatePassword(form.password);
    if (passwordError) {
      setFormError(passwordError);
      return;
    }
    if (form.password !== form.confirmPassword) {
      setFormError('Girdiğiniz şifreler birbiriyle eşleşmiyor!');
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.post('/auth/admins', {
        full_name: form.full_name,
        email: form.email,
        password: form.password,
      });
      setAdmins((prev) => [...prev, res.data]);
      setSuccessMsg(`${res.data.full_name} yönetici olarak eklendi. Bu bilgilerle giriş yapabilir.`);
      closeForm();
    } catch (err) {
      setFormError(getErrorMessage(err, 'Yönetici eklenemedi.'));
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass = 'w-full border border-gray-300 p-2.5 rounded-lg text-xs focus:outline-indigo-500';

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-xs p-6 space-y-4 w-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-bold text-gray-800 flex items-center gap-2">
            <ShieldCheck size={18} className="text-indigo-600" /> Yönetici Hesapları
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Kayıt sayfası yalnızca müşteri hesabı açar. Yeni yöneticileri buradan ekleyebilirsiniz.
          </p>
        </div>
        {!showForm && (
          <button
            onClick={() => { setShowForm(true); setSuccessMsg(''); }}
            className="self-start sm:self-auto flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 text-white px-3.5 py-2 rounded-lg text-xs font-semibold transition cursor-pointer"
          >
            <UserPlus size={15} /> Yeni Yönetici Ekle
          </button>
        )}
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl text-xs font-medium">
          {successMsg}
        </div>
      )}

      {showForm && (
        <form onSubmit={handleSubmit} className="p-4 bg-gray-50/70 border border-gray-200 rounded-xl space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-xs font-bold text-gray-700">Yeni Yönetici Bilgileri</span>
            <button type="button" onClick={closeForm} className="text-gray-400 hover:text-gray-600 p-1 rounded-lg cursor-pointer">
              <X size={16} />
            </button>
          </div>

          {formError && (
            <div className="bg-red-50 text-red-600 p-2.5 rounded-lg text-xs text-center font-medium border border-red-200">
              {formError}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Ad Soyad</label>
              <input
                type="text"
                required
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                placeholder="Örn: Ahmet Yılmaz"
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">E-posta Adresi</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="ornek@sirket.com"
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Geçici Şifre</label>
              <input
                type="password"
                required
                autoComplete="new-password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="••••••••"
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Şifre Tekrarı</label>
              <input
                type="password"
                required
                autoComplete="new-password"
                value={form.confirmPassword}
                onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
                placeholder="Şifreyi tekrar giriniz"
                className={inputClass}
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={closeForm}
              className="px-4 py-2 border border-gray-300 bg-white rounded-lg text-xs font-semibold text-gray-600 hover:bg-gray-50 cursor-pointer"
            >
              İptal
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold transition cursor-pointer flex items-center gap-2 disabled:opacity-60"
            >
              {submitting && <Loader2 size={14} className="animate-spin" />}
              {submitting ? 'Ekleniyor...' : 'Yöneticiyi Ekle'}
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="flex justify-center py-6 text-indigo-600">
          <Loader2 size={24} className="animate-spin" />
        </div>
      ) : (
        <ul className="divide-y divide-gray-100 border border-gray-100 rounded-xl">
          {admins.map((a) => (
            <li key={a.id} className="p-3 flex items-center gap-3 text-xs">
              {a.avatar_url ? (
                <img src={getImageUrl(a.avatar_url)} alt={a.full_name} className="w-8 h-8 rounded-full object-cover border border-gray-200 shrink-0" />
              ) : (
                <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold shrink-0">
                  {a.full_name?.charAt(0).toUpperCase()}
                </div>
              )}
              <div className="min-w-0 flex-1">
                <p className="font-bold text-gray-800 truncate">{a.full_name}</p>
                <p className="text-gray-500 truncate">{a.email}</p>
              </div>
              <span className="text-[10px] text-gray-400 shrink-0">
                {a.created_at ? new Date(a.created_at).toLocaleDateString('tr-TR') : ''}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
