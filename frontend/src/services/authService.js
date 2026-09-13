import api from './api';

export const authService = {
  /**
   * Register a new user account.
   * Expects: { email, password, password_confirm, full_name }
   */
  async register(userData) {
    const response = await api.post('/auth/register/', userData);
    const { tokens, user } = response.data;
    if (tokens?.access && tokens?.refresh) {
      authService.setSession(tokens.access, tokens.refresh, user);
    }
    return response.data;
  },

  /**
   * Log in user with email and password.
   * Expects: { email, password }
   */
  async login(credentials) {
    const response = await api.post('/auth/login/', credentials);
    const { access, refresh, user } = response.data;
    if (access && refresh) {
      authService.setSession(access, refresh, user);
    }
    return response.data;
  },

  /**
   * Log out user and clear stored tokens.
   */
  logout() {
    authService.clearSession();
    window.dispatchEvent(new Event('auth:logout'));
  },

  /**
   * Store JWT tokens and user metadata in localStorage.
   */
  setSession(accessToken, refreshToken, user) {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    }
  },

  /**
   * Clear session data.
   */
  clearSession() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },

  /**
   * Retrieve current stored user.
   */
  getStoredUser() {
    try {
      const userStr = localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  },

  /**
   * Check if an access token is stored.
   */
  hasToken() {
    return Boolean(localStorage.getItem('access_token'));
  },
};

export default authService;
