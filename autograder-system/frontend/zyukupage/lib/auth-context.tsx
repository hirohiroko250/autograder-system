'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User } from './types';
import { authApi, setTokens, clearTokens, getStoredTokens } from './api-client';

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const tokens = getStoredTokens();
      if (tokens.access && tokens.refresh) {
        try {
          // First try to get user from localStorage
          const storedUser = typeof window !== 'undefined' ? localStorage.getItem('user') : null;
          if (storedUser) {
            const userData = JSON.parse(storedUser);
            
            // 教室管理者で権限情報がない場合は、教室情報を再取得
            if (userData.role === 'classroom_admin' && userData.classroom_id && !userData.permissions) {
              console.log('zyukupage AuthContext: Classroom admin without permissions, fetching from API');
              try {
                const classroomUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL}/classrooms/${userData.classroom_id}/`;
                console.log('zyukupage AuthContext: Fetching classroom permissions from:', classroomUrl);
                
                const classroomResponse = await fetch(classroomUrl, {
                  headers: {
                    'Authorization': `Bearer ${tokens.access}`,
                  },
                });
                
                if (classroomResponse.ok) {
                  const classroomData = await classroomResponse.json();
                  console.log('zyukupage AuthContext: Retrieved classroom data:', classroomData);
                  
                  if (classroomData.permissions) {
                    userData.permissions = classroomData.permissions;
                    console.log('zyukupage AuthContext: Applied permissions to stored user:', classroomData.permissions);
                    localStorage.setItem('user', JSON.stringify(userData));
                  }
                }
              } catch (error) {
                console.error('zyukupage AuthContext: Failed to fetch classroom permissions on init:', error);
              }
            }
            
            setUser(userData);
          } else {
            // Fallback to API call if no stored user data
            const profile = await authApi.getProfile();
            setUser(profile);
            if (typeof window !== 'undefined') {
              localStorage.setItem('user', JSON.stringify(profile));
            }
          }
        } catch (error) {
          console.error('Failed to load user profile:', error);
          clearTokens();
        }
      }
      setIsLoading(false);
    };

    initAuth();

    // 権限更新イベントのリスナーを追加
    const handlePermissionUpdate = (event: CustomEvent) => {
      console.log('Received permission update event:', event.detail);
      setUser(prevUser => {
        if (prevUser) {
          const updatedUser = { ...prevUser, permissions: event.detail.permissions };
          console.log('AuthContext: Updated user permissions:', updatedUser);
          return updatedUser;
        }
        return prevUser;
      });
    };

    window.addEventListener('user-permissions-updated', handlePermissionUpdate as EventListener);

    return () => {
      window.removeEventListener('user-permissions-updated', handlePermissionUpdate as EventListener);
    };
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const response = await authApi.login(username, password);
      setTokens(response.access, response.refresh);
      
      // 教室管理者の場合、教室の権限設定を取得
      if (response.user.role === 'classroom_admin' && response.user.classroom_id) {
        try {
          const classroomResponse = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/classrooms/${response.user.classroom_id}/`, {
            headers: {
              'Authorization': `Bearer ${response.access}`,
            },
          });
          
          if (classroomResponse.ok) {
            const classroomData = await classroomResponse.json();
            console.log('zyukupage AuthContext: Classroom data:', classroomData);
            
            // 教室の権限設定をユーザーオブジェクトに追加
            if (classroomData.permissions) {
              response.user.permissions = classroomData.permissions;
              console.log('zyukupage AuthContext: Applied classroom permissions:', classroomData.permissions);
            }
          }
        } catch (error) {
          console.error('zyukupage AuthContext: Failed to fetch classroom permissions:', error);
        }
      }
      
      setUser(response.user);
    } catch (error: any) {
      console.error('Login failed:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      console.error('Error headers:', error.response?.headers);
      throw error;
    }
  };

  const logout = () => {
    clearTokens();
    setUser(null);
  };

  const value: AuthContextType = {
    user,
    login,
    logout,
    isLoading,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};