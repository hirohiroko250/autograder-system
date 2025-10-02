import axios, { AxiosError, AxiosResponse } from 'axios';
import { 
  AuthResponse, 
  User, 
  School, 
  Classroom, 
  Student, 
  ApiResponse,
  CreateClassroomRequest,
  CreateClassroomResponse,
  CreateStudentRequest,
  TestResult,
  TestStatistics,
  TestInfo,
  TestSchedule
} from './types';

const PUBLIC_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '/api';
const INTERNAL_API_BASE_URL = process.env.INTERNAL_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://backend:8000/api';

const resolveBaseURL = () => (typeof window === 'undefined' ? INTERNAL_API_BASE_URL : PUBLIC_API_BASE_URL);

// Axios instance
const apiClient = axios.create({
  baseURL: resolveBaseURL(),
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
let accessToken: string | null = null;
let refreshToken: string | null = null;

export const setTokens = (access: string, refresh: string) => {
  accessToken = access;
  refreshToken = refresh;
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  }
};

export const clearTokens = () => {
  accessToken = null;
  refreshToken = null;
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
};

export const getStoredTokens = () => {
  if (typeof window !== 'undefined') {
    return {
      access: localStorage.getItem('access_token'),
      refresh: localStorage.getItem('refresh_token'),
    };
  }
  return { access: null, refresh: null };
};

// Initialize tokens from localStorage
if (typeof window !== 'undefined') {
  const tokens = getStoredTokens();
  if (tokens.access && tokens.refresh) {
    accessToken = tokens.access;
    refreshToken = tokens.refresh;
  }
}

// Request interceptor to add auth header
apiClient.interceptors.request.use((config) => {
  config.baseURL = resolveBaseURL();
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// Response interceptor for token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && originalRequest && !(originalRequest as any)._retry) {
      (originalRequest as any)._retry = true;

      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });
          
          const newAccessToken = response.data.access;
          setTokens(newAccessToken, refreshToken);
          
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          }
          
          return apiClient(originalRequest);
        } catch (refreshError) {
          clearTokens();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        clearTokens();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// API functions
export const authApi = {
  login: async (username: string, password: string): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/login/', {
      username,
      password,
    });
    return response.data;
  },

  changePassword: async (currentPassword: string, newPassword: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/auth/change-password/', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },

  getProfile: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/profile/');
    return response.data;
  },
};

export const schoolApi = {
  getSchools: async (): Promise<ApiResponse<School>> => {
    const response = await apiClient.get<ApiResponse<School>>('/schools/');
    return response.data;
  },
  
  updateSchool: async (id: number, data: { name?: string; is_active?: boolean; can_register_students?: boolean; can_input_scores?: boolean; can_view_reports?: boolean }): Promise<School> => {
    const response = await apiClient.patch<School>(`/schools/${id}/`, data);
    return response.data;
  },

  createClassroom: async (schoolId: number, data: CreateClassroomRequest): Promise<CreateClassroomResponse> => {
    const response = await apiClient.post<CreateClassroomResponse>('/classrooms/', data);
    return response.data;
  },

  getClassrooms: async (): Promise<ApiResponse<Classroom>> => {
    const response = await apiClient.get<ApiResponse<Classroom>>('/classrooms/');
    return response.data;
  },
  updateClassroom: async (id: number, data: { name: string; is_active: boolean; permissions?: any }): Promise<any> => {
    const response = await apiClient.patch<any>(`/classrooms/${id}/`, data);
    return response.data;
  },
  getSchoolSettings: async (): Promise<any> => {
    const response = await apiClient.get<any>('/school-settings/');
    return response.data;
  },
  updateSchoolSettings: async (data: any): Promise<any> => {
    const response = await apiClient.patch<any>('/school-settings/', data);
    return response.data;
  },
};

export const studentApi = {
  getStudents: async (params?: { classroom?: number; grade?: string; search?: string; membership_type?: string; page_size?: number }): Promise<ApiResponse<Student>> => {
    const response = await apiClient.get<ApiResponse<Student>>('/students/', { params });
    return response.data;
  },

  createStudent: async (data: CreateStudentRequest): Promise<Student> => {
    const response = await apiClient.post<Student>('/students/', data);
    return response.data;
  },

  updateStudent: async (id: number, data: Partial<CreateStudentRequest>): Promise<Student> => {
    const response = await apiClient.put<Student>(`/students/${id}/`, data);
    return response.data;
  },

  deleteStudent: async (id: number): Promise<void> => {
    await apiClient.delete(`/students/${id}/`);
  },

  getNextStudentId: async (classroomId: string): Promise<{ next_id: string }> => {
    const response = await apiClient.get<{ next_id: string }>(`/students/next_id/?classroom=${classroomId}`);
    return response.data;
  },

  getStudentsByEnrollment: async (year: string, period: string): Promise<ApiResponse<Student>> => {
    const response = await apiClient.get<ApiResponse<Student>>(`/students/by_enrollment/?year=${year}&period=${period}&page_size=10000`);
    return response.data;
  },

  getStudentsForScoreEntry: async (params: { year: number; period: string; grade?: string }): Promise<ApiResponse<Student>> => {
    const queryParams = new URLSearchParams({
      year: params.year.toString(),
      period: params.period,
      ...(params.grade && { grade: params.grade })
    });
    const response = await apiClient.get<ApiResponse<Student>>(`/student-enrollments/for_score_entry/?${queryParams}`);
    return response.data;
  },

  getStudentEnrollments: async (studentId: number): Promise<any[]> => {
    const response = await apiClient.get<ApiResponse<any>>(`/student-enrollments/by_student/?student_id=${studentId}`);
    return response.data.results;
  },

  createStudentEnrollment: async (data: { student: number; year: number; period: string }): Promise<any> => {
    const response = await apiClient.post<any>('/student-enrollments/', data);
    return response.data;
  },

  deleteStudentEnrollment: async (id: number): Promise<void> => {
    await apiClient.delete(`/student-enrollments/${id}/`);
  },

  // 生徒データエクスポート（CSV形式）
  exportStudents: async (): Promise<any> => {
    const response = await apiClient.get('/students/export_data_csv/', { 
      responseType: 'blob'
    });
    
    // Blobレスポンスをファイルダウンロード用に処理
    const blob = new Blob([response.data], { 
      type: 'text/csv; charset=utf-8-sig' 
    });
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    
    // レスポンスヘッダーからファイル名を取得
    const contentDisposition = response.headers['content-disposition'] || response.headers['Content-Disposition'];
    let filename = `生徒データ_${new Date().toISOString().split('T')[0]}.csv`;
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/['"]/g, '');
      }
    }
    
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
    
    return { success: true, message: 'CSVファイルをダウンロードしました' };
  },
};

export const testApi = {
  getTestSchedules: async (params?: { year?: string; period?: string }): Promise<ApiResponse<TestSchedule>> => {
    const response = await apiClient.get<ApiResponse<TestSchedule>>('/test-schedules/', { params });
    return response.data;
  },

  getTestDefinitions: async (params?: { year?: string; period?: string }): Promise<ApiResponse<any>> => {
    const response = await apiClient.get<ApiResponse<any>>('/tests/', { params });
    return response.data;
  },

  getQuestionGroups: async (testId: number): Promise<any> => {
    const response = await apiClient.get<any>(`/tests/${testId}/question_groups/`);
    return response.data;
  },

  getQuestions: async (groupId: number): Promise<ApiResponse<any>> => {
    const response = await apiClient.get<ApiResponse<any>>(`/questions/?group=${groupId}`);
    return response.data;
  },

  createScore: async (data: any): Promise<any> => {
    const response = await apiClient.post<any>('/scores/', data);
    return response.data;
  },

  submitScore: async (data: {
    student_id: string;
    test_id: number;
    question_group_number: number;
    score: number;
    attendance: boolean;
  }): Promise<any> => {
    const response = await apiClient.post<any>('/scores/submit_score/', data);
    return response.data;
  },

  getScores: async (params?: { test?: number; student?: number }): Promise<ApiResponse<any>> => {
    const response = await apiClient.get<ApiResponse<any>>('/scores/', { params });
    return response.data;
  },

  // フロントエンド用: 大問別得点入力
  submitTestScores: async (data: {
    test_id: number;
    student_id: string;
    scores: { [key: string]: number };
  }): Promise<any> => {
    const response = await apiClient.post<any>('/scores/submit_test_scores/', data);
    return response.data;
  },

  // フロントエンド用: 生徒の得点取得
  getStudentScores: async (testId: number, studentId: string): Promise<any> => {
    const response = await apiClient.get<any>(`/scores/student_scores/?test_id=${testId}&student_id=${studentId}`);
    return response.data;
  },

  // 新しい仕様に基づく得点データの一括インポート
  bulkImportScores: async (data: {
    test_id: number;
    import_data: Array<{
      student_id: string;
      subject_code: number;
      grade: string;
      attendance: boolean;
      scores: { [key: string]: number };
    }>;
  }): Promise<any> => {
    const response = await apiClient.post<any>('/scores/bulk_import_scores/', data);
    return response.data;
  },

  // 小問レベルでのスコア入力
  submitQuestionScores: async (data: {
    test_id: number;
    student_id: string;
    attendance_status?: number;
    attendance_reason?: string;
    question_scores: Array<{
      question_id: number;
      score: number;
    }>;
  }): Promise<any> => {
    const response = await apiClient.post<any>('/school-statistics/submit_question_scores/', data);
    return response.data;
  },

  // 小問スコア取得（階層的に大問でグループ化）
  getQuestionScores: async (test_id: number, student_id: string): Promise<any> => {
    const response = await apiClient.get<any>(`/school-statistics/get_question_scores/?test_id=${test_id}&student_id=${student_id}`);
    return response.data;
  },

  // 出席管理
  manageAttendance: async (data: {
    test_id: number;
    student_id: string;
    attendance_status: number;
    reason?: string;
    notes?: string;
  }): Promise<any> => {
    const response = await apiClient.post<any>('/school-statistics/manage_attendance/', data);
    return response.data;
  },

  // テスト出席情報取得
  getTestAttendance: async (test_id: number): Promise<any> => {
    const response = await apiClient.get<any>(`/school-statistics/get_test_attendance/?test_id=${test_id}`);
    return response.data;
  },

  // テスト結果を取得
  getTestResults: async (params: { year: string; period: string; subject?: string }): Promise<ApiResponse<TestResult>> => {
    const requestParams = { ...params, app_context: 'zyuku' };
    const response = await apiClient.get<ApiResponse<TestResult>>('/test-results/detailed_results/', { params: requestParams });
    return response.data;
  },

  // 統合テスト結果を取得（生徒ID単位で国語・算数合算）
  getIntegratedTestResults: async (params: { year: string; period: string; school?: string }): Promise<ApiResponse<any>> => {
    const requestParams = { ...params, app_context: 'zyuku' };
    const response = await apiClient.get<ApiResponse<any>>('/test-results/integrated_student_results/', { params: requestParams });
    return response.data;
  },

  // テスト統計情報を取得
  getTestStatistics: async (params: { year: string; period: string; subject?: string }): Promise<TestStatistics> => {
    const requestParams = { ...params, app_context: 'zyuku' };
    const response = await apiClient.get<TestStatistics>('/test-statistics/', { params: requestParams });
    return response.data;
  },

  // スコア入力テンプレート生成
  generateScoreTemplate: async (params: { year: number; period: string; subject?: string; grade_level?: string }): Promise<any> => {
    const response = await apiClient.get('/scores/generate_all_grades_template/', { 
      params: { year: params.year, period: params.period },
      responseType: 'blob'
    });
    
    // Excelファイルとしてダウンロード
    const blob = new Blob([response.data], { 
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
    });
    const link = document.createElement('a');
    const url = window.URL.createObjectURL(blob);
    link.href = url;
    
    const period_display = { spring: '春期', summer: '夏期', winter: '冬期' }[params.period] || params.period;
    link.download = `スコア入力テンプレート_${params.year}年${period_display}.xlsx`;
    
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(link);
    
    return { success: true, message: 'テンプレートをダウンロードしました' };
  },

  // 統合スコアテンプレート生成（全教科対応）
  generateUnifiedScoreTemplate: async (params: { year: number; period: string; grade_level: string }): Promise<any> => {
    const response = await apiClient.get<any>('/scores/generate_unified_template/', { params });
    return response.data;
  },

  // 全学年対応スコアテンプレート生成（CSV形式）
  generateAllGradesTemplate: async (params: { year: number; period: string }): Promise<any> => {
    const response = await apiClient.get('/scores/generate_all_grades_template/', { 
      params,
      responseType: 'blob'
    });
    
    // Blobレスポンスをファイルダウンロード用に処理
    const blob = new Blob([response.data], { 
      type: 'text/csv; charset=utf-8-sig' 
    });
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    
    // レスポンスヘッダーからファイル名を取得
    const contentDisposition = response.headers['content-disposition'] || response.headers['Content-Disposition'];
    let filename = `スコア入力テンプレート_${params.year}_${params.period}.csv`;
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/['"]/g, '');
      }
    }
    
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
    
    return { success: true, message: 'CSVファイルをダウンロードしました' };
  },

  // スコアデータファイルインポート
  importScoresFromFile: async (formData: FormData): Promise<any> => {
    const response = await apiClient.post<any>('/scores/import_excel/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // 個別帳票生成
  generateIndividualReport: async (params: {
    studentId: string;
    year: number;
    period: string;
    format: string;
  }): Promise<any> => {
    const response = await apiClient.post<any>('/individual-problem-scores/generate_individual_report/', params);
    return response.data;
  },

  // 一括帳票生成
  generateBulkReports: async (params: {
    studentIds: string[];
    year: number;
    period: string;
    format: string;
  }): Promise<any> => {
    const response = await apiClient.post<any>('/individual-problem-scores/generate_bulk_reports/', params);
    return response.data;
  },

  // 生徒コメント保存
  saveStudentComments: async (params: {
    studentId: string;
    year: number;
    period: string;
    comments: { [key: string]: string };
  }): Promise<any> => {
    const response = await apiClient.post<any>('/individual-problem-scores/save_student_comments/', params);
    return response.data;
  },

  // 点数に応じたコメントテンプレート取得
  getScoreBasedComments: async (params: {
    studentId: string;
    year: number;
    period: string;
  }): Promise<any> => {
    const response = await apiClient.post<any>('/individual-problem-scores/get_score_based_comments/', params);
    return response.data;
  },
};

export const commentApi = {
  // 旧コメントテンプレートAPI（互換性のため残す）
  getCommentTemplates: async (params?: { subject?: string }): Promise<ApiResponse<any>> => {
    const response = await apiClient.get<ApiResponse<any>>('/comment-templates/', { params });
    return response.data;
  },

  createCommentTemplate: async (data: any): Promise<any> => {
    const response = await apiClient.post<any>('/comment-templates/', data);
    return response.data;
  },

  updateCommentTemplate: async (id: number, data: any): Promise<any> => {
    const response = await apiClient.put<any>(`/comment-templates/${id}/`, data);
    return response.data;
  },

  deleteCommentTemplate: async (id: number): Promise<void> => {
    await apiClient.delete(`/comment-templates/${id}/`);
  },

  // 新しいコメント管理API
  // 生徒コメント関連
  getStudentComments: async (params?: { student_id?: string; comment_type?: string }): Promise<ApiResponse<any>> => {
    const response = await apiClient.get<ApiResponse<any>>('/student-comments/', { params });
    return response.data;
  },

  createStudentComment: async (data: {
    student_id: string;
    content: string;
    comment_type: string;
  }): Promise<any> => {
    const response = await apiClient.post<any>('/student-comments/', data);
    return response.data;
  },

  updateStudentComment: async (id: string, data: {
    content: string;
    comment_type: string;
  }): Promise<any> => {
    const response = await apiClient.patch<any>(`/student-comments/${id}/`, data);
    return response.data;
  },

  deleteStudentComment: async (id: string): Promise<void> => {
    await apiClient.delete(`/student-comments/${id}/`);
  },

  autoGenerateComments: async (student_id: string): Promise<any> => {
    const response = await apiClient.post<any>('/student-comments/auto_generate_comments/', { student_id });
    return response.data;
  },

  // テストコメント関連
  getTestComments: async (params?: { student_id?: string; test_id?: string; comment_type?: string }): Promise<ApiResponse<any>> => {
    const response = await apiClient.get<ApiResponse<any>>('/test-comments/', { params });
    return response.data;
  },

  createTestComment: async (data: {
    student_id: string;
    test_id: string;
    content: string;
    comment_type: string;
  }): Promise<any> => {
    const response = await apiClient.post<any>('/test-comments/', data);
    return response.data;
  },

  updateTestComment: async (id: string, data: {
    content: string;
    comment_type: string;
  }): Promise<any> => {
    const response = await apiClient.patch<any>(`/test-comments/${id}/`, data);
    return response.data;
  },

  deleteTestComment: async (id: string): Promise<void> => {
    await apiClient.delete(`/test-comments/${id}/`);
  },

  // コメントテンプレートV2関連
  getCommentTemplatesV2: async (params?: { category?: string; comment_type?: string; is_active?: boolean }): Promise<ApiResponse<any>> => {
    const response = await apiClient.get<ApiResponse<any>>('/comment-templates/', { params });
    return response.data;
  },

  createCommentTemplateV2: async (data: {
    name: string;
    content: string;
    category: string;
    comment_type: string;
    is_active?: boolean;
  }): Promise<any> => {
    const response = await apiClient.post<any>('/comment-templates/', data);
    return response.data;
  },

  updateCommentTemplateV2: async (id: string, data: {
    name?: string;
    content?: string;
    category?: string;
    comment_type?: string;
    is_active?: boolean;
  }): Promise<any> => {
    const response = await apiClient.patch<any>(`/comment-templates/${id}/`, data);
    return response.data;
  },

  deleteCommentTemplateV2: async (id: string): Promise<void> => {
    await apiClient.delete(`/comment-templates/${id}/`);
  },

  // 個別問題関連
  getIndividualProblems: async (testId: number): Promise<ApiResponse<any>> => {
    const response = await apiClient.get<ApiResponse<any>>(`/individual-problems/?test=${testId}`);
    return response.data;
  },

  createDefaultProblems: async (testId: number, problemCount: number = 10, maxScorePerProblem: number = 10): Promise<any> => {
    const response = await apiClient.post<any>('/individual-problems/create_default_problems/', {
      test_id: testId,
      problem_count: problemCount,
      max_score_per_problem: maxScorePerProblem
    });
    return response.data;
  },

  // 個別問題スコア関連
  getIndividualScores: async (testId: number, studentId: string): Promise<any> => {
    const response = await apiClient.get<any>('/individual-problem-scores/get_individual_scores/', {
      params: { test_id: testId, student_id: studentId }
    });
    return response.data;
  },

  submitIndividualScores: async (data: {
    test_id: number;
    student_id: string;
    scores: { [problemNumber: string]: number };
    attendance_status?: number;
    attendance_reason?: string;
  }): Promise<any> => {
    const response = await apiClient.post<any>('/individual-problem-scores/submit_individual_scores/', data);
    return response.data;
  },

  // 通知関連
  getUserNotifications: async (): Promise<ApiResponse<any>> => {
    const response = await apiClient.get<ApiResponse<any>>('/user-notifications/');
    return response.data;
  },

  getUnreadNotificationCount: async (): Promise<any> => {
    const response = await apiClient.get<any>('/user-notifications/unread_count/');
    return response.data;
  },

  markNotificationAsRead: async (notificationId: number): Promise<any> => {
    const response = await apiClient.post<any>(`/user-notifications/${notificationId}/mark_as_read/`);
    return response.data;
  },

  markAllNotificationsAsRead: async (): Promise<any> => {
    const response = await apiClient.post<any>('/user-notifications/mark_all_as_read/');
    return response.data;
  },
};

// 請求管理API
export const billingApi = {
  // 請求詳細データ取得（出席かつ点数入力済み生徒のみ）
  getBillingDetails: async (params: { year: string; period: string; classroom_id?: string }): Promise<any> => {
    const response = await apiClient.get<any>('/classrooms/billing_details/', { params });
    return response.data;
  },

  // 請求サマリー取得
  getBillingSummary: async (params: { year: string; period: string }): Promise<any> => {
    const response = await apiClient.get<any>('/classrooms/billing_summary/', { params });
    return response.data;
  },

  // 請求レポート生成・保存
  generateBillingReport: async (data: { year: number; period: string }): Promise<any> => {
    const response = await apiClient.post<any>('/classrooms/generate_billing_report/', data);
    return response.data;
  },

  // 保存済み請求レポート一覧取得
  getBillingReports: async (params?: { year?: string; period?: string }): Promise<any> => {
    const response = await apiClient.get<any>('/classrooms/billing_reports/', { params });
    return response.data;
  },

  // 教室の受講者数・課金対象者数取得
  getAttendanceCount: async (classroomId: string, params: { year: string; period: string }): Promise<any> => {
    const response = await apiClient.get<any>(`/classrooms/${classroomId}/attendance_count/`, { params });
    return response.data;
  },
};

export default apiClient;
