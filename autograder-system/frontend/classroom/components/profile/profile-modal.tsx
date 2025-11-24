'use client';

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { User, Mail, Building, School } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';

interface ProfileModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ProfileModal({ open, onOpenChange }: ProfileModalProps) {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            プロフィール
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6">
          {/* プロフィール情報 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">基本情報</CardTitle>
              <CardDescription>
                アカウントの基本情報を確認できます
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <Avatar className="h-16 w-16">
                  <AvatarImage src={`/users/${user.id}.jpg`} alt={user.username} />
                  <AvatarFallback className="text-lg">
                    {user.school_name?.charAt(0) || user.username?.charAt(0) || 'U'}
                  </AvatarFallback>
                </Avatar>
                <div className="space-y-1">
                  <h3 className="text-xl font-semibold">
                    {user.school_name || user.classroom_name || user.username}
                  </h3>
                  <div className="flex items-center gap-2">
                    <Badge variant={user.role === 'school_admin' ? 'default' : 'secondary'}>
                      {user.role === 'school_admin' ? '塾管理者' : '教室管理者'}
                    </Badge>
                  </div>
                </div>
              </div>
              
              <Separator />
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium flex items-center gap-2">
                    <User className="h-4 w-4" />
                    ユーザーID
                  </Label>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm">{user.username}</p>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label className="text-sm font-medium flex items-center gap-2">
                    <Mail className="h-4 w-4" />
                    メールアドレス
                  </Label>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm">{user.email || 'メールアドレス未設定'}</p>
                  </div>
                </div>
                
                {user.school_id && (
                  <div className="space-y-2">
                    <Label className="text-sm font-medium flex items-center gap-2">
                      <Building className="h-4 w-4" />
                      塾ID
                    </Label>
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm">{user.school_id}</p>
                    </div>
                  </div>
                )}
                
                {user.classroom_id && (
                  <div className="space-y-2">
                    <Label className="text-sm font-medium flex items-center gap-2">
                      <School className="h-4 w-4" />
                      教室ID
                    </Label>
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm">{user.classroom_id}</p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

        </div>
      </DialogContent>
    </Dialog>
  );
}