'use client';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Edit } from 'lucide-react';

interface Student {
  id: string;
  name: string;
  classroom: string;
}

interface BigQuestionTableProps {
  students: Student[];
  subject: string;
  scores: Record<string, any>;
  onScoreChange: (scores: Record<string, any>) => void;
  onSubQuestionClick: (question: any) => void;
  questionCount?: number; // 大問数（デフォルト6問、最大10問）
}

export function BigQuestionTable({ 
  students, 
  subject, 
  scores, 
  onScoreChange, 
  onSubQuestionClick,
  questionCount = 6
}: BigQuestionTableProps) {
  // 大問数を動的に設定（最大10問）
  const clampedQuestionCount = Math.min(Math.max(questionCount, 1), 10);
  const bigQuestions = Array.from({ length: clampedQuestionCount }, (_, i) => i + 1);

  const handleScoreChange = (studentId: string, questionId: number, value: string) => {
    const newScores = { ...scores };
    if (!newScores[studentId]) {
      newScores[studentId] = {};
    }
    newScores[studentId][`q${questionId}`] = value;
    onScoreChange(newScores);
  };

  const handleSubQuestionClick = (questionId: number) => {
    onSubQuestionClick({
      id: questionId,
      subject,
      students,
      title: `大問${questionId}の小問詳細`
    });
  };

  return (
    <div className="rounded-xl border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-48">生徒</TableHead>
            {bigQuestions.map((q) => (
              <TableHead key={q} className="text-center min-w-24">
                <div className="flex items-center justify-center gap-2">
                  <span>大問{q}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0"
                    onClick={() => handleSubQuestionClick(q)}
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                </div>
              </TableHead>
            ))}
            <TableHead className="text-center">合計</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {students.map((student) => (
            <TableRow key={student.id}>
              <TableCell>
                <div>
                  <div className="font-medium">{student.name}</div>
                  <div className="text-sm text-muted-foreground">
                    {student.classroom}
                  </div>
                </div>
              </TableCell>
              {bigQuestions.map((q) => (
                <TableCell key={q} className="text-center">
                  <Input
                    type="number"
                    min="0"
                    max="20"
                    value={scores[student.id]?.[`q${q}`] || ''}
                    onChange={(e) => handleScoreChange(student.id, q, e.target.value)}
                    className="w-16 text-center rounded-lg"
                    placeholder="0"
                  />
                </TableCell>
              ))}
              <TableCell className="text-center font-medium">
                {Object.values(scores[student.id] || {})
                  .reduce((sum: number, score: any) => sum + (parseInt(score) || 0), 0)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}