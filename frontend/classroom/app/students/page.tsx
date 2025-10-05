'use client';

export const dynamic = 'force-dynamic';

import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { PermissionGuard } from '@/components/auth/permission-guard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AdvancedSearch, commonFilterOptions } from '@/components/ui/advanced-search';
import { StudentTable } from '@/components/students/student-table';
import { StudentImportModal } from '@/components/students/student-import-modal';
import { StudentRegistrationModal } from '@/components/students/student-registration-modal';
import { StudentEditModal } from '@/components/students/student-edit-modal';
import { useQuery } from '@tanstack/react-query';
import { Search, Plus, Upload, Download, Filter } from 'lucide-react';
import { useState } from 'react';
import { studentApi, schoolApi } from '@/lib/api-client';
import { useAuth } from '@/lib/auth-context';

export default function StudentsPage() {
  const { user } = useAuth();
  
  console.log('StudentsPage: Current user:', user);
  console.log('StudentsPage: User permissions:', user?.permissions);
  const [classroom, setClassroom] = useState('all');
  const [year, setYear] = useState('all');
  const [period, setPeriod] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchFilters, setSearchFilters] = useState<any>({});
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [registrationModalOpen, setRegistrationModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<any>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(50);

  const years = [
    { value: 'all', label: '全年度' },
    { value: '2025', label: '2025年度' },
          { value: '2026', label: '2026年度' },
          { value: '2027', label: '2027年度' },
    
    
  ];

  const periods = [
    { value: 'all', label: '全期間' },
    { value: 'spring', label: '春期' },
    { value: 'summer', label: '夏期' },
    { value: 'winter', label: '冬期' },
  ];

  // 高度検索のフィルターオプション
  const filterOptions = [
    commonFilterOptions.studentGrade,
    commonFilterOptions.studentStatus,
    commonFilterOptions.studentId,
  ];

  // 検索ハンドラー
  const handleSearch = (query: string, filters: any) => {
    setSearchQuery(query);
    setSearchFilters(filters);
    setCurrentPage(1); // ページを1にリセット
  };

  // 検索クリアハンドラー
  const handleClearSearch = () => {
    setSearchQuery('');
    setSearchFilters({});
    setCurrentPage(1); // ページを1にリセット
  };
  
  // フィルター変更時にページをリセット
  const handleClassroomChange = (value: string) => {
    setClassroom(value);
    setCurrentPage(1);
  };
  
  const handleYearChange = (value: string) => {
    setYear(value);
    setCurrentPage(1);
  };
  
  const handlePeriodChange = (value: string) => {
    setPeriod(value);
    setCurrentPage(1);
  };

  // フィルター条件があるかチェック（従来のフィルター + 新しい検索）
  const hasActiveFilters = classroom !== 'all' || year !== 'all' || period !== 'all' || searchQuery || Object.keys(searchFilters).length > 0;

  const { data: students, isLoading: studentsLoading } = useQuery({
    queryKey: ['students', classroom, year, period, searchQuery, searchFilters],
    queryFn: async () => {
      // デバッグログ
      console.log('フィルター条件:', { classroom, year, period, searchQuery, searchFilters });
      console.log('年度・期間チェック:', year !== 'all', period !== 'all', '→', year !== 'all' && period !== 'all');
      
      // 年度と期間の両方が指定されている場合
      if (year !== 'all' && period !== 'all') {
        const response = await studentApi.getStudentsByEnrollment(year, period);
        let results = response.results;
        
        // 教室フィルターを適用
        if (classroom !== 'all') {
          results = results.filter((student: any) => {
            const studentClassroomId = student.classroom?.toString() || student.classroom_id?.toString();
            return studentClassroomId === classroom;
          });
        }
        
        // 検索フィルターを適用
        if (searchQuery) {
          results = results.filter((student: any) => 
            student.name?.includes(searchQuery) ||
            student.student_id?.includes(searchQuery)
          );
        }
        
        console.log('年度・期間フィルター結果:', results.length, '件');
        return results;
      }
      
      // 通常のフィルター（教室、検索など）
      const params: any = {};
      if (classroom !== 'all') params.classroom = classroom;
      if (searchQuery) params.search = searchQuery;
      
      // 大きなページサイズを指定して全件取得
      params.page_size = 10000;
      
      // 検索フィルターを追加
      Object.entries(searchFilters).forEach(([key, value]) => {
        if (value !== '' && value !== null && value !== undefined) {
          if (Array.isArray(value) && value.length > 0) {
            params[key] = value.join(',');
          } else if (typeof value === 'object' && (value as any).min !== undefined && (value as any).max !== undefined) {
            if ((value as any).min) params[`${key}_min`] = (value as any).min;
            if ((value as any).max) params[`${key}_max`] = (value as any).max;
          } else {
            params[key] = value;
          }
        }
      });
      
      console.log('API パラメーター:', params);
      const response = await studentApi.getStudents(params);
      console.log('API レスポンス:', response.results.length, '件');
      console.log('レスポンス詳細:', response);
      return response.results;
    },
    enabled: !!hasActiveFilters,
  });

  const { data: classroomsData } = useQuery({
    queryKey: ['classrooms'],
    queryFn: async () => {
      const response = await schoolApi.getClassrooms();
      return response;
    },
  });

  const classrooms = classroomsData?.results || [];

  // ページネーション計算
  const allStudents = students || [];
  const totalItems = allStudents.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentStudents = allStudents.slice(startIndex, endIndex);

  // ページ変更ハンドラー
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // 全生徒数統計を取得
  const { data: allStudentsStats } = useQuery({
    queryKey: ['all-students-stats'],
    queryFn: async () => {
      const response = await studentApi.getStudents({ page_size: 10000 });
      return response.results;
    },
  });

  // 統計情報の計算
  const stats = {
    total: allStudentsStats?.length || 0,
    classroomCount: classrooms.length,
    filtered: totalItems, // フィルター適用後の件数
  };

  const handleExport = async () => {
    try {
      // バックエンドのテンプレートエンドポイントを使用
      const response = await fetch('/api/students/export_template/', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `student_template_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        console.log('テンプレートをダウンロードしました');
      } else {
        throw new Error('テンプレートの取得に失敗しました');
      }
    } catch (error) {
      console.error('Template download error:', error);
      
      // フォールバック: フロントエンドでCSVを生成
      try {
        const csvContent = `塾ID,塾名,教室ID,教室名,生徒ID,生徒名,学年,年度,期間
100001,サンプル学習塾,001001,メイン教室,123456,田中太郎,小6,2025,夏期
100001,サンプル学習塾,001001,メイン教室,123456,田中太郎,小6,2025,冬期
100001,サンプル学習塾,001001,メイン教室,123457,佐藤花子,小5,2025,夏期
100001,サンプル学習塾,001001,メイン教室,123458,高橋次郎,中1,2025,夏期
,,,,,,,,,
,,,,,,,,,`;

        const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `student_template_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        console.log('テンプレートをダウンロードしました（フォールバック）');
      } catch (fallbackError) {
        console.error('Fallback download error:', fallbackError);
        console.log('テンプレートのダウンロードに失敗しました');
      }
    }
  };


  const handleEditStudent = (student: any) => {
    setSelectedStudent(student);
    setEditModalOpen(true);
  };

  return (
    <DashboardLayout>
      <PermissionGuard permission="can_register_students">
        <div className="space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">生徒管理</h1>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => setImportModalOpen(true)}
              className="rounded-xl"
            >
              <Upload className="h-4 w-4 mr-2" />
              インポート
            </Button>
            <Button
              variant="outline"
              onClick={handleExport}
              className="rounded-xl"
            >
              <Download className="h-4 w-4 mr-2" />
              テンプレートダウンロード
            </Button>
            <Button
              onClick={() => setRegistrationModalOpen(true)}
              className="rounded-xl bg-primary hover:bg-primary/90"
            >
              <Plus className="h-4 w-4 mr-2" />
              生徒登録
            </Button>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">
                {hasActiveFilters ? '絞り込み結果' : '総生徒数'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {hasActiveFilters ? stats.filtered : stats.total}
              </div>
              <p className="text-xs text-muted-foreground">
                {hasActiveFilters ? '条件に一致する生徒' : '登録済み生徒'}
              </p>
              {hasActiveFilters && stats.total > 0 && (
                <p className="text-xs text-muted-foreground mt-1">
                  全体: {stats.total}名
                </p>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">教室数</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.classroomCount}</div>
              <p className="text-xs text-muted-foreground">登録済み教室</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">表示中</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {hasActiveFilters && totalItems > 0 ? currentStudents.length : 0}
              </div>
              <p className="text-xs text-muted-foreground">
                現在のページ
                {totalPages > 1 && ` (${currentPage}/${totalPages})`}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* 高度検索 */}
        <Card>
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>生徒検索・フィルター</CardTitle>
                <CardDescription>
                  生徒を名前、IDなどで検索できます
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Select value={classroom} onValueChange={handleClassroomChange}>
                  <SelectTrigger className="w-48 rounded-xl">
                    <Filter className="h-4 w-4 mr-2" />
                    <SelectValue placeholder="教室で絞り込み" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">すべての教室</SelectItem>
                    {Array.isArray(classrooms) && classrooms.map((room) => (
                      <SelectItem key={room.id} value={room.id.toString()}>
                        {room.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={year} onValueChange={handleYearChange}>
                  <SelectTrigger className="w-32 rounded-xl">
                    <SelectValue placeholder="年度" />
                  </SelectTrigger>
                  <SelectContent>
                    {years.map((yearOption) => (
                      <SelectItem key={yearOption.value} value={yearOption.value}>
                        {yearOption.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={period} onValueChange={handlePeriodChange}>
                  <SelectTrigger className="w-24 rounded-xl">
                    <SelectValue placeholder="期間" />
                  </SelectTrigger>
                  <SelectContent>
                    {periods.map((periodOption) => (
                      <SelectItem key={periodOption.value} value={periodOption.value}>
                        {periodOption.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <AdvancedSearch
              placeholder="生徒名、IDで検索..."
              filterOptions={filterOptions}
              onSearch={handleSearch}
              onClear={handleClearSearch}
              showResultCount={true}
              resultCount={(students || []).length}
            />
          </CardContent>
        </Card>

        {/* 生徒一覧 */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>生徒一覧</CardTitle>
                <CardDescription>
                  生徒の登録・編集・削除を行えます
                </CardDescription>
              </div>
              {hasActiveFilters && totalItems > 0 && (
                <div className="text-sm text-muted-foreground">
                  {totalItems}件中 {startIndex + 1}-{Math.min(endIndex, totalItems)}件を表示 
                  (ページ {currentPage}/{totalPages})
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!hasActiveFilters ? (
              <div className="text-center py-8 text-muted-foreground">
                <Filter className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium mb-2">フィルターを使用して生徒を表示</p>
                <p className="text-sm">教室、年度、期間を選択してください</p>
              </div>
            ) : totalItems > 0 ? (
              <div className="space-y-4">
                <StudentTable students={currentStudents} onEditStudent={handleEditStudent} />
                
                {/* ページネーション */}
                {totalPages > 1 && (
                  <div className="flex justify-center items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                    >
                      前へ
                    </Button>
                    
                    <div className="flex gap-1">
                      {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                        // 現在のページの前後3ページのみ表示
                        if (
                          page === 1 ||
                          page === totalPages ||
                          (page >= currentPage - 2 && page <= currentPage + 2)
                        ) {
                          return (
                            <Button
                              key={page}
                              variant={currentPage === page ? "default" : "outline"}
                              size="sm"
                              className="w-8 h-8 p-0"
                              onClick={() => handlePageChange(page)}
                            >
                              {page}
                            </Button>
                          );
                        } else if (
                          page === currentPage - 3 ||
                          page === currentPage + 3
                        ) {
                          return <span key={page} className="px-1">...</span>;
                        }
                        return null;
                      })}
                    </div>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages}
                    >
                      次へ
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <p>該当する生徒が見つかりませんでした</p>
              </div>
            )}
          </CardContent>
        </Card>

        <StudentImportModal
          open={importModalOpen}
          onOpenChange={setImportModalOpen}
        />
        <StudentRegistrationModal
          open={registrationModalOpen}
          onOpenChange={setRegistrationModalOpen}
        />
        <StudentEditModal
          open={editModalOpen}
          onOpenChange={setEditModalOpen}
          student={selectedStudent}
        />
        </div>
      </PermissionGuard>
    </DashboardLayout>
  );
}