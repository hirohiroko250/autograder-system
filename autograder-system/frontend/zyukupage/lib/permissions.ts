import { useAuth } from '@/lib/auth-context';

export const usePermissions = () => {
  const { user } = useAuth();
  
  // デフォルトの権限（学校管理者は全権限、教室管理者は権限設定に基づく）
  const getPermissions = () => {
    if (!user) {
      return {
        canRegisterStudents: false,
        canInputScores: false,
        canViewReports: false,
      };
    }

    // 学校管理者は全権限を持つ
    if (user.role === 'school_admin') {
      return {
        canRegisterStudents: true,
        canInputScores: true,
        canViewReports: true,
      };
    }

    // 教室管理者の場合は設定された権限に基づく  
    if (user.role === 'classroom_admin') {
      return {
        canRegisterStudents: user.permissions?.can_register_students ?? false, // デフォルトは制限
        canInputScores: user.permissions?.can_input_scores ?? false, // デフォルトは制限
        canViewReports: user.permissions?.can_view_reports ?? true, // 結果出力のみデフォルト許可
      };
    }

    return {
      canRegisterStudents: false,
      canInputScores: false,
      canViewReports: false,
    };
  };

  return getPermissions();
};

export const checkPermission = (user: any, permission: 'can_register_students' | 'can_input_scores' | 'can_view_reports', schoolSettings?: any): boolean => {
  console.log('checkPermission called:', {
    user: user ? { role: user.role, permissions: user.permissions, classroom_name: user.classroom_name } : null,
    permission,
    schoolSettings
  });

  if (!user) {
    console.log('checkPermission: No user, returning false');
    return false;
  }
  
  // 学校管理者は全権限を持つ
  if (user.role === 'school_admin') {
    console.log('checkPermission: School admin, returning true');
    return true;
  }
  
  // 教室管理者の場合
  if (user.role === 'classroom_admin') {
    console.log('checkPermission: Classroom admin detected');
    
    // 権限情報がない場合は、デフォルト値を使用
    if (!user.permissions) {
      console.log('checkPermission: No permissions found, using strict default permissions');
      const defaultValue = permission === 'can_view_reports' ? true : false; // 結果出力のみデフォルト許可
      console.log('checkPermission: Default permission result:', { permission, defaultValue });
      return defaultValue;
    }
    
    // 生徒管理権限の場合、学校全体での制限をチェック
    if (permission === 'can_register_students') {
      console.log('checkPermission: Checking student registration permission');
      // 学校全体で教室ごとの生徒管理が禁止されている場合は無効
      if (schoolSettings?.allow_classroom_student_management === false) {
        console.log('checkPermission: School-wide student management disabled, returning false');
        return false;
      }
    }
    
    const defaultValue = permission === 'can_view_reports' ? true : false; // 結果出力のみデフォルト許可
    const hasPermission = user.permissions?.[permission] ?? defaultValue;
    
    console.log('checkPermission: Final result:', {
      permission,
      userPermissionValue: user.permissions?.[permission],
      defaultValue,
      hasPermission
    });
    
    return hasPermission;
  }
  
  console.log('checkPermission: Unknown role, returning false');
  return false;
};