'use client';

import React from 'react';
import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
// import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { IndividualProblemTable } from './individual-problem-table';
import { ScoreImportModal } from './score-import-modal';
import { DeadlineBanner } from '@/components/ui/deadline-banner';
import { 
  ChevronLeft, 
  ChevronRight, 
  CheckCircle, 
  Upload, 
  Download,
  GraduationCap, 
  BookOpen,
  Users,
  FileCheck,
  AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';
import { useQuery } from '@tanstack/react-query';
import { testApi, commentApi, studentApi } from '@/lib/api-client';

interface ScoreEntryWizardProps {
  year: string;
  period?: string;
}

export function ScoreEntryWizard({ year, period }: ScoreEntryWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedGrade, setSelectedGrade] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [currentPeriod, setCurrentPeriod] = useState('');
  const [selectedStudents, setSelectedStudents] = useState<string[]>([]);
  const [scores, setScores] = useState<Record<string, any>>({});
  const [scoreImportModalOpen, setScoreImportModalOpen] = useState(false);
  const [isDeadlinePassed, setIsDeadlinePassed] = useState(false);

  const steps = [
    { id: 'grade', title: '学年選択', icon: GraduationCap },
    { id: 'subject', title: '教科選択', icon: BookOpen },
    { id: 'students', title: '生徒選択', icon: Users },
    { id: 'scores', title: 'スコア入力', icon: FileCheck },
    { id: 'confirm', title: '確認', icon: CheckCircle },
  ];

  const grades = [
    { value: 'elementary_1', label: '小学1年生', level: 'elementary' },
    { value: 'elementary_2', label: '小学2年生', level: 'elementary' },
    { value: 'elementary_3', label: '小学3年生', level: 'elementary' },
    { value: 'elementary_4', label: '小学4年生', level: 'elementary' },
    { value: 'elementary_5', label: '小学5年生', level: 'elementary' },
    { value: 'elementary_6', label: '小学6年生', level: 'elementary' },
    { value: 'middle_1', label: '中学1年生', level: 'middle_school' },
    { value: 'middle_2', label: '中学2年生', level: 'middle_school' },
    { value: 'middle_3', label: '中学3年生', level: 'middle_school' },
  ];

  const getSubjectsForGrade = (gradeValue: string) => {
    const grade = grades.find(g => g.value === gradeValue);
    if (!grade) return [];
    
    if (grade.level === 'elementary') {
      return [
        { value: 'japanese', label: '国語' },
        { value: 'math', label: '算数' }
      ];
    } else if (grade.level === 'middle_school') {
      return [
        { value: 'english', label: '英語' },
        { value: 'mathematics', label: '数学' }
      ];
    }
    return [];
  };

  const availableSubjects = selectedGrade ? getSubjectsForGrade(selectedGrade) : [];
  
  // 現在の時期を自動判定
  useEffect(() => {
    const now = new Date();
    const month = now.getMonth() + 1; // 1-12
    
    let period = 'summer'; // デフォルト
    if (month >= 1 && month <= 3) {
      period = 'winter';
    } else if (month >= 4 && month <= 6) {
      period = 'spring';
    } else if (month >= 7 && month <= 12) {
      period = 'summer';
    }
    
    setCurrentPeriod(period);
  }, []);

  // 利用可能なテストを取得
  const { data: availableTests, isLoading: testsLoading } = useQuery({
    queryKey: ['available-tests', year, currentPeriod, selectedGrade],
    queryFn: async () => {
      if (!selectedGrade || !currentPeriod) return [];
      
      try {
        console.log('🔍 Fetching tests for:', { year, period: currentPeriod, selectedGrade });
        const response = await testApi.getTestDefinitions({ year, period: currentPeriod });
        console.log('🔍 Raw API response:', response.results?.length, 'tests found');
        
        const filteredTests = response.results.filter((test: any) => {
          const matches = test.grade_level === selectedGrade;
          console.log(`🔍 Test ${test.id}: grade_level=${test.grade_level}, selectedGrade=${selectedGrade}, matches=${matches}`);
          return matches;
        });
        
        console.log('🔍 Filtered tests:', filteredTests.length, 'tests match criteria');
        return filteredTests;
      } catch (error) {
        console.error('❌ Failed to fetch tests:', error);
        return [];
      }
    },
    enabled: !!selectedGrade && !!currentPeriod,
  });

  // テストスケジュールから締切情報を取得
  const { data: testSchedules } = useQuery({
    queryKey: ['test-schedules', year, currentPeriod],
    queryFn: async () => {
      if (!currentPeriod) return [];
      try {
        const response = await testApi.getTestSchedules({ year, period: currentPeriod });
        return response.results;
      } catch (error) {
        console.error('Failed to fetch test schedules:', error);
        return [];
      }
    },
    enabled: !!currentPeriod,
  });

  // 締切日チェック
  useEffect(() => {
    if (testSchedules && testSchedules.length > 0) {
      const currentSchedule = testSchedules[0];
      const now = new Date();
      const deadline = new Date(currentSchedule.deadline_at);
      setIsDeadlinePassed(now > deadline);
    }
  }, [testSchedules]);

  // 選択されたテストの詳細情報 - 最新のテスト（ID最大）を選択
  const selectedTest = availableTests?.filter((test: any) => 
    test.subject === selectedSubject
  ).sort((a: any, b: any) => b.id - a.id)[0]; // ID降順で最初（最新）を選択

  // 大問情報を取得
  const { data: questionGroupsData, isLoading: isLoadingQuestions, error: questionGroupsError } = useQuery({
    queryKey: ['question-groups', selectedTest?.id],
    queryFn: async () => {
      if (!selectedTest?.id) return null;
      
      try {
        const response = await testApi.getQuestionGroups(selectedTest.id);
        
        if (response && response.groups && response.groups.length > 0) {
          console.log(`✅ Loaded ${response.groups.length} question groups from backend (Total: ${response.total_max_score}点)`);
          return response;
        } else {
          console.warn('⚠️ No question groups found in API response, using fallback');
        }
      } catch (error) {
        console.error('❌ Failed to fetch question groups from API:', error);
      }
      
      // フォールバック: デフォルトの大問構造を作成
      const defaultProblemCount = selectedSubject === 'japanese' || selectedSubject === 'math' ? 5 :
                                 selectedSubject === 'english' || selectedSubject === 'mathematics' ? 6 : 5;
      
      const defaultGroups = Array.from({ length: Math.min(defaultProblemCount, 10) }, (_, i) => ({
        id: null,
        group_number: i + 1,
        max_score: 20,
        title: `大問${i + 1}`,
        question_count: 0
      }));
      
      return {
        test_id: selectedTest.id,
        total_max_score: defaultGroups.reduce((sum, group) => sum + group.max_score, 0),
        groups: defaultGroups
      };
    },
    enabled: !!selectedTest?.id,
    retry: 2
  });

  // レスポンスから大問グループを抽出
  const questionGroups = questionGroupsData?.groups || [];

  // 個別問題を取得
  const { data: individualProblems, isLoading: isLoadingProblems } = useQuery({
    queryKey: ['individual-problems', selectedTest?.id],
    queryFn: async () => {
      if (!selectedTest?.id) return null;
      try {
        const response = await commentApi.getIndividualProblems(selectedTest.id);
        return response.results;
      } catch (error) {
        console.error('Failed to fetch individual problems:', error);
        // デフォルト問題を作成して再取得
        try {
          await commentApi.createDefaultProblems(selectedTest.id, 6, 10);
          const retryResponse = await commentApi.getIndividualProblems(selectedTest.id);
          return retryResponse.results;
        } catch (createError) {
          console.error('Failed to create default problems:', createError);
          return [];
        }
      }
    },
    enabled: !!selectedTest?.id
  });
  
  // 実際の生徒データを取得
  const { data: studentsData } = useQuery({
    queryKey: ['students-for-score-entry', year, currentPeriod, selectedGrade],
    queryFn: async () => {
      if (!currentPeriod) return { results: [], count: 0 };
      
      try {
        const response = await studentApi.getStudentsForScoreEntry({
          year: parseInt(year),
          period: currentPeriod,
          grade: selectedGrade || undefined
        });
        return response;
      } catch (error) {
        console.error('Failed to fetch students:', error);
        return { results: [], count: 0 };
      }
    },
    enabled: !!currentPeriod,
  });

  // 生徒データ（実際のAPIから取得）
  const students = studentsData?.results || [];

  // 生徒を校舎ごとにグループ化
  const groupedStudents = students.reduce((groups: Record<string, any[]>, student) => {
    const schoolKey = `${student.school_id}-${student.school_name}`;
    if (!groups[schoolKey]) {
      groups[schoolKey] = [];
    }
    groups[schoolKey].push(student);
    return groups;
  }, {});

  // 締切情報を取得
  const currentDeadline = testSchedules && testSchedules.length > 0 
    ? new Date(testSchedules[0].deadline_at)
    : null;

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      // 学年が変更された場合、教科選択をリセット
      if (currentStep === 0 && selectedSubject && !availableSubjects.find(s => s.value === selectedSubject)) {
        setSelectedSubject('');
      }
      // 教科選択後は全生徒を自動選択
      if (currentStep === 1) {
        setSelectedStudents(students.map(s => s.id));
      }
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStudentToggle = (studentId: string) => {
    setSelectedStudents(prev => 
      prev.includes(studentId) 
        ? prev.filter(id => id !== studentId)
        : [...prev, studentId]
    );
  };

  const handleSchoolToggle = (schoolStudents: any[], selectAll: boolean) => {
    const schoolStudentIds = schoolStudents.map(s => s.id);
    if (selectAll) {
      // 校舎の全生徒を選択に追加
      setSelectedStudents(prev => [...new Set([...prev, ...schoolStudentIds])]);
    } else {
      // 校舎の全生徒を選択から除外
      setSelectedStudents(prev => prev.filter(id => !schoolStudentIds.includes(id)));
    }
  };

  const handleSubmit = async () => {
    try {
      if (!selectedTest?.id) {
        toast.error('テスト情報が見つかりません');
        return;
      }

      // スコアデータを整理してバックエンドの構造に合わせる
      const scoreSubmissions = [];
      
      for (const studentId of selectedStudents) {
        const studentScores = scores[studentId] || {};
        const attendance = studentScores.attendance ?? true;
        
        // 大問ごとのスコアを準備
        for (const problem of questionGroups || []) {
          const scoreValue = studentScores[problem.group_number?.toString() || problem.number?.toString()] || 0;
          
          scoreSubmissions.push({
            student_id: studentId,
            test_id: selectedTest.id,
            question_group_number: problem.group_number || problem.number,
            score: scoreValue,
            attendance: attendance
          });
        }
      }

      // バックエンドAPIに送信
      for (const submission of scoreSubmissions) {
        try {
          await testApi.submitScore(submission);
        } catch (error) {
          console.error('Score submission error:', error);
          // 個別のエラーは記録するが、続行
        }
      }

      toast.success(`${selectedStudents.length}名分のスコアを保存しました`);
      
      // 保存後にフォームをリセット
      setScores({});
      setCurrentStep(0);
      
    } catch (error) {
      console.error('Submit error:', error);
      toast.error('スコアの保存に失敗しました');
    }
  };

  const handleExcelImport = () => {
    setScoreImportModalOpen(true);
  };

  const handleExcelImportComplete = (importedData: Record<string, any>) => {
    setScores(prev => ({ ...prev, ...importedData }));
  };

  const handleExcelExport = () => {
    // エクスポート機能
    const csvContent = generateExportData();
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    const gradeName = grades.find(g => g.value === selectedGrade)?.label || selectedGrade;
    const subjectName = availableSubjects.find(s => s.value === selectedSubject)?.label || selectedSubject;
    link.setAttribute('download', `scores_${gradeName}_${subjectName}_${year}_${currentPeriod}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('スコアデータをエクスポートしました');
  };

  const generateExportData = () => {
    const questionHeaders = Array.from({ length: 10 }, (_, i) => `問題${i + 1}`);
    const headers = ['生徒ID', '生徒名', '教室', ...questionHeaders, '合計'];
    
    const rows = students.map(student => {
      const studentScores = scores[student.id] || {};
      const total = Object.values(studentScores).reduce((sum: number, score: any) => sum + (parseInt(score) || 0), 0);
      
      const scoreValues = Array.from({ length: 10 }, (_, i) => studentScores[`${i + 1}`] || '');
      
      return [
        student.student_id,
        student.name,
        student.classroom,
        ...scoreValues,
        total
      ];
    });
    
    return [headers, ...rows]
      .map(row => row.join(','))
      .join('\n');
  };


  const handleDownloadBlankTemplate = async (specificSubject?: string) => {
    if (!currentPeriod) {
      toast.error('期間情報が取得できません');
      return;
    }

    // 特定の教科が指定されていない場合は、選択された教科または利用可能な全教科
    const subjectsToDownload = specificSubject 
      ? [specificSubject] 
      : selectedSubject 
        ? [selectedSubject]
        : availableSubjects.map(s => s.value);

    if (subjectsToDownload.length === 0) {
      toast.error('利用可能な教科がありません');
      return;
    }

    try {
      // 複数教科の場合は順次ダウンロード
      for (const subjectValue of subjectsToDownload) {
        const response = await testApi.generateScoreTemplate({
          year: parseInt(year),
          period: currentPeriod,
          subject: subjectValue
        });

        if (response.success && response.csv_data) {
          // BOM付きUTF-8でCSVファイルを作成
          const csv = response.csv_data;
          const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
          const link = document.createElement('a');
          link.href = URL.createObjectURL(blob);
          
          const subjectName = [...availableSubjects, 
            { value: 'japanese', label: '国語' },
            { value: 'math', label: '算数' },
            { value: 'english', label: '英語' },
            { value: 'mathematics', label: '数学' }
          ].find(s => s.value === subjectValue)?.label || subjectValue;
          
          link.download = `全国学力向上テスト_${year}_${currentPeriod}_${subjectName}.csv`;
          link.click();
          
          // 複数ファイルダウンロード時の間隔
          if (subjectsToDownload.length > 1) {
            await new Promise(resolve => setTimeout(resolve, 500));
          }
        } else {
          toast.error(`${subjectValue}のテンプレート生成に失敗しました: ${response.error || '不明なエラー'}`);
        }
      }
      
      toast.success(
        subjectsToDownload.length === 1 
          ? 'テンプレートファイルをダウンロードしました'
          : `${subjectsToDownload.length}個のテンプレートファイルをダウンロードしました`
      );
    } catch (error) {
      console.error('Template download error:', error);
      toast.error('テンプレートのダウンロードに失敗しました');
    }
  };

  const handleDownloadAllGradesTemplate = async () => {
    if (!currentPeriod) {
      toast.error('期間情報が取得できません');
      return;
    }

    try {
      toast.info('生徒データ（得点入り）をダウンロードしています...');

      // 実データエクスポートAPIを呼び出し（生徒情報+既存の点数）
      const response = await testApi.exportScoresWithStudents({
        year: parseInt(year),
        period: currentPeriod
      });

      console.log('Export response:', response);

      // responseがundefinedでないことを確認
      if (response && response.success === true) {
        toast.success('生徒データ（得点入り）をダウンロードしました');
      } else if (response && response.success === false) {
        // 明示的にfalseの場合のみエラー表示
        console.error('Export failed:', response);
        toast.error(`エクスポートに失敗しました: ${response.message || response.error || '不明なエラー'}`);
      }
      // response.successが未定義の場合は何も表示しない（ダウンロードは成功している）
    } catch (error: any) {
      console.error('Export error:', error);
      toast.error(`生徒データのエクスポートに失敗しました: ${error.message || ''}`);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 0: return selectedGrade !== '' && currentPeriod !== '';
      case 1: return selectedSubject !== '';
      case 2: return selectedStudents.length > 0;
      case 3: return !isDeadlinePassed; // 締切日チェック
      case 4: return true;
      default: return false;
    }
  };

  const progress = ((currentStep + 1) / steps.length) * 100;

  return (
    <>
      <div className="space-y-6">
        {currentDeadline && (
          <DeadlineBanner deadline={currentDeadline} />
        )}
        
        {isDeadlinePassed && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-red-700">
                <AlertTriangle className="h-5 w-5" />
                <span className="font-medium">入力期限が過ぎています</span>
              </div>
              <p className="text-sm text-red-600 mt-1">
                現在は点数入力ができません。詳細は管理者にお問い合わせください。
              </p>
            </CardContent>
          </Card>
        )}
        
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {React.createElement(steps[currentStep].icon, { className: "h-5 w-5" })}
              {steps[currentStep].title}
            </CardTitle>
            <CardDescription>
              Step {currentStep + 1} of {steps.length}
            </CardDescription>
            <div className="w-full h-2 bg-gray-200 rounded-full">
              <div 
                className="h-full bg-primary rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </CardHeader>
          <CardContent>
            {currentStep === 0 && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">学年を選択してください</h3>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadAllGradesTemplate()}
                      className="rounded-xl"
                      disabled={isDeadlinePassed || !currentPeriod}
                      title={
                        !currentPeriod ? "期間情報を取得中..." : 
                        "全学年対応（小学生・中学生全教科）の統合エクスポートファイルをダウンロード"
                      }
                    >
                      <Download className="h-4 w-4 mr-2" />
                      生徒一括エクスポート
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setScoreImportModalOpen(true)}
                      className="rounded-xl"
                      disabled={isDeadlinePassed}
                      title="一括エクセル読み込み"
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      一括エクセル読み込み
                    </Button>
                  </div>
                </div>
                
                {currentPeriod && (
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-700">
                      <strong>現在の対象期間:</strong> {year}年度 {currentPeriod === 'spring' ? '春期' : currentPeriod === 'summer' ? '夏期' : '冬期'}
                    </p>
                  </div>
                )}
                
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">学年</label>
                    <div className="grid grid-cols-3 gap-3">
                      {grades.map((grade) => (
                        <Button
                          key={grade.value}
                          variant={selectedGrade === grade.value ? "default" : "outline"}
                          className="h-16 flex flex-col gap-2 rounded-xl"
                          onClick={() => setSelectedGrade(grade.value)}
                          disabled={isDeadlinePassed}
                        >
                          <GraduationCap className="h-4 w-4" />
                          <span className="text-xs text-center">{grade.label}</span>
                        </Button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {currentStep === 1 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">教科を選択してください</h3>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadBlankTemplate()}
                      className="rounded-xl"
                      disabled={isDeadlinePassed || !selectedSubject}
                      title={!selectedSubject ? "教科を選択してください" : "選択した教科のテンプレートをダウンロード"}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      テンプレートダウンロード
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setScoreImportModalOpen(true)}
                      className="rounded-xl"
                      disabled={isDeadlinePassed || !selectedSubject}
                      title={!selectedSubject ? "教科を選択してください" : "一括エクセル読み込み"}
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      一括エクセル読み込み
                    </Button>
                  </div>
                </div>
                {availableSubjects.length > 0 ? (
                  <div className="grid grid-cols-2 gap-4">
                    {availableSubjects.map((subject) => (
                      <Button
                        key={subject.value}
                        variant={selectedSubject === subject.value ? "default" : "outline"}
                        className="h-20 flex flex-col gap-2 rounded-xl"
                        onClick={() => setSelectedSubject(subject.value)}
                        disabled={isDeadlinePassed}
                      >
                        <BookOpen className="h-5 w-5" />
                        <span>{subject.label}</span>
                      </Button>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    先に学年を選択してください
                  </div>
                )}
              </div>
            )}


            {currentStep === 2 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">生徒を選択してください</h3>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">
                      {selectedStudents.length}名選択中
                    </Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadBlankTemplate()}
                      className="rounded-xl"
                      disabled={isDeadlinePassed || !selectedSubject}
                      title={!selectedSubject ? "教科を選択してください" : "選択した教科のテンプレートをダウンロード"}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      テンプレートダウンロード
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setScoreImportModalOpen(true)}
                      className="rounded-xl"
                      disabled={isDeadlinePassed || !selectedSubject}
                      title={!selectedSubject ? "教科を選択してください" : "一括エクセル読み込み"}
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      一括エクセル読み込み
                    </Button>
                  </div>
                </div>
                <div className="space-y-4">
                  {Object.entries(groupedStudents).length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <p>該当する生徒が見つかりません</p>
                      <p className="text-sm mt-1">学年や期間の設定を確認してください</p>
                    </div>
                  ) : (
                    Object.entries(groupedStudents).map(([schoolKey, schoolStudents]) => {
                      const school = schoolStudents[0];
                      return (
                        <div key={schoolKey} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-semibold text-lg">
                              {school.school_name}
                            </h4>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">
                                {schoolStudents.length}名
                              </Badge>
                              <div className="flex gap-1">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="text-xs px-2 py-1 h-6"
                                  onClick={() => handleSchoolToggle(schoolStudents, true)}
                                >
                                  全選択
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="text-xs px-2 py-1 h-6"
                                  onClick={() => handleSchoolToggle(schoolStudents, false)}
                                >
                                  全解除
                                </Button>
                              </div>
                            </div>
                          </div>
                          <div className="space-y-2">
                            {schoolStudents.map((student) => (
                              <div
                                key={student.id}
                                className={`flex items-center justify-between p-3 border rounded-lg cursor-pointer transition-colors ${
                                  selectedStudents.includes(student.id) 
                                    ? 'border-primary bg-primary/5' 
                                    : 'hover:bg-gray-50'
                                }`}
                                onClick={() => handleStudentToggle(student.id)}
                              >
                                <div className="flex items-center gap-3">
                                  <div className={`w-4 h-4 rounded border-2 ${
                                    selectedStudents.includes(student.id) 
                                      ? 'bg-primary border-primary' 
                                      : 'border-gray-300'
                                  }`}>
                                    {selectedStudents.includes(student.id) && (
                                      <CheckCircle className="w-full h-full text-white" />
                                    )}
                                  </div>
                                  <div>
                                    <p className="font-medium">{student.name}</p>
                                    <p className="text-sm text-muted-foreground">
                                      生徒ID: {student.student_id} • {student.classroom} {student.classroom_id ? `(${student.classroom_id})` : ''}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            )}

            {currentStep === 3 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">スコアを入力してください</h3>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadBlankTemplate()}
                      className="rounded-xl"
                      disabled={isDeadlinePassed || !selectedSubject}
                      title={!selectedSubject ? "教科を選択してください" : "選択した教科のテンプレートをダウンロード"}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      テンプレートダウンロード
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setScoreImportModalOpen(true)}
                      className="rounded-xl"
                      disabled={isDeadlinePassed || !selectedSubject}
                      title={!selectedSubject ? "教科を選択してください" : "一括エクセル読み込み"}
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      一括エクセル読み込み
                    </Button>
                  </div>
                </div>
                <div className="text-sm text-muted-foreground mb-4">
                  {grades.find(g => g.value === selectedGrade)?.label || selectedGrade} {availableSubjects.find(s => s.value === selectedSubject)?.label || selectedSubject} - {selectedStudents.length}名
                </div>
                {!isDeadlinePassed ? (
                  <>
                    
                    <IndividualProblemTable
                    students={students.filter(s => selectedStudents.includes(s.id)).map(s => ({
                      ...s,
                      attendance: scores[s.id]?.attendance ?? true
                    }))}
                    problems={questionGroups?.map((group: any) => ({
                      number: group.group_number,
                      maxScore: group.max_score,
                      title: group.title || `大問${group.group_number}`
                    })) || Array.from({ length: Math.min(5, 10) }, (_, i) => ({
                      number: i + 1,
                      maxScore: 20,
                      title: `大問${i + 1}`
                    }))}
                    scores={scores}
                    onScoreChange={setScores}
                    onAttendanceChange={(studentId, attendance) => {
                      setScores(prev => ({
                        ...prev,
                        [studentId]: {
                          ...prev[studentId],
                          attendance
                        }
                      }));
                    }}
                  />
                  </>
                ) : (
                  <div className="text-center py-8 text-red-600">
                    <AlertTriangle className="h-12 w-12 mx-auto mb-4" />
                    <p className="text-lg font-medium">入力期限が過ぎています</p>
                    <p className="text-sm">現在は点数入力ができません。</p>
                  </div>
                )}
              </div>
            )}

            {currentStep === 4 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">入力内容を確認してください</h3>
                <div className="space-y-4">
                  <div className="grid grid-cols-4 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">学年</label>
                      <Badge variant="outline">{grades.find(g => g.value === selectedGrade)?.label || selectedGrade}</Badge>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">時期</label>
                      <Badge variant="outline">{currentPeriod === 'spring' ? '春期' : currentPeriod === 'summer' ? '夏期' : '冬期'}</Badge>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">教科</label>
                      <Badge variant="outline">{availableSubjects.find(s => s.value === selectedSubject)?.label || selectedSubject}</Badge>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">大問数</label>
                      <Badge variant="outline">{questionGroups?.length || '未設定'}問</Badge>
                    </div>
                    {questionGroups && questionGroups.length > 0 && (
                      <div className="space-y-2">
                        <label className="text-sm font-medium">大問別満点</label>
                        <div className="flex flex-wrap gap-1">
                          {questionGroups.map((group: any) => (
                            <Badge key={group.group_number} variant="secondary" className="text-xs">
                              大問{group.group_number}: {group.max_score}点
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">対象生徒</label>
                    <div className="flex flex-wrap gap-2">
                      {students
                        .filter(s => selectedStudents.includes(s.id))
                        .map(student => (
                          <Badge key={student.id} variant="outline">
                            {student.name} (ID: {student.student_id})
                          </Badge>
                        ))}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">入力状況</label>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm">
                        {Object.keys(scores).length > 0 
                          ? `${Object.keys(scores).length}件のスコアが入力されています`
                          : 'スコアが入力されていません'
                        }
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-between pt-6">
              <Button
                variant="outline"
                onClick={handleBack}
                disabled={currentStep === 0}
                className="rounded-xl"
              >
                <ChevronLeft className="h-4 w-4 mr-2" />
                戻る
              </Button>
              {currentStep < steps.length - 1 ? (
                <Button
                  onClick={handleNext}
                  disabled={!canProceed()}
                  className="rounded-xl bg-primary hover:bg-primary/90"
                >
                  次へ
                  <ChevronRight className="h-4 w-4 ml-2" />
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  disabled={isDeadlinePassed}
                  className="rounded-xl bg-primary hover:bg-primary/90"
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  保存
                </Button>
              )}
            </div>
          </CardContent>
        </Card>


        <ScoreImportModal
          open={scoreImportModalOpen}
          onOpenChange={setScoreImportModalOpen}
          testId={selectedTest?.id}
        />
      </div>
    </>
  );
}