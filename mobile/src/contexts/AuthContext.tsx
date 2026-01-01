/**Контекст аутентификации.*/
import React, {createContext, useContext, useState, useEffect, ReactNode} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

import {apiService} from '../services/api';
import {ENDPOINTS} from '../config/api';

interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  avatar_url?: string;
  is_active: boolean;
  is_verified: boolean;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{children: ReactNode}> = ({children}) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async (): Promise<void> => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (token) {
        await refreshUser();
      }
    } catch (error) {
      console.error('[AuthContext] Auth check failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<void> => {
    try {
      const response = await apiService.post(ENDPOINTS.AUTH.LOGIN, {
        email,
        password,
      });

      await AsyncStorage.setItem('auth_token', response.access_token);
      await refreshUser();
    } catch (error) {
      console.error('[AuthContext] Login failed:', error);
      throw error;
    }
  };

  const register = async (
    email: string,
    username: string,
    password: string,
  ): Promise<void> => {
    try {
      await apiService.post(ENDPOINTS.AUTH.REGISTER, {
        email,
        username,
        password,
      });
      // После регистрации автоматически войти
      await login(email, password);
    } catch (error) {
      console.error('[AuthContext] Registration failed:', error);
      throw error;
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await AsyncStorage.removeItem('auth_token');
      setUser(null);
    } catch (error) {
      console.error('[AuthContext] Logout failed:', error);
    }
  };

  const refreshUser = async (): Promise<void> => {
    try {
      const userData = await apiService.get<User>(ENDPOINTS.AUTH.ME);
      setUser(userData);
    } catch (error) {
      console.error('[AuthContext] Refresh user failed:', error);
      await AsyncStorage.removeItem('auth_token');
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
