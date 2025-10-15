'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import React from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Clock, 
  Users, 
  CheckCircle,
  Edit,
  Save,
  Filter,
  Search,
  ArrowUpDown,
  CheckSquare,
  Square
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { testApi, commentApi } from '@/lib/api-client';
import { toast } from 'sonner';

interface Student {
  id: string;
  name: string;
  grade: string;
  scores: { [problemNumber: string]: number | null };  // problemNumber: score
  totalScore: number | null;
  status: 'pending' | 'completed';
  isEditing?: boolean;
  attendance?: boolean;
}

interface Problem {
  problem_number: number;
  max_score: number;
  description: string;
}

export default function ScoreEntryPage() {
  const [selectedYear, setSelectedYear] = useState('2025');
  const [selectedPeriod, setSelectedPeriod] = useState('spring');
  const [selectedSubject, setSelectedSubject] = useState('math');
  const [selectedTestId, setSelectedTestId] = useState<number | null>(null);
  
  // 新しい状態
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'completed'>('all');
  const [selectedStudents, setSelectedStudents] = useState<Set<string>>(new Set());
  const [editingStudents, setEditingStudents] = useState<Set<string>>(new Set());
  const [tempScores, setTempScores] = useState<{ [studentId: string]: { [questionId: string]: string } }>({});
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');

  // 実際のテスト情報を取得
  const { data: testDefinitions, isLoading: isLoadingTests } = useQuery({
    queryKey: ['test-definitions', selectedYear, selectedPeriod],
    queryFn: () => testApi.getTestDefinitions({
      year: selectedYear,
      period: selectedPeriod
    }),
    enabled: !!selectedYear && !!selectedPeriod
  });

  // 選択されたテストの詳細情報
  const selectedTest = testDefinitions?.results?.find((test: any) => 
    test.subject === selectedSubject
  );

  // 個別問題を取得
  const { data: individualProblems, isLoading: isLoadingProblems } = useQuery({
    queryKey: ['individual-problems', selectedTestId],
    queryFn: async () => {
      if (!selectedTestId) return null;
      // まずデフォルト問題を作成
      await commentApi.createDefaultProblems(selectedTestId, 10, 10);
      // その後問題リストを取得
      return commentApi.getIndividualProblems(selectedTestId);
    },
    enabled: !!selectedTestId
  });

  // 選択されたテストが変更されたらテストIDを更新
  useEffect(() => {
    if (selectedTest) {
      setSelectedTestId(selectedTest.id);
    }
  }, [selectedTest]);

  // 個別問題リストを生成（フォールバック付き）
  const problems: Problem[] = individualProblems?.results?.map((problem: any) => ({
    problem_number: problem.problem_number,
    max_score: problem.max_score,
    description: problem.description
  })) || Array.from({ length: 10 }, (_, i) => ({
    problem_number: i + 1,
    max_score: 10,
    description: `問題${i + 1}`
  }));

  // 生徒データを取得（モック）
  const [students, setStudents] = useState<Student[]>([
    {
      id: '100001',
      name: '佐藤太郎',
      grade: '中学1年',
      scores: { '1': 8, '2': 9, '3': 7, '4': 10, '5': 8, '6': 9, '7': 7, '8': 8, '9': 10, '10': 9 },
      totalScore: 85,
      status: 'completed',
      attendance: true
    },
    {
      id: '100002',
      name: '田中花子',
      grade: '中学1年',
      scores: { '1': 9, '2': 8, '3': null, '4': null, '5': null, '6': null, '7': null, '8': null, '9': null, '10': null },
      totalScore: null,
      status: 'pending',
      attendance: true
    },
    {
      id: '100003',
      name: '山田次郎',
      grade: '中学2年',
      scores: {},
      totalScore: null,
      status: 'pending',
      attendance: false
    },
    {
      id: '100004',
      name: '鈴木美咲',
      grade: '中学1年',
      scores: { '1': 10, '2': 9, '3': 8, '4': 10, '5': 9, '6': 8, '7': 9, '8': 10, '9': 8, '10': 9 },
      totalScore: 90,
      status: 'completed',
      attendance: true
    },
    {
      id: '100005',
      name: '高橋大輔',
      grade: '中学2年',
      scores: { '1': 7, '2': 8, '3': 6, '4': null, '5': null, '6': null, '7': null, '8': null, '9': null, '10': null },
      totalScore: null,
      status: 'pending',
      attendance: true
    }
  ]);


  // 新しいヘルパー関数
  const toggleStudentSelection = (studentId: string) => {
    setSelectedStudents(prev => {
      const newSet = new Set(Array.from(prev));
      if (newSet.has(studentId)) {
        newSet.delete(studentId);
      } else {
        newSet.add(studentId);
      }
      return newSet;
    });
  };

  const toggleAllStudents = () => {
    if (selectedStudents.size === filteredStudents.length) {
      setSelectedStudents(new Set());
    } else {
      setSelectedStudents(new Set(filteredStudents.map(s => s.id)));
    }
  };

  const startEditingStudent = (studentId: string) => {
    setEditingStudents(prev => new Set(Array.from(prev).concat(studentId)));
    // 現在のスコアを一時保存にコピー
    const student = students.find(s => s.id === studentId);
    if (student) {
      setTempScores(prev => ({
        ...prev,
        [studentId]: Object.fromEntries(
          problems.map(p => [p.problem_number.toString(), String(student.scores[p.problem_number.toString()] || '')])
        )
      }));
    }
  };

  const saveStudentScores = (studentId: string) => {
    const tempScore = tempScores[studentId];
    if (!tempScore) return;

    setStudents(prev => prev.map(student => {
      if (student.id === studentId) {
        const newScores = { ...student.scores };
        let totalScore = 0;
        let hasAnyScore = false;

        problems.forEach(problem => {
          const problemKey = problem.problem_number.toString();
          const scoreValue = tempScore[problemKey];
          if (scoreValue && scoreValue !== '') {
            const score = Number(scoreValue);
            // Validate score doesn't exceed max_score
            if (score > problem.max_score) {
              toast.error(`問題${problem.problem_number}の得点が満点（${problem.max_score}点）を超えています`);
              return;
            }
            newScores[problemKey] = score;
            totalScore += score;
            hasAnyScore = true;
          } else {
            newScores[problemKey] = null;
          }
        });

        return {
          ...student,
          scores: newScores,
          totalScore: hasAnyScore ? totalScore : null,
          status: hasAnyScore && Object.values(newScores).every(score => score !== null) ? 'completed' : 'pending'
        };
      }
      return student;
    }));

    setEditingStudents(prev => {
      const newSet = new Set(Array.from(prev));
      newSet.delete(studentId);
      return newSet;
    });

    toast.success('スコアを保存しました');
  };

  const cancelEditingStudent = (studentId: string) => {
    setEditingStudents(prev => {
      const newSet = new Set(Array.from(prev));
      newSet.delete(studentId);
      return newSet;
    });
    setTempScores(prev => {
      const newTemp = { ...prev };
      delete newTemp[studentId];
      return newTemp;
    });
  };

  const updateTempScore = (studentId: string, problemNumber: string, value: string) => {
    setTempScores(prev => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        [problemNumber]: value
      }
    }));
  };

  const toggleAttendance = (studentId: string) => {
    setStudents(prev => prev.map(student => 
      student.id === studentId 
        ? { ...student, attendance: !student.attendance }
        : student
    ));
  };

  const handleSort = (key: string) => {
    setSortConfig(prev => ({
      key,
      direction: prev?.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  // フィルタリングとソート
  const filteredStudents = students
    .filter(student => {
      const matchesSearch = student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           student.id.includes(searchTerm);
      const matchesStatus = statusFilter === 'all' || student.status === statusFilter;
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      if (!sortConfig) return 0;
      
      const { key, direction } = sortConfig;
      let aValue, bValue;

      switch (key) {
        case 'name':
          aValue = a.name;
          bValue = b.name;
          break;
        case 'grade':
          aValue = a.grade;
          bValue = b.grade;
          break;
        case 'totalScore':
          aValue = a.totalScore || 0;
          bValue = b.totalScore || 0;
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return direction === 'asc' ? 1 : -1;
      return 0;
    });

  const completedStudents = students.filter(s => s.status === 'completed').length;
  const completionRate = students.length > 0 ? (completedStudents / students.length) * 100 : 0;

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
              効率的にテストの得点を入力・管理します
            </p>
          </div>
          <div className="flex gap-2">
            <Select value={selectedYear} onValueChange={setSelectedYear}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="2025">2025年度</SelectItem>
                <SelectItem value="2024">2024年度</SelectItem>
                <SelectItem value="2023">2023年度</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="spring">春期</SelectItem>
                <SelectItem value="summer">夏期</SelectItem>
                <SelectItem value="winter">冬期</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedSubject} onValueChange={setSelectedSubject}>
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="math">算数</SelectItem>
                <SelectItem value="japanese">国語</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Test Info */}
        <Card className="bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-700">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-3">
                <Clock className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                <div>
                  <p className="text-sm text-blue-700 dark:text-blue-300">締切日</p>
                  <p className="font-semibold text-blue-900 dark:text-blue-100">
                    {selectedTest?.schedule?.deadline_at ? new Date(selectedTest.schedule.deadline_at).toLocaleDateString() : '未設定'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                <div>
                  <p className="text-sm text-blue-700 dark:text-blue-300">対象生徒</p>
                  <p className="font-semibold text-blue-900 dark:text-blue-100">
                    {filteredStudents.length}名
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                <div>
                  <p className="text-sm text-blue-700 dark:text-blue-300">完了</p>
                  <p className="font-semibold text-blue-900 dark:text-blue-100">
                    {completedStudents}名 ({Math.round(completionRate)}%)
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Edit className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                <div>
                  <p className="text-sm text-blue-700 dark:text-blue-300">編集中</p>
                  <p className="font-semibold text-blue-900 dark:text-blue-100">
                    {editingStudents.size}名
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-4">
              <p className="text-sm text-blue-700 dark:text-blue-300 mb-2">
                {selectedTest?.get_subject_display || '算数'} - {selectedYear}年度 {selectedPeriod === 'spring' ? '春期' : selectedPeriod === 'summer' ? '夏期' : '冬期'}
              </p>
              <div className="w-full h-2 bg-gray-200 rounded-full">
                <div 
                  className="h-full bg-primary rounded-full transition-all duration-300"
                  style={{ width: `${completionRate}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Controls */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
              <div className="flex gap-2 flex-wrap">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    placeholder="生徒名またはIDで検索..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 w-64"
                  />
                </div>
                <Select value={statusFilter} onValueChange={(value: any) => setStatusFilter(value)}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">すべて</SelectItem>
                    <SelectItem value="pending">未完了</SelectItem>
                    <SelectItem value="completed">完了</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-2">
                {selectedStudents.size > 0 && (
                  <Button variant="outline" size="sm">
                    <Save className="h-4 w-4 mr-2" />
                    選択した{selectedStudents.size}名を一括保存
                  </Button>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setViewMode(viewMode === 'table' ? 'cards' : 'table')}
                >
                  {viewMode === 'table' ? 'カード表示' : 'テーブル表示'}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Score Entry Table */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>点数入力テーブル</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleAllStudents}
                className="flex items-center gap-2"
              >
                {selectedStudents.size === filteredStudents.length ? (
                  <CheckSquare className="h-4 w-4" />
                ) : (
                  <Square className="h-4 w-4" />
                )}
                全選択
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={toggleAllStudents}
                        className="p-1"
                      >
                        {selectedStudents.size === filteredStudents.length ? (
                          <CheckSquare className="h-4 w-4" />
                        ) : (
                          <Square className="h-4 w-4" />
                        )}
                      </Button>
                    </th>
                    <th className="text-left p-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleSort('name')}
                        className="flex items-center gap-1"
                      >
                        生徒名
                        <ArrowUpDown className="h-3 w-3" />
                      </Button>
                    </th>
                    <th className="text-left p-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleSort('grade')}
                        className="flex items-center gap-1"
                      >
                        学年
                        <ArrowUpDown className="h-3 w-3" />
                      </Button>
                    </th>
                    <th className="text-left p-2">出席</th>
                    {problems.map((problem) => (
                      <th key={problem.problem_number} className="text-center p-2 min-w-[80px]">
                        <div className="flex flex-col">
                          <span className="font-medium">問題{problem.problem_number}</span>
                          <span className="text-xs text-gray-500">/{problem.max_score}点</span>
                        </div>
                      </th>
                    ))}
                    <th className="text-center p-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleSort('totalScore')}
                        className="flex items-center gap-1"
                      >
                        合計
                        <ArrowUpDown className="h-3 w-3" />
                      </Button>
                    </th>
                    <th className="text-center p-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleSort('status')}
                        className="flex items-center gap-1"
                      >
                        状態
                        <ArrowUpDown className="h-3 w-3" />
                      </Button>
                    </th>
                    <th className="text-center p-2">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredStudents.map((student) => (
                    <tr key={student.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <td className="p-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleStudentSelection(student.id)}
                          className="p-1"
                        >
                          {selectedStudents.has(student.id) ? (
                            <CheckSquare className="h-4 w-4" />
                          ) : (
                            <Square className="h-4 w-4" />
                          )}
                        </Button>
                      </td>
                      <td className="p-2">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                            {student.name.charAt(0)}
                          </div>
                          <div>
                            <p className="font-medium">{student.name}</p>
                            <p className="text-xs text-gray-500">ID: {student.id}</p>
                          </div>
                        </div>
                      </td>
                      <td className="p-2">
                        <Badge variant="outline" className="text-xs">
                          {student.grade}
                        </Badge>
                      </td>
                      <td className="p-2 text-center">
                        <Button
                          size="sm"
                          variant={student.attendance ? 'default' : 'secondary'}
                          onClick={() => toggleAttendance(student.id)}
                          className={student.attendance 
                            ? 'bg-green-100 text-green-800 hover:bg-green-200' 
                            : 'bg-red-100 text-red-800 hover:bg-red-200'
                          }
                        >
                          {student.attendance ? '出席' : '欠席'}
                        </Button>
                      </td>
                      {problems.map((problem) => (
                        <td key={problem.problem_number} className="p-1 text-center">
                          {editingStudents.has(student.id) ? (
                            <Input
                              type="number"
                              min="0"
                              max={problem.max_score}
                              value={tempScores[student.id]?.[problem.problem_number.toString()] || ''}
                              onChange={(e) => updateTempScore(student.id, problem.problem_number.toString(), e.target.value)}
                              className="w-16 h-8 text-center text-sm"
                              placeholder="0"
                            />
                          ) : (
                            <span 
                              className={`inline-block px-2 py-1 rounded text-sm cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 ${
                                student.scores[problem.problem_number.toString()] !== null ? 'font-medium' : 'text-gray-400'
                              }`}
                              onClick={() => startEditingStudent(student.id)}
                            >
                              {student.scores[problem.problem_number.toString()] ?? '-'}
                            </span>
                          )}
                        </td>
                      ))}
                      <td className="p-2 text-center">
                        <span className="font-bold">
                          {student.totalScore !== null ? `${student.totalScore}点` : '-'}
                        </span>
                      </td>
                      <td className="p-2 text-center">
                        <Badge 
                          className={
                            student.status === 'completed' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-yellow-100 text-yellow-800'
                          }
                        >
                          {student.status === 'completed' ? '完了' : '未完了'}
                        </Badge>
                      </td>
                      <td className="p-2 text-center">
                        <div className="flex gap-1 justify-center">
                          {editingStudents.has(student.id) ? (
                            <>
                              <Button
                                size="sm"
                                onClick={() => saveStudentScores(student.id)}
                                className="h-7 px-2"
                              >
                                <Save className="h-3 w-3" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => cancelEditingStudent(student.id)}
                                className="h-7 px-2"
                              >
                                ×
                              </Button>
                            </>
                          ) : (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => startEditingStudent(student.id)}
                              className="h-7 px-2"
                            >
                              <Edit className="h-3 w-3" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

      </div>
    </DashboardLayout>
  );
}