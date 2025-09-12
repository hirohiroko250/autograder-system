'use client';

import { DashboardLayout } from '@/components/layout/dashboard-layout';

interface TestResultsPageProps {
  params: {
    year: string;
    period: string;
  };
}

export default function TestResultsPage({ params }: TestResultsPageProps) {
  const { year, period } = params;

  const getPeriodLabel = (period: string) => {
    switch (period) {
      case 'spring': return '春期';
      case 'summer': return '夏期';
      case 'winter': return '冬期';
      default: return period;
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold">テスト結果</h1>
          <p className="text-muted-foreground mt-1">
            {year}年度 {getPeriodLabel(period)}テストの結果を表示します
          </p>
        </div>

        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <h2 className="text-xl font-semibold mb-2">準備中</h2>
          <p className="text-gray-600">
            この機能は現在開発中です。<br />
            しばらくお待ちください。
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}