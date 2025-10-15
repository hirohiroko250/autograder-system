'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Save, User } from 'lucide-react';
import { toast } from 'sonner';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { testApi } from '@/lib/api-client';

interface QuestionGroupData {
  group_id: number;
  group_number: number;
  title: string;
  max_score: number;
  questions: Array<{
    question_id: number;
    question_number: number;
    content: string;
    max_score: number;
    score: number | null;
    is_correct: boolean;
  }>;
}

interface DetailedScoreModalProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  testId: number | null;
  studentId: string | null;
  studentName: string;
  onScoreSubmitted: () => void;
}

interface AttendanceStatus {
  value: number;
  label: string;
  color: string;
}

const attendanceStatuses: AttendanceStatus[] = [
  { value: 1, label: '出席', color: 'bg-green-100 text-green-800' },
  { value: 0, label: '欠席', color: 'bg-red-100 text-red-800' },
  { value: 2, label: '遅刻', color: 'bg-yellow-100 text-yellow-800' },
  { value: 3, label: '早退', color: 'bg-orange-100 text-orange-800' },
  { value: 4, label: '途中退席', color: 'bg-purple-100 text-purple-800' },
];

export function DetailedScoreModal({
  isOpen,
  onOpenChange,
  testId,
  studentId,
  studentName,
  onScoreSubmitted
}: DetailedScoreModalProps) {
  const [attendanceStatus, setAttendanceStatus] = useState(1);
  const [attendanceReason, setAttendanceReason] = useState('');
  const [questionScores, setQuestionScores] = useState<{ [key: number]: number | string }>({});
  
  const queryClient = useQueryClient();

  // 個別問題スコアデータを取得
  const { data: scoreData, isLoading: isLoadingScores, refetch } = useQuery({
    queryKey: ['individual-scores', testId, studentId],
    queryFn: () => testApi.getIndividualScores(testId!, studentId!),
    enabled: !!testId && !!studentId && isOpen,
  });


  // 個別問題スコア送信ミューテーション
  const submitIndividualScoresMutation = useMutation({
    mutationFn: testApi.submitIndividualScores,
    onSuccess: (data) => {
      if (data.success) {
        toast.success('スコアを保存しました');
        queryClient.invalidateQueries({ queryKey: ['individual-scores', testId, studentId] });
        onScoreSubmitted();
        onOpenChange(false);
      } else {
        toast.error(data.error || 'スコアの保存に失敗しました');
      }
    },
    onError: (error) => {
      toast.error('スコアの保存に失敗しました');
      console.error('Score submission error:', error);
    }
  });


  // データが取得されたら初期値を設定
  useEffect(() => {
    if (scoreData?.success) {
      // 出席状況を設定
      if (scoreData.attendance) {
        setAttendanceStatus(scoreData.attendance.attendance_status);
        setAttendanceReason(scoreData.attendance.reason || '');
      }

      // 個別問題スコアを設定
      const newQuestionScores: { [key: number]: number | string } = {};
      
      if (scoreData.problems) {
        scoreData.problems.forEach((problem: any) => {
          newQuestionScores[problem.problem_number] = problem.score ?? '';
        });
      }
      
      setQuestionScores(newQuestionScores);
    }
  }, [scoreData]);

  const handleProblemScoreChange = (problemNumber: number, value: string) => {
    setQuestionScores(prev => ({
      ...prev,
      [problemNumber]: value
    }));
  };

  const validateScores = () => {
    const warnings: string[] = [];
    let totalScore = 0;
    let maxPossibleScore = 0;

    // 個別問題の検証
    if (scoreData?.problems) {
      scoreData.problems.forEach((problem: any) => {
        const score = Number(questionScores[problem.problem_number]) || 0;
        totalScore += score;
        maxPossibleScore += problem.max_score;

        if (score > problem.max_score) {
          warnings.push(`問題${problem.problem_number}の得点が最大点（${problem.max_score}点）を超えています`);
        }
      });
    }

    return { warnings, totalScore, maxPossibleScore };
  };

  const handleSubmit = async () => {
    if (!testId || !studentId) return;

    const { warnings } = validateScores();

    if (warnings.length > 0) {
      const confirmMessage = `以下の警告があります:\n${warnings.join('\n')}\n\nそれでも保存しますか?`;
      if (!confirm(confirmMessage)) {
        return;
      }
    }

    // 個別問題スコアを送信
    const scores: { [key: string]: number } = {};
    Object.entries(questionScores)
      .filter(([_, score]) => score !== '' && score !== null)
      .forEach(([problemNumber, score]) => {
        scores[problemNumber] = Number(score);
      });

    submitIndividualScoresMutation.mutate({
      test_id: testId,
      student_id: studentId,
      scores: scores,
      attendance_status: attendanceStatus,
      attendance_reason: attendanceReason
    });
  };

  const getCurrentAttendanceStatus = () => {
    return attendanceStatuses.find(status => status.value === attendanceStatus) || attendanceStatuses[0];
  };

  if (isLoadingScores) {
    return (
      <Dialog open={isOpen} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-[800px]">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            <span className="ml-2">データを読み込み中...</span>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[900px] max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            {studentName} - スコア入力
            <Badge className={getCurrentAttendanceStatus().color}>
              {getCurrentAttendanceStatus().label}
            </Badge>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 overflow-y-auto max-h-[70vh] pr-2">
          {/* 出席管理セクション */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">出席状況</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="attendance">出席状況</Label>
                  <Select
                    value={attendanceStatus.toString()}
                    onValueChange={(value) => setAttendanceStatus(Number(value))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {attendanceStatuses.map((status) => (
                        <SelectItem key={status.value} value={status.value.toString()}>
                          {status.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="reason">理由（任意）</Label>
                  <Input
                    id="reason"
                    placeholder="欠席・遅刻の理由など"
                    value={attendanceReason}
                    onChange={(e) => setAttendanceReason(e.target.value)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>


          {/* スコア入力セクション */}
          <div className="space-y-3">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">点数入力</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  {scoreData?.problems && scoreData.problems.map((problem: any) => (
                    <div key={problem.problem_number} className="flex items-center gap-2">
                      <Label className="text-sm font-medium w-16">
                        問題{problem.problem_number}:
                      </Label>
                      <Input
                        type="number"
                        min="0"
                        max={problem.max_score}
                        value={questionScores[problem.problem_number] || ''}
                        onChange={(e) => handleProblemScoreChange(problem.problem_number, e.target.value)}
                        placeholder="0"
                        className="w-20"
                      />
                      <span className="text-sm text-gray-500">/{problem.max_score}点</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 合計表示 */}
          <Card className="bg-gray-50">
            <CardContent className="pt-6">
              <div className="flex justify-between items-center">
                <Label className="text-lg font-bold">合計点</Label>
                <span className="text-2xl font-bold">
                  {(() => {
                    const { totalScore, maxPossibleScore } = validateScores();
                    return `${totalScore}点 / ${maxPossibleScore}点`;
                  })()}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* フッター */}
        <div className="flex gap-2 pt-4 border-t">
          <Button 
            onClick={handleSubmit} 
            className="flex-1"
            disabled={submitIndividualScoresMutation.isPending}
          >
            <Save className="h-4 w-4 mr-2" />
            スコアを保存
          </Button>
          <Button 
            variant="outline" 
            onClick={() => onOpenChange(false)}
          >
            キャンセル
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}