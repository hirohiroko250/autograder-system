import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { ScoreEntryWizard } from '@/components/tests/score-entry-wizard';

interface ClassroomScoreEntryPageProps {
  params: {
    id: string;
  };
  searchParams: {
    year?: string;
    period?: string;
  };
}

export default function ClassroomScoreEntryPage({ params, searchParams }: ClassroomScoreEntryPageProps) {
  const { id } = params;
  const year = searchParams.year || '2025';
  const period = searchParams.period || 'summer';

  return (
    <DashboardLayout>
      <div className="space-y-6 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold">スコア入力</h1>
          <p className="text-muted-foreground mt-1">
            教室 {id} - {year}年度 {period === 'spring' ? '春期' : period === 'summer' ? '夏期' : '冬期'} テストのスコアを入力します
          </p>
        </div>

        <ScoreEntryWizard year={year} period={period} />
      </div>
    </DashboardLayout>
  );
}