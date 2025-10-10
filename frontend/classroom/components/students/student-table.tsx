'use client';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Edit, Trash2, Eye, History } from 'lucide-react';
import Link from 'next/link';
import { Student } from '@/lib/types';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { studentApi } from '@/lib/api-client';
import { toast } from 'sonner';
import { useState } from 'react';
import { formatGrade } from '@/lib/utils';

interface StudentTableProps {
  students: Student[];
  onEditStudent?: (student: Student) => void;
}

export function StudentTable({ students, onEditStudent }: StudentTableProps) {
  const queryClient = useQueryClient();
  
  const deleteStudentMutation = useMutation({
    mutationFn: studentApi.deleteStudent,
    onSuccess: () => {
      toast.success('生徒を削除しました');
      queryClient.invalidateQueries({ queryKey: ['students'] });
      queryClient.invalidateQueries({ queryKey: ['students-stats'] });
    },
    onError: (error: any) => {
      toast.error('生徒の削除に失敗しました');
      console.error('Delete error:', error);
    },
  });

  const handleDelete = (student: Student) => {
    if (confirm(`${student.name}さんを削除してもよろしいですか？`)) {
      deleteStudentMutation.mutate(student.id);
    }
  };

  const handleEdit = (student: Student) => {
    if (onEditStudent) {
      onEditStudent(student);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'enrolled':
        return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">入会</Badge>;
      case 'new':
        return <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100">新規</Badge>;
      case 'withdrawn':
        return <Badge className="bg-red-100 text-red-800 hover:bg-red-100">退会</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <>
      {/* デスクトップ表示 */}
      <div className="hidden md:block rounded-xl border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>生徒</TableHead>
              <TableHead>学年</TableHead>
              <TableHead>教室</TableHead>
              <TableHead>最終受講履歴</TableHead>
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {students.map((student) => (
              <TableRow key={student.id}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src={`/students/${student.id}.jpg`} alt={student.name} />
                      <AvatarFallback>{student.name.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="font-medium">{student.name}</div>
                      <div className="text-sm text-muted-foreground">ID: {student.student_id}</div>
                    </div>
                  </div>
                </TableCell>
                <TableCell>{formatGrade(student.grade)}</TableCell>
                <TableCell>{student.classroom_name || '未設定'}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <History className="h-3 w-3 text-muted-foreground" />
                    <span className="text-sm">
                      {student.latest_enrollment
                        ? `${student.latest_enrollment.year}年${student.latest_enrollment.period === 'spring' ? '春期' : student.latest_enrollment.period === 'summer' ? '夏期' : '冬期'}`
                        : '未設定'
                      }
                    </span>
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Link href={`/students/${student.student_id}`}>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      onClick={() => handleEdit(student)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 text-red-500 hover:text-red-700"
                      onClick={() => handleDelete(student)}
                      disabled={deleteStudentMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* モバイル表示 */}
      <div className="md:hidden space-y-4">
        {students.map((student) => (
          <div key={student.id} className="border rounded-lg p-4 space-y-3">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3 flex-1">
                <Avatar className="h-10 w-10">
                  <AvatarImage src={`/students/${student.id}.jpg`} alt={student.name} />
                  <AvatarFallback>{student.name.charAt(0)}</AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <div className="font-medium">{student.name}</div>
                  <div className="text-xs text-muted-foreground">ID: {student.student_id}</div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-muted-foreground">学年:</span>
                <span className="ml-1 font-medium">{formatGrade(student.grade)}</span>
              </div>
              <div>
                <span className="text-muted-foreground">教室:</span>
                <span className="ml-1 font-medium">{student.classroom_name || '未設定'}</span>
              </div>
              <div className="col-span-2">
                <span className="text-muted-foreground">最終受講:</span>
                <span className="ml-1 font-medium">
                  {student.latest_enrollment
                    ? `${student.latest_enrollment.year}年${student.latest_enrollment.period === 'spring' ? '春期' : student.latest_enrollment.period === 'summer' ? '夏期' : '冬期'}`
                    : '未設定'
                  }
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2 border-t">
              <Link href={`/students/${student.student_id}`} className="flex-1">
                <Button variant="outline" size="sm" className="w-full">
                  <Eye className="h-4 w-4 mr-2" />
                  詳細
                </Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={() => handleEdit(student)}
              >
                <Edit className="h-4 w-4 mr-2" />
                編集
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="text-red-500 hover:text-red-700"
                onClick={() => handleDelete(student)}
                disabled={deleteStudentMutation.isPending}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}