import { ProtectedRoute } from '@/components/auth/protected-route';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { ResultsClient } from './results-client';

interface ResultsPageProps {
  params: {
    year: string;
  };
}

export default function ResultsPage({ params }: ResultsPageProps) {
  const { year } = params;

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <ResultsClient year={year} />
      </DashboardLayout>
    </ProtectedRoute>
  );
}