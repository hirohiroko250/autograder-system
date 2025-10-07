'use client';

export const dynamic = 'force-dynamic';

import { Suspense, useState } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { 
  Download, 
  FileText, 
  CheckCircle, 
  XCircle,
  Clock, 
  AlertTriangle, 
  Calendar,
  Filter,
  SortAsc,
  SortDesc,
  Users,
  FileOutput,
  Edit
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { testApi, commentApi } from '@/lib/api-client';
import { toast } from 'sonner';
import { useAuth } from '@/lib/auth-context';
import { PermissionGuard } from '@/components/auth/permission-guard';

interface TestDownloadPageProps {
  params: {
    year: string;
    period: string;
  };
}

function StudentManagementContent({ year, period }: { year: string; period: string }) {
  const { user } = useAuth();
  const [selectedStudents, setSelectedStudents] = useState<string[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterClassroom, setFilterClassroom] = useState<string>(user?.classroom_name || 'all');
  const [sortOrder, setSortOrder] = useState<string>('rank');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [commentDialogOpen, setCommentDialogOpen] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<any>(null);
  const [studentComments, setStudentComments] = useState<{ [key: string]: string }>({});
  const [availableTemplates, setAvailableTemplates] = useState<{ [key: string]: any[] }>({});
  const [subjectScores, setSubjectScores] = useState<{ [key: string]: number }>({});

  const getPeriodLabel = (period: string) => {
    switch (period) {
      case 'spring': return '春期';
      case 'summer': return '夏期';
      case 'winter': return '冬期';
      default: return period;
    }
  };

  const getSubjectLabel = (subject: string) => {
    switch (subject.toLowerCase()) {
      case 'japanese': return '国語';
      case 'math': return '算数';
      case 'mathematics': return '算数';
      case '国語': return '国語';
      case '算数': return '算数';
      case '数学': return '算数';
      default: return subject;
    }
  };

  // バックエンドから統合テスト結果データを取得（生徒ID単位・教室フィルター適用）
  const { 
    data: testResultsData, 
    isLoading: isLoadingResults,
    error: resultsError 
  } = useQuery({
    queryKey: ['integratedTestResults', year, period, user?.classroom_name],
    queryFn: () => {
      console.log('API Call params:', { year, period, classroom: user?.classroom_name });
      console.log('User info:', user);
      return testApi.getIntegratedTestResults({ 
        year, 
        period,
        classroom: user?.classroom_name 
      });
    },
    enabled: !!year && !!period && !!user
  });

  const results = testResultsData?.results || [];
  
  // デバッグログ
  console.log('API Response:', testResultsData);
  console.log('Results count:', results.length);
  console.log('First result classroom:', results[0]?.classroom_name);
  
  // 教室フィルタリングを強制適用（APIがフィルタリングしていない場合）
  const classroomFilteredResults = user?.classroom_name 
    ? results.filter((result: any) => result.classroom_name === user.classroom_name)
    : results;

  type ScoreInputStatus = 'complete' | 'partial' | 'not_started' | 'absent';

  // 生徒の点数入力状況を判定
  const getScoreInputStatus = (student: any): ScoreInputStatus => {
    if (student?.attendance_status === 'absent' || student?.is_absent === true || student?.attendance === false) {
      return 'absent';
    }

    if (student?.combined_results && student.combined_results.total_score > 0) {
      return 'complete';
    }

    const hasPartialScores = Object.values(student?.subject_results || {}).some((subject: any) => {
      const total = Number(subject?.total_score ?? 0);
      return !Number.isNaN(total) && total > 0;
    });
    if (hasPartialScores) {
      return 'partial';
    }

    return 'not_started';
  };

  // フィルターとソートを適用
  const getFilteredAndSortedResults = () => {
    let filtered = classroomFilteredResults;

    // ステータスフィルター
    if (filterStatus !== 'all') {
      filtered = filtered.filter((result: any) => {
        const status = getScoreInputStatus(result);
        return status === filterStatus;
      });
    }

    // 教室フィルター
    if (filterClassroom !== 'all') {
      filtered = filtered.filter((result: any) => {
        return result.classroom_name === filterClassroom;
      });
    }

    // ソート
    filtered = [...filtered].sort((a: any, b: any) => {
      let comparison = 0;
      
      switch (sortOrder) {
        case 'name':
          comparison = a.student_name.localeCompare(b.student_name, 'ja');
          break;
        case 'id':
          comparison = a.student_id.localeCompare(b.student_id);
          break;
        case 'total_score':
          comparison = (a.combined_results?.total_score || 0) - (b.combined_results?.total_score || 0);
          break;
        case 'classroom':
          comparison = (a.classroom_name || '').localeCompare(b.classroom_name || '', 'ja');
          break;
        case 'rank':
        default:
          comparison = (a.combined_results?.grade_rank || 999) - (b.combined_results?.grade_rank || 999);
          break;
      }
      
      return sortDirection === 'desc' ? -comparison : comparison;
    });

    return filtered;
  };

  const filteredResults = getFilteredAndSortedResults();

  // 利用可能な教室のリストを取得
  const getAvailableClassrooms = () => {
    const classrooms = new Set<string>();
    classroomFilteredResults.forEach((result: any) => {
      if (result.classroom_name) {
        classrooms.add(result.classroom_name);
      }
    });
    return Array.from(classrooms).sort((a, b) => a.localeCompare(b, 'ja'));
  };

  const availableClassrooms = getAvailableClassrooms();

  // 個別帳票ダウンロード（HTMLプレビュー方式）
  const handleDownloadIndividualReport = async (studentId: string) => {
    try {
      const student = classroomFilteredResults.find((r: any) => r.student_id === studentId);
      if (!student) {
        toast.error('生徒データが見つかりません');
        return;
      }

      // 新しいHTMLプレビューエンドポイントを開く
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace('/api', '') || 'http://162.43.55.80:8000';
      const previewUrl = `${baseUrl}/api/scores/preview-individual-report/?studentId=${studentId}&year=${year}&period=${period}`;

      // 新しいタブで開く
      window.open(previewUrl, '_blank');

      toast.success(`${student.student_name}の成績表を開きました。ブラウザの印刷機能でPDF保存できます。`);
    } catch (error) {
      console.error('個別帳票プレビューエラー:', error);
      toast.error('帳票のプレビューに失敗しました');
    }
  };

  // 一括帳票ダウンロード（HTMLプレビュー方式）
  const handleDownloadBulkReports = async () => {
    if (selectedStudents.length === 0) {
      toast.error('生徒を選択してください');
      return;
    }

    try {
      // 一括帳票プレビューエンドポイントを開く
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace('/api', '') || 'http://162.43.55.80:8000';

      // 全生徒選択の場合は教室IDでフィルタリング
      const isAllSelected = selectedStudents.length === filteredResults.length;
      let previewUrl = '';

      if (isAllSelected && user?.classroom_id) {
        previewUrl = `${baseUrl}/api/scores/preview-bulk-reports/?year=${year}&period=${period}&classroomId=${user.classroom_id}`;
      } else {
        // 個別選択の場合は各生徒のプレビューを順番に開く
        for (const studentId of selectedStudents) {
          const student = classroomFilteredResults.find((r: any) => r.student_id === studentId);
          const studentPreviewUrl = `${baseUrl}/api/scores/preview-individual-report/?studentId=${studentId}&year=${year}&period=${period}`;
          window.open(studentPreviewUrl, '_blank');
          // 連続して開く際のブラウザの制限を避けるため少し待機
          await new Promise(resolve => setTimeout(resolve, 500));
        }
        toast.success(`${selectedStudents.length}名の成績表を開きました。各タブから印刷できます。`);
        return;
      }

      // 新しいタブで開く
      window.open(previewUrl, '_blank');

      toast.success(`${selectedStudents.length}名の成績表を開きました。ブラウザの印刷機能でPDF保存できます。`);
    } catch (error) {
      console.error('一括帳票プレビューエラー:', error);
      toast.error('一括帳票のプレビューに失敗しました');
    }
  };

  const handleSelectStudent = (studentId: string, checked: boolean) => {
    if (checked) {
      setSelectedStudents(prev => [...prev, studentId]);
    } else {
      setSelectedStudents(prev => prev.filter(id => id !== studentId));
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedStudents(filteredResults.map((r: any) => r.student_id));
    } else {
      setSelectedStudents([]);
    }
  };

  // 生徒名をクリックした時のコメント編集ダイアログを開く
  const handleStudentNameClick = async (student: any) => {
    setSelectedStudent(student);
    
    try {
      // 点数に応じたコメントテンプレートを取得
      const scoreBasedResponse = await testApi.getScoreBasedComments({
        studentId: student.student_id,
        year: parseInt(year),
        period: period
      });

      if (scoreBasedResponse.success) {
        // 点数に応じて自動生成されたコメントを設定
        const comments: { [key: string]: string } = {};
        Object.entries(scoreBasedResponse.suggested_comments).forEach(([subject, data]: [string, any]) => {
          comments[subject] = data.template_text;
        });
        setStudentComments(comments);
        setSubjectScores(scoreBasedResponse.subject_scores || {});
      } else {
        // フォールバック: 既存のコメント取得方法
        const comments: { [key: string]: string } = {};
        if (student.subject_results) {
          Object.entries(student.subject_results).forEach(([subject, data]: [string, any]) => {
            comments[subject] = data.comment || `${subject}の成績についてコメントを入力してください。`;
          });
        }
        setStudentComments(comments);
      }
    } catch (error) {
      console.error('Failed to load score-based comments:', error);
      // エラー時のフォールバック
      const comments: { [key: string]: string } = {};
      if (student.subject_results) {
        Object.entries(student.subject_results).forEach(([subject, data]: [string, any]) => {
          comments[subject] = data.comment || `${subject}の成績についてコメントを入力してください。`;
        });
      }
      setStudentComments(comments);
    }
    
    // 科目別のコメントテンプレートを取得（手動選択用）
    const templates: { [key: string]: any[] } = {};
    if (student.subject_results) {
      for (const subject of Object.keys(student.subject_results)) {
        try {
          const templateResponse = await commentApi.getCommentTemplates({ subject });
          templates[subject] = templateResponse.results || [];
        } catch (error) {
          console.error(`Failed to load templates for ${subject}:`, error);
          templates[subject] = [];
        }
      }
    }
    
    setAvailableTemplates(templates);
    setCommentDialogOpen(true);
  };

  // コメントを保存
  const handleSaveComments = async () => {
    try {
      await testApi.saveStudentComments({
        studentId: selectedStudent.student_id,
        year: parseInt(year),
        period: period,
        comments: studentComments
      });
      
      toast.success('コメントを保存しました');
      setCommentDialogOpen(false);
    } catch (error) {
      console.error('コメント保存エラー:', error);
      toast.error('コメントの保存に失敗しました');
    }
  };

  // コメントを更新
  const handleCommentChange = (subject: string, comment: string) => {
    setStudentComments(prev => ({
      ...prev,
      [subject]: comment
    }));
  };

  // コメントテンプレートを適用
  const handleApplyTemplate = (subject: string, template: any) => {
    setStudentComments(prev => ({
      ...prev,
      [subject]: template.template_text || template.content || template.name || ''
    }));
  };

  // ローディング状態
  if (isLoadingResults) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Clock className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">生徒データを読み込み中...</p>
        </div>
      </div>
    );
  }

  // エラー状態
  if (resultsError) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <AlertTriangle className="h-8 w-8 text-red-600 mx-auto mb-4" />
          <p className="text-red-600 mb-4">生徒データの取得に失敗しました</p>
          <Button onClick={() => window.location.reload()}>
            再読み込み
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            生徒管理・帳票ダウンロード
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            {year}年度 {getPeriodLabel(period)}テスト - {user?.classroom_name || '教室'}の生徒管理と成績表ダウンロード
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleDownloadBulkReports} variant="outline" disabled={selectedStudents.length === 0}>
            <Download className="h-4 w-4 mr-2" />
            一括ダウンロード ({selectedStudents.length})
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>生徒管理 ({filteredResults.length}名)</CardTitle>
            <div className="flex items-center gap-2">
              <Checkbox
                id="select-all"
                checked={selectedStudents.length === filteredResults.length && filteredResults.length > 0}
                onCheckedChange={handleSelectAll}
              />
              <Label htmlFor="select-all" className="text-sm">
                全選択
              </Label>
            </div>
          </div>
          
          {/* フィルタリングとソートコントロール */}
          <div className="flex flex-wrap items-center gap-4 pt-4 border-t">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-500" />
              <Label className="text-sm font-medium">ステータス:</Label>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全て</SelectItem>
                  <SelectItem value="complete">入力完了</SelectItem>
                  <SelectItem value="partial">部分入力</SelectItem>
                  <SelectItem value="not_started">未入力</SelectItem>
                  <SelectItem value="absent">欠席</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-center gap-2">
              <Label className="text-sm font-medium">教室:</Label>
              <Select value={filterClassroom} onValueChange={setFilterClassroom} disabled>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={user?.classroom_name || 'all'}>
                    {user?.classroom_name || '教室未設定'}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-center gap-2">
              <Label className="text-sm font-medium">並び順:</Label>
              <Select value={sortOrder} onValueChange={setSortOrder}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="rank">順位</SelectItem>
                  <SelectItem value="name">名前</SelectItem>
                  <SelectItem value="id">生徒ID</SelectItem>
                  <SelectItem value="total_score">合計点</SelectItem>
                  <SelectItem value="classroom">教室</SelectItem>
                </SelectContent>
              </Select>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')}
              >
                {sortDirection === 'asc' ? <SortAsc className="h-4 w-4" /> : <SortDesc className="h-4 w-4" />}
              </Button>
            </div>
            
            <div className="flex items-center gap-2 ml-auto">
              <Users className="h-4 w-4 text-gray-500" />
              <span className="text-sm text-gray-600">
                表示中: {filteredResults.length}名 | 選択中: {selectedStudents.length}名
              </span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredResults.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p className="text-lg mb-2">該当する生徒がいません</p>
                <p className="text-sm">
                  フィルター条件を変更してください
                </p>
              </div>
            ) : (
              filteredResults.map((result: any) => {
                const inputStatus = getScoreInputStatus(result);
                const statusConfigMap: Record<ScoreInputStatus, {
                  icon: typeof CheckCircle;
                  color: string;
                  bg: string;
                  border: string;
                  text: string;
                }> = {
                  complete: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200', text: '入力完了' },
                  partial: { icon: Clock, color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200', text: '部分入力' },
                  not_started: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200', text: '未入力' },
                  absent: { icon: XCircle, color: 'text-gray-600', bg: 'bg-gray-50', border: 'border-gray-200', text: '欠席' }
                };
                const statusConfig = statusConfigMap[inputStatus];
                const StatusIcon = statusConfig.icon;

                return (
                  <div
                    key={result.student_id}
                    className={`flex items-center gap-4 p-4 border rounded-lg transition-colors ${
                      selectedStudents.includes(result.student_id) 
                        ? 'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-700' 
                        : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                    } ${statusConfig.border}`}
                  >
                    <Checkbox
                      checked={selectedStudents.includes(result.student_id)}
                      onCheckedChange={(checked) => handleSelectStudent(result.student_id, checked as boolean)}
                    />
                    
                    {/* 入力状況インジケーター */}
                    <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${statusConfig.bg} ${statusConfig.border} border`}>
                      <StatusIcon className={`h-4 w-4 ${statusConfig.color}`} />
                      <span className={`text-xs font-medium ${statusConfig.color}`}>
                        {statusConfig.text}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-4 flex-1">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                        {result.combined_results?.grade_rank || '-'}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleStudentNameClick(result)}
                            className="font-medium text-blue-600 hover:text-blue-800 hover:underline cursor-pointer flex items-center gap-1"
                          >
                            {result.student_name}
                            <Edit className="h-3 w-3" />
                          </button>
                          <Badge variant="outline">{result.grade}年生</Badge>
                          <Badge variant="outline">{result.classroom_name}</Badge>
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          ID: {result.student_id} | {result.school_name} | 学年平均: {result.combined_results?.grade_average?.toFixed(1)}点 | 塾内平均: {result.combined_results?.school_average?.toFixed(1)}点
                        </p>
                        <div className="flex gap-2 mt-1">
                          {Object.entries(result.subject_results || {}).map(([subject, data]: [string, any]) => (
                            <Badge key={subject} variant="secondary" className="text-xs">
                              {getSubjectLabel(subject)}: {data.total_score}点 (学年{data.rankings.grade_rank}位)
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-xl font-bold">{result.combined_results?.total_score || '-'}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          学年{result.combined_results?.grade_rank || '-'}位/{result.combined_results?.grade_total || '-'}名
                        </p>
                        <p className="text-xs text-gray-400">
                          塾内{result.combined_results?.school_rank || '-'}位/{result.combined_results?.school_total || '-'}名
                        </p>
                      </div>
                      <div className="flex flex-col gap-1">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDownloadIndividualReport(result.student_id)}
                          disabled={inputStatus === 'not_started' || inputStatus === 'absent'}
                        >
                          <Download className="h-3 w-3 mr-1" />
                          帳票
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </CardContent>
      </Card>

      {/* コメント編集ダイアログ */}
      <Dialog open={commentDialogOpen} onOpenChange={setCommentDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>コメント編集</DialogTitle>
            <DialogDescription>
              {selectedStudent?.student_name}のコメントを編集します
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {selectedStudent && Object.entries(selectedStudent.subject_results || {}).map(([subject, data]: [string, any]) => (
              <div key={subject} className="space-y-3">
                <div className="space-y-2">
                  <Label htmlFor={`comment-${subject}`} className="text-sm font-medium">
                    {subject}のコメント
                    {subjectScores[subject] && (
                      <span className="ml-2 text-xs text-gray-500">
                        (得点: {subjectScores[subject]}点)
                      </span>
                    )}
                  </Label>
                  {availableTemplates[subject] && availableTemplates[subject].length > 0 && (
                    <Select onValueChange={(value) => {
                      const template = availableTemplates[subject].find(t => t.id.toString() === value);
                      if (template) handleApplyTemplate(subject, template);
                    }}>
                      <SelectTrigger className="w-48">
                        <SelectValue placeholder="テンプレートを選択" />
                      </SelectTrigger>
                      <SelectContent>
                        {availableTemplates[subject].map((template) => (
                          <SelectItem key={template.id} value={template.id.toString()}>
                            {template.template_text || template.content ? 
                              ((template.template_text || template.content).length > 40 ? 
                                (template.template_text || template.content).substring(0, 40) + '...' : 
                                (template.template_text || template.content)
                              ) : 
                              (template.name || 'テンプレート')
                            }
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>
                <Textarea
                  id={`comment-${subject}`}
                  value={studentComments[subject] || ''}
                  onChange={(e) => handleCommentChange(subject, e.target.value)}
                  placeholder={`${subject}の成績についてコメントを入力してください。`}
                  rows={3}
                />
              </div>
            ))}
            <div className="flex justify-end gap-2 pt-4">
              <Button
                variant="outline"
                onClick={() => setCommentDialogOpen(false)}
              >
                キャンセル
              </Button>
              <Button onClick={handleSaveComments}>
                保存
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function StudentManagementPage({ params }: TestDownloadPageProps) {
  const { year, period } = params;

  return (
    <DashboardLayout>
      <PermissionGuard permission="can_view_reports">
        <div className="animate-fade-in">
          <Suspense fallback={<div>Loading...</div>}>
            <StudentManagementContent year={year} period={period} />
          </Suspense>
        </div>
      </PermissionGuard>
    </DashboardLayout>
  );
}
