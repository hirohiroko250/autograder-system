'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Save, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

const commentFormSchema = z.object({
  content: z.string().min(1, 'コメント内容を入力してください'),
  comment_type: z.string().min(1, 'コメントタイプを選択してください'),
});

type CommentFormData = z.infer<typeof commentFormSchema>;

interface CommentFormProps {
  studentId: string;
  studentName: string;
  testId?: string;
  testName?: string;
  onSubmit: (data: CommentFormData) => Promise<void>;
  onCancel?: () => void;
  isSubmitting?: boolean;
  templates?: Array<{
    id: string;
    name: string;
    content: string;
    category: string;
  }>;
}

const COMMENT_TYPES = [
  { value: 'general', label: '総合コメント', color: 'bg-blue-100 text-blue-800' },
  { value: 'improvement', label: '改善点', color: 'bg-orange-100 text-orange-800' },
  { value: 'strength', label: '強み', color: 'bg-green-100 text-green-800' },
  { value: 'homework', label: '宿題・課題', color: 'bg-purple-100 text-purple-800' },
  { value: 'parent_note', label: '保護者連絡', color: 'bg-pink-100 text-pink-800' },
  { value: 'behavioral', label: '学習態度', color: 'bg-indigo-100 text-indigo-800' },
  { value: 'academic', label: '学習内容', color: 'bg-yellow-100 text-yellow-800' },
];

export function CommentForm({ 
  studentId, 
  studentName, 
  testId, 
  testName, 
  onSubmit, 
  onCancel, 
  isSubmitting = false,
  templates = []
}: CommentFormProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');

  const form = useForm<CommentFormData>({
    resolver: zodResolver(commentFormSchema),
    defaultValues: {
      content: '',
      comment_type: 'general',
    },
  });

  const handleSubmit = async (data: CommentFormData) => {
    try {
      await onSubmit(data);
      form.reset();
      setSelectedTemplate('');
      toast.success('コメントを保存しました');
    } catch (error) {
      console.error('Error saving comment:', error);
      toast.error('コメントの保存に失敗しました');
    }
  };

  const handleTemplateSelect = (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (template) {
      form.setValue('content', template.content);
      setSelectedTemplate(templateId);
    }
  };

  const currentType = form.watch('comment_type');
  const selectedTypeInfo = COMMENT_TYPES.find(type => type.value === currentType);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          コメント作成
        </CardTitle>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>対象:</span>
          <Badge variant="outline">{studentName}</Badge>
          {testName && <Badge variant="outline">{testName}</Badge>}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="comment_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>コメントタイプ</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="コメントタイプを選択" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {COMMENT_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          <div className="flex items-center gap-2">
                            <div className={`w-3 h-3 rounded-full ${type.color}`} />
                            {type.label}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {selectedTypeInfo && (
              <Badge className={selectedTypeInfo.color} variant="secondary">
                {selectedTypeInfo.label}
              </Badge>
            )}

            {templates.length > 0 && (
              <div className="space-y-2">
                <FormLabel>テンプレート（任意）</FormLabel>
                <Select value={selectedTemplate} onValueChange={handleTemplateSelect}>
                  <SelectTrigger>
                    <SelectValue placeholder="テンプレートを選択（任意）">
                      <div className="flex items-center gap-2">
                        <Sparkles className="h-4 w-4" />
                        テンプレートを選択
                      </div>
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {templates.map((template) => (
                      <SelectItem key={template.id} value={template.id}>
                        <div>
                          <div className="font-medium">{template.name}</div>
                          <div className="text-xs text-muted-foreground truncate">
                            {template.content.substring(0, 50)}...
                          </div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <FormField
              control={form.control}
              name="content"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>コメント内容</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="コメントを入力してください..."
                      className="min-h-32"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-2">
              {onCancel && (
                <Button type="button" variant="outline" onClick={onCancel}>
                  キャンセル
                </Button>
              )}
              <Button type="submit" disabled={isSubmitting}>
                <Save className="h-4 w-4 mr-2" />
                {isSubmitting ? '保存中...' : '保存'}
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}