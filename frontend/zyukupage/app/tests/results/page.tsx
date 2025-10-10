'use client';

import { Suspense, useState } from 'react';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
  Edit,
  BarChart3
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { testApi, commentApi } from '@/lib/api-client';
import { toast } from 'sonner';

function TestResultsContent({ year, period }: { year: string; period: string }) {
  const [selectedStudents, setSelectedStudents] = useState<string[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterClassroom, setFilterClassroom] = useState<string>('all');
  const [sortOrder, setSortOrder] = useState<string>('rank');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [commentDialogOpen, setCommentDialogOpen] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<any>(null);
  const [studentComments, setStudentComments] = useState<{ [key: string]: string }>({});
  const [availableTemplates, setAvailableTemplates] = useState<{ [key: string]: any[] }>({});
  const [subjectScores, setSubjectScores] = useState<{ [key: string]: number }>({});
  const [useTemplate, setUseTemplate] = useState<{ [key: string]: boolean }>({});
  const [originalComments, setOriginalComments] = useState<{ [key: string]: string }>({});
  const [templateComments, setTemplateComments] = useState<{ [key: string]: string }>({});

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

  // バックエンドから統合テスト結果データを取得（生徒ID単位）
  const { 
    data: testResultsData, 
    isLoading: isLoadingResults,
    error: resultsError 
  } = useQuery({
    queryKey: ['integratedTestResults', year, period],
    queryFn: () => testApi.getIntegratedTestResults({ year, period }),
    enabled: !!year && !!period
  });

  const results = testResultsData?.results || [];

  // 生徒の点数入力状況を判定
  const getScoreInputStatus = (student: any) => {
    // 統合結果形式に対応
    if (student.combined_results && student.combined_results.total_score > 0) {
      return 'complete'; // 完了
    }
    return 'not_started'; // 未入力
  };

  // フィルターとソートを適用
  const getFilteredAndSortedResults = () => {
    let filtered = results;

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
    results.forEach((result: any) => {
      if (result.classroom_name) {
        classrooms.add(result.classroom_name);
      }
    });
    return Array.from(classrooms).sort((a, b) => a.localeCompare(b, 'ja'));
  };

  const availableClassrooms = getAvailableClassrooms();

  // 個別帳票ダウンロード
  const handleDownloadIndividualReport = async (studentId: string) => {
    try {
      const student = results.find((r: any) => r.student_id === studentId);
      if (!student) {
        toast.error('生徒データが見つかりません');
        return;
      }

      // 認証トークンを取得
      const token = localStorage.getItem('access_token');
      if (!token) {
        toast.error('認証トークンが見つかりません。再ログインしてください。');
        return;
      }

      // 新しいHTMLプレビューエンドポイントを開く
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace('/api', '') || 'https://kouzyoutest.com';
      const previewUrl = `${baseUrl}/api/scores/preview-individual-report/?studentId=${studentId}&year=${year}&period=${period}&token=${token}`;

      // 新しいタブで開く
      window.open(previewUrl, '_blank');

      toast.success(`${student.student_name}の成績表を開きました。ブラウザの印刷機能でPDF保存できます。`);
    } catch (error) {
      console.error('個別帳票プレビューエラー:', error);
      toast.error('帳票のプレビューに失敗しました');
    }
  };

  // 一括帳票ダウンロード
  const handleDownloadBulkReports = async () => {
    if (selectedStudents.length === 0) {
      toast.error('生徒を選択してください');
      return;
    }

    try {
      // 認証トークンを取得
      const token = localStorage.getItem('access_token');
      if (!token) {
        toast.error('認証トークンが見つかりません。再ログインしてください。');
        return;
      }

      // 新しいHTMLプレビューエンドポイントを開く
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace('/api', '') || 'https://kouzyoutest.com';
      const studentIdsParam = selectedStudents.join(',');
      const previewUrl = `${baseUrl}/api/scores/preview-bulk-reports/?year=${year}&period=${period}&studentIds=${studentIdsParam}&token=${token}`;

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

    // 既存のコメントを保存
    const existingComments: { [key: string]: string } = {};
    if (student.subject_results) {
      Object.entries(student.subject_results).forEach(([subject, data]: [string, any]) => {
        existingComments[subject] = data.comment || '';
      });
    }
    setOriginalComments(existingComments);

    try {
      // 点数に応じたコメントテンプレートを取得
      const scoreBasedResponse = await testApi.getScoreBasedComments({
        studentId: student.student_id,
        year: parseInt(year),
        period: period
      });

      if (scoreBasedResponse.success) {
        // テンプレートコメントを保存
        const templateComms: { [key: string]: string } = {};
        const useTemplateFlags: { [key: string]: boolean } = {};

        Object.entries(scoreBasedResponse.suggested_comments).forEach(([subject, data]: [string, any]) => {
          templateComms[subject] = data.template_text;
          // 既存のコメントがあればオリジナル、なければテンプレートを使用
          useTemplateFlags[subject] = !existingComments[subject];
        });

        setTemplateComments(templateComms);
        setUseTemplate(useTemplateFlags);

        // 初期表示用のコメントを設定
        const initialComments: { [key: string]: string } = {};
        Object.keys(templateComms).forEach(subject => {
          initialComments[subject] = useTemplateFlags[subject]
            ? templateComms[subject]
            : existingComments[subject];
        });
        setStudentComments(initialComments);
        setSubjectScores(scoreBasedResponse.subject_scores || {});
      } else {
        // フォールバック
        setStudentComments(existingComments);
        const useTemplateFlags: { [key: string]: boolean } = {};
        Object.keys(existingComments).forEach(subject => {
          useTemplateFlags[subject] = false;
        });
        setUseTemplate(useTemplateFlags);
      }
    } catch (error) {
      console.error('Failed to load score-based comments:', error);
      setStudentComments(existingComments);
      const useTemplateFlags: { [key: string]: boolean } = {};
      Object.keys(existingComments).forEach(subject => {
        useTemplateFlags[subject] = false;
      });
      setUseTemplate(useTemplateFlags);
    }

    // 科目別のコメントテンプレート（点数範囲別）を取得
    const templates: { [key: string]: any[] } = {};
    if (student.subject_results) {
      for (const subject of Object.keys(student.subject_results)) {
        try {
          const subjectTemplates = await commentApi.getSubjectCommentTemplates(subject);
          // 各テンプレートにIDを追加（score_rangeをIDとして使用）
          templates[subject] = subjectTemplates.map((t: any, idx: number) => ({
            ...t,
            id: `${subject}_${t.score_range}`,
            name: `${t.score_range}点`,
          }));
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
    const templateText = template.content || template.template_text || template.name || '';
    setTemplateComments(prev => ({
      ...prev,
      [subject]: templateText
    }));
    setStudentComments(prev => ({
      ...prev,
      [subject]: templateText
    }));
  };

  // テンプレート/オリジナル切り替え
  const handleToggleCommentType = (subject: string, useTemplateMode: boolean) => {
    setUseTemplate(prev => ({
      ...prev,
      [subject]: useTemplateMode
    }));

    setStudentComments(prev => ({
      ...prev,
      [subject]: useTemplateMode
        ? (templateComments[subject] || '')
        : (originalComments[subject] || '')
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
            テスト結果データ出力
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            {year}年度 {getPeriodLabel(period)}テストの結果閲覧と成績表ダウンロード
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
            <CardTitle>
              <span className="hidden sm:inline">生徒管理</span>
              <span className="sm:hidden">生徒</span>
              {" "}({filteredResults.length}名)
            </CardTitle>
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
              <Select value={filterClassroom} onValueChange={setFilterClassroom}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全教室</SelectItem>
                  {availableClassrooms.map((classroom) => (
                    <SelectItem key={classroom} value={classroom}>
                      {classroom}
                    </SelectItem>
                  ))}
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
                const statusConfig = {
                  complete: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200', text: '入力完了' },
                  partial: { icon: Clock, color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200', text: '部分入力' },
                  not_started: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200', text: '未入力' },
                  absent: { icon: XCircle, color: 'text-gray-600', bg: 'bg-gray-50', border: 'border-gray-200', text: '欠席' }
                }[inputStatus];
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
              <div key={subject} className="space-y-3 p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <Label className="text-sm font-medium">
                    {getSubjectLabel(subject)}のコメント
                    {subjectScores[subject] !== undefined && (
                      <span className="ml-2 text-xs text-gray-500">
                        (得点: {subjectScores[subject]}点)
                      </span>
                    )}
                  </Label>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      size="sm"
                      variant={useTemplate[subject] ? "default" : "outline"}
                      onClick={() => handleToggleCommentType(subject, true)}
                    >
                      テンプレート
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant={!useTemplate[subject] ? "default" : "outline"}
                      onClick={() => handleToggleCommentType(subject, false)}
                    >
                      オリジナル
                    </Button>
                  </div>
                </div>

                {useTemplate[subject] && availableTemplates[subject] && availableTemplates[subject].length > 0 && (
                  <Select onValueChange={(value) => {
                    const template = availableTemplates[subject].find(t => t.id.toString() === value);
                    if (template) handleApplyTemplate(subject, template);
                  }}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="別の点数範囲のテンプレートを選択" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableTemplates[subject].map((template) => (
                        <SelectItem key={template.id} value={template.id.toString()}>
                          {template.name || template.score_range} - {
                            template.content ?
                              (template.content.length > 30 ?
                                template.content.substring(0, 30) + '...' :
                                template.content
                              ) :
                              'テンプレート'
                          }
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}

                <Textarea
                  id={`comment-${subject}`}
                  value={studentComments[subject] || ''}
                  onChange={(e) => handleCommentChange(subject, e.target.value)}
                  placeholder={useTemplate[subject]
                    ? `${getSubjectLabel(subject)}のテンプレートコメント（編集可能）`
                    : `${getSubjectLabel(subject)}のオリジナルコメントを入力してください`}
                  rows={4}
                  className={useTemplate[subject] ? 'bg-blue-50/50' : ''}
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

export default function TestResultsPage() {
  const [selectedYear, setSelectedYear] = useState<string>('2025');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('summer');
  const [showResults, setShowResults] = useState(false);

  const years = [
    { value: '2025', label: '2025年度' },
    { value: '2026', label: '2026年度' },
    { value: '2027', label: '2027年度' },
  ];

  const periods = [
    { value: 'spring', label: '春期' },
    { value: 'summer', label: '夏期' },
    { value: 'winter', label: '冬期' },
  ];

  const handleViewResults = () => {
    if (selectedYear && selectedPeriod) {
      setShowResults(true);
    }
  };

  const handleBackToSelection = () => {
    setShowResults(false);
  };

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="animate-fade-in">
          {!showResults ? (
            <div className="space-y-6">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                  テスト結果データ出力
                </h1>
                <p className="text-gray-500 dark:text-gray-400 mt-1">
                  閲覧したい年度と期間を選択してください
                </p>
              </div>

              <Card className="max-w-md">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    年度・期間選択
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="year">年度</Label>
                    <Select value={selectedYear} onValueChange={setSelectedYear}>
                      <SelectTrigger>
                        <SelectValue placeholder="年度を選択" />
                      </SelectTrigger>
                      <SelectContent>
                        {years.map((year) => (
                          <SelectItem key={year.value} value={year.value}>
                            {year.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="period">時期</Label>
                    <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                      <SelectTrigger>
                        <SelectValue placeholder="時期を選択" />
                      </SelectTrigger>
                      <SelectContent>
                        {periods.map((period) => (
                          <SelectItem key={period.value} value={period.value}>
                            {period.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <Button 
                    onClick={handleViewResults}
                    disabled={!selectedYear || !selectedPeriod}
                    className="w-full"
                  >
                    テスト結果を表示
                  </Button>
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="space-y-4">
              <Button
                variant="outline"
                onClick={handleBackToSelection}
                className="mb-4"
              >
                ← 戻る
              </Button>
              <Suspense fallback={<div>Loading...</div>}>
                <TestResultsContent year={selectedYear} period={selectedPeriod} />
              </Suspense>
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}
