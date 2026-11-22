import { useCallback, useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import api from '../api/axios';
import { NotificationContext } from './notificationContext';

const REFRESH_INTERVAL_MS = 60 * 1000;

// Okundu olarak işaretlenen bildirimler kullanıcıya özel saklanır (çıkış yapınca silinmez)
const dismissedKey = () => `dismissed_notifications_${localStorage.getItem('user_name') || ''}`;

const readDismissed = () => {
  try {
    return new Set(JSON.parse(localStorage.getItem(dismissedKey()) || '[]'));
  } catch {
    return new Set();
  }
};

const saveDismissed = (set) => {
  // Liste sınırsız büyümesin diye son 500 kayıt tutulur
  localStorage.setItem(dismissedKey(), JSON.stringify([...set].slice(-500)));
};

export default function NotificationProvider({ children }) {
  const [allNotifications, setAllNotifications] = useState([]);
  const [dismissed, setDismissed] = useState(readDismissed);
  const location = useLocation();
  const token = localStorage.getItem('token');

  const refresh = useCallback(async () => {
    if (!localStorage.getItem('token')) {
      setAllNotifications([]);
      return;
    }
    try {
      const res = await api.get('/notifications');
      setAllNotifications(Array.isArray(res.data) ? res.data : []);
      setDismissed(readDismissed());
    } catch (err) {
      console.error('Bildirimler alınamadı:', err);
    }
  }, []);

  // Giriş/çıkış veya sayfa değişiminde ve belirli aralıklarla yenilenir
  useEffect(() => {
    refresh();
  }, [refresh, token, location.pathname]);

  useEffect(() => {
    if (!token) return undefined;
    const timer = setInterval(refresh, REFRESH_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [refresh, token]);

  const notifications = useMemo(
    () => (token ? allNotifications.filter((n) => !dismissed.has(n.id)) : []),
    [allNotifications, dismissed, token]
  );

  const dismiss = useCallback((id) => {
    setDismissed((prev) => {
      const next = new Set(prev);
      next.add(id);
      saveDismissed(next);
      return next;
    });
  }, []);

  const dismissAll = useCallback(() => {
    setDismissed((prev) => {
      const next = new Set(prev);
      allNotifications.forEach((n) => next.add(n.id));
      saveDismissed(next);
      return next;
    });
  }, [allNotifications]);

  const value = useMemo(
    () => ({ notifications, dismiss, dismissAll, refresh }),
    [notifications, dismiss, dismissAll, refresh]
  );

  return <NotificationContext.Provider value={value}>{children}</NotificationContext.Provider>;
}
