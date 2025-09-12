'use client';

import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Calendar, Clock } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

export default function TestSchedulePage() {
  const { data: schedules } = useQuery({
    queryKey: ['test-schedule-info'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/test-schedules-info/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      const data = await response.json();
      return data.results;
    },
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-100 text-green-800">完了</Badge>;
      case 'scheduled':
        return <Badge className="bg-blue-100 text-blue-800">予定</Badge>;
      case 'in-progress':
        return <Badge className="bg-orange-100 text-orange-800">実施中</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold">テスト日程管理</h1>
          <p className="text-muted-foreground mt-1">
            年度・期別のテスト締切を確認できます
          </p>
        </div>

        <div className="grid gap-6">
          {schedules?.filter((schedule: any) => {
            // 完了済み、または締切日が過ぎた場合は非表示
            const now = new Date();
            const deadline = new Date(schedule.deadline);
            return schedule.status !== 'completed' && deadline > now;
          }).map((schedule: any) => (
            <Card key={schedule.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Calendar className="h-5 w-5" />
                      {schedule.year}年度 {schedule.period === 'summer' ? '夏期' : '冬期'}テスト
                      {schedule.period === 'winter' && (
                        <span className="text-xs text-muted-foreground">
                          ({parseInt(schedule.year) + 1}年1月実施)
                        </span>
                      )}
                    </CardTitle>
                    <CardDescription>
                      テスト締切の情報
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(schedule.status)}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center text-center space-y-4">
                  {schedule.status === 'completed' ? (
                    <div className="space-y-3">
                      <Label className="text-lg font-semibold text-green-600">テスト完了</Label>
                      <div className="flex items-center justify-center gap-2 text-xl font-bold">
                        <Clock className="h-6 w-6 text-green-500" />
                        <span className="text-green-600">
                          テスト実施完了
                        </span>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        締切日時: {new Date(schedule.deadline).toLocaleDateString('ja-JP')} {new Date(schedule.deadline).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <Label className="text-lg font-semibold text-red-600">締切日時</Label>
                      <div className="flex items-center justify-center gap-2 text-xl font-bold">
                        <Clock className="h-6 w-6 text-red-500" />
                        <span className="text-red-600">
                          {new Date(schedule.deadline).toLocaleDateString('ja-JP')} {new Date(schedule.deadline).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {(() => {
                          const now = new Date();
                          const deadline = new Date(schedule.deadline);
                          const diffMs = deadline.getTime() - now.getTime();
                          const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
                          
                          if (diffDays > 0) {
                            if (diffDays > 30) {
                              const months = Math.floor(diffDays / 30);
                              const remainingDays = diffDays % 30;
                              if (remainingDays > 0) {
                                return `約${months}ヶ月${remainingDays}日後`;
                              } else {
                                return `約${months}ヶ月後`;
                              }
                            } else {
                              return `あと${diffDays}日`;
                            }
                          } else if (diffDays === 0) {
                            return '本日締切';
                          } else {
                            return '締切済み';
                          }
                        })()}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}