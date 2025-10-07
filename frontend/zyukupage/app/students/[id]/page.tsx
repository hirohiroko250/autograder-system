'use client';

import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, User, GraduationCap, Calendar, BookOpen, Trophy, TrendingUp, MessageSquare } from 'lucide-react';
import { useState } from 'react';
import { studentApi, testApi } from '@/lib/api-client';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { CommentManager } from '@/components/comments';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface StudentDetailPageProps {
  params: {
    id: string;
  };
}

export default function StudentDetailPage({ params }: StudentDetailPageProps) {
  const router = useRouter();
  const [selectedYear, setSelectedYear] = useState('2025');
  const [selectedPeriod, setSelectedPeriod] = useState('all');

  const years = [
    { value: '2025', label: '2025年度' },
          { value: '2026', label: '2026年度' },
          { value: '2027', label: '2027年度' },
    
    
  ];

  const periods = [
    { value: 'all', label: '全期間' },
    { value: 'spring', label: '春期' },
    { value: 'summer', label: '夏期' },
    { value: 'winter', label: '冬期' },
  ];

  // 生徒情報取得
  const { data: student, isLoading: isStudentLoading } = useQuery({
    queryKey: ['student', params.id],
    queryFn: async () => {
      const response = await studentApi.getStudents({ search: params.id, page_size: 10000 });
      const foundStudent = response.results.find((s: any) => s.student_id === params.id);
      if (!foundStudent) {
        throw new Error('生徒が見つかりません');
      }
      return foundStudent;
    },
  });

  // 受講履歴取得
  const { data: enrollments } = useQuery({
    queryKey: ['student-enrollments', params.id],
    queryFn: async () => {
      if (!student) return [];
      const response = await studentApi.getStudentEnrollments(student.id);
      return response;
    },
    enabled: !!student,
  });

  // テスト結果取得
  const { data: testResults } = useQuery({
    queryKey: ['test-results', params.id, selectedYear, selectedPeriod],
    queryFn: async () => {
      const params_obj: any = { 
        year: selectedYear,
        student_id: params.id 
      };
      if (selectedPeriod !== 'all') {
        params_obj.period = selectedPeriod;
      }
      const response = await testApi.getTestResults(params_obj);
      return response.results;
    },
    enabled: !!student,
  });

  if (isStudentLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p>読み込み中...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (!student) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <p className="text-lg text-muted-foreground">生徒が見つかりません</p>
            <Button onClick={() => router.back()} className="mt-4">
              戻る
            </Button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'enrolled': return 'bg-green-100 text-green-800';
      case 'new': return 'bg-blue-100 text-blue-800';
      case 'withdrawn': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'enrolled': return '入会';
      case 'new': return '新規';
      case 'withdrawn': return '退会';
      default: return status;
    }
  };

  const getPeriodLabel = (period: string) => {
    switch (period) {
      case 'spring': return '春期';
      case 'summer': return '夏期';
      case 'winter': return '冬期';
      default: return period;
    }
  };

  // 教科別データ処理
  const processSubjectData = (results: any[]) => {
    if (!results || results.length === 0) return {};
    
    const subjects: any = {
      japanese: { name: '国語', results: [], average: 0, latest: 0, trend: 0 },
      math: { name: '算数/数学', results: [], average: 0, latest: 0, trend: 0 }
    };
    
    console.log('Processing test results:', results);
    
    results.forEach(result => {
      // より柔軟な教科判定
      const subject = result.test_name || result.test_subject || result.subject || '';
      console.log('Subject detected:', subject, 'for result:', result);
      
      if (subject.includes('国語') || subject === 'japanese' || subject === 'Japanese') {
        subjects.japanese.results.push(result);
      } else if (subject.includes('算数') || subject.includes('数学') || subject === 'math' || subject === 'mathematics' || subject === 'Math') {
        subjects.math.results.push(result);
      }
    });
    
    console.log('Processed subjects:', subjects);
    
    // 各教科の統計計算
    Object.keys(subjects).forEach(key => {
      const subjectData = subjects[key];
      if (subjectData.results.length > 0) {
        // 最新の日付順にソート
        subjectData.results.sort((a: any, b: any) => {
          const dateA = new Date(a.test_info?.year || a.year, a.test_info?.period || a.period === 'summer' ? 7 : 0);
          const dateB = new Date(b.test_info?.year || b.year, b.test_info?.period || b.period === 'summer' ? 7 : 0);
          return dateB.getTime() - dateA.getTime();
        });
        
        // 平均点
        subjectData.average = Math.round(
          subjectData.results.reduce((sum: number, r: any) => sum + (r.total_score || 0), 0) / subjectData.results.length
        );
        // 最新の点数
        subjectData.latest = subjectData.results[0]?.total_score || 0;
        // 傾向（最新と前回の差）
        if (subjectData.results.length >= 2) {
          subjectData.trend = (subjectData.results[0]?.total_score || 0) - (subjectData.results[1]?.total_score || 0);
        }
      }
    });
    
    return subjects;
  };
  
  const subjectData = processSubjectData(testResults || []);
  
  // 全体平均点計算
  const averageScore = testResults && testResults.length > 0 
    ? Math.round(testResults.reduce((sum: number, result: any) => sum + (result.total_score || 0), 0) / testResults.length)
    : 0;

  return (
    <DashboardLayout>
      <div className="space-y-6 animate-fade-in">
        {/* ヘッダー */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/students">
              <Button variant="ghost" size="sm" className="rounded-xl">
                <ArrowLeft className="h-4 w-4 mr-2" />
                生徒一覧に戻る
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold">{student.name}</h1>
              <p className="text-muted-foreground">生徒ID: {student.student_id}</p>
            </div>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {/* 生徒基本情報 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                基本情報
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <GraduationCap className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">学年:</span>
                <span className="font-medium">{student.grade}</span>
              </div>
              <div className="flex items-center gap-3">
                <BookOpen className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">教室:</span>
                <span className="font-medium">{student.classroom_name}</span>
              </div>
              <div className="flex items-center gap-3">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">登録日:</span>
                <span className="font-medium">
                  {new Date(student.created_at).toLocaleDateString('ja-JP')}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* 成績サマリー */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="h-5 w-5" />
                成績サマリー
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary">{averageScore}</div>
                  <p className="text-sm text-muted-foreground">総合平均点</p>
                </div>
                <Separator />
                
                {/* 教科別平均点 */}
                <div className="space-y-3">
                  {Object.entries(subjectData).map(([key, data]: [string, any]) => (
                    data.results.length > 0 && (
                      <div key={key} className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">{data.name}</span>
                        <div className="text-right">
                          <div className="font-semibold">{data.average}点</div>
                          <div className="text-xs text-muted-foreground">
                            {data.results.length}回受験
                          </div>
                        </div>
                      </div>
                    )
                  ))}
                </div>
                
                <Separator />
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-lg font-semibold">{testResults?.length || 0}</div>
                    <p className="text-xs text-muted-foreground">総受験回数</p>
                  </div>
                  <div>
                    <div className="text-lg font-semibold">{enrollments?.length || 0}</div>
                    <p className="text-xs text-muted-foreground">受講期間</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 最新の成績傾向 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                成績傾向
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(subjectData).map(([key, data]: [string, any]) => (
                  data.results.length > 0 && (
                    <div key={key}>
                      <h4 className="font-semibold text-sm mb-2">{data.name}</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-muted-foreground">最新の成績</span>
                          <span className="font-medium">{data.latest}点</span>
                        </div>
                        {data.results.length >= 2 && (
                          <>
                            <div className="flex justify-between items-center">
                              <span className="text-sm text-muted-foreground">前回の成績</span>
                              <span className="font-medium">{data.results[1]?.total_score || 0}点</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-sm text-muted-foreground">変化</span>
                              <span className={`font-medium ${
                                data.trend > 0 ? 'text-green-600' : data.trend < 0 ? 'text-red-600' : 'text-gray-600'
                              }`}>
                                {data.trend > 0 ? '+' : ''}{data.trend}点
                              </span>
                            </div>
                          </>
                        )}
                      </div>
                      {key === 'japanese' && Object.keys(subjectData).length > 1 && subjectData.math.results.length > 0 && (
                        <Separator className="mt-3" />
                      )}
                    </div>
                  )
                ))}
                
                {Object.values(subjectData).every((data: any) => data.results.length === 0) && (
                  <p className="text-sm text-muted-foreground text-center">
                    成績データが不足しています
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 受講履歴 */}
        <Card>
          <CardHeader>
            <CardTitle>受講履歴</CardTitle>
          </CardHeader>
          <CardContent>
            {enrollments && enrollments.length > 0 ? (
              <div className="space-y-3">
                {enrollments.map((enrollment: any) => (
                  <div
                    key={enrollment.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-4">
                      <div>
                        <p className="font-medium">{enrollment.year}年度</p>
                        <p className="text-sm text-muted-foreground">
                          {getPeriodLabel(enrollment.period)}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">登録日</p>
                      <p className="font-medium">
                        {new Date(enrollment.enrolled_at).toLocaleDateString('ja-JP')}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">
                受講履歴がありません
              </p>
            )}
          </CardContent>
        </Card>

        {/* タブ式コンテンツ */}
        <Tabs defaultValue="test-results" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="test-results">
              <Trophy className="h-4 w-4 mr-2" />
              テスト結果
            </TabsTrigger>
            <TabsTrigger value="comments">
              <MessageSquare className="h-4 w-4 mr-2" />
              コメント管理
            </TabsTrigger>
          </TabsList>

          <TabsContent value="test-results">
            {/* 教科別最新成績カード */}
            {Object.entries(subjectData).map(([key, data]: [string, any]) => 
              data.results.length > 0 && (
                <Card key={key} className="mb-4 border-l-4 border-l-primary">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <BookOpen className="h-5 w-5 text-primary" />
                        <h3 className="text-lg font-semibold">{data.name}</h3>
                        <Badge variant="secondary">
                          {data.results[0]?.year}年度 {getPeriodLabel(data.results[0]?.period)}
                        </Badge>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-primary">{data.latest}点</div>
                        <div className="text-sm text-muted-foreground">
                          満点: {data.results[0]?.max_score || 100}点
                        </div>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-4 gap-4">
                      <div className="text-center">
                        <div className="text-lg font-semibold text-gray-600">
                          {data.results[0]?.averages?.grade_average ? Math.round(data.results[0].averages.grade_average) : '-'}点
                        </div>
                        <div className="text-xs text-muted-foreground">学年平均</div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-lg font-semibold text-purple-600">
                          {data.results[0]?.rankings?.deviation_score || '-'}
                        </div>
                        <div className="text-xs text-muted-foreground">偏差値</div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-lg font-semibold text-green-600">
                          {data.results[0]?.rankings?.grade_rank ? `${data.results[0].rankings.grade_rank}位` : '-'}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {data.results[0]?.rankings?.grade_total ? `/${data.results[0].rankings.grade_total}名中` : '学年順位'}
                        </div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-lg font-semibold text-orange-600">
                          {Math.round((data.latest / (data.results[0]?.max_score || 100)) * 100)}%
                        </div>
                        <div className="text-xs text-muted-foreground">正答率</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            )}

            {/* 教科別詳細分析 */}
            {Object.entries(subjectData).map(([key, data]: [string, any]) => (
              data.results.length > 0 && (
                <Card key={key} className="mb-6">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BookOpen className="h-5 w-5" />
                      {data.name} - 詳細分析
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {data.results.map((result: any) => (
                        <div key={result.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                          <div className="flex justify-between items-start mb-4">
                            <div>
                              <h4 className="font-semibold text-lg mb-1">
                                {result.year}年度 {getPeriodLabel(result.period)}
                              </h4>
                              <div className="text-sm text-muted-foreground">
                                受験日: {result.test_date || `${result.year}/7/28`}
                              </div>
                            </div>
                            <Badge variant="outline" className="text-lg px-3 py-1">
                              {result.total_score}点 / {result.max_score || 100}点
                            </Badge>
                          </div>
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                              <h5 className="font-medium mb-3 text-gray-700">成績詳細</h5>
                              <div className="space-y-2">
                                <div className="flex justify-between">
                                  <span className="text-sm text-muted-foreground">正答率</span>
                                  <span className="font-semibold">{Math.round((result.total_score / (result.max_score || 100)) * 100)}%</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-sm text-muted-foreground">満点からの差</span>
                                  <span className="font-semibold text-red-600">-{(result.max_score || 100) - result.total_score}点</span>
                                </div>
                              </div>
                            </div>
                            <div>
                              <h5 className="font-medium mb-3 text-gray-700">統計情報</h5>
                              <div className="space-y-3">
                                <div className="p-2 bg-gray-50 rounded">
                                  <div className="flex justify-between">
                                    <span className="text-sm text-muted-foreground">学年平均との差</span>
                                    <span className={`font-semibold ${
                                      result.averages?.grade_average && result.total_score > result.averages.grade_average 
                                        ? 'text-green-600' 
                                        : 'text-red-600'
                                    }`}>
                                      {result.averages?.grade_average 
                                        ? `${result.total_score > result.averages.grade_average ? '+' : ''}${result.total_score - Math.round(result.averages.grade_average)}点`
                                        : '-'
                                      }
                                    </span>
                                  </div>
                                  <div className="text-xs text-muted-foreground mt-1">
                                    学年平均: {result.averages?.grade_average ? Math.round(result.averages.grade_average) : '-'}点
                                  </div>
                                </div>
                                
                                {result.rankings?.deviation_score && (
                                  <div className="p-2 bg-purple-50 rounded">
                                    <div className="flex justify-between">
                                      <span className="text-sm text-muted-foreground">偏差値</span>
                                      <span className="font-bold text-purple-600 text-lg">{result.rankings.deviation_score}</span>
                                    </div>
                                  </div>
                                )}
                                
                                {result.rankings?.grade_rank && result.rankings?.grade_total && (
                                  <div className="p-2 bg-green-50 rounded">
                                    <div className="flex justify-between">
                                      <span className="text-sm text-muted-foreground">学年順位</span>
                                      <span className="font-bold text-green-600 text-lg">
                                        {result.rankings.grade_rank}位 / {result.rankings.grade_total}名
                                      </span>
                                    </div>
                                    <div className="text-xs text-muted-foreground mt-1">
                                      上位 {Math.round((result.rankings.grade_rank / result.rankings.grade_total) * 100)}%
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                          
                          {/* 大問別得点 */}
                          {result.scores?.question_details && result.scores.question_details.length > 0 && (
                            <div className="mt-6 pt-4 border-t">
                              <h5 className="font-medium mb-3 text-gray-700">大問別得点</h5>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                {result.scores.question_details.map((detail: any, index: number) => {
                                  const percentage = (detail.score / detail.max_score) * 100;
                                  const average = result.averages?.question_averages?.[detail.question_number];
                                  return (
                                    <div key={index} className={`p-3 rounded-lg border-2 ${
                                      percentage === 100 
                                        ? 'border-green-200 bg-green-50' 
                                        : percentage >= 70 
                                        ? 'border-blue-200 bg-blue-50'
                                        : percentage >= 50
                                        ? 'border-yellow-200 bg-yellow-50'
                                        : 'border-red-200 bg-red-50'
                                    }`}>
                                      <div className="text-center">
                                        <div className="text-xs font-medium text-gray-600 mb-1">大問{detail.question_number}</div>
                                        <div className="text-lg font-bold">{detail.score}/{detail.max_score}</div>
                                        <div className={`text-xs font-medium ${
                                          percentage === 100 
                                            ? 'text-green-600' 
                                            : percentage >= 70 
                                            ? 'text-blue-600'
                                            : percentage >= 50
                                            ? 'text-yellow-600'
                                            : 'text-red-600'
                                        }`}>
                                          {Math.round(percentage)}%
                                        </div>
                                        {average && (
                                          <div className="text-xs text-muted-foreground mt-1">
                                            平均: {Math.round(average * 10) / 10}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )
            ))}
            
            {/* 全体テスト結果（教科別に分けられないもの） */}
            <Card>
              <CardHeader>
                <CardTitle>全テスト結果一覧</CardTitle>
              </CardHeader>
              <CardContent>
                {testResults && testResults.length > 0 ? (
                  <div className="space-y-3">
                    {testResults.map((result: any) => (
                      <div
                        key={result.id}
                        className="flex items-center justify-between p-3 border rounded-lg"
                      >
                        <div className="flex items-center gap-4">
                          <div>
                            <p className="font-medium">
                              {result.test_name || `${result.test_subject === 'japanese' ? '国語' : result.test_subject === 'math' ? '算数/数学' : result.test_subject}`}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              {result.year}年度 {getPeriodLabel(result.period)}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-primary">{result.total_score}点</p>
                          <p className="text-sm text-muted-foreground">
                            満点: {result.max_score || 100}点
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-muted-foreground py-8">
                    テスト結果がありません
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="comments">
            {student && (
              <CommentManager
                studentId={student.id.toString()}
                studentName={student.name}
                showTestComments={true}
              />
            )}
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}