// Kullanıcı rolüne göre giriş sonrası açılacak ana sayfa
export const getHomePath = (role) => (role === 'customer' ? '/portal/anasayfa' : '/dashboard');
