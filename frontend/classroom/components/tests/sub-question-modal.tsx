'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { CheckCircle, XCircle, Triangle, Save } from 'lucide-react';

interface SubQuestionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  question: any;
  onSave: (data: any) => void;
}

export function SubQuestionModal({ open, onOpenChange, question, onSave }: SubQuestionModalProps) {
  const [answers, setAnswers] = useState<Record<string, Record<string, string>>>({});

  if (!question) return null;

  const subQuestions = Array.from({ length: 5 }, (_, i) => i + 1);
  const answerTypes = [
    { value: 'correct', label: '○', icon: CheckCircle, color: 'text-green-600' },
    { value: 'incorrect', label: '×', icon: XCircle, color: 'text-red-600' },
    { value: 'partial', label: '△', icon: Triangle, color: 'text-orange-600' },
  ];

  const handleAnswerChange = (studentId: string, subQuestionId: number, answer: string) => {
    setAnswers(prev => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        [`sub${subQuestionId}`]: answer
      }
    }));
  };

  const handleSave = () => {
    onSave(answers);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>{question.title}</DialogTitle>
          <DialogDescription>
            小問の〇×△を入力してください
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="text-sm font-medium">評価基準：</div>
            {answerTypes.map((type) => (
              <div key={type.value} className="flex items-center gap-2">
                <type.icon className={`h-4 w-4 ${type.color}`} />
                <span className="text-sm">{type.label}</span>
              </div>
            ))}
          </div>

          <div className="rounded-xl border overflow-hidden max-h-96 overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-48">生徒</TableHead>
                  {subQuestions.map((sub) => (
                    <TableHead key={sub} className="text-center min-w-20">
                      小問{sub}
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {question.students?.map((student: any) => (
                  <TableRow key={student.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{student.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {student.classroom}
                        </div>
                      </div>
                    </TableCell>
                    {subQuestions.map((sub) => (
                      <TableCell key={sub} className="text-center">
                        <div className="flex justify-center gap-1">
                          {answerTypes.map((type) => (
                            <Button
                              key={type.value}
                              variant={
                                answers[student.id]?.[`sub${sub}`] === type.value 
                                  ? 'default' 
                                  : 'outline'
                              }
                              size="sm"
                              className="h-8 w-8 p-0"
                              onClick={() => handleAnswerChange(student.id, sub, type.value)}
                            >
                              <type.icon className={`h-3 w-3 ${
                                answers[student.id]?.[`sub${sub}`] === type.value 
                                  ? 'text-white' 
                                  : type.color
                              }`} />
                            </Button>
                          ))}
                        </div>
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          <div className="flex justify-between pt-4">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="rounded-xl"
            >
              キャンセル
            </Button>
            <Button
              onClick={handleSave}
              className="rounded-xl bg-primary hover:bg-primary/90"
            >
              <Save className="h-4 w-4 mr-2" />
              保存
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}