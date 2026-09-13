import { useCallback, useEffect, useState } from 'react';
import authService from '../services/authService';
import profileService from '../services/profileService';
import { AuthContext } from './authContextDef';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => authService.getStoredUser());
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(() => authService.hasToken());
  const [error, setError] = useState(null);

  const syncProfile = useCallback(async () => {
    if (!authService.hasToken()) {
      setUser(null);
      setProfile(null);
      setLoading(false);
      return;
    }

    try {
      const profileData = await profileService.getProfile();
      setProfile(profileData);
      setUser({
        id: profileData.id,
        email: profileData.email,
        full_name: profileData.full_name,
      });
      setError(null);
    } catch (err) {
      console.error('Failed to fetch user profile:', err);
      authService.clearSession();
      setUser(null);
      setProfile(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    if (authService.hasToken()) {
      profileService
        .getProfile()
        .then((profileData) => {
          if (!isMounted) return;
          setProfile(profileData);
          setUser({
            id: profileData.id,
            email: profileData.email,
            full_name: profileData.full_name,
          });
        })
        .catch((err) => {
          if (!isMounted) return;
          console.error('Session initialization failed:', err);
          authService.clearSession();
          setUser(null);
          setProfile(null);
        })
        .finally(() => {
          if (isMounted) {
            setLoading(false);
          }
        });
    }

    const handleLogoutEvent = () => {
      setUser(null);
      setProfile(null);
    };

    window.addEventListener('auth:logout', handleLogoutEvent);
    return () => {
      isMounted = false;
      window.removeEventListener('auth:logout', handleLogoutEvent);
    };
  }, []);

  const login = async (credentials) => {
    setError(null);
    const data = await authService.login(credentials);
    await syncProfile();
    return data;
  };

  const register = async (userData) => {
    setError(null);
    const data = await authService.register(userData);
    await syncProfile();
    return data;
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setProfile(null);
  };

  const updateProfile = async (profileData) => {
    const updated = await profileService.updateProfile(profileData);
    setProfile(updated);
    setUser((prev) => ({
      ...prev,
      full_name: updated.full_name,
    }));
    return updated;
  };

  const value = {
    user,
    profile,
    loading,
    error,
    isAuthenticated: Boolean(user && authService.hasToken()),
    login,
    register,
    logout,
    refreshProfile: syncProfile,
    updateProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export default AuthProvider;
