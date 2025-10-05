'use client';

import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { PermissionGuard } from '@/components/auth/permission-guard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useQuery } from '@tanstack/react-query';
import { Calendar, FileText, Plus, BarChart3, Edit } from 'lucide-react';
import { useState } from 'react';
import { testApi } from '@/lib/api-client';
import Link from 'next/link';

export default function TestsPage() {
  const [selectedYear, setSelectedYear] = useState('2025');
  const [selectedPeriod, setSelectedPeriod] = useState('summer');

  const { data: testSchedules } = useQuery({
    queryKey: ['test-schedules', selectedYear, selectedPeriod],
    queryFn: async () => {
      const params: any = {};
      if (selectedYear !== 'all') params.year = selectedYear;
      if (selectedPeriod !== 'all') params.period = selectedPeriod;
      
      const response = await testApi.getTestSchedules(params);
      return response.results || [];
    },
  });

  const getPeriodLabel = (period: string) => {
    switch (period) {
      case 'spring': return '春期';
      case 'summer': return '夏期';
      case 'winter': return '冬期';
      default: return period;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">実施中</Badge>;
      case 'completed':
        return <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100">完了</Badge>;
      case 'scheduled':
        return <Badge className="bg-orange-100 text-orange-800 hover:bg-orange-100">予定</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <DashboardLayout>
      <PermissionGuard permission="can_input_scores">
        <div className="space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">テスト管理</h1>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              テスト一覧
            </CardTitle>
            <CardDescription>
              年度・期間を選択してテストを管理できます
            </CardDescription>
            <div className="flex items-center gap-4 pt-4">
              <Select value={selectedYear} onValueChange={setSelectedYear}>
                <SelectTrigger className="w-32 rounded-xl">
                  <SelectValue placeholder="年度" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="2025">2025年度</SelectItem>
                  <SelectItem value="2026">2026年度</SelectItem>
                  <SelectItem value="2027">2027年度</SelectItem>
                </SelectContent>
              </Select>
              <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                <SelectTrigger className="w-32 rounded-xl">
                  <SelectValue placeholder="期間" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="spring">春期</SelectItem>
                  <SelectItem value="summer">夏期</SelectItem>
                  <SelectItem value="winter">冬期</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {(testSchedules?.length || 0) > 0 ? (
                <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-2">
                  {testSchedules?.map((schedule: any) => (
                    <Card key={schedule.id} className="hover:shadow-md transition-shadow">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg">
                            {selectedYear}年度 {getPeriodLabel(selectedPeriod)}テスト
                          </CardTitle>
                          {getStatusBadge(schedule.status || 'active')}
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div className="space-y-2">
                            <div className="flex items-center gap-2 text-sm">
                              <Calendar className="h-4 w-4" />
                              <span>実施期間: {schedule.start_date ? new Date(schedule.start_date).toLocaleDateString('ja-JP') : '未設定'} - {schedule.end_date ? new Date(schedule.end_date).toLocaleDateString('ja-JP') : '未設定'}</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm">
                              <FileText className="h-4 w-4" />
                              <span>科目: 国語・算数</span>
                            </div>
                          </div>
                          <div className="flex flex-col gap-2">
                            <Link href={`/tests/${selectedYear}/${selectedPeriod}/entry`} className="w-full">
                              <Button size="sm" variant="outline" className="rounded-xl w-full">
                                <Edit className="h-4 w-4 mr-2" />
                                スコア入力
                              </Button>
                            </Link>
                            <Link href={`/tests/${selectedYear}/${selectedPeriod}/download`} className="w-full">
                              <Button size="sm" variant="outline" className="rounded-xl w-full">
                                <BarChart3 className="h-4 w-4 mr-2" />
                                結果ダウンロード
                              </Button>
                            </Link>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="w-full">
                    <Card className="hover:shadow-md transition-shadow">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg">
                            {selectedYear}年度 {getPeriodLabel(selectedPeriod)}テスト
                          </CardTitle>
                          <Badge className="bg-orange-100 text-orange-800 hover:bg-orange-100">予定</Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div className="space-y-2">
                            <div className="flex items-center gap-2 text-sm">
                              <Calendar className="h-4 w-4" />
                              <span>実施期間: 未設定</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm">
                              <FileText className="h-4 w-4" />
                              <span>科目: 国語・算数</span>
                            </div>
                          </div>
                          <div className="flex flex-col gap-2">
                            <Link href={`/tests/${selectedYear}/${selectedPeriod}/entry`} className="w-full">
                              <Button size="sm" variant="outline" className="rounded-xl w-full">
                                <Edit className="h-4 w-4 mr-2" />
                                スコア入力
                              </Button>
                            </Link>
                            <Link href={`/tests/${selectedYear}/${selectedPeriod}/download`} className="w-full">
                              <Button size="sm" variant="outline" className="rounded-xl w-full">
                                <BarChart3 className="h-4 w-4 mr-2" />
                                結果ダウンロード
                              </Button>
                            </Link>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
        </div>
      </PermissionGuard>
    </DashboardLayout>
  );
}