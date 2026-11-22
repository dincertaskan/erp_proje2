import { useEffect, useState } from 'react';
import { Building2, Store, KeyRound, Loader2, Save, CheckCircle2 } from 'lucide-react';
import api, { getErrorMessage } from '../api/axios';
import { validatePassword } from '../utils/validation';
import AdminManagement from '../component/AdminManagement';

const inputClass = 'w-full border border-gray-300 p-2.5 rounded-lg text-xs focus:outline-indigo-500';
const labelClass = 'block text-xs font-semibold text-gray-600 mb-1';

function Section({ icon: Icon, title, description, children }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-xs p-6 space-y-4 w-full">
      <div>
        <h2 className="text-sm font-bold text-gray-800 flex items-center gap-2">
          <Icon size={18} className="text-indigo-600" /> {title}
        </h2>
        {description && <p className="text-xs text-gray-500 mt-0.5">{description}</p>}
      </div>
      {children}
    </div>
  );
}

function Toggle({ checked, onChange, title, description }) {
  return (
    <label className="flex items-start justify-between gap-4 p-3 border border-gray-200 rounded-xl cursor-pointer hover:bg-gray-50/60 transition">
      <span>
        <span className="block text-xs font-semibold text-gray-800">{title}</span>
        <span className="block text-[11px] text-gray-500 mt-0.5">{description}</span>
      </span>
      <span className="relative shrink-0 mt-0.5">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          className="peer sr-only"
        />
        <span className="block w-10 h-6 rounded-full bg-gray-300 peer-checked:bg-indigo-600 peer-focus-visible:ring-2 peer-focus-visible:ring-indigo-300 transition" />
        <span className="absolute top-1 left-1 w-4 h-4 rounded-full bg-white shadow transition peer-checked:translate-x-4" />
      </span>
    </label>
  );
}

// Firma ve mağaza ayarları formu
function StoreSettingsForm() {
  const [form, setForm] = useState(null);
  const [loadError, setLoadError] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    api.get('/settings')
      .then((res) => setForm(res.data))
      .catch((err) => setLoadError(getErrorMessage(err, 'Ayarlar yüklenemedi.')));
  }, []);

  const update = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setMessage({ type: '', text: '' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage({ type: '', text: '' });
    try {
      const minStock = parseInt(form.default_min_stock, 10);
      const res = await api.put('/settings', {
        ...form,
        default_min_stock: Number.isNaN(minStock) ? 0 : minStock,
      });
      setForm(res.data);
      setMessage({ type: 'success', text: 'Ayarlar kaydedildi.' });
    } catch (err) {
      setMessage({ type: 'error', text: getErrorMessage(err, 'Ayarlar kaydedilemedi.') });
    } finally {
      setSaving(false);
    }
  };

  if (loadError) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-xl text-center text-xs font-medium">
        {loadError}
      </div>
    );
  }

  if (!form) {
    return (
      <div className="flex justify-center py-12 text-indigo-600">
        <Loader2 size={28} className="animate-spin" />
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Section
        icon={Building2}
        title="Firma Bilgileri"
        description="Sipariş faturalarının başlığında bu bilgiler kullanılır."
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="md:col-span-2">
            <label className={labelClass}>Firma Adı</label>
            <input type="text" required value={form.company_name} onChange={(e) => update('company_name', e.target.value)} className={inputClass} />
          </div>
          <div className="md:col-span-2">
            <label className={labelClass}>Adres</label>
            <textarea rows={2} value={form.company_address} onChange={(e) => update('company_address', e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Telefon</label>
            <input type="tel" value={form.company_phone} onChange={(e) => update('company_phone', e.target.value)} placeholder="0 (212) 000 00 00" className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>E-posta</label>
            <input type="email" value={form.company_email} onChange={(e) => update('company_email', e.target.value)} placeholder="info@firma.com" className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Vergi Dairesi</label>
            <input type="text" value={form.tax_office} onChange={(e) => update('tax_office', e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Vergi Numarası</label>
            <input type="text" inputMode="numeric" value={form.tax_number} onChange={(e) => update('tax_number', e.target.value)} className={inputClass} />
          </div>
        </div>
      </Section>

      <Section icon={Store} title="Mağaza Ayarları" description="Müşteri portalının davranışını belirler.">
        <div className="space-y-3">
          <Toggle
            checked={form.allow_registration}
            onChange={(v) => update('allow_registration', v)}
            title="Yeni müşteri kaydı açık"
            description="Kapalıyken kayıt sayfasından yeni müşteri hesabı oluşturulamaz. Mevcut müşteriler giriş yapmaya devam eder."
          />
          <Toggle
            checked={form.accept_orders}
            onChange={(v) => update('accept_orders', v)}
            title="Müşteri siparişleri açık"
            description="Kapalıyken müşteriler katalogda gezinebilir ama sipariş veremez (ör. sayım veya bakım sırasında)."
          />
          <div className="max-w-xs">
            <label className={labelClass}>Varsayılan Kritik Stok Sınırı</label>
            <input
              type="number"
              min="0"
              required
              value={form.default_min_stock}
              onChange={(e) => update('default_min_stock', e.target.value)}
              className={inputClass}
            />
            <p className="text-[11px] text-gray-400 mt-1">Yeni ürün eklerken forma otomatik gelir.</p>
          </div>
        </div>
      </Section>

      <div className="flex items-center justify-end gap-3">
        {message.text && (
          <span className={`text-xs font-medium flex items-center gap-1 ${message.type === 'success' ? 'text-emerald-600' : 'text-red-600'}`}>
            {message.type === 'success' && <CheckCircle2 size={14} />}
            {message.text}
          </span>
        )}
        <button
          type="submit"
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold transition cursor-pointer disabled:opacity-60"
        >
          {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
          {saving ? 'Kaydediliyor...' : 'Ayarları Kaydet'}
        </button>
      </div>
    </form>
  );
}

// Oturum sahibinin şifre değiştirme formu
function PasswordForm() {
  const empty = { current: '', next: '', confirm: '' };
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage({ type: '', text: '' });

    const passwordError = validatePassword(form.next);
    if (passwordError) {
      setMessage({ type: 'error', text: passwordError });
      return;
    }
    if (form.next !== form.confirm) {
      setMessage({ type: 'error', text: 'Yeni şifreler birbiriyle eşleşmiyor.' });
      return;
    }

    setSaving(true);
    try {
      await api.post('/auth/change-password', { current_password: form.current, new_password: form.next });
      setForm(empty);
      setMessage({ type: 'success', text: 'Şifreniz değiştirildi.' });
    } catch (err) {
      setMessage({ type: 'error', text: getErrorMessage(err, 'Şifre değiştirilemedi.') });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Section icon={KeyRound} title="Şifre Değiştir" description="Hesabınızın giriş şifresini güncelleyin.">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className={labelClass}>Mevcut Şifre</label>
            <input type="password" required autoComplete="current-password" value={form.current} onChange={(e) => setForm({ ...form, current: e.target.value })} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Yeni Şifre</label>
            <input type="password" required autoComplete="new-password" value={form.next} onChange={(e) => setForm({ ...form, next: e.target.value })} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Yeni Şifre Tekrarı</label>
            <input type="password" required autoComplete="new-password" value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} className={inputClass} />
          </div>
        </div>
        <p className="text-[11px] text-gray-400">En az 8 karakter; büyük harf, küçük harf, rakam ve özel karakter içermelidir.</p>
        <div className="flex items-center justify-end gap-3">
          {message.text && (
            <span className={`text-xs font-medium flex items-center gap-1 ${message.type === 'success' ? 'text-emerald-600' : 'text-red-600'}`}>
              {message.type === 'success' && <CheckCircle2 size={14} />}
              {message.text}
            </span>
          )}
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold transition cursor-pointer disabled:opacity-60"
          >
            {saving && <Loader2 size={14} className="animate-spin" />}
            Şifreyi Güncelle
          </button>
        </div>
      </form>
    </Section>
  );
}

export default function Settings() {
  return (
    <div className="space-y-6 pb-8 w-full">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Ayarlar</h1>
      </div>

      <StoreSettingsForm />
      <PasswordForm />
      <AdminManagement />
    </div>
  );
}
