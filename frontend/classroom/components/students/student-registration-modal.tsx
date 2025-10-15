'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Shuffle, User, Phone, GraduationCap, Building, Calendar } from 'lucide-react';
import { toast } from 'sonner';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studentApi, schoolApi } from '@/lib/api-client';
import { formatGrade } from '@/lib/utils';

interface StudentRegistrationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  classroomId?: number;
}

export function StudentRegistrationModal({ open, onOpenChange, classroomId }: StudentRegistrationModalProps) {
  const [formData, setFormData] = useState({
    student_id: '',
    name: '',
    grade: '1',
    classroom: classroomId ? classroomId.toString() : '',
    year: '2025',
    period: 'summer',
  });
  const [loading, setLoading] = useState(false);
  const queryClient = useQueryClient();

  const { data: classroomsData } = useQuery({
    queryKey: ['classrooms'],
    queryFn: async () => {
      const response = await schoolApi.getClassrooms();
      return response;
    },
    enabled: open,
  });

  const classrooms = classroomsData?.results || [];

  // 小学1年生から中学3年生まで（1-9）
  const grades = Array.from({ length: 9 }, (_, i) => i + 1);
  
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

  // モーダルが開くたびにフォームデータをリセット
  useEffect(() => {
    if (open) {
      setFormData({
        student_id: '',
        name: '',
        grade: '1',
        classroom: classroomId ? classroomId.toString() : '',
        year: '2025',
        period: 'summer',
      });
    }
  }, [open, classroomId]);

  const createStudentMutation = useMutation({
    mutationFn: studentApi.createStudent,
    onSuccess: () => {
      toast.success('生徒を登録しました');
      queryClient.invalidateQueries({ queryKey: ['students'] });
      handleClose();
    },
    onError: (error: any) => {
      console.error('生徒登録エラー:', error);
      toast.error('生徒の登録に失敗しました');
    },
  });

  const generateStudentId = async () => {
    if (!formData.classroom) {
      toast.error('教室を選択してください');
      return;
    }
    
    setLoading(true);
    try {
      const response = await studentApi.getNextStudentId(formData.classroom);
      setFormData(prev => ({ ...prev, student_id: response.next_id }));
      toast.success('生徒IDを生成しました');
    } catch (error) {
      toast.error('生徒IDの生成に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.student_id.match(/^[0-9]{1,10}$/)) {
      toast.error('生徒IDは1〜10桁の数字で入力してください');
      return;
    }

    createStudentMutation.mutate({
      student_id: formData.student_id,
      name: formData.name,
      grade: formData.grade,
      classroom: parseInt(formData.classroom),
      year: parseInt(formData.year),
      period: formData.period,
    });
  };

  const handleClose = () => {
    setFormData({
      student_id: '',
      name: '',
      grade: '1',
      classroom: '',
      year: '2025',
      period: 'summer',
    });
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>生徒登録</DialogTitle>
          <DialogDescription>
            新しい生徒を登録します
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <User className="h-4 w-4" />
                基本情報
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="student-id">生徒ID</Label>
                <div className="flex gap-2">
                  <Input
                    id="student-id"
                    value={formData.student_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, student_id: e.target.value }))}
                    placeholder="1〜10桁の数字を入力"
                    pattern="[0-9]{1,10}"
                    maxLength={10}
                    className="rounded-xl"
                    required
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={generateStudentId}
                    disabled={loading}
                    className="rounded-xl"
                  >
                    <Shuffle className="h-4 w-4" />
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  1〜10桁の数字で入力してください（例：12345、123456789）
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="name">氏名</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="田中太郎"
                  className="rounded-xl"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="grade">学年</Label>
                <Select value={formData.grade} onValueChange={(value) => setFormData(prev => ({ ...prev, grade: value }))}>
                  <SelectTrigger className="rounded-xl">
                    <GraduationCap className="h-4 w-4 mr-2" />
                    <SelectValue placeholder="学年を選択" />
                  </SelectTrigger>
                  <SelectContent>
                    {grades.map((grade) => (
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
                  <SelectTrigger className="rounded-xl">
                    <Building className="h-4 w-4 mr-2" />
                    <SelectValue placeholder="教室を選択" />
                  </SelectTrigger>
                  <SelectContent>
                    {classrooms?.map((classroom) => (
                      <SelectItem key={classroom.id} value={classroom.id.toString()}>
                        {classroom.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="year">年度</Label>
                <Select value={formData.year} onValueChange={(value) => setFormData(prev => ({ ...prev, year: value }))}>
                  <SelectTrigger className="rounded-xl">
                    <Calendar className="h-4 w-4 mr-2" />
                    <SelectValue placeholder="年度を選択" />
                  </SelectTrigger>
                  <SelectContent>
                    {years.map((year) => (
                      <SelectItem key={year.value} value={year.value}>
                        {year.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="period">期間</Label>
                <Select value={formData.period} onValueChange={(value) => setFormData(prev => ({ ...prev, period: value }))}>
                  <SelectTrigger className="rounded-xl">
                    <Calendar className="h-4 w-4 mr-2" />
                    <SelectValue placeholder="期間を選択" />
                  </SelectTrigger>
                  <SelectContent>
                    {periods.map((period) => (
                      <SelectItem key={period.value} value={period.value}>
                        {period.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

            </CardContent>
          </Card>

          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              className="flex-1 rounded-xl"
            >
              キャンセル
            </Button>
            <Button
              type="submit"
              disabled={createStudentMutation.isPending}
              className="flex-1 rounded-xl bg-primary hover:bg-primary/90"
            >
              {createStudentMutation.isPending ? '登録中...' : '登録'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}