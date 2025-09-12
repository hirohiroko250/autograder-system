import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { ScoreEntryWizard } from '@/components/tests/score-entry-wizard';

interface ScoreEntryPageProps {
  params: {
    year: string;
    period: string;
  };
}

export default function ScoreEntryPage({ params }: ScoreEntryPageProps) {
  const { year, period } = params;

  return (
    <DashboardLayout>
      <div className="space-y-6 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold">スコア入力</h1>
          <p className="text-muted-foreground mt-1">
            {year}年度 {period === 'spring' ? '春期' : period === 'summer' ? '夏期' : period === 'winter' ? '冬期' : period}テストのスコアを入力します
          </p>
        </div>

        <ScoreEntryWizard year={year} period={period} />
      </div>
    </DashboardLayout>
  );
}