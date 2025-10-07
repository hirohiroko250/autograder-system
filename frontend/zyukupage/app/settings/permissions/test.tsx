'use client';

import { DashboardLayout } from '@/components/layout/dashboard-layout';

export default function PermissionsTestPage() {
  return (
    <DashboardLayout>
      <div className="p-6">
        <h1 className="text-2xl font-bold">権限設定テストページ</h1>
        <p>このページが表示されれば基本的なルーティングは動作しています。</p>
      </div>
    </DashboardLayout>
  );
}