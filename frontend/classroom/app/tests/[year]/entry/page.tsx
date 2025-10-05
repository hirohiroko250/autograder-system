import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { ScoreEntryWizard } from '@/components/tests/score-entry-wizard';

interface ScoreEntryPageProps {
  params: {
    year: string;
  };
}

export default function ScoreEntryPage({ params }: ScoreEntryPageProps) {
  const { year } = params;

  return (
    <DashboardLayout>
      <div className="space-y-6 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold">スコア入力</h1>
          <p className="text-muted-foreground mt-1">
            {year}年度テストのスコアを入力します
          </p>
        </div>

        <ScoreEntryWizard year={year} />
      </div>
    </DashboardLayout>
  );
}