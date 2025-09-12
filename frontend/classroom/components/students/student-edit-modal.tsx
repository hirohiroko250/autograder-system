'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { User, GraduationCap, Building, Calendar, Plus, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studentApi, schoolApi } from '@/lib/api-client';
import { Student } from '@/lib/types';
import { formatGrade } from '@/lib/utils';

interface StudentEditModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  student: Student | null;
}

interface Enrollment {
  id?: number;
  year: string;
  period: string;
  isNew?: boolean;
}

export function StudentEditModal({ open, onOpenChange, student }: StudentEditModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    grade: '',
    classroom: '',
  });
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [newEnrollment, setNewEnrollment] = useState({ year: '2025', period: 'summer' });
  const [loading, setLoading] = useState(false);
  const queryClient = useQueryClient();

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

  const { data: classroomsData } = useQuery({
    queryKey: ['classrooms'],
    queryFn: async () => {
      const response = await schoolApi.getClassrooms();
      return response;
    },
    enabled: open,
  });

  // 生徒のEnrollment情報を取得
  const { data: enrollmentData } = useQuery({
    queryKey: ['student-enrollments', student?.id],
    queryFn: async () => {
      if (!student?.id) return [];
      return await studentApi.getStudentEnrollments(student.id);
    },
    enabled: open && !!student?.id,
  });

  const classrooms = classroomsData?.results || [];

  // 小学1年生から中学3年生まで（1-9）
  const grades = Array.from({ length: 9 }, (_, i) => i + 1);

  // 生徒データをフォームにセット
  useEffect(() => {
    if (student && open) {
      console.log('Setting form data for student:', student);
      setFormData({
        name: student.name || '',
        grade: student.grade || '',
        classroom: student.classroom?.toString() || '',
      });
    }
  }, [student, open]);

  // Enrollment データをセット
  useEffect(() => {
    if (enrollmentData && open) {
      setEnrollments(enrollmentData.map((enrollment: any) => ({
        id: enrollment.id,
        year: enrollment.year.toString(),
        period: enrollment.period,
      })));
    }
  }, [enrollmentData, open]);

  // 年度・期間追加
  const addEnrollment = () => {
    const exists = enrollments.some(
      enrollment => enrollment.year === newEnrollment.year && enrollment.period === newEnrollment.period
    );
    
    if (exists) {
      toast.error('同じ年度・期間の登録が既に存在します');
      return;
    }

    setEnrollments(prev => [...prev, { ...newEnrollment, isNew: true }]);
    toast.success('年度・期間を追加しました');
  };

  // 年度・期間削除
  const removeEnrollment = (index: number) => {
    setEnrollments(prev => prev.filter((_, i) => i !== index));
    toast.success('年度・期間を削除しました');
  };

  const updateStudentMutation = useMutation({
    mutationFn: (data: any) => {
      if (!student) throw new Error('生徒が選択されていません');
      return studentApi.updateStudent(student.id, data);
    },
    onSuccess: () => {
      toast.success('生徒情報を更新しました');
      queryClient.invalidateQueries({ queryKey: ['students'] });
      queryClient.invalidateQueries({ queryKey: ['students-stats'] });
      handleClose();
    },
    onError: (error: any) => {
      console.error('Update error:', error);
      if (error.response?.data) {
        console.error('Error details:', error.response.data);
        const errorMessage = Object.entries(error.response.data)
          .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(', ') : messages}`)
          .join('; ');
        toast.error(`更新エラー: ${errorMessage}`);
      } else {
        toast.error('生徒情報の更新に失敗しました');
      }
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!student) return;

    if (!formData.name.trim()) {
      toast.error('氏名を入力してください');
      return;
    }
    
    if (!formData.grade) {
      toast.error('学年を選択してください');
      return;
    }

    setLoading(true);
    try {
      const submitData = {
        name: formData.name.trim(),
        grade: formData.grade,
        classroom: parseInt(formData.classroom) || null,
      };
      
      updateStudentMutation.mutate(submitData);
    } catch (error) {
      toast.error('更新に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      name: '',
      grade: '',
      classroom: '',
    });
    setEnrollments([]);
    setNewEnrollment({ year: '2025', period: 'summer' });
    onOpenChange(false);
  };

  if (!student) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            生徒情報編集
          </DialogTitle>
          <DialogDescription>
            生徒の基本情報を編集できます
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">氏名 *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="田中太郎"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="grade">学年 *</Label>
              <Select value={formData.grade} onValueChange={(value) => setFormData(prev => ({ ...prev, grade: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="学年を選択" />
                </SelectTrigger>
                <SelectContent>
                  {grades.map(grade => (
                    <SelectItem key={grade} value={grade.toString()}>
                      {formatGrade(grade)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>


            <div className="space-y-2">
              <Label htmlFor="classroom">教室</Label>
              <Select value={formData.classroom} onValueChange={(value) => setFormData(prev => ({ ...prev, classroom: value }))}>
                <SelectTrigger>
                  <SelectValue placeholder="教室を選択" />
                </SelectTrigger>
                <SelectContent>
                  {classrooms.map((classroom: any) => (
                    <SelectItem key={classroom.id} value={classroom.id.toString()}>
                      {classroom.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

          </div>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                受講履歴（年度・期間）
              </CardTitle>
              <CardDescription>
                生徒が受講した年度と期間を管理できます
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* 既存の年度・期間一覧 */}
              <div className="space-y-2">
                <Label>登録済み年度・期間</Label>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {enrollments.length === 0 ? (
                    <p className="text-sm text-muted-foreground">受講履歴がありません</p>
                  ) : (
                    enrollments.map((enrollment, index) => (
                      <div key={index} className="flex items-center justify-between p-2 border rounded-lg">
                        <div className="flex items-center gap-2">
                          <Badge variant={enrollment.isNew ? 'secondary' : 'default'}>
                            {years.find(y => y.value === enrollment.year)?.label} - {periods.find(p => p.value === enrollment.period)?.label}
                          </Badge>
                          {enrollment.isNew && (
                            <Badge variant="outline" className="text-xs">
                              新規追加
                            </Badge>
                          )}
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeEnrollment(index)}
                          className="h-6 w-6 p-0 text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* 新しい年度・期間追加 */}
              <div className="space-y-3 border-t pt-4">
                <Label>新しい年度・期間を追加</Label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                  <Select value={newEnrollment.year} onValueChange={(value) => setNewEnrollment(prev => ({ ...prev, year: value }))}>
                    <SelectTrigger>
                      <SelectValue placeholder="年度選択" />
                    </SelectTrigger>
                    <SelectContent>
                      {years.map((year) => (
                        <SelectItem key={year.value} value={year.value}>
                          {year.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select value={newEnrollment.period} onValueChange={(value) => setNewEnrollment(prev => ({ ...prev, period: value }))}>
                    <SelectTrigger>
                      <SelectValue placeholder="期間選択" />
                    </SelectTrigger>
                    <SelectContent>
                      {periods.map((period) => (
                        <SelectItem key={period.value} value={period.value}>
                          {period.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button type="button" onClick={addEnrollment} size="sm">
                    <Plus className="h-4 w-4 mr-1" />
                    追加
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="space-y-2">
            <Label>現在の情報</Label>
            <div className="p-3 bg-gray-50 rounded-lg space-y-2">
              <div className="text-sm">
                <span className="font-medium">生徒ID:</span> {student.student_id}
              </div>
              <div className="text-sm">
                <span className="font-medium">登録日:</span> {new Date(student.created_at).toLocaleDateString('ja-JP')}
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-2">
            <Button type="button" variant="outline" onClick={handleClose}>
              キャンセル
            </Button>
            <Button 
              type="submit" 
              disabled={loading || updateStudentMutation.isPending}
            >
              {loading || updateStudentMutation.isPending ? '更新中...' : '更新'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}