'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { BookOpen, Calculator, Save } from 'lucide-react';
import { toast } from 'sonner';
import { commentApi } from '@/lib/api-client';

interface SubjectCommentTemplate {
  score_range: string;
  template_id: number | null;
  title: string;
  content: string;
}

const SCORE_RANGE_LABELS: Record<string, string> = {
  '0-20': '0-20点',
  '21-40': '21-40点',
  '41-60': '41-60点',
  '61-80': '61-80点',
  '81-100': '81-100点',
};

export function SubjectCommentTemplates() {
  const [activeSubject, setActiveSubject] = useState<'japanese' | 'math'>('japanese');
  const [editedTemplates, setEditedTemplates] = useState<Record<string, string>>({});
  const queryClient = useQueryClient();

  // 国語テンプレート取得
  const { data: japaneseTemplates = [], isLoading: isLoadingJapanese } = useQuery({
    queryKey: ['subject-comment-templates', 'japanese'],
    queryFn: async () => {
      const response = await commentApi.getSubjectCommentTemplates('japanese');
      return response;
    },
  });

  // 算数テンプレート取得
  const { data: mathTemplates = [], isLoading: isLoadingMath } = useQuery({
    queryKey: ['subject-comment-templates', 'math'],
    queryFn: async () => {
      const response = await commentApi.getSubjectCommentTemplates('math');
      return response;
    },
  });

  // テンプレート更新
  const updateTemplate = useMutation({
    mutationFn: async ({ subject, scoreRange, content }: { subject: string; scoreRange: string; content: string }) => {
      return await commentApi.updateSubjectCommentTemplate({
        subject,
        score_range: scoreRange,
        content,
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['subject-comment-templates', variables.subject] });
      toast.success('総評を保存しました');
      // 編集済みフラグをクリア
      const key = `${variables.subject}_${variables.scoreRange}`;
      setEditedTemplates(prev => {
        const newState = { ...prev };
        delete newState[key];
        return newState;
      });
    },
    onError: () => {
      toast.error('総評の保存に失敗しました');
    },
  });

  const handleContentChange = (subject: string, scoreRange: string, content: string) => {
    const key = `${subject}_${scoreRange}`;
    setEditedTemplates(prev => ({ ...prev, [key]: content }));
  };

  const handleSave = async (subject: string, scoreRange: string) => {
    const key = `${subject}_${scoreRange}`;
    const content = editedTemplates[key];

    if (content !== undefined) {
      await updateTemplate.mutateAsync({ subject, scoreRange, content });
    }
  };

  const handleSaveAll = async (subject: string) => {
    const templates = subject === 'japanese' ? japaneseTemplates : mathTemplates;
    const promises = templates.map(template => {
      const key = `${subject}_${template.score_range}`;
      const content = editedTemplates[key];

      if (content !== undefined) {
        return updateTemplate.mutateAsync({ subject, scoreRange: template.score_range, content });
      }
      return Promise.resolve();
    });

    await Promise.all(promises);
  };

  const getContent = (subject: string, template: SubjectCommentTemplate) => {
    const key = `${subject}_${template.score_range}`;
    return editedTemplates[key] !== undefined ? editedTemplates[key] : template.content;
  };

  const hasChanges = (subject: string) => {
    return Object.keys(editedTemplates).some(key => key.startsWith(`${subject}_`));
  };

  const renderTemplateEditor = (subject: string, templates: SubjectCommentTemplate[], isLoading: boolean) => {
    if (isLoading) {
      return <div className="text-center py-8 text-muted-foreground">読み込み中...</div>;
    }

    return (
      <div className="space-y-6">
        <div className="flex justify-end">
          <Button
            onClick={() => handleSaveAll(subject)}
            disabled={!hasChanges(subject) || updateTemplate.isPending}
            variant="default"
            className="rounded-xl"
          >
            <Save className="h-4 w-4 mr-2" />
            すべて保存
          </Button>
        </div>

        <div className="space-y-4">
          {templates.map(template => {
            const key = `${subject}_${template.score_range}`;
            const hasChanged = editedTemplates[key] !== undefined;

            return (
              <Card key={template.score_range} className={hasChanged ? 'border-primary' : ''}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">
                      {SCORE_RANGE_LABELS[template.score_range]}
                    </CardTitle>
                    <Button
                      size="sm"
                      onClick={() => handleSave(subject, template.score_range)}
                      disabled={!hasChanged || updateTemplate.isPending}
                      variant={hasChanged ? 'default' : 'ghost'}
                      className="rounded-xl"
                    >
                      <Save className="h-3 w-3 mr-1" />
                      保存
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <Label htmlFor={`template-${template.score_range}`}>
                      総評内容（約200字）
                    </Label>
                    <Textarea
                      id={`template-${template.score_range}`}
                      value={getContent(subject, template)}
                      onChange={(e) => handleContentChange(subject, template.score_range, e.target.value)}
                      rows={4}
                      className="resize-none"
                      placeholder="点数範囲に応じた総評を入力してください..."
                    />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>{getContent(subject, template).length} 文字</span>
                      {hasChanged && <span className="text-primary">• 未保存の変更があります</span>}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          教科ごとの総評
        </CardTitle>
        <p className="text-sm text-muted-foreground mt-2">
          点数範囲に応じて自動的に適用される総評コメントを編集できます。
          生徒ごとに個別のコメントを入力することも可能です。
        </p>
      </CardHeader>
      <CardContent>
        <Tabs value={activeSubject} onValueChange={(v) => setActiveSubject(v as 'japanese' | 'math')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="japanese">
              <BookOpen className="h-4 w-4 mr-2" />
              国語
            </TabsTrigger>
            <TabsTrigger value="math">
              <Calculator className="h-4 w-4 mr-2" />
              算数
            </TabsTrigger>
          </TabsList>

          <TabsContent value="japanese" className="mt-6">
            {renderTemplateEditor('japanese', japaneseTemplates, isLoadingJapanese)}
          </TabsContent>

          <TabsContent value="math" className="mt-6">
            {renderTemplateEditor('math', mathTemplates, isLoadingMath)}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
