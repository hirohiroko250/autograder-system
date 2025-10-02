'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MessageSquare, Plus, Edit2, Trash2, Save, X, Sparkles, Search, ExternalLink, Info } from 'lucide-react';
import { toast } from 'sonner';

const templateSchema = z.object({
  name: z.string().min(1, 'テンプレート名を入力してください'),
  content: z.string().min(1, 'コメント内容を入力してください'),
  category: z.string().min(1, 'カテゴリを選択してください'),
  comment_type: z.string().min(1, 'コメントタイプを選択してください'),
  subject: z.string().default('japanese'),
  score_range_min: z.number().min(0, '最小点数は0以上である必要があります').default(0),
  score_range_max: z.number().max(100, '最大点数は100以下である必要があります').default(100),
  is_active: z.boolean().default(true),
});

type TemplateFormData = z.infer<typeof templateSchema>;

interface CommentTemplate {
  id: string;
  name: string;
  content: string;
  category: string;
  comment_type: string;
  subject: string;
  score_range_min: number;
  score_range_max: number;
  is_active: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

const CATEGORIES = [
  { value: 'positive', label: '肯定的評価', color: 'bg-green-100 text-green-800' },
  { value: 'improvement', label: '改善提案', color: 'bg-orange-100 text-orange-800' },
  { value: 'encouragement', label: '励まし・応援', color: 'bg-blue-100 text-blue-800' },
  { value: 'academic', label: '学習指導', color: 'bg-purple-100 text-purple-800' },
  { value: 'behavioral', label: '行動指導', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'parent_communication', label: '保護者連絡', color: 'bg-pink-100 text-pink-800' },
];

const COMMENT_TYPES = [
  { value: 'general', label: '総合コメント' },
  { value: 'improvement', label: '改善点' },
  { value: 'strength', label: '強み' },
  { value: 'homework', label: '宿題・課題' },
  { value: 'parent_note', label: '保護者連絡' },
  { value: 'behavioral', label: '学習態度' },
  { value: 'academic', label: '学習内容' },
];

const SUBJECTS = [
  { value: 'japanese', label: '国語' },
  { value: 'math', label: '算数' },
];

export default function CommentTemplatesPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<CommentTemplate | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const queryClient = useQueryClient();

  const form = useForm<TemplateFormData>({
    resolver: zodResolver(templateSchema),
    defaultValues: {
      name: '',
      content: '',
      category: '',
      comment_type: 'general',
      subject: 'japanese',
      score_range_min: 0,
      score_range_max: 100,
      is_active: true,
    },
  });

  // テンプレート一覧取得
  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['comment-templates'],
    queryFn: async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/comment-templates-v2/`);
      if (!response.ok) throw new Error('Failed to fetch templates');
      const data = await response.json();
      return data.results || [];
    },
  });

  // テンプレート作成
  const createMutation = useMutation({
    mutationFn: async (data: TemplateFormData) => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/comment-templates-v2/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to create template');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comment-templates'] });
      setIsDialogOpen(false);
      form.reset();
      toast.success('テンプレートを作成しました');
    },
    onError: () => {
      toast.error('テンプレートの作成に失敗しました');
    },
  });

  // テンプレート更新
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TemplateFormData }) => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/comment-templates-v2/${id}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to update template');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comment-templates'] });
      setIsDialogOpen(false);
      setEditingTemplate(null);
      form.reset();
      toast.success('テンプレートを更新しました');
    },
    onError: () => {
      toast.error('テンプレートの更新に失敗しました');
    },
  });

  // テンプレート削除
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/comment-templates-v2/${id}/`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete template');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comment-templates'] });
      toast.success('テンプレートを削除しました');
    },
    onError: () => {
      toast.error('テンプレートの削除に失敗しました');
    },
  });

  const handleCreate = () => {
    setEditingTemplate(null);
    form.reset();
    setIsDialogOpen(true);
  };

  const handleEdit = (template: CommentTemplate) => {
    setEditingTemplate(template);
    form.reset({
      name: template.name,
      content: template.content,
      category: template.category,
      comment_type: template.comment_type,
      subject: template.subject || 'japanese',
      score_range_min: template.score_range_min || 0,
      score_range_max: template.score_range_max || 100,
      is_active: template.is_active,
    });
    setIsDialogOpen(true);
  };

  const handleSubmit = (data: TemplateFormData) => {
    if (editingTemplate) {
      updateMutation.mutate({ id: editingTemplate.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleDelete = (id: string) => {
    if (confirm('このテンプレートを削除しますか？')) {
      deleteMutation.mutate(id);
    }
  };

  const getCategoryInfo = (category: string) => {
    return CATEGORIES.find(c => c.value === category) || CATEGORIES[0];
  };

  const getCommentTypeLabel = (type: string) => {
    return COMMENT_TYPES.find(t => t.value === type)?.label || type;
  };

  const getSubjectLabel = (subject: string) => {
    return SUBJECTS.find(s => s.value === subject)?.label || subject;
  };

  // フィルタリング
  const filteredTemplates = templates.filter((template: CommentTemplate) => {
    const matchesSearch = searchQuery === '' || 
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.content.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesCategory = categoryFilter === 'all' || template.category === categoryFilter;
    
    return matchesSearch && matchesCategory;
  });

  // カテゴリ別グループ化
  const groupedTemplates = CATEGORIES.reduce((acc, category) => {
    acc[category.value] = filteredTemplates.filter(
      (template: CommentTemplate) => template.category === category.value
    );
    return acc;
  }, {} as Record<string, CommentTemplate[]>);

  return (
    <DashboardLayout>
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">コメントテンプレート管理</h1>
            <p className="text-muted-foreground mt-1">
              よく使用するコメントのテンプレートを管理します
            </p>
          </div>
          
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button onClick={handleCreate} className="rounded-xl">
                <Plus className="h-4 w-4 mr-2" />
                新しいテンプレート
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>
                  {editingTemplate ? 'テンプレート編集' : '新しいテンプレート'}
                </DialogTitle>
              </DialogHeader>
              
              <Form {...form}>
                <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
                  <FormField
                    control={form.control}
                    name="name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>テンプレート名</FormLabel>
                        <FormControl>
                          <Input placeholder="テンプレート名を入力" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="category"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>カテゴリ</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="カテゴリを選択" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {CATEGORIES.map((category) => (
                              <SelectItem key={category.value} value={category.value}>
                                <div className="flex items-center gap-2">
                                  <div className={`w-3 h-3 rounded-full ${category.color}`} />
                                  {category.label}
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="comment_type"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>コメントタイプ</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="コメントタイプを選択" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {COMMENT_TYPES.map((type) => (
                              <SelectItem key={type.value} value={type.value}>
                                {type.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="subject"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>科目</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="科目を選択" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {SUBJECTS.map((subject) => (
                              <SelectItem key={subject.value} value={subject.value}>
                                {subject.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="grid grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="score_range_min"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>最小点数</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              min="0"
                              max="100"
                              placeholder="0"
                              {...field}
                              onChange={(e) => field.onChange(parseInt(e.target.value) || 0)}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="score_range_max"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>最大点数</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              min="0"
                              max="100"
                              placeholder="100"
                              {...field}
                              onChange={(e) => field.onChange(parseInt(e.target.value) || 100)}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <FormField
                    control={form.control}
                    name="content"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>コメント内容</FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="コメントの内容を入力..."
                            className="min-h-32"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="flex justify-end gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setIsDialogOpen(false)}
                    >
                      <X className="h-4 w-4 mr-2" />
                      キャンセル
                    </Button>
                    <Button
                      type="submit"
                      disabled={createMutation.isPending || updateMutation.isPending}
                    >
                      <Save className="h-4 w-4 mr-2" />
                      {editingTemplate ? '更新' : '作成'}
                    </Button>
                  </div>
                </form>
              </Form>
            </DialogContent>
          </Dialog>
        </div>

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

        <Card>
          <CardHeader>
            <CardTitle>検索・フィルター</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="h-4 w-4 absolute left-3 top-3 text-muted-foreground" />
                  <Input
                    placeholder="テンプレート名またはコンテンツで検索..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="カテゴリで絞り込み" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">すべてのカテゴリ</SelectItem>
                  {CATEGORIES.map((category) => (
                    <SelectItem key={category.value} value={category.value}>
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${category.color}`} />
                        {category.label}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {isLoading ? (
          <Card>
            <CardContent className="p-8 text-center text-muted-foreground">
              読み込み中...
            </CardContent>
          </Card>
        ) : (
          <Tabs defaultValue={CATEGORIES[0].value}>
            <TabsList className="grid w-full grid-cols-6">
              {CATEGORIES.map((category) => (
                <TabsTrigger key={category.value} value={category.value}>
                  {category.label} ({groupedTemplates[category.value]?.length || 0})
                </TabsTrigger>
              ))}
            </TabsList>

            {CATEGORIES.map((category) => (
              <TabsContent key={category.value} value={category.value} className="mt-6">
                {groupedTemplates[category.value]?.length === 0 ? (
                  <Card>
                    <CardContent className="p-8 text-center text-muted-foreground">
                      <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>{category.label}のテンプレートはありません</p>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {groupedTemplates[category.value]?.map((template: CommentTemplate) => (
                      <Card key={template.id} className="hover:shadow-md transition-shadow">
                        <CardHeader className="pb-2">
                          <div className="flex items-start justify-between">
                            <div className="space-y-1">
                              <CardTitle className="text-base">{template.name}</CardTitle>
                              <div className="flex items-center gap-2 flex-wrap">
                                <Badge
                                  className={getCategoryInfo(template.category).color}
                                  variant="secondary"
                                >
                                  {getCategoryInfo(template.category).label}
                                </Badge>
                                <Badge variant="outline">
                                  {getCommentTypeLabel(template.comment_type)}
                                </Badge>
                                <Badge variant="outline" className="bg-blue-50 text-blue-700">
                                  {getSubjectLabel(template.subject)}
                                </Badge>
                                {template.score_range_min !== undefined && template.score_range_max !== undefined && (
                                  <Badge variant="outline" className="bg-green-50 text-green-700">
                                    {template.score_range_min}-{template.score_range_max}点
                                  </Badge>
                                )}
                              </div>
                            </div>
                            <div className="flex gap-1">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleEdit(template)}
                              >
                                <Edit2 className="h-3 w-3" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleDelete(template.id)}
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            <p className="text-sm text-muted-foreground line-clamp-3">
                              {template.content}
                            </p>
                            <div className="flex items-center justify-between text-xs text-muted-foreground">
                              <div className="flex items-center gap-1">
                                <Sparkles className="h-3 w-3" />
                                使用回数: {template.usage_count}
                              </div>
                              <div className="flex items-center gap-1">
                                {template.is_active ? (
                                  <Badge className="bg-green-100 text-green-800">有効</Badge>
                                ) : (
                                  <Badge variant="secondary">無効</Badge>
                                )}
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </TabsContent>
            ))}
          </Tabs>
        )}
      </div>
    </DashboardLayout>
  );
}