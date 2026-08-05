export const Endpoints = {
  // Auth
  LOGIN: '/api/auth/login',
  REGISTER: '/api/auth/register',
  FORGOT_PASSWORD: '/api/auth/forgot-password',
  RESET_PASSWORD: '/api/auth/reset-password',
  CHANGE_PASSWORD: '/api/auth/change-password',
  UPDATE_PROFILE: '/api/auth/update-profile',
  DELETE_ACCOUNT: '/api/auth/delete-account',
  ME: '/api/auth/me',
  SAVE_FACE: '/api/auth/save-face',
  VERIFY_FACE: '/api/auth/verify-face',

  // Measurements
  PROCESS: '/api/process',
  VALIDATE: '/validate/person-count',
  SAVE_MEASUREMENTS: '/api/measurements/save',
  HISTORY: '/api/measurements/history',
  LATEST: '/api/measurements/latest',
  DELETE_MEASUREMENT: '/api/measurements/delete',

  // Downloads
  DOWNLOAD_PDF: '/api/download/pdf',
  DOWNLOAD_DOCX: '/api/download/docx',
  DOWNLOAD_XML: '/api/download/xml',

  // Health
  HEALTH: '/api/health',
};
