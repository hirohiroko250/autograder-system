'use client';

import { useState } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { 
  Save, 
  Clock, 
  Users, 
  AlertCircle,
  CheckCircle,
  Edit
} from 'lucide-react';
import { toast } from 'sonner';

interface Student {
  id: string;
  name: string;
  grade: string;
  scores: { [key: string]: number | null };
  totalScore: number | null;
  status: 'pending' | 'completed';
}

interface Question {
  id: string;
  name: string;
  maxScore: number;
  subQuestions?: {
    id: string;
    name: string;
    maxScore: number;
  }[];
}

interface ScoreEntryClientProps {
  year: string;
  period: string;
  subject: string;
}

export default function ScoreEntryClient({ year, period, subject }: ScoreEntryClientProps) {
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  // Mock data
  const testInfo = {
    subject: subject,
    year: year,
    period: period,
    deadline: '2024-06-15',
    totalStudents: 45,
    completedStudents: 38
  };

  const questions: Question[] = [
    {
      id: 'q1',
      name: '大問1',
      maxScore: 25,
      subQuestions: [
        { id: 'q1-1', name: '(1)', maxScore: 5 },
        { id: 'q1-2', name: '(2)', maxScore: 8 },
        { id: 'q1-3', name: '(3)', maxScore: 12 }
      ]
    },
    {
      id: 'q2',
      name: '大問2',
      maxScore: 30,
      subQuestions: [
        { id: 'q2-1', name: '(1)', maxScore: 10 },
        { id: 'q2-2', name: '(2)', maxScore: 20 }
      ]
    },
    {
      id: 'q3',
      name: '大問3',
      maxScore: 25
    },
    {
      id: 'q4',
      name: '大問4',
      maxScore: 20
    }
  ];

  const [students, setStudents] = useState<Student[]>([
    {
      id: '240001',
      name: '田中太郎',
      grade: '中学3年',
      scores: { 'q1': 20, 'q2': 25, 'q3': 22, 'q4': 18 },
      totalScore: 85,
      status: 'completed'
    },
    {
      id: '240002',
      name: '佐藤花子',
      grade: '中学2年',
      scores: { 'q1': 23, 'q2': 28, 'q3': 25, 'q4': 16 },
      totalScore: 92,
      status: 'completed'
    },
    {
      id: '240003',
      name: '山田次郎',
      grade: '中学1年',
      scores: {},
      totalScore: null,
      status: 'pending'
    }
  ]);

  const [editingScores, setEditingScores] = useState<{ [key: string]: number | string }>({});

  const handleScoreChange = (questionId: string, value: string) => {
    setEditingScores(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const handleSaveScores = () => {
    if (!selectedStudent) return;

    const newScores: { [key: string]: number | null } = {};
    let totalScore = 0;

    questions.forEach(question => {
      const score = editingScores[question.id];
      if (score !== undefined && score !== '') {
        const numScore = Number(score);
        if (!isNaN(numScore)) {
          newScores[question.id] = numScore;
          totalScore += numScore;
        }
      }
    });

    setStudents(prev => prev.map(student => 
      student.id === selectedStudent.id 
        ? { 
            ...student, 
            scores: newScores,
            totalScore: totalScore || null,
            status: Object.keys(newScores).length > 0 ? 'completed' : 'pending'
          }
        : student
    ));

    setIsDialogOpen(false);
    toast.success('得点を保存しました');
  };

  const handleEditStudent = (student: Student) => {
    setSelectedStudent(student);
    setEditingScores(
      questions.reduce((acc, question) => {
        acc[question.id] = student.scores[question.id] || '';
        return acc;
      }, {} as { [key: string]: number | string })
    );
    setIsDialogOpen(true);
  };

  const completionRate = (testInfo.completedStudents / testInfo.totalStudents) * 100;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              得点入力
            </h1>
            <p className="text-gray-500 dark:text-gray-400">
              {testInfo.subject} - {testInfo.year}年度 {testInfo.period}期
            </p>
          </div>
        </div>

        {/* Test Info */}
        <Card className="bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-700">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center gap-3">
                <Clock className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                <div>
                  <p className="text-sm text-blue-700 dark:text-blue-300">締切日</p>
                  <p className="font-semibold text-blue-900 dark:text-blue-100">
                    {testInfo.deadline}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                <div>
                  <p className="text-sm text-blue-700 dark:text-blue-300">対象生徒</p>
                  <p className="font-semibold text-blue-900 dark:text-blue-100">
                    {testInfo.totalStudents}名
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                <div>
                  <p className="text-sm text-blue-700 dark:text-blue-300">完了</p>
                  <p className="font-semibold text-blue-900 dark:text-blue-100">
                    {testInfo.completedStudents}名 ({Math.round(completionRate)}%)
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-4">
              <Progress value={completionRate} className="h-2" />
            </div>
          </CardContent>
        </Card>

        {/* Students List */}
        <Card>
          <CardHeader>
            <CardTitle>生徒一覧</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {students.map((student) => (
                <div
                  key={student.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                      {student.name.charAt(0)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{student.name}</p>
                        <Badge variant="outline">{student.grade}</Badge>
                        <Badge 
                          className={
                            student.status === 'completed' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-yellow-100 text-yellow-800'
                          }
                        >
                          {student.status === 'completed' ? '完了' : '未完了'}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        ID: {student.id}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-bold text-lg">
                        {student.totalScore !== null ? `${student.totalScore}点` : '未入力'}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        100点満点
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEditStudent(student)}
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      {student.status === 'completed' ? '編集' : '入力'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Score Entry Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>
                {selectedStudent?.name} - 得点入力
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 max-h-[60vh] overflow-y-auto">
              {questions.map((question) => (
                <div key={question.id} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <Label className="text-base font-medium">
                      {question.name}
                    </Label>
                    <span className="text-sm text-gray-500">
                      {question.maxScore}点満点
                    </span>
                  </div>
                  <Input
                    type="number"
                    min="0"
                    max={question.maxScore}
                    value={editingScores[question.id] || ''}
                    onChange={(e) => handleScoreChange(question.id, e.target.value)}
                    placeholder={`0-${question.maxScore}点`}
                  />
                  {question.subQuestions && (
                    <div className="ml-4 space-y-1 text-sm text-gray-600 dark:text-gray-400">
                      {question.subQuestions.map((subQ) => (
                        <div key={subQ.id} className="flex justify-between">
                          <span>{subQ.name}</span>
                          <span>{subQ.maxScore}点</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              <div className="pt-4 border-t">
                <div className="flex justify-between items-center">
                  <Label className="text-lg font-bold">合計点</Label>
                  <span className="text-xl font-bold">
                    {Object.values(editingScores).reduce((sum, score) => {
                      const num = Number(score);
                      return sum + (isNaN(num) ? 0 : num);
                    }, 0)}点 / 100点
                  </span>
                </div>
              </div>
            </div>
            <div className="flex gap-2 pt-4">
              <Button onClick={handleSaveScores} className="flex-1">
                <Save className="h-4 w-4 mr-2" />
                保存
              </Button>
              <Button 
                variant="outline" 
                onClick={() => setIsDialogOpen(false)}
              >
                キャンセル
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}