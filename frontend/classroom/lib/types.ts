// API Response Types
export interface User {
  id: number;
  username: string;
  email: string;
  role: 'school_admin' | 'classroom_admin';
  school_id: string;
  classroom_id?: string;
  school_name?: string;
  classroom_name?: string;
  permissions?: {
    can_register_students: boolean;
    can_input_scores: boolean;
    can_view_reports: boolean;
  };
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface School {
  id: number;
  school_id: string;
  name: string;
  email: string;
  phone: string;
  address: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Classroom {
  id: number;
  classroom_id: string;
  school: number;
  school_name: string;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Student {
  id: string;
  student_id: string;
  classroom: string;
  classroom_id?: string;
  classroom_name?: string;
  name: string;
  grade: string;
  grade_label?: string;
  email?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  latest_enrollment?: {
    year: string;
    period: string;
  };
}

export interface ApiResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface CreateClassroomRequest {
  name: string;
}

export interface CreateClassroomResponse {
  classroom: Classroom;
  credentials: {
    login_id: string;
    classroom_id: string;
    password: string;
  };
}

export interface CreateStudentRequest {
  student_id: string;
  classroom: number;
  name: string;
  grade: string;
  year?: number;
  period?: string;
  email?: string;
}

// Test Result Types
export interface TestResult {
  id: number;
  student_id: string;
  student_name: string;
  grade: number;
  school_name: string;
  classroom_name: string;
  test_info: {
    year: number;
    period: string;
    subject: string;
    grade_level: string;
  };
  scores: {
    total_score: number;
    correct_rate: number;
    question_details: Array<{
      question_number: number;
      score: number;
      max_score: number;
    }>;
  };
  rankings: {
    grade_rank: number;
    grade_total: number;
    national_rank: number;
    national_total: number;
  };
  averages: {
    grade_average: number;
    question_averages: { [key: number]: number };
  };
  improvement?: {
    previous_score?: number;
    score_change?: number;
    rank_change?: number;
  };
  // 後方互換性のため
  total_score?: number;
  rank?: number;
  attendance?: boolean;
}

export interface TestStatistics {
  subject: string;
  year: string;
  period: string;
  completed_date: string;
  total_students: number;
  average_score: number;
  max_score: number;
  min_score: number;
  attendance_rate: number;
}

export interface TestInfo {
  id: number;
  subject: string;
  year: string;
  period: string;
  name: string;
  description?: string;
  max_score: number;
  created_at: string;
}

export interface TestSchedule {
  id: number;
  year: number;
  period: string;
  period_display: string;
  planned_date: string;
  actual_date?: string;
  deadline_at: string;
  is_active: boolean;
  start_date: string;
  end_date: string;
  created_at: string;
  updated_at: string;
}