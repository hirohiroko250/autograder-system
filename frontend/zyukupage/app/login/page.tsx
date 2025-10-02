'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Eye, EyeOff, GraduationCap } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '@/lib/auth-context';

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  // サーバーサイドでも判定できるよう、ビルド時の判定を追加
  const isClassroomBuild = process.env.NEXT_PUBLIC_CLASSROOM_MODE === 'true';
  const [isClassroomPage, setIsClassroomPage] = useState(isClassroomBuild);
  const router = useRouter();
  const { login } = useAuth();
  const classroomLoginUrl = `${(process.env.NEXT_PUBLIC_CLASSROOM_URL ?? 'http://162.43.55.80:3001').replace(/\/$/, '')}/login`;

  useEffect(() => {
    // クライアントサイドでポート番号で教室ページかどうかを判定
    if (typeof window !== 'undefined') {
      const port = window.location.port;
      const isClientClassroom = port === '3001';
      if (isClientClassroom !== isClassroomPage) {
        setIsClassroomPage(isClientClassroom);
      }
    }
  }, [isClassroomPage]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await login(username, password);
      toast.success('ログインしました');
      // ポートに応じて適切なダッシュボードにリダイレクト
      if (isClassroomPage) {
        router.push('/classrooms');  // 教室ページ用ダッシュボード
      } else {
        router.push('/dashboard');   // 塾ページ用ダッシュボード
      }
    } catch (error: any) {
      console.error('Login error:', error);
      toast.error('ログインIDまたはパスワードが間違っています');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 via-background to-accent/10 p-4">
      <Card className="w-full max-w-md animate-fade-in">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
            <GraduationCap className="w-8 h-8 text-primary" />
          </div>
          <CardTitle className="text-2xl font-bold">全国学力向上テスト</CardTitle>
          <CardDescription className="text-muted-foreground">
            {isClassroomPage
              ? '教室管理者としてログインしてください'
              : '塾管理者・教室管理者としてログインしてください'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">ログインID</Label>
              <Input
                id="username"
                type="text"
                placeholder="ログインIDを入力してください"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="rounded-xl"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">パスワード</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="パスワード"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="rounded-xl pr-10"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </div>
            <Button
              type="submit"
              className="w-full rounded-xl bg-primary hover:bg-primary/90"
              disabled={loading}
            >
              {loading ? 'ログイン中...' : 'ログイン'}
            </Button>
          </form>

          <div className="mt-6 pt-4 border-t">
            <div className="text-center text-sm text-muted-foreground">
              {isClassroomPage ? (
                <>
                  <p className="font-semibold mb-2">教室管理者専用ページ</p>
                  <p className="text-xs">このページは教室管理者専用です</p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-2 text-xs"
                    onClick={() => window.open('http://162.43.55.80:3000/login', '_blank')}
                  >
                    塾管理者ページでログイン
                  </Button>
                </>
              ) : (
                <>
                  <p className="font-semibold mb-2">教室ページ</p>
                  <p className="text-xs">教室管理者専用のログインページ</p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-2 text-xs"
                    onClick={() => window.open(classroomLoginUrl, '_blank')}
                  >
                    教室ページでログイン
                  </Button>
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
