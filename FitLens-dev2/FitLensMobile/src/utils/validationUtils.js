export const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(String(email).toLowerCase());
};

export const validatePassword = (password) => {
  return password && password.length >= 8;
};

export const validateHeight = (heightCm) => {
  const val = parseFloat(heightCm);
  return !isNaN(val) && val >= 50 && val <= 250;
};
