import { createContext, useContext } from 'react';

export const NotificationContext = createContext({
  notifications: [],
  dismiss: () => {},
  dismissAll: () => {},
  refresh: () => {},
});

export const useNotifications = () => useContext(NotificationContext);
