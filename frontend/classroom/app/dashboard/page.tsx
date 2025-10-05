'use client';

import { ProtectedRoute } from '@/components/auth/protected-route';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { YearPicker } from '@/components/ui/year-picker';
import { DeadlineBanner } from '@/components/ui/deadline-banner';
import { useQuery } from '@tanstack/react-query';
import { Users, FileText, TrendingUp, TrendingDown, Clock, CheckCircle, User, Phone } from 'lucide-react';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { studentApi } from '@/lib/api-client';
import { formatGrade } from '@/lib/utils';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

export default function DashboardPage() {
  const [selectedYear, setSelectedYear] = useState('2025');
  const router = useRouter();

  const { data: dashboardData } = useQuery({
    queryKey: ['dashboard', selectedYear],
    queryFn: async () => {
      // Mock data
      return {
        totalStudents: 1245,
        activeTests: 3,
        completedTests: 8,
        studentGrowth: 12.5,
      };
    },
  });

  // テスト日程情報から締切日を取得
  const { data: schedules } = useQuery({
    queryKey: ['test-schedule-info'],
    queryFn: async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/test-schedules-info/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      const data = await response.json();
      return data.results;
    },
  });

  // 現在有効な締切日を取得（完了していない、かつ締切が過ぎていない）
  const currentDeadline = schedules?.find((schedule: any) => {
    const now = new Date();
    const deadline = new Date(schedule.deadline);
    return schedule.status !== 'completed' && deadline > now;
  })?.deadline;

  const { data: enrolledStudents } = useQuery({
    queryKey: ['enrolled-students', selectedYear],
    queryFn: async () => {
      try {
        const response = await studentApi.getStudents({ page_size: 10000 });
        return response.results;
      } catch (error) {
        // エラーの場合は空配列を返す
        return [];
      }
    },
  });

  const stats = [
    {
      title: '受講生徒数',
      value: enrolledStudents?.length.toLocaleString() || '0',
      icon: Users,
      change: `${selectedYear}年度`,
      changeType: 'neutral' as 'increase' | 'decrease' | 'neutral',
      color: 'text-blue-600',
    },
  ];

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">ダッシュボード</h1>
          <div className="flex items-center gap-4">
            <YearPicker value={selectedYear} onValueChange={setSelectedYear} />
          </div>
        </div>

        <DeadlineBanner deadline={currentDeadline ? new Date(currentDeadline) : undefined} />

        <div className="grid gap-6 md:grid-cols-1">
          {stats.map((stat, index) => (
            <Card key={stat.title} className="animate-slide-in" style={{ animationDelay: `${index * 100}ms` }}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  {stat.changeType === 'increase' && <TrendingUp className="h-3 w-3 text-green-500" />}
                  {stat.changeType === 'decrease' && <TrendingDown className="h-3 w-3 text-red-500" />}
                  {stat.changeType === 'neutral' && <Clock className="h-3 w-3 text-blue-500" />}
                  <span>{stat.change}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                受講生徒一覧
              </CardTitle>
              <CardDescription>
                {selectedYear}年度の受講生徒
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {(enrolledStudents?.length || 0) > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>生徒</TableHead>
                        <TableHead>学年</TableHead>
                        <TableHead>教室</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {enrolledStudents?.slice(0, 5).map((student: any) => (
                        <TableRow key={student.id}>
                          <TableCell>
                            <div className="flex items-center gap-3">
                              <Avatar className="h-8 w-8">
                                <AvatarFallback>{student.name?.charAt(0) || 'S'}</AvatarFallback>
                              </Avatar>
                              <div>
                                <div className="font-medium">{student.name}</div>
                                <div className="text-sm text-muted-foreground">ID: {student.student_id}</div>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>{formatGrade(student.grade)}</TableCell>
                          <TableCell>{student.classroom?.name || student.classroom_name || '未設定'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    選択した期間に受講している生徒はいません
                  </div>
                )}
                {(enrolledStudents?.length || 0) > 5 && (
                  <div className="text-center pt-4">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => router.push('/students')}
                    >
                      すべて表示 ({enrolledStudents?.length || 0}名)
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}