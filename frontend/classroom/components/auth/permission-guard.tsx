'use client';

import { useAuth } from '@/lib/auth-context';
import { checkPermission } from '@/lib/permissions';
import { ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useQuery } from '@tanstack/react-query';
import { schoolApi } from '@/lib/api-client';

interface PermissionGuardProps {
  children: ReactNode;
  permission: 'can_register_students' | 'can_input_scores' | 'can_view_reports';
  fallback?: ReactNode;
}

export function PermissionGuard({ children, permission, fallback }: PermissionGuardProps) {
  const { user } = useAuth();

  // 学校設定を取得（教室管理者の場合は常に取得）
  // 一時的に無効化（API未実装のため）
  const { data: schoolSettings } = useQuery({
    queryKey: ['school-settings'],
    queryFn: () => schoolApi.getSchoolSettings(),
    enabled: false, // 一時的に無効化
  });
  
  // デフォルトで教室ごとの生徒管理を許可
  const defaultSchoolSettings = {
    allow_classroom_student_management: true,
  };

  console.log('PermissionGuard render:', { 
    permission, 
    user: user ? { 
      role: user.role, 
      permissions: user.permissions, 
      classroom_name: user.classroom_name,
      classroom_id: user.classroom_id,
      id: user.id
    } : null,
    schoolSettings: schoolSettings || defaultSchoolSettings
  });

  const hasPermission = checkPermission(user, permission, schoolSettings || defaultSchoolSettings);
  console.log('PermissionGuard result:', hasPermission);

  if (!hasPermission) {
    if (fallback) {
      return <>{fallback}</>;
    }

    const permissionNames = {
      can_register_students: '生徒登録',
      can_input_scores: '点数入力',
      can_view_reports: '結果出力'
    };

    const getPermissionMessage = () => {
      // 学校全体で生徒管理が制限されている場合
      if (permission === 'can_register_students' && schoolSettings?.allow_classroom_student_management === false) {
        return 'この機能は学校管理者により制限されています。学校管理者にお問い合わせください。';
      }
      
      // サーバーサイドレンダリング対応のため、URLベースの判定は削除し、権限ベースのメッセージに統一
      const permissionMessages: { [key: string]: string } = {
        can_register_students: 'この機能（生徒管理）を利用するには「生徒登録」の権限が必要です。塾管理者にお問い合わせください。',
        can_input_scores: 'この機能（点数入力）を利用するには「点数入力」の権限が必要です。塾管理者にお問い合わせください。',
        can_view_reports: 'この機能（結果出力）を利用するには「結果出力」の権限が必要です。塾管理者にお問い合わせください。'
      };
      
      return permissionMessages[permission] || `この機能を利用するには「${permissionNames[permission]}」の権限が必要です。塾管理者にお問い合わせください。`;
    };

    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
            <CardTitle>アクセス権限がありません</CardTitle>
          </CardHeader>
          <CardContent className="text-center text-sm text-muted-foreground">
            <p>{getPermissionMessage()}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}