'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { CommentForm } from './comment-form';
import { CommentList } from './comment-list';
import { MessageSquare, Plus, Sparkles, FileText } from 'lucide-react';
import { toast } from 'sonner';
import { commentApi } from '@/lib/api-client';

interface CommentManagerProps {
  studentId: string;
  studentName: string;
  testId?: string;
  testName?: string;
  showTestComments?: boolean;
}

interface CommentData {
  content: string;
  comment_type: string;
}

interface StudentComment {
  id: string;
  content: string;
  comment_type: string;
  created_at: string;
  updated_at: string;
  created_by_name: string;
  student_id: string;
}

interface TestComment {
  id: string;
  content: string;
  comment_type: string;
  created_at: string;
  updated_at: string;
  created_by_name: string;
  student_id: string;
  test_id: string;
  test_name: string;
}

interface CommentTemplate {
  id: string;
  name: string;
  content: string;
  category: string;
  comment_type: string;
}

export function CommentManager({ 
  studentId, 
  studentName, 
  testId, 
  testName, 
  showTestComments = false 
}: CommentManagerProps) {
  const [showForm, setShowForm] = useState(false);
  const [activeTab, setActiveTab] = useState('student');
  const queryClient = useQueryClient();

  // 生徒コメント取得
  const { data: studentComments = [], isLoading: isLoadingStudentComments } = useQuery({
    queryKey: ['student-comments', studentId],
    queryFn: async () => {
      const response = await commentApi.getStudentComments({ student_id: studentId });
      return response.results || [];
    },
  });

  // テストコメント取得
  const { data: testComments = [], isLoading: isLoadingTestComments } = useQuery({
    queryKey: ['test-comments', studentId, testId],
    queryFn: async () => {
      if (!testId) return [];
      const response = await commentApi.getTestComments({ student_id: studentId, test_id: testId });
      return response.results || [];
    },
    enabled: !!testId,
  });

  // コメントテンプレート取得
  const { data: templates = [] } = useQuery({
    queryKey: ['comment-templates'],
    queryFn: async () => {
      const response = await commentApi.getCommentTemplatesV2();
      return response.results || [];
    },
  });

  // 生徒コメント作成
  const createStudentComment = useMutation({
    mutationFn: async (data: CommentData) => {
      return await commentApi.createStudentComment({
        student_id: studentId,
        content: data.content,
        comment_type: data.comment_type,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student-comments', studentId] });
      setShowForm(false);
      toast.success('生徒コメントを作成しました');
    },
    onError: () => {
      toast.error('生徒コメントの作成に失敗しました');
    },
  });

  // テストコメント作成
  const createTestComment = useMutation({
    mutationFn: async (data: CommentData) => {
      return await commentApi.createTestComment({
        student_id: studentId,
        test_id: testId!,
        content: data.content,
        comment_type: data.comment_type,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['test-comments', studentId, testId] });
      setShowForm(false);
      toast.success('テストコメントを作成しました');
    },
    onError: () => {
      toast.error('テストコメントの作成に失敗しました');
    },
  });

  // コメント更新
  const updateComment = useMutation({
    mutationFn: async ({ id, data, type }: { id: string; data: CommentData; type: 'student' | 'test' }) => {
      if (type === 'student') {
        return await commentApi.updateStudentComment(id, {
          content: data.content,
          comment_type: data.comment_type,
        });
      } else {
        return await commentApi.updateTestComment(id, {
          content: data.content,
          comment_type: data.comment_type,
        });
      }
    },
    onSuccess: (_, variables) => {
      if (variables.type === 'student') {
        queryClient.invalidateQueries({ queryKey: ['student-comments', studentId] });
      } else {
        queryClient.invalidateQueries({ queryKey: ['test-comments', studentId, testId] });
      }
    },
  });

  // コメント削除
  const deleteComment = useMutation({
    mutationFn: async ({ id, type }: { id: string; type: 'student' | 'test' }) => {
      if (type === 'student') {
        return await commentApi.deleteStudentComment(id);
      } else {
        return await commentApi.deleteTestComment(id);
      }
    },
    onSuccess: (_, variables) => {
      if (variables.type === 'student') {
        queryClient.invalidateQueries({ queryKey: ['student-comments', studentId] });
      } else {
        queryClient.invalidateQueries({ queryKey: ['test-comments', studentId, testId] });
      }
    },
  });

  // 自動コメント生成
  const generateAutoComments = useMutation({
    mutationFn: async () => {
      return await commentApi.autoGenerateComments(studentId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student-comments', studentId] });
      toast.success('自動コメントを生成しました');
    },
    onError: () => {
      toast.error('自動コメントの生成に失敗しました');
    },
  });

  const handleStudentCommentSubmit = async (data: CommentData) => {
    await createStudentComment.mutateAsync(data);
  };

  const handleTestCommentSubmit = async (data: CommentData) => {
    await createTestComment.mutateAsync(data);
  };

  const handleStudentCommentEdit = async (commentId: string, data: CommentData) => {
    await updateComment.mutateAsync({ id: commentId, data, type: 'student' });
  };

  const handleTestCommentEdit = async (commentId: string, data: CommentData) => {
    await updateComment.mutateAsync({ id: commentId, data, type: 'test' });
  };

  const handleStudentCommentDelete = async (commentId: string) => {
    await deleteComment.mutateAsync({ id: commentId, type: 'student' });
  };

  const handleTestCommentDelete = async (commentId: string) => {
    await deleteComment.mutateAsync({ id: commentId, type: 'test' });
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              コメント管理
            </CardTitle>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Badge variant="outline">{studentName}</Badge>
              {testName && <Badge variant="outline">{testName}</Badge>}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <Button
              onClick={() => setShowForm(!showForm)}
              className="rounded-xl"
            >
              <Plus className="h-4 w-4 mr-2" />
              新しいコメント
            </Button>
            
            <Button
              variant="outline"
              onClick={() => generateAutoComments.mutate()}
              disabled={generateAutoComments.isPending}
              className="rounded-xl"
            >
              <Sparkles className="h-4 w-4 mr-2" />
              {generateAutoComments.isPending ? '生成中...' : '自動生成'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {showForm && (
        <CommentForm
          studentId={studentId}
          studentName={studentName}
          testId={activeTab === 'test' ? testId : undefined}
          testName={activeTab === 'test' ? testName : undefined}
          onSubmit={activeTab === 'student' ? handleStudentCommentSubmit : handleTestCommentSubmit}
          onCancel={() => setShowForm(false)}
          isSubmitting={createStudentComment.isPending || createTestComment.isPending}
          templates={templates}
        />
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="student">
            <MessageSquare className="h-4 w-4 mr-2" />
            生徒コメント ({studentComments.length})
          </TabsTrigger>
          {showTestComments && testId && (
            <TabsTrigger value="test">
              <FileText className="h-4 w-4 mr-2" />
              テストコメント ({testComments.length})
            </TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="student" className="mt-4">
          <CommentList
            comments={studentComments}
            onEdit={handleStudentCommentEdit}
            onDelete={handleStudentCommentDelete}
            isLoading={isLoadingStudentComments}
          />
        </TabsContent>

        {showTestComments && testId && (
          <TabsContent value="test" className="mt-4">
            <CommentList
              comments={testComments}
              onEdit={handleTestCommentEdit}
              onDelete={handleTestCommentDelete}
              isLoading={isLoadingTestComments}
              showTestName={true}
            />
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}