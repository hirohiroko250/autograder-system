'use client';

import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ExternalLink, Info } from 'lucide-react';
import { SubjectCommentTemplates } from '@/components/comments/subject-comment-templates';

export default function CommentTemplatesPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold">コメントテンプレート管理</h1>
          <p className="text-muted-foreground mt-1">
            よく使用するコメントのテンプレートを管理します
          </p>
        </div>

        {/* 教科別コメントテンプレート */}
        <SubjectCommentTemplates />

        {/* 使用方法の案内 */}
        <Card className="border-blue-200 bg-blue-50/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Info className="h-4 w-4 text-blue-600" />
              <CardTitle className="text-blue-900">テンプレートの使用方法</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-blue-800">
              作成したテンプレートは、生徒管理・帳票ダウンロードページのコメント編集機能で使用できます。
            </p>
            <div className="flex items-center gap-2">
              <span className="text-sm text-blue-700">→</span>
              <a
                href="/tests"
                className="text-sm text-blue-600 hover:text-blue-800 underline flex items-center gap-1"
              >
                テスト管理ページで年度・期間を選択
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
            <div className="text-xs text-blue-600 space-y-1">
              <p>• 生徒名をクリックするとコメント編集ダイアログが開きます</p>
              <p>• 生徒の点数に応じて適切なテンプレートが自動選択されます</p>
              <p>• プルダウンから他のテンプレートも選択できます</p>
            </div>
          </CardContent>
        </Card>

      </div>
    </DashboardLayout>
  );
}