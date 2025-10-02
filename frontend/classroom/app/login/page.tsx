'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { GraduationCap, Lock, User } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '@/lib/auth-context';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [apiUrl, setApiUrl] = useState('');
  const router = useRouter();
  const { login } = useAuth();

  useEffect(() => {
    // Set API URL on client side to avoid hydration mismatch
    setApiUrl(process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api');
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    console.log('LoginPage: Attempting login with:', { username, password: password ? '***' : '' });
    console.log('LoginPage: API Base URL:', apiUrl);

    try {
      // Use auth context login method
      const profile = await login(username, password);
      console.log('LoginPage: Auth context login completed successfully');
      console.log('LoginPage: Profile data:', profile);
      
      // 教室管理者のみログイン可能
      if (profile.role !== 'classroom_admin') {
        toast.error('教室管理者としてログインしてください');
        return;
      }

      // 教室情報を保存
      localStorage.setItem('classroom_id', profile.classroom_id || '');
      localStorage.setItem('classroom_name', profile.classroom_name || '教室');
      console.log('LoginPage: Saved classroom info:', { 
        classroom_id: profile.classroom_id, 
        classroom_name: profile.classroom_name 
      });
      
      toast.success('ログインしました');
      console.log('LoginPage: Navigating to dashboard');
      router.push('/dashboard');
    } catch (error: any) {
      console.error('LoginPage: Login error:', error);
      console.error('LoginPage: Error response:', error.response?.data);
      console.error('LoginPage: Error status:', error.response?.status);
      
      if (error.response?.status === 400 || error.response?.status === 401) {
        toast.error('ユーザー名またはパスワードが正しくありません');
      } else if (error.code === 'NETWORK_ERROR' || error.message?.includes('Network')) {
        toast.error('ネットワークエラー: バックエンドAPIに接続できません');
      } else {
        toast.error(`ログインに失敗しました: ${error.message || 'Unknown error'}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4">
            <img
              src="/logo.png"
              alt="全国学力向上テスト"
              className="h-16 w-auto mx-auto"
            />
          </div>
          <CardDescription>
            教室管理者ログイン
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">ログインID</Label>
              <div className="relative">
                <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  id="username"
                  type="text"
                  placeholder="塾ID + 教室ID（例：100001001001）"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="pl-10"
                  required
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">パスワード</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10"
                  required
                />
              </div>
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'ログイン中...' : 'ログイン'}
            </Button>
          </form>
          <div className="mt-4 text-center text-sm text-gray-600 dark:text-gray-400">
            <p>教室管理者としてログインしてください</p>
            <p>ログインID（塾ID6桁 + 教室ID6桁）とパスワードは塾管理者から取得してください</p>
          </div>
          <div className="mt-6 pt-4 border-t">
            <div className="text-center text-sm text-muted-foreground">
              <p className="font-semibold mb-2">塾管理者ページ</p>
              <p className="text-xs">塾管理者専用のログインページ</p>
              <Button
                variant="outline"
                size="sm"
                className="mt-2 text-xs"
                onClick={() => window.open('https://kouzyoutest.com/login', '_blank')}
              >
                塾管理者ページでログイン
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
