// Şifre kuralları: kayıt ve yönetici ekleme formlarında ortak kullanılır (backend'de de aynı kurallar var)
export const validatePassword = (pass) => {
  if (pass.length < 8) {
    return "Şifre en az 8 karakter olmalıdır.";
  }
  if (!/[A-Z]/.test(pass)) {
    return "Şifre en az bir büyük harf içermelidir (A-Z).";
  }
  if (!/[a-z]/.test(pass)) {
    return "Şifre en az bir küçük harf içermelidir (a-z).";
  }
  if (!/[0-9]/.test(pass)) {
    return "Şifre en az bir rakam içermelidir (0-9).";
  }
  if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(pass)) {
    return "Şifre en az bir özel karakter içermelidir (örn: !, @, #, $, %).";
  }
  return null;
};
