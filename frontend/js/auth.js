/**
 * Authentication & Role State Manager
 */
class Auth {
  static checkAuth() {
    const token = ApiClient.getToken();
    const user = ApiClient.getUser();
    if (!token || !user) {
      window.location.href = 'login.html';
      return null;
    }
    return user;
  }

  static isAdmin() {
    const user = ApiClient.getUser();
    return user && user.role === 'admin';
  }

  static isEngineer() {
    const user = ApiClient.getUser();
    return user && (user.role === 'admin' || user.role === 'engineer');
  }

  static logout() {
    ApiClient.clearToken();
    window.location.href = 'login.html';
  }
}

window.Auth = Auth;
