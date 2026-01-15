'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, AuthContextType, LoginRequest, RegisterRequest } from '@/types/auth';
import { apiClient } from '@/lib/api';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state on mount
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = apiClient.getAuthToken();
      
      if (storedToken) {
        try {
          // Verify token is still valid by fetching current user
          const currentUser = await apiClient.getCurrentUser();
          setUser(currentUser);
          setToken(storedToken);
        } catch (error) {
          // Token is invalid, clear it
          apiClient.setAuthToken(null);
          setUser(null);
          setToken(null);
        }
      }
      
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (credentials: LoginRequest) => {
    try {
      const authResponse = await apiClient.login(credentials);
      setUser(authResponse.user);
      setToken(authResponse.access_token);
      apiClient.setAuthToken(authResponse.access_token); // Update token in API client
    } catch (error) {
      // Re-throw error to be handled by the component
      throw error;
    }
  };

  const register = async (userData: RegisterRequest) => {
    try {
      const authResponse = await apiClient.register(userData);
      setUser(authResponse.user);
      setToken(authResponse.access_token);
      apiClient.setAuthToken(authResponse.access_token); // Update token in API client
    } catch (error) {
      // Re-throw error to be handled by the component
      throw error;
    }
  };

  const logout = () => {
    apiClient.logout();
    setUser(null);
    setToken(null);
  };

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}