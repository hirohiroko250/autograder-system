import { http, HttpResponse } from 'msw';

// Mock API handlers
export const handlers = [
  // Dashboard
  http.get('/api/dashboard', ({ request }) => {
    const url = new URL(request.url);
    const year = url.searchParams.get('year');
    const period = url.searchParams.get('period');
    
    return HttpResponse.json({
      status: 'success',
      data: {
        totalStudents: 1245,
        activeTests: 3,
        completedTests: 8,
        studentGrowth: 12.5,
        deadline: new Date('2025-08-15T23:59:59'),
      },
    });
  }),

  // Students
  http.get('/api/students', ({ request }) => {
    const url = new URL(request.url);
    const search = url.searchParams.get('search') || '';
    const classroom = url.searchParams.get('classroom') || 'all';
    
    let students = [
      {
        id: '000001',
        name: '田中太郎',
        grade: 6,
        phone: '090-1234-5678',
        classroom: '本校舎A',
        status: 'active',
        createdAt: new Date('2024-04-01'),
      },
      {
        id: '000002',
        name: '佐藤花子',
        grade: 5,
        phone: '090-2345-6789',
        classroom: '本校舎B',
        status: 'active',
        createdAt: new Date('2024-04-02'),
      },
      {
        id: '000003',
        name: '鈴木一郎',
        grade: 4,
        phone: '090-3456-7890',
        classroom: '分校舎A',
        status: 'pending',
        createdAt: new Date('2024-04-03'),
      },
    ];

    // Filter by search
    if (search) {
      students = students.filter(student => 
        student.name.includes(search) || student.id.includes(search)
      );
    }

    // Filter by classroom
    if (classroom !== 'all') {
      students = students.filter(student => student.classroom === classroom);
    }

    return HttpResponse.json({
      status: 'success',
      data: students,
    });
  }),

  http.get('/api/students/next-id', () => {
    const nextId = Math.floor(Math.random() * 900000 + 100000).toString();
    return HttpResponse.json({
      status: 'success',
      data: { id: nextId },
    });
  }),

  http.post('/api/students', async ({ request }) => {
    const body = await request.json() as any;
    return HttpResponse.json({
      status: 'success',
      data: { id: body?.id, ...body },
      message: '生徒を登録しました',
    });
  }),

  // Test Schedule
  http.get('/api/test-schedule', ({ request }) => {
    const url = new URL(request.url);
    const year = url.searchParams.get('year');
    const period = url.searchParams.get('period');
    
    return HttpResponse.json({
      status: 'success',
      data: [
        {
          id: 1,
          year: '2025',
          period: 'summer',
          plannedDate: '2024-07-20',
          actualDate: '2024-07-20',
          deadline: '2024-08-15T23:59:59',
        },
      ],
    });
  }),

  // Test Files
  http.get('/api/tests/:year/:period/files', ({ params }) => {
    const { year, period } = params;
    
    return HttpResponse.json({
      status: 'success',
      data: [
        {
          id: 1,
          name: '第1回国語問題',
          type: 'problem',
          subject: '国語',
          size: '2.5MB',
          status: 'available',
          downloadCount: 45,
          lastUpdated: new Date('2024-07-15'),
        },
        {
          id: 2,
          name: '第1回国語解答',
          type: 'answer',
          subject: '国語',
          size: '1.2MB',
          status: 'available',
          downloadCount: 38,
          lastUpdated: new Date('2024-07-15'),
        },
      ],
    });
  }),

  // Scores
  http.post('/api/scores/bulk', async ({ request }) => {
    const body = await request.json() as any;
    return HttpResponse.json({
      status: 'success',
      data: { processed: Object.keys(body?.scores || {}).length },
      message: 'スコアを一括登録しました',
    });
  }),

  // Reports
  http.get('/api/reports/bulk', ({ request }) => {
    const url = new URL(request.url);
    const ids = url.searchParams.get('ids')?.split(',') || [];
    
    return HttpResponse.json({
      status: 'success',
      data: {
        zipUrl: '/downloads/reports.zip',
        fileCount: ids.length,
      },
    });
  }),

  http.post('/api/mail/reports/bulk', async ({ request }) => {
    const body = await request.json() as any;
    return HttpResponse.json({
      status: 'success',
      data: { sent: body?.studentIds?.length || 0 },
      message: '帳票をメール送信しました',
    });
  }),


  // Authentication
  http.post('/api/auth/login', async ({ request }) => {
    const body = await request.json() as any;
    const { email, password } = body;
    
    if (email === 'admin@school.com' && password === 'password') {
      return HttpResponse.json({
        status: 'success',
        data: {
          token: 'mock_auth_token',
          user: {
            id: 1,
            email: 'admin@school.com',
            name: '管理者',
            role: 'school_admin',
          },
        },
      });
    }
    
    return HttpResponse.json({
      status: 'error',
      message: 'Invalid credentials',
    }, { status: 401 });
  }),
];