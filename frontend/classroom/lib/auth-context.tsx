'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User } from './types';
import { authApi, setTokens, clearTokens, getStoredTokens } from './api-client';

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<User>;
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
            
            // 学校・教室管理者で権限情報がない場合は、学校情報を再取得
            if ((userData.role === 'classroom_admin' || userData.role === 'school_admin') && userData.school_id && !userData.permissions) {
              console.log('AuthContext: User without permissions, fetching from API');
              try {
                const schoolUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api'}/schools/?school_id=${userData.school_id}`;
                console.log('AuthContext: Fetching school permissions from:', schoolUrl);
                
                const schoolResponse = await fetch(schoolUrl, {
                  headers: {
                    'Authorization': `Bearer ${tokens.access}`,
                  },
                });
                
                if (schoolResponse.ok) {
                  const schoolData = await schoolResponse.json();
                  console.log('AuthContext: Retrieved school data:', schoolData);
                  
                  const school = schoolData.results?.[0];
                  if (school && school.permissions) {
                    userData.permissions = school.permissions;
                    console.log('AuthContext: Applied permissions to stored user:', school.permissions);
                    localStorage.setItem('user', JSON.stringify(userData));
                  } else if (school) {
                    // フォールバック：直接フィールドから権限を取得
                    userData.permissions = {
                      can_register_students: school.can_register_students ?? true,
                      can_input_scores: school.can_input_scores ?? true,
                      can_view_reports: school.can_view_reports ?? true,
                    };
                    console.log('AuthContext: Applied permissions from fields:', userData.permissions);
                    localStorage.setItem('user', JSON.stringify(userData));
                  }
                }
              } catch (error) {
                console.error('AuthContext: Failed to fetch school permissions on init:', error);
              }
            }
            
            setUser(userData);
            // 開発ログを完全に無効化（必要に応じてコメントアウトを外す）
            // if (process.env.NODE_ENV === 'development') {
            //   console.log('AuthContext: Loaded user from localStorage:', userData);
            //   console.log('AuthContext: User permissions from localStorage:', userData.permissions);
            // }
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
          if (typeof window !== 'undefined') {
            localStorage.removeItem('user');
          }
        }
      }
      setIsLoading(false);
    };

    initAuth();

    // 権限更新イベントのリスナーを追加
    const handlePermissionUpdate = (event: CustomEvent) => {
      console.log('AuthContext: Received permission update event:', event.detail);
      setUser(prevUser => {
        if (prevUser) {
          const updatedUser = { ...prevUser, permissions: event.detail.permissions };
          console.log('AuthContext: Updated user permissions from event:', {
            before: prevUser.permissions,
            after: updatedUser.permissions
          });
          
          // localStorageも同期更新
          localStorage.setItem('user', JSON.stringify(updatedUser));
          
          return updatedUser;
        }
        console.log('AuthContext: No user to update permissions for');
        return prevUser;
      });
    };

    window.addEventListener('user-permissions-updated', handlePermissionUpdate as EventListener);

    return () => {
      window.removeEventListener('user-permissions-updated', handlePermissionUpdate as EventListener);
    };
  }, []);

  const login = async (username: string, password: string): Promise<User> => {
    try {
      console.log('AuthContext: Starting login process');
      const response = await authApi.login(username, password);
      console.log('AuthContext: Login API response received:', response);
      console.log('AuthContext: Full user object from API:', response.user);
      
      setTokens(response.access, response.refresh);
      console.log('AuthContext: Tokens set successfully');
      
      // 教室管理者の場合、学校の権限設定を取得
      console.log('AuthContext: Checking if should fetch school permissions:', {
        role: response.user.role,
        school_id: response.user.school_id,
        condition_result: (response.user.role === 'classroom_admin' || response.user.role === 'school_admin') && !!response.user.school_id
      });
      
      if ((response.user.role === 'classroom_admin' || response.user.role === 'school_admin') && response.user.school_id) {
        console.log('AuthContext: Fetching school permissions for school_id:', response.user.school_id);
        try {
          const schoolUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api'}/schools/?school_id=${response.user.school_id}`;
          console.log('AuthContext: School API URL:', schoolUrl);
          
          const schoolResponse = await fetch(schoolUrl, {
            headers: {
              'Authorization': `Bearer ${response.access}`,
            },
          });
          
          console.log('AuthContext: School response status:', schoolResponse.status);
          
          if (schoolResponse.ok) {
            const schoolData = await schoolResponse.json();
            console.log('AuthContext: Raw school data:', schoolData);
            
            // 学校の権限設定をユーザーオブジェクトに追加
            const school = schoolData.results?.[0];
            if (school && school.permissions) {
              response.user.permissions = school.permissions;
              console.log('AuthContext: Applied school permissions:', school.permissions);
            } else if (school) {
              // フォールバック：直接フィールドから権限を取得
              response.user.permissions = {
                can_register_students: school.can_register_students ?? true,
                can_input_scores: school.can_input_scores ?? true,
                can_view_reports: school.can_view_reports ?? true,
              };
              console.log('AuthContext: Applied school permissions from fields:', response.user.permissions);
            } else {
              console.log('AuthContext: No school data found');
            }
          } else {
            console.error('AuthContext: School API failed with status:', schoolResponse.status);
            const errorText = await schoolResponse.text();
            console.error('AuthContext: Error response:', errorText);
          }
        } catch (error) {
          console.error('AuthContext: Failed to fetch school permissions:', error);
        }
      } else {
        console.log('AuthContext: User is not school/classroom_admin or no school_id:', {
          role: response.user.role,
          school_id: response.user.school_id
        });
      }

      setUser(response.user);
      console.log('AuthContext: User state updated:', response.user);
      console.log('AuthContext: User permissions:', response.user.permissions);
      console.log('AuthContext: Full user object keys:', Object.keys(response.user));
      
      // Save user data to localStorage for access in login page
      if (typeof window !== 'undefined') {
        localStorage.setItem('user', JSON.stringify(response.user));
        console.log('AuthContext: User data saved to localStorage');
      }
      
      return response.user;
    } catch (error: any) {
      console.error('AuthContext: Login failed:', error);
      console.error('AuthContext: Error response:', error.response?.data);
      console.error('AuthContext: Error status:', error.response?.status);
      console.error('AuthContext: Error headers:', error.response?.headers);
      throw error;
    }
  };

  const logout = () => {
    clearTokens();
    setUser(null);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('user');
      localStorage.removeItem('classroom_id');
      localStorage.removeItem('classroom_name');
    }
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