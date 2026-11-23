# ERP Yönetim Sistemi – Frontend

ERP uygulamasının React arayüzü: yönetici paneli ve müşteri portalı.

**Teknolojiler:** React 19, Vite, Tailwind CSS, React Router, Axios, Recharts

## Çalıştırma

```bash
npm install
npm run dev
```

Uygulama `http://localhost:5173` adresinde açılır. Backend'in çalışıyor olması gerekir.

Backend varsayılan olarak `http://127.0.0.1:8000` adresinde aranır. Farklı bir adres kullanılıyorsa bu klasörde bir `.env` dosyası oluşturun:

```env
VITE_API_URL=http://127.0.0.1:8000
```

## Komutlar

| Komut | Açıklama |
| --- | --- |
| `npm run dev` | Geliştirme sunucusunu başlatır |
| `npm run build` | Üretim derlemesi alır (`dist/`) |
| `npm run preview` | Derlemeyi yerelde önizler |
| `npm run lint` | Oxlint ile kod denetimi yapar |

Kurulumun tamamı, backend ayarları ve proje hakkında ayrıntılı bilgi için [ana README](../README.md) dosyasına bakın.
