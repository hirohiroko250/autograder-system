'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Edit, Save, CheckSquare, Square } from 'lucide-react';
import { toast } from 'sonner';

interface Student {
  id: string;
  name: string;
  classroom?: string;
  attendance?: boolean;
}

interface Problem {
  number: number;
  maxScore: number;
  title?: string;
}

interface IndividualProblemTableProps {
  students: Student[];
  problems?: Problem[];
  scores: Record<string, Record<string, number>>;
  onScoreChange: (scores: Record<string, Record<string, number>>) => void;
  onAttendanceChange: (studentId: string, attendance: boolean) => void;
}

export function IndividualProblemTable({
  students,
  problems = Array.from({ length: Math.min(5, 10) }, (_, i) => ({
    number: i + 1,
    maxScore: 20,
    title: `大問${i + 1}`
  })),
  scores,
  onScoreChange,
  onAttendanceChange
}: IndividualProblemTableProps) {
  const [editingStudents, setEditingStudents] = useState<Set<string>>(new Set());
  const [tempScores, setTempScores] = useState<Record<string, Record<string, string>>>({});
  const [selectedStudents, setSelectedStudents] = useState<Set<string>>(new Set());

  const startEditingStudent = (studentId: string) => {
    setEditingStudents(prev => new Set(Array.from(prev).concat(studentId)));
    // 現在のスコアを一時保存にコピー
    const currentScores = scores[studentId] || {};
    setTempScores(prev => ({
      ...prev,
      [studentId]: Object.fromEntries(
        problems.map(p => [p.number.toString(), String(currentScores[p.number.toString()] || '')])
      )
    }));
  };

  const saveStudentScores = (studentId: string) => {
    const tempScore = tempScores[studentId];
    if (!tempScore) return;

    const newScores = { ...scores };
    if (!newScores[studentId]) {
      newScores[studentId] = {};
    }

    let hasErrors = false;
    problems.forEach(problem => {
      const problemKey = problem.number.toString();
      const scoreValue = tempScore[problemKey];
      if (scoreValue && scoreValue !== '') {
        const score = Number(scoreValue);
        // バリデーション: 満点以上は無効
        if (score > problem.maxScore) {
          toast.error(`問題${problem.number}の得点が満点（${problem.maxScore}点）を超えています`);
          hasErrors = true;
          return;
        }
        if (score < 0) {
          toast.error(`問題${problem.number}の得点は0以上である必要があります`);
          hasErrors = true;
          return;
        }
        newScores[studentId][problemKey] = score;
      } else {
        newScores[studentId][problemKey] = 0;
      }
    });

    if (!hasErrors) {
      onScoreChange(newScores);
      setEditingStudents(prev => {
        const newSet = new Set(prev);
        newSet.delete(studentId);
        return newSet;
      });
      toast.success('スコアを保存しました');
    }
  };

  const cancelEditingStudent = (studentId: string) => {
    setEditingStudents(prev => {
      const newSet = new Set(prev);
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

  const toggleStudentSelection = (studentId: string) => {
    setSelectedStudents(prev => {
      const newSet = new Set(prev);
      if (newSet.has(studentId)) {
        newSet.delete(studentId);
      } else {
        newSet.add(studentId);
      }
      return newSet;
    });
  };

  const toggleAllStudents = () => {
    if (selectedStudents.size === students.length) {
      setSelectedStudents(new Set());
    } else {
      setSelectedStudents(new Set(students.map(s => s.id)));
    }
  };

  const toggleAttendance = (studentId: string, currentAttendance: boolean) => {
    onAttendanceChange(studentId, !currentAttendance);
  };

  const calculateTotalScore = (studentId: string) => {
    const studentScores = scores[studentId] || {};
    return problems.reduce((total, problem) => {
      const score = studentScores[problem.number.toString()] || 0;
      return total + score;
    }, 0);
  };

  const calculateMaxTotalScore = () => {
    return problems.reduce((total, problem) => total + problem.maxScore, 0);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>点数入力テーブル</CardTitle>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleAllStudents}
              className="flex items-center gap-2"
            >
              {selectedStudents.size === students.length ? (
                <CheckSquare className="h-4 w-4" />
              ) : (
                <Square className="h-4 w-4" />
              )}
              全選択
            </Button>
          </div>
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
                    {selectedStudents.size === students.length ? (
                      <CheckSquare className="h-4 w-4" />
                    ) : (
                      <Square className="h-4 w-4" />
                    )}
                  </Button>
                </th>
                <th className="text-left p-2">生徒名</th>
                <th className="text-left p-2">教室</th>
                <th className="text-left p-2">出席</th>
                {problems.map((problem) => (
                  <th key={problem.number} className="text-center p-2 min-w-[80px]">
                    <div className="flex flex-col">
                      <span className="font-medium">{problem.title || `大問${problem.number}`}</span>
                      <span className="text-xs text-gray-500">/{problem.maxScore}点</span>
                    </div>
                  </th>
                ))}
                <th className="text-center p-2">合計</th>
                <th className="text-center p-2">操作</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => (
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
                      {student.classroom || 'N/A'}
                    </Badge>
                  </td>
                  <td className="p-2 text-center">
                    <Button
                      size="sm"
                      variant={student.attendance ? 'default' : 'secondary'}
                      onClick={() => toggleAttendance(student.id, student.attendance || false)}
                      className={student.attendance 
                        ? 'bg-green-100 text-green-800 hover:bg-green-200' 
                        : 'bg-red-100 text-red-800 hover:bg-red-200'
                      }
                    >
                      {student.attendance ? '出席' : '欠席'}
                    </Button>
                  </td>
                  {problems.map((problem) => (
                    <td key={problem.number} className="p-1 text-center">
                      {editingStudents.has(student.id) ? (
                        <Input
                          type="number"
                          min="0"
                          max={problem.maxScore}
                          value={tempScores[student.id]?.[problem.number.toString()] || ''}
                          onChange={(e) => updateTempScore(student.id, problem.number.toString(), e.target.value)}
                          className="w-16 h-8 text-center text-sm"
                          placeholder="0"
                        />
                      ) : (
                        <span 
                          className={`inline-block px-2 py-1 rounded text-sm cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 ${
                            scores[student.id]?.[problem.number.toString()] !== undefined ? 'font-medium' : 'text-gray-400'
                          }`}
                          onClick={() => startEditingStudent(student.id)}
                        >
                          {scores[student.id]?.[problem.number.toString()] ?? '-'}
                        </span>
                      )}
                    </td>
                  ))}
                  <td className="p-2 text-center">
                    <span className="font-bold">
                      {calculateTotalScore(student.id)}点 / {calculateMaxTotalScore()}点
                    </span>
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
  );
}