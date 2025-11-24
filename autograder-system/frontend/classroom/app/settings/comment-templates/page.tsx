'use client';

import { SubjectCommentTemplates } from '@/components/comments/subject-comment-templates';

export default function CommentTemplatesPage() {
  return (
    <div className="container mx-auto py-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">総評テンプレート設定</h1>
        <p className="text-muted-foreground mt-2">
          各教科の点数範囲に応じた総評コメントのテンプレートを管理します。
        </p>
      </div>

      <SubjectCommentTemplates />
    </div>
  );
}