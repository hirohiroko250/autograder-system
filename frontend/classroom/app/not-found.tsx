'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Home, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <Card className="w-full max-w-md mx-4">
        <CardHeader className="text-center">
          <CardTitle className="text-6xl font-bold text-gray-400 mb-4">404</CardTitle>
          <CardTitle className="text-2xl">ページが見つかりません</CardTitle>
          <CardDescription>
            お探しのページは存在しないか、移動された可能性があります。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-2">
            <Link href="/" className="flex-1">
              <Button className="w-full" variant="default">
                <Home className="h-4 w-4 mr-2" />
                ホームに戻る
              </Button>
            </Link>
            <Button
              className="flex-1"
              variant="outline"
              onClick={() => window.history.back()}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              前のページ
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}