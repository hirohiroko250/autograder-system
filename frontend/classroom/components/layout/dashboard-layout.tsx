'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import { Header } from './header';
import ErrorBoundary from '@/components/ui/error-boundary';
import { Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';

const Sidebar = dynamic(() => import('./sidebar').then(mod => ({ default: mod.Sidebar })), {
  ssr: false
});

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <ErrorBoundary>
      <div className="flex h-screen overflow-hidden">
        {/* デスクトップサイドバー */}
        <div className="hidden md:block">
          <Sidebar />
        </div>

        {/* モバイルサイドバー（オーバーレイ） */}
        {mobileMenuOpen && (
          <>
            <div
              className="fixed inset-0 bg-black/50 z-40 md:hidden"
              onClick={() => setMobileMenuOpen(false)}
            />
            <div className="fixed inset-y-0 left-0 z-50 md:hidden">
              <Sidebar onClose={() => setMobileMenuOpen(false)} />
            </div>
          </>
        )}

        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />

          {/* モバイルメニューボタン */}
          <div className="md:hidden p-4 border-b bg-card">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setMobileMenuOpen(true)}
            >
              <Menu className="h-6 w-6" />
            </Button>
          </div>

          <main className="flex-1 overflow-y-auto p-3 md:p-6 bg-background">
            <ErrorBoundary>
              {children}
            </ErrorBoundary>
          </main>
        </div>
      </div>
    </ErrorBoundary>
  );
}