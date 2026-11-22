import axios from 'axios';

// Backend adresi tek yerden yönetilir.
// Farklı bir adres gerekiyorsa frontend/.env dosyasına VITE_API_URL=... yazmak yeterli.
export const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');

// Oturumla birlikte tutulan localStorage anahtarları
const SESSION_KEYS = ['token', 'user_name', 'user_role', 'cart_items'];

export const clearSession = () => {
  SESSION_KEYS.forEach((key) => localStorage.removeItem(key));
};

// Backend'den dönen hata mesajını (string veya doğrulama listesi) okunabilir metne çevirir
export const getErrorMessage = (err, fallback = 'Bir hata oluştu.') => {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail[0]?.msg || fallback;
  if (!err?.response) return 'Sunucuya ulaşılamadı. Lütfen bağlantınızı kontrol edin.';
  return fallback;
};

// Görsel adresi tam URL ise olduğu gibi, backend'e ait göreli yol ise API adresiyle birlikte döner
export const getImageUrl = (url) => {
  if (!url) return null;
  if (/^(https?:|data:|blob:)/i.test(url)) return url;
  const cleanPath = url.startsWith('/') ? url : `/${url}`;
  return `${API_URL}${cleanPath}`;
};

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Her isteğe oturum token'ı eklenir
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Token geçersizse veya süresi dolduysa oturum kapatılıp giriş sayfasına dönülür
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAuthRequest = error.config?.url?.startsWith('/auth/login') || error.config?.url?.startsWith('/auth/register');
    if (error.response?.status === 401 && !isAuthRequest && localStorage.getItem('token')) {
      clearSession();
      window.location.replace('/login?oturum=sona-erdi');
    }
    return Promise.reject(error);
  }
);

export default api;
