'use client';

export const dynamic = 'force-dynamic';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ClassroomRegistrationModal } from '@/components/classroom/classroom-registration-modal';
import { ClassroomEditModal } from '@/components/classroom/classroom-edit-modal';
import { useAuth } from '@/lib/auth-context';
import { schoolApi } from '@/lib/api-client';
import { Plus, Users, Calendar, Settings, ChevronRight, Search } from 'lucide-react';
import Link from 'next/link';

interface Classroom {
  id: number;
  name: string;
  classroom_id: string;
  school_name: string;
  student_count: number;
  is_active: boolean;
}

export default function ClassroomsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedClassroom, setSelectedClassroom] = useState<Classroom | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchFilters, setSearchFilters] = useState<any>({});
  const { user } = useAuth();

  const { data: schoolData } = useQuery({
    queryKey: ['schools'],
    queryFn: () => schoolApi.getSchools(),
    enabled: !!user && user.role === 'school_admin',
  });

  const { data: classroomsData } = useQuery({
    queryKey: ['classrooms'],
    queryFn: async () => {
      const response = await schoolApi.getClassrooms();
      console.log('Classrooms API response:', response);
      return response;
    },
    enabled: !!user,
  });

  const school = schoolData?.results?.[0];
  const classrooms = classroomsData?.results || [];
  

  // 検索ハンドラー
  const handleSearch = (query: string, filters: any) => {
    setSearchQuery(query);
    setSearchFilters(filters);
  };

  // 検索クリアハンドラー
  const handleClearSearch = () => {
    setSearchQuery('');
    setSearchFilters({});
  };

  // フィルタリングされた教室一覧
  const filteredClassrooms = classrooms.filter((classroom: any) => {
    // テキスト検索
    if (searchQuery) {
      const searchLower = searchQuery.toLowerCase();
      const matchesName = classroom.name.toLowerCase().includes(searchLower);
      const matchesId = classroom.classroom_id.toString().includes(searchQuery);
      const matchesSchoolName = classroom.school_name.toLowerCase().includes(searchLower);
      if (!matchesName && !matchesId && !matchesSchoolName) return false;
    }

    // フィルター検索
    for (const [key, value] of Object.entries(searchFilters)) {
      if (!value || (Array.isArray(value) && value.length === 0)) continue;
      
      switch (key) {
        case 'is_active':
          if (value === 'true' && !classroom.is_active) return false;
          if (value === 'false' && classroom.is_active) return false;
          break;
        case 'classroom_id':
          if (!classroom.classroom_id.toString().includes(value as string)) return false;
          break;
        case 'student_count_range':
          const studentCount = classroom.student_count || 0;
          const range = value as { min?: string; max?: string };
          if (range.min && studentCount < parseInt(range.min)) return false;
          if (range.max && studentCount > parseInt(range.max)) return false;
          break;
      }
    }

    return true;
  });
  
  console.log('Current user:', user);
  console.log('School data:', school);
  console.log('Classrooms data:', classrooms);
  
  // 教室の権限設定をデバッグ出力
  if (classrooms.length > 0) {
    console.log('First few classrooms with permissions:');
    classrooms.slice(0, 5).forEach((classroom: any) => {
      console.log(`Classroom ${classroom.name} (ID: ${classroom.id}):`, {
        permissions: classroom.permissions,
        is_active: classroom.is_active
      });
    });
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">教室管理</h1>
            <p className="text-muted-foreground">
              教室の登録・管理を行います
            </p>
          </div>
          <Button onClick={() => setIsModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            新しい教室を登録
          </Button>
        </div>

        {/* 教室統計 */}
        <div className="grid gap-6 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">登録教室数</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{classrooms.filter(c => c.is_active).length}</div>
              <p className="text-xs text-muted-foreground">
                アクティブな教室
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">総生徒数</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{classrooms.reduce((sum, c: any) => sum + (c.student_count || 0), 0)}</div>
              <p className="text-xs text-muted-foreground">
                全教室合計
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">登録教室数</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{classrooms.length}</div>
              <p className="text-xs text-muted-foreground">
                全教室数
              </p>
            </CardContent>
          </Card>
        </div>

        {/* 基本検索 */}
        <Card>
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>教室検索</CardTitle>
                <CardDescription>
                  教室を名前、ID、学校名などで検索できます
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  placeholder="教室名、教室ID、学校名で検索..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <Button onClick={() => handleSearch(searchQuery, {})}>
                検索
              </Button>
              <Button variant="outline" onClick={handleClearSearch}>
                クリア
              </Button>
            </div>
            <div className="mt-2 text-sm text-gray-600">
              {filteredClassrooms.length}件の結果
            </div>
          </CardContent>
        </Card>

        {/* 教室一覧 */}
        <Card>
          <CardHeader>
            <CardTitle>教室一覧</CardTitle>
            <CardDescription>
              登録されている教室とその詳細情報
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredClassrooms.map((classroom) => (
                <div
                  key={classroom.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Link 
                    href={`/classrooms/${classroom.id}`}
                    className="flex items-center space-x-4 flex-1 cursor-pointer"
                  >
                    <div>
                      <h3 className="font-semibold hover:text-blue-600 transition-colors">
                        {classroom.name}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        教室ID: {classroom.classroom_id}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        学校: {classroom.school_name}
                      </p>
                    </div>
                    <div className="flex items-center">
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </Link>
                  
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <p className="font-medium">{(classroom as any).student_count || 0}名</p>
                      <p className="text-sm text-muted-foreground">生徒数</p>
                    </div>
                    
                    <Badge variant={classroom.is_active ? 'default' : 'secondary'}>
                      {classroom.is_active ? 'アクティブ' : '非アクティブ'}
                    </Badge>
                    
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={(e) => {
                        e.preventDefault();
                        setSelectedClassroom(classroom as any);
                        setIsEditModalOpen(true);
                      }}
                    >
                      <Settings className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 教室登録に関する注意事項 */}
        <Card>
          <CardHeader>
            <CardTitle>教室登録について</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>• 教室を登録すると、6桁の教室IDが自動発行されます</p>
              <p>• 初期パスワードは教室IDと同じです</p>
              <p>• 教室管理者には最初のログイン後にパスワード変更を推奨してください</p>
              <p>• 教室IDとパスワードは大切に保管し、教室管理者にお渡しください</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {school && (
        <ClassroomRegistrationModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          schoolId={school.id}
        />
      )}

      <ClassroomEditModal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setSelectedClassroom(null);
        }}
        classroom={selectedClassroom}
      />
    </DashboardLayout>
  );
}