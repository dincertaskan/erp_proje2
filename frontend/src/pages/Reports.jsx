import { useEffect, useState } from 'react';
import {
  TrendingUp, TrendingDown, ShoppingBag, Wallet, PiggyBank, XCircle,
  Download, Loader2, Calendar, Package, Boxes, AlertTriangle
} from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LabelList
} from 'recharts';
import api, { getErrorMessage } from '../api/axios';

// ---------- Biçimlendirme yardımcıları ----------
const formatTL = (value) =>
  `$${Number(value || 0).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const formatCompactTL = (value) => {
  const v = Number(value || 0);
  if (Math.abs(v) >= 1_000_000) return `$${(v / 1_000_000).toLocaleString('tr-TR', { maximumFractionDigits: 1 })} Mn`;
  if (Math.abs(v) >= 1_000) return `$${(v / 1_000).toLocaleString('tr-TR', { maximumFractionDigits: 1 })} bin`;
  return `$${v.toLocaleString('tr-TR', { maximumFractionDigits: 0 })}`;
};

const formatNumber = (value) => Number(value || 0).toLocaleString('tr-TR');

const formatDate = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString('tr-TR');

// Tarihi yerel saate göre YYYY-AA-GG biçimine çevirir (toISOString UTC kayması yapmasın diye)
const toInputDate = (d) => {
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
};

const addDays = (d, days) => {
  const copy = new Date(d);
  copy.setDate(copy.getDate() + days);
  return copy;
};

const PRESETS = [
  { key: '7d', label: 'Son 7 Gün', range: (t) => [addDays(t, -6), t] },
  { key: '30d', label: 'Son 30 Gün', range: (t) => [addDays(t, -29), t] },
  { key: 'month', label: 'Bu Ay', range: (t) => [new Date(t.getFullYear(), t.getMonth(), 1), t] },
  { key: '12m', label: 'Son 12 Ay', range: (t) => [new Date(t.getFullYear() - 1, t.getMonth() + 1, 1), t] },
  { key: 'year', label: 'Bu Yıl', range: (t) => [new Date(t.getFullYear(), 0, 1), t] },
];

const presetRange = (key) => {
  const preset = PRESETS.find((p) => p.key === key);
  const [start, end] = preset.range(new Date());
  return { start: toInputDate(start), end: toInputDate(end) };
};

// Sipariş durumları: uygulamanın diğer sayfalarındaki rozet renkleriyle aynı
const STATUS_STYLES = {
  'Onay Bekliyor': { dot: 'bg-amber-500', bar: 'bg-amber-400' },
  'Hazırlanıyor': { dot: 'bg-blue-500', bar: 'bg-blue-400' },
  'Kargolandı': { dot: 'bg-purple-500', bar: 'bg-purple-400' },
  'Tamamlandı': { dot: 'bg-emerald-500', bar: 'bg-emerald-400' },
  'İptal': { dot: 'bg-red-500', bar: 'bg-red-400' },
};

const CHART_COLOR = '#6366f1';
const AXIS_TICK = { fontSize: 11, fill: '#94a3b8' };
const TOOLTIP_STYLE = { backgroundColor: '#ffffff', borderRadius: '12px', borderColor: '#e2e8f0', fontSize: '12px' };

// ---------- CSV (Excel'de Türkçe karakterlerle düzgün açılır) ----------
const csvCell = (value) => {
  let text;
  if (typeof value === 'number') {
    text = value.toLocaleString('tr-TR', { useGrouping: false, maximumFractionDigits: 2 });
  } else {
    text = String(value ?? '');
  }
  return /[;"\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
};

const buildCsv = (report) => {
  const rows = [];
  const section = (title, header, data) => {
    rows.push([title], header, ...data, []);
  };
  const s = report.summary;
  section(`Satış Raporu (${formatDate(report.period.start)} - ${formatDate(report.period.end)})`, ['Gösterge', 'Değer'], [
    ['Ciro ($)', s.revenue],
    ['Sipariş Sayısı', s.order_count],
    ['Ortalama Sepet ($)', s.avg_order_value],
    ['Satılan Ürün Adedi', s.items_sold],
    ['Maliyet ($)', s.cost],
    ['Brüt Kâr ($)', s.gross_profit],
    ['Kâr Marjı (%)', s.profit_margin],
    ['İptal Edilen Sipariş', s.cancelled_count],
    ['İptal Oranı (%)', s.cancel_rate],
  ]);
  section('Ciro Trendi', ['Dönem', 'Ciro ($)', 'Sipariş'], report.timeseries.map((t) => [t.label, t.revenue, t.orders]));
  section('En Çok Satan Ürünler', ['Ürün', 'Kategori', 'Adet', 'Ciro ($)', 'Kâr ($)', 'Kâr Marjı (%)'],
    report.top_products.map((p) => [p.name, p.category, p.quantity, p.revenue, p.profit, p.profit_margin]));
  section('Kategori Satışları', ['Kategori', 'Adet', 'Ciro ($)'],
    report.category_sales.map((c) => [c.name, c.quantity, c.revenue]));
  section('En İyi Müşteriler', ['Müşteri', 'Sipariş', 'Ciro ($)'],
    report.top_customers.map((c) => [c.name, c.order_count, c.revenue]));
  section('Ödeme Yöntemleri', ['Yöntem', 'Sipariş', 'Ciro ($)'],
    report.payment_methods.map((p) => [p.method, p.order_count, p.revenue]));
  section('Sipariş Durumları', ['Durum', 'Sipariş', 'Tutar ($)'],
    report.status_breakdown.map((x) => [x.status, x.count, x.amount]));
  section('Stok Değeri (güncel)', ['Kategori', 'Ürün', 'Stok', 'Maliyet Değeri ($)', 'Satış Değeri ($)', 'Potansiyel Kâr ($)'],
    report.inventory.categories.map((c) => [c.name, c.product_count, c.stock, c.cost_value, c.sale_value, c.potential_profit]));

  return '﻿' + rows.map((r) => r.map(csvCell).join(';')).join('\r\n');
};

const downloadCsv = (report) => {
  const blob = new Blob([buildCsv(report)], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `satis-raporu_${report.period.start}_${report.period.end}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};

// ---------- Küçük bileşenler ----------
function ChangeBadge({ value, invert = false }) {
  if (value === null || value === undefined) {
    return <span className="text-[11px] text-gray-400">Önceki dönemde veri yok</span>;
  }
  const positive = invert ? value < 0 : value > 0;
  const neutral = value === 0;
  const Icon = value >= 0 ? TrendingUp : TrendingDown;
  const color = neutral ? 'text-gray-500' : positive ? 'text-emerald-600' : 'text-red-600';
  return (
    <span className="text-[11px] block">
      <span className={`font-semibold inline-flex items-center gap-1 whitespace-nowrap ${color}`}>
        <Icon size={13} />
        {value > 0 ? '+' : value < 0 ? '−' : ''}%{Math.abs(value).toLocaleString('tr-TR')}
      </span>
      <span className="text-gray-400"> önceki döneme göre</span>
    </span>
  );
}

function KpiCard({ label, value, icon: Icon, iconClass, children }) {
  return (
    <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-xs flex items-start justify-between gap-3">
      <div className="min-w-0">
        <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block">{label}</span>
        <p className="text-xl font-extrabold text-gray-800 mt-1 truncate">{value}</p>
        <div className="mt-1">{children}</div>
      </div>
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${iconClass}`}>
        <Icon size={20} />
      </div>
    </div>
  );
}

function Card({ title, subtitle, children, className = '' }) {
  return (
    <div className={`bg-white p-6 rounded-xl border border-gray-200 shadow-xs space-y-4 ${className}`}>
      <div>
        <h2 className="text-base font-bold text-gray-800">{title}</h2>
        {subtitle && <p className="text-xs text-gray-400">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

function EmptyNote({ children = 'Bu tarih aralığında veri yok.' }) {
  return <div className="py-10 text-center text-xs text-gray-400">{children}</div>;
}

// ---------- Sayfa ----------
export default function Reports() {
  const [preset, setPreset] = useState('30d');
  const [range, setRange] = useState(() => presetRange('30d'));
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    api.get('/reports/sales', { params: { start: range.start, end: range.end } })
      .then((res) => { if (!cancelled) setReport(res.data); })
      .catch((err) => { if (!cancelled) setError(getErrorMessage(err, 'Rapor yüklenemedi.')); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [range.start, range.end]);

  const selectPreset = (key) => {
    setPreset(key);
    setRange(presetRange(key));
  };

  const changeDate = (field, value) => {
    if (!value) return;
    setPreset('custom');
    setRange((prev) => ({ ...prev, [field]: value }));
  };

  const s = report?.summary;
  const hasOrders = (s?.total_order_count || 0) > 0;
  const maxProductRevenue = Math.max(1, ...(report?.top_products || []).map((p) => p.revenue));
  const totalStatusCount = Math.max(1, (report?.status_breakdown || []).reduce((acc, x) => acc + x.count, 0));

  return (
    <div className="space-y-6 pb-8">
      {/* BAŞLIK VE FİLTRELER */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Raporlar</h1>
          {report && (
            <p className="text-xs text-gray-500 mt-0.5">
              {formatDate(report.period.start)} – {formatDate(report.period.end)} · {report.period.days} gün
              {' · '}karşılaştırma: {formatDate(report.period.previous_start)} – {formatDate(report.period.previous_end)}
            </p>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex bg-white border border-gray-200 rounded-lg p-0.5 shadow-xs">
            {PRESETS.map((p) => (
              <button
                key={p.key}
                onClick={() => selectPreset(p.key)}
                className={`px-2.5 py-1.5 rounded-md text-xs font-semibold transition cursor-pointer ${
                  preset === p.key ? 'bg-indigo-600 text-white' : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-1.5 bg-white border border-gray-200 rounded-lg px-2.5 py-1.5 shadow-xs text-xs">
            <Calendar size={14} className="text-gray-400" />
            <input
              type="date"
              value={range.start}
              max={range.end}
              onChange={(e) => changeDate('start', e.target.value)}
              className="bg-transparent text-gray-700 focus:outline-none"
              aria-label="Başlangıç tarihi"
            />
            <span className="text-gray-400">–</span>
            <input
              type="date"
              value={range.end}
              min={range.start}
              onChange={(e) => changeDate('end', e.target.value)}
              className="bg-transparent text-gray-700 focus:outline-none"
              aria-label="Bitiş tarihi"
            />
          </div>

          <button
            onClick={() => report && downloadCsv(report)}
            disabled={!report || loading}
            className="flex items-center gap-1.5 px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download size={14} /> CSV İndir
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-xl text-center text-sm font-medium">
          {error}
        </div>
      )}

      {!report && loading && (
        <div className="flex flex-col items-center justify-center h-96 gap-3 text-indigo-600">
          <Loader2 size={40} className="animate-spin" />
          <p className="text-sm font-semibold text-gray-500">Rapor hazırlanıyor...</p>
        </div>
      )}

      {report && (
        <div className={`space-y-6 transition-opacity ${loading ? 'opacity-50 pointer-events-none' : ''}`}>
          {/* KPI KARTLARI */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
            <KpiCard label="Ciro" value={formatTL(s.revenue)} icon={Wallet} iconClass="bg-emerald-50 text-emerald-600">
              <ChangeBadge value={report.changes.revenue} />
            </KpiCard>
            <KpiCard label="Sipariş" value={`${formatNumber(s.order_count)} Adet`} icon={ShoppingBag} iconClass="bg-indigo-50 text-indigo-600">
              <ChangeBadge value={report.changes.order_count} />
            </KpiCard>
            <KpiCard label="Ortalama Sepet" value={formatTL(s.avg_order_value)} icon={Package} iconClass="bg-blue-50 text-blue-600">
              <ChangeBadge value={report.changes.avg_order_value} />
            </KpiCard>
            <KpiCard label="Brüt Kâr" value={formatTL(s.gross_profit)} icon={PiggyBank} iconClass="bg-violet-50 text-violet-600">
              <span className="text-[11px] text-gray-500 block">Kâr marjı: <b>%{s.profit_margin.toLocaleString('tr-TR')}</b></span>
              <ChangeBadge value={report.changes.gross_profit} />
            </KpiCard>
            <KpiCard label="İptal Oranı" value={`%${s.cancel_rate.toLocaleString('tr-TR')}`} icon={XCircle} iconClass="bg-red-50 text-red-600">
              <span className="text-[11px] text-gray-500">
                {s.cancelled_count} / {s.total_order_count} sipariş iptal edildi
              </span>
            </KpiCard>
          </div>

          {/* CİRO TRENDİ */}
          <Card
            title="Ciro Trendi"
            subtitle={report.period.granularity === 'daily' ? 'Günlük ciro (iptaller hariç)' : 'Aylık ciro (iptaller hariç)'}
          >
            {hasOrders ? (
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={report.timeseries} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="reportRevenueFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={CHART_COLOR} stopOpacity={0.25} />
                        <stop offset="95%" stopColor={CHART_COLOR} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="label" tickLine={false} axisLine={false} tick={AXIS_TICK} minTickGap={16} />
                    <YAxis tickLine={false} axisLine={false} tick={AXIS_TICK} tickFormatter={formatCompactTL} width={64} />
                    <Tooltip
                      contentStyle={TOOLTIP_STYLE}
                      cursor={{ stroke: '#cbd5e1', strokeWidth: 1 }}
                      formatter={(val, _name, item) => [
                        `${formatTL(val)} · ${item.payload.orders} sipariş`,
                        'Ciro',
                      ]}
                    />
                    <Area
                      type="monotone"
                      dataKey="revenue"
                      stroke={CHART_COLOR}
                      strokeWidth={2}
                      fill="url(#reportRevenueFill)"
                      activeDot={{ r: 5, stroke: '#ffffff', strokeWidth: 2 }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <EmptyNote>Bu tarih aralığında sipariş yok.</EmptyNote>
            )}
          </Card>

          {/* KATEGORİ SATIŞLARI & SİPARİŞ DURUMLARI */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card title="Kategori Bazlı Satışlar" subtitle="Kategorilere göre ciro" className="lg:col-span-2">
              {report.category_sales.length > 0 ? (
                <div className="w-full" style={{ height: Math.max(160, report.category_sales.length * 44) }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={report.category_sales} layout="vertical" margin={{ top: 0, right: 72, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                      <XAxis type="number" tickLine={false} axisLine={false} tick={AXIS_TICK} tickFormatter={formatCompactTL} />
                      <YAxis type="category" dataKey="name" tickLine={false} axisLine={false} tick={{ ...AXIS_TICK, fill: '#475569' }} width={120} />
                      <Tooltip
                        contentStyle={TOOLTIP_STYLE}
                        cursor={{ fill: '#f8fafc' }}
                        formatter={(val, _name, item) => [`${formatTL(val)} · ${item.payload.quantity} adet`, 'Ciro']}
                      />
                      <Bar dataKey="revenue" fill={CHART_COLOR} radius={[0, 4, 4, 0]} barSize={18}>
                        <LabelList dataKey="revenue" position="right" formatter={formatCompactTL} style={{ fontSize: 11, fill: '#475569' }} />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <EmptyNote />
              )}
            </Card>

            <Card title="Sipariş Durumları" subtitle="Seçilen dönemdeki tüm siparişler">
              <ul className="space-y-3">
                {report.status_breakdown.map((x) => {
                  const style = STATUS_STYLES[x.status] || { dot: 'bg-gray-400', bar: 'bg-gray-300' };
                  return (
                    <li key={x.status} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="flex items-center gap-2 font-semibold text-gray-700">
                          <span className={`w-2.5 h-2.5 rounded-full ${style.dot}`} />
                          {x.status}
                        </span>
                        <span className="text-gray-500">
                          <b className="text-gray-800">{x.count}</b> · {formatTL(x.amount)}
                        </span>
                      </div>
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${style.bar}`} style={{ width: `${(x.count / totalStatusCount) * 100}%` }} />
                      </div>
                    </li>
                  );
                })}
              </ul>
            </Card>
          </div>

          {/* EN ÇOK SATAN ÜRÜNLER */}
          <Card title="En Çok Satan Ürünler" subtitle="Ciroya göre ilk 10 ürün (iptaller hariç)">
            {report.top_products.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs min-w-[640px]">
                  <thead>
                    <tr className="border-b border-gray-100 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                      <th className="py-2 pr-3">Ürün</th>
                      <th className="py-2 px-3">Kategori</th>
                      <th className="py-2 px-3 text-right">Adet</th>
                      <th className="py-2 px-3 w-[30%]">Ciro</th>
                      <th className="py-2 px-3 text-right">Kâr</th>
                      <th className="py-2 pl-3 text-right">Marj</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50 text-gray-700">
                    {report.top_products.map((p) => (
                      <tr key={p.product_id} className="hover:bg-gray-50/80">
                        <td className="py-2.5 pr-3 font-semibold text-gray-800">{p.name}</td>
                        <td className="py-2.5 px-3 text-gray-500">{p.category}</td>
                        <td className="py-2.5 px-3 text-right">{formatNumber(p.quantity)}</td>
                        <td className="py-2.5 px-3">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                              <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${(p.revenue / maxProductRevenue) * 100}%` }} />
                            </div>
                            <span className="font-semibold whitespace-nowrap">{formatTL(p.revenue)}</span>
                          </div>
                        </td>
                        <td className={`py-2.5 px-3 text-right font-semibold ${p.profit < 0 ? 'text-red-600' : 'text-gray-800'}`}>
                          {formatTL(p.profit)}
                        </td>
                        <td className="py-2.5 pl-3 text-right text-gray-500">%{p.profit_margin.toLocaleString('tr-TR')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyNote />
            )}
          </Card>

          {/* MÜŞTERİLER & ÖDEME YÖNTEMLERİ */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card title="En İyi Müşteriler" subtitle="Ciroya göre ilk 10 müşteri">
              {report.top_customers.length > 0 ? (
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-gray-100 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                      <th className="py-2 pr-3">#</th>
                      <th className="py-2 px-3">Müşteri</th>
                      <th className="py-2 px-3 text-right">Sipariş</th>
                      <th className="py-2 pl-3 text-right">Ciro</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50 text-gray-700">
                    {report.top_customers.map((c, i) => (
                      <tr key={`${c.name}-${i}`}>
                        <td className="py-2.5 pr-3 text-gray-400">{i + 1}</td>
                        <td className="py-2.5 px-3 font-semibold text-gray-800">{c.name}</td>
                        <td className="py-2.5 px-3 text-right">{c.order_count}</td>
                        <td className="py-2.5 pl-3 text-right font-semibold">{formatTL(c.revenue)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <EmptyNote />
              )}
            </Card>

            <Card title="Ödeme Yöntemleri" subtitle="İptaller hariç">
              {report.payment_methods.length > 0 ? (
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-gray-100 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                      <th className="py-2 pr-3">Yöntem</th>
                      <th className="py-2 px-3 text-right">Sipariş</th>
                      <th className="py-2 px-3 text-right">Ciro</th>
                      <th className="py-2 pl-3 text-right">Pay</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50 text-gray-700">
                    {report.payment_methods.map((p) => (
                      <tr key={p.method}>
                        <td className="py-2.5 pr-3 font-semibold text-gray-800">{p.method}</td>
                        <td className="py-2.5 px-3 text-right">{p.order_count}</td>
                        <td className="py-2.5 px-3 text-right font-semibold">{formatTL(p.revenue)}</td>
                        <td className="py-2.5 pl-3 text-right text-gray-500">
                          %{(s.revenue ? (p.revenue / s.revenue) * 100 : 0).toLocaleString('tr-TR', { maximumFractionDigits: 1 })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <EmptyNote />
              )}
            </Card>
          </div>

          {/* STOK DEĞER RAPORU */}
          <Card title="Stok Değer Raporu" subtitle="Güncel stok durumu (tarih aralığından bağımsız)">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <div className="p-4 rounded-xl bg-gray-50/70 border border-gray-100">
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1"><Boxes size={12} /> Toplam Stok</span>
                <p className="text-lg font-extrabold text-gray-800 mt-1">{formatNumber(report.inventory.stock)} Adet</p>
                <span className="text-[11px] text-gray-500">{report.inventory.product_count} ürün</span>
              </div>
              <div className="p-4 rounded-xl bg-gray-50/70 border border-gray-100">
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Maliyet Değeri</span>
                <p className="text-lg font-extrabold text-gray-800 mt-1">{formatTL(report.inventory.cost_value)}</p>
                <span className="text-[11px] text-gray-500">Stoğa bağlı sermaye</span>
              </div>
              <div className="p-4 rounded-xl bg-gray-50/70 border border-gray-100">
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Satış Değeri</span>
                <p className="text-lg font-extrabold text-gray-800 mt-1">{formatTL(report.inventory.sale_value)}</p>
                <span className="text-[11px] text-gray-500">Potansiyel kâr: {formatTL(report.inventory.potential_profit)}</span>
              </div>
              <div className="p-4 rounded-xl bg-amber-50/60 border border-amber-100">
                <span className="text-[10px] font-bold text-amber-700 uppercase tracking-wider flex items-center gap-1"><AlertTriangle size={12} /> Stok Uyarıları</span>
                <p className="text-lg font-extrabold text-gray-800 mt-1">{report.inventory.critical_count} Kritik</p>
                <span className="text-[11px] text-gray-500">{report.inventory.out_of_stock_count} ürün stokta yok</span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs min-w-[560px]">
                <thead>
                  <tr className="border-b border-gray-100 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                    <th className="py-2 pr-3">Kategori</th>
                    <th className="py-2 px-3 text-right">Ürün</th>
                    <th className="py-2 px-3 text-right">Stok</th>
                    <th className="py-2 px-3 text-right">Maliyet Değeri</th>
                    <th className="py-2 px-3 text-right">Satış Değeri</th>
                    <th className="py-2 pl-3 text-right">Potansiyel Kâr</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50 text-gray-700">
                  {report.inventory.categories.map((c) => (
                    <tr key={c.name}>
                      <td className="py-2.5 pr-3 font-semibold text-gray-800">{c.name}</td>
                      <td className="py-2.5 px-3 text-right">{c.product_count}</td>
                      <td className="py-2.5 px-3 text-right">{formatNumber(c.stock)}</td>
                      <td className="py-2.5 px-3 text-right">{formatTL(c.cost_value)}</td>
                      <td className="py-2.5 px-3 text-right">{formatTL(c.sale_value)}</td>
                      <td className="py-2.5 pl-3 text-right font-semibold">{formatTL(c.potential_profit)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
