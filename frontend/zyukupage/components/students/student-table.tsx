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
    <div className="rounded-xl border overflow-hidden">
      {/* Mobile responsive table with horizontal scroll */}
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="min-w-[140px] sm:min-w-[180px]">生徒</TableHead>
              <TableHead className="min-w-[50px] sm:min-w-[60px] whitespace-nowrap text-xs sm:text-sm">学年</TableHead>
              <TableHead className="min-w-[80px] sm:min-w-[100px] hidden md:table-cell whitespace-nowrap text-xs sm:text-sm">教室</TableHead>
              <TableHead className="min-w-[100px] sm:min-w-[120px] hidden lg:table-cell whitespace-nowrap text-xs sm:text-sm">最終受講履歴</TableHead>
              <TableHead className="min-w-[80px] sm:min-w-[100px] text-right whitespace-nowrap text-xs sm:text-sm">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {students.map((student) => (
              <TableRow key={student.id}>
                <TableCell className="min-w-[140px] sm:min-w-[180px]">
                  <div className="flex items-center gap-2 md:gap-3">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src={`/students/${student.id}.jpg`} alt={student.name} />
                      <AvatarFallback>{student.name.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <div className="min-w-0 flex-1">
                      <div className="font-medium truncate">{student.name}</div>
                      <div className="text-xs md:text-sm text-muted-foreground truncate">
                        ID: {student.student_id}
                        {/* Show classroom on mobile */}
                        <span className="md:hidden ml-2">• {student.classroom_name || '未設定'}</span>
                      </div>
                    </div>
                  </div>
                </TableCell>
                <TableCell className="min-w-[60px] sm:min-w-[80px] whitespace-nowrap">
                  <span className="text-xs sm:text-sm font-medium">{formatGrade(student.grade)}</span>
                </TableCell>
                <TableCell className="min-w-[80px] sm:min-w-[100px] hidden md:table-cell whitespace-nowrap">
                  <span className="text-xs sm:text-sm truncate max-w-[100px]">{student.classroom_name || '未設定'}</span>
                </TableCell>
                <TableCell className="min-w-[100px] sm:min-w-[120px] hidden lg:table-cell whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <History className="h-3 w-3 text-muted-foreground" />
                    <span className="text-xs sm:text-sm truncate max-w-[100px]">
                      {student.latest_enrollment 
                        ? `${student.latest_enrollment.year}年${student.latest_enrollment.period === 'spring' ? '春期' : student.latest_enrollment.period === 'summer' ? '夏期' : '冬期'}`
                        : '未設定'
                      }
                    </span>
                  </div>
                </TableCell>
                <TableCell className="min-w-[80px] sm:min-w-[100px] text-right whitespace-nowrap">
                  <div className="flex items-center justify-end gap-1">
                    <Link href={`/students/${student.student_id}`}>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="h-8 w-8 p-0"
                        title="詳細"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </Link>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="h-8 w-8 p-0"
                      onClick={() => handleEdit(student)}
                      title="編集"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="h-8 w-8 p-0 text-red-500 hover:text-red-700"
                      onClick={() => handleDelete(student)}
                      disabled={deleteStudentMutation.isPending}
                      title="削除"
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
    </div>
  );
}