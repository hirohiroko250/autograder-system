'use client';

export const dynamic = 'force-dynamic';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { ArrowLeft, Users, Search, Plus, Edit, Trash2, FileText } from 'lucide-react';
import { schoolApi, studentApi } from '@/lib/api-client';
import { StudentRegistrationModal } from '@/components/students/student-registration-modal';
import { StudentImportModal } from '@/components/students/student-import-modal';

interface Student {
  id: number;
  student_id: string;
  name: string;
  grade: string;
  classroom_name: string;
  created_at: string;
  status?: string;
}

interface Classroom {
  id: number;
  name: string;
  classroom_id: string;
  school_name: string;
  student_count: number;
  is_active: boolean;
}

export default function ClassroomDetailPage() {
  const params = useParams();
  const router = useRouter();
  const classroomId = params?.id as string;
  
  const [search, setSearch] = useState('');
  const [isRegistrationModalOpen, setIsRegistrationModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);

  // 教室情報を取得
  const { data: classroomsData } = useQuery({
    queryKey: ['classrooms'],
    queryFn: () => schoolApi.getClassrooms(),
  });

  const classroom = classroomsData?.results?.find((c: any) => c.id === parseInt(classroomId));

  // 教室の生徒一覧を取得
  const { data: students } = useQuery({
    queryKey: ['students', search, classroomId],
    queryFn: async () => {
      const params: any = {};
      if (search) params.search = search;
      if (classroomId) params.classroom = parseInt(classroomId);
      
      // 大きなページサイズを指定して全件取得
      params.page_size = 10000;
      
      const response = await studentApi.getStudents(params);
      return response.results;
    },
    enabled: !!classroomId,
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">有効</Badge>;
      case 'pending':
        return <Badge className="bg-orange-100 text-orange-800 hover:bg-orange-100">保留</Badge>;
      case 'inactive':
        return <Badge className="bg-gray-100 text-gray-800 hover:bg-gray-100">無効</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const handleCSVExport = () => {
    if (!students || students.length === 0) return;
    
    const headers = ['生徒ID', '氏名', '学年', '年度', '期', '登録日'];
    const csvData = students.map((student: any) => [
      student.student_id,
      student.name,
      student.grade,
      student.year || '2025',
      student.period || 'summer',
      new Date(student.created_at).toLocaleDateString('ja-JP')
    ]);
    
    const csvContent = [headers, ...csvData]
      .map(row => row.join(','))
      .join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${classroom?.name}_生徒一覧.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!classroom) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-2">教室が見つかりません</h2>
            <Button onClick={() => router.push('/classrooms')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              教室一覧に戻る
            </Button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* ヘッダー */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => router.push('/classrooms')}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              教室一覧に戻る
            </Button>
            <div>
              <h1 className="text-3xl font-bold">{classroom.name}</h1>
              <p className="text-muted-foreground">
                教室ID: {classroom.classroom_id} | 学校: {classroom.school_name}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              onClick={() => router.push(`/classrooms/${classroomId}/scores/entry?year=2025&period=summer`)}
              className="mr-2"
            >
              <Edit className="h-4 w-4 mr-2" />
              スコア入力
            </Button>
            <Badge variant={classroom.is_active ? 'default' : 'secondary'}>
              {classroom.is_active ? 'アクティブ' : '非アクティブ'}
            </Badge>
          </div>
        </div>

        {/* 統計情報 */}
        <div className="grid gap-6 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">総生徒数</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{students?.length || 0}</div>
              <p className="text-xs text-muted-foreground">
                この教室の生徒数
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">有効な生徒</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {students?.filter((s: any) => s.status !== 'inactive').length || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                アクティブな生徒
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">学年数</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {new Set(students?.map((s: any) => s.grade)).size || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                異なる学年の数
              </p>
            </CardContent>
          </Card>
        </div>

        {/* 生徒管理 */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>生徒一覧</CardTitle>
                <CardDescription>
                  {classroom.name}に所属する生徒の一覧です
                </CardDescription>
              </div>
              <div className="flex items-center space-x-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => router.push(`/classrooms/${classroomId}/scores/entry?year=2025&period=summer`)}
                  className="bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  <Edit className="h-4 w-4 mr-2" />
                  スコア入力
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setIsImportModalOpen(true)}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  CSVインポート
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={handleCSVExport}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  CSVエクスポート
                </Button>
                <Button 
                  size="sm"
                  onClick={() => setIsRegistrationModalOpen(true)}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  生徒登録
                </Button>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="生徒を検索..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-xl border overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>生徒</TableHead>
                    <TableHead>学年</TableHead>
                    <TableHead>ステータス</TableHead>
                    <TableHead>登録日</TableHead>
                    <TableHead className="text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {students?.map((student: any) => (
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
                      <TableCell>{student.grade}</TableCell>
                      <TableCell>{getStatusBadge(student.status || 'active')}</TableCell>
                      <TableCell>
                        {new Date(student.created_at).toLocaleDateString('ja-JP')}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-red-500 hover:text-red-700">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* モーダル */}
      <StudentRegistrationModal
        open={isRegistrationModalOpen}
        onOpenChange={setIsRegistrationModalOpen}
        classroomId={parseInt(classroomId)}
      />

      <StudentImportModal
        open={isImportModalOpen}
        onOpenChange={setIsImportModalOpen}
        classroomId={parseInt(classroomId)}
      />
    </DashboardLayout>
  );
}