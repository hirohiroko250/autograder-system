'use client';

import { useState } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
// import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  Award,
  Calendar,
  Clock
} from 'lucide-react';

export default function ClassroomDashboardPage() {
  const [selectedYear, setSelectedYear] = useState('2024');

  // Mock data
  const kpiData = {
    totalStudents: 45,
    testsCompleted: 8,
    averageScore: 78.5,
    improvementRate: 12.3,
    upcomingDeadline: '2024年6月15日',
    completionRate: 85,
    topPerformers: [
      { name: '田中太郎', score: 95, subject: '算数' },
      { name: '佐藤花子', score: 92, subject: '国語' },
      { name: '山田次郎', score: 90, subject: '算数' }
    ],
    recentTests: [
      { subject: '算数', date: '2024-06-01', completed: 42, total: 45 },
      { subject: '国語', date: '2024-05-28', completed: 45, total: 45 },
      { subject: '算数', date: '2024-05-25', completed: 38, total: 45 }
    ]
  };

  const years = ['2024', '2023', '2022'];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              教室ダッシュボード
            </h1>
            <p className="text-gray-500 dark:text-gray-400">
              教室の学習状況を確認できます
            </p>
          </div>
          <div className="flex gap-2">
            <Select value={selectedYear} onValueChange={setSelectedYear}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="年度" />
              </SelectTrigger>
              <SelectContent>
                {years.map(year => (
                  <SelectItem key={year} value={year}>
                    {year}年度
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-6">

            {/* Next Deadline Banner */}
            <Card className="bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-700">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <Clock className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  <div>
                    <p className="font-semibold text-blue-900 dark:text-blue-100">
                      次回締切日
                    </p>
                    <p className="text-sm text-blue-700 dark:text-blue-300">
                      {kpiData.upcomingDeadline} - 算数テスト
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Charts Section */}
            <div className="grid gap-6 md:grid-cols-2">
              {/* Top Performers */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Award className="h-5 w-5" />
                    優秀者
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {kpiData.topPerformers.map((student, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                          {index + 1}
                        </div>
                        <div>
                          <p className="font-medium">{student.name}</p>
                          <p className="text-sm text-muted-foreground">{student.subject}</p>
                        </div>
                      </div>
                      <Badge variant="outline" className="font-bold">
                        {student.score}点
                      </Badge>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Recent Tests */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="h-5 w-5" />
                    最近のテスト
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {kpiData.recentTests.map((test, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="font-medium">{test.subject}</p>
                          <p className="text-sm text-muted-foreground">{test.date}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium">{test.completed}/{test.total}</p>
                          <p className="text-sm text-muted-foreground">
                            {Math.round((test.completed / test.total) * 100)}%
                          </p>
                        </div>
                      </div>
                      <div className="w-full h-2 bg-gray-200 rounded-full">
                        <div 
                          className="h-full bg-primary rounded-full transition-all duration-300"
                          style={{ width: `${(test.completed / test.total) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
        </div>
      </div>
    </DashboardLayout>
  );
}