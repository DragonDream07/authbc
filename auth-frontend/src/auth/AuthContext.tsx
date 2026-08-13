import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { login as apiLogin, logout as apiLogout, me as apiMe, refresh as apiRefresh, register as apiRegister } from '../api/auth';
import type { LoginRequest, RegisterRequest, UserResponse } from '../api/types';
import { clearTokens, getAccessToken, setTokens } from './tokenStore';

interface AuthUser {
  id: string;
  fullName: string;
  email: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function mapUser(raw: UserResponse): AuthUser {
  return {
    id: raw.id,
    fullName: raw.full_name,
    email: raw.email,
    isActive: raw.is_active,
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refresh = useCallback(async (): Promise<void> => {
    try {
      const response = await apiRefresh();
      if (response.access_token) {
        setTokens(response.access_token);
      }
      const meResponse = await apiMe();
      setUser(mapUser(meResponse));
    } catch {
      clearTokens();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    apiMe()
      .then((meResponse) => {
        setUser(mapUser(meResponse));
      })
      .catch(() => {
        return refresh();
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [refresh]);

  const login = useCallback(async (data: LoginRequest): Promise<void> => {
    const response = await apiLogin(data);
    if (response.access_token) {
      setTokens(response.access_token);
    }
    const meResponse = await apiMe();
    setUser(mapUser(meResponse));
  }, []);

  const register = useCallback(async (data: RegisterRequest): Promise<void> => {
    const response = await apiRegister(data);
    if (response.access_token) {
      setTokens(response.access_token);
    }
    const meResponse = await apiMe();
    setUser(mapUser(meResponse));
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    try {
      await apiLogout();
    } finally {
      clearTokens();
      setUser(null);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      register,
      logout,
      refresh,
    }),
    [user, isLoading, login, register, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
