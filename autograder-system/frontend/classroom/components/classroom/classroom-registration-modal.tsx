'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Copy, Eye, EyeOff, CheckCircle } from 'lucide-react';
import { schoolApi } from '@/lib/api-client';
import { CreateClassroomRequest, CreateClassroomResponse } from '@/lib/types';
import { toast } from 'sonner';

const formSchema = z.object({
  name: z.string().min(1, '教室名は必須です').max(100, '教室名は100文字以内で入力してください'),
});

interface ClassroomRegistrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  schoolId: number;
}

export const ClassroomRegistrationModal: React.FC<ClassroomRegistrationModalProps> = ({
  isOpen,
  onClose,
  schoolId,
}) => {
  const [showCredentials, setShowCredentials] = useState(false);
  const [createdClassroom, setCreatedClassroom] = useState<CreateClassroomResponse | null>(null);
  const queryClient = useQueryClient();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
    },
  });

  const createClassroomMutation = useMutation({
    mutationFn: (data: CreateClassroomRequest) => schoolApi.createClassroom(schoolId, data),
    onSuccess: (data) => {
      setCreatedClassroom(data);
      form.reset();
      queryClient.invalidateQueries({ queryKey: ['classrooms'] });
      toast.success('教室が正常に登録されました');
    },
    onError: (error: any) => {
      console.error('教室登録エラー:', error);
      if (error.response?.data?.error) {
        toast.error(`教室登録エラー: ${error.response.data.error}`);
      } else if (error.response?.data) {
        const errorMessage = Object.entries(error.response.data)
          .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(', ') : messages}`)
          .join('; ');
        toast.error(`教室登録エラー: ${errorMessage}`);
      } else {
        toast.error('教室の登録に失敗しました');
      }
    },
  });

  const onSubmit = (values: z.infer<typeof formSchema>) => {
    createClassroomMutation.mutate(values);
  };

  const handleCopyCredentials = () => {
    if (createdClassroom) {
      const credentials = `ログインID: ${createdClassroom.credentials.login_id}\n教室ID: ${createdClassroom.credentials.classroom_id}\nパスワード: ${createdClassroom.credentials.password}`;
      navigator.clipboard.writeText(credentials);
      toast.success('認証情報をクリップボードにコピーしました');
    }
  };

  const handleClose = () => {
    setCreatedClassroom(null);
    setShowCredentials(false);
    form.reset();
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>新しい教室を登録</DialogTitle>
          <DialogDescription>
            教室を登録すると、教室管理者用のIDとパスワードが自動発行されます。
          </DialogDescription>
        </DialogHeader>

        {!createdClassroom ? (
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>教室名</FormLabel>
                    <FormControl>
                      <Input placeholder="例: A教室" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="flex justify-end space-x-2">
                <Button type="button" variant="outline" onClick={handleClose}>
                  キャンセル
                </Button>
                <Button 
                  type="submit" 
                  disabled={createClassroomMutation.isPending}
                >
                  {createClassroomMutation.isPending ? '登録中...' : '教室を登録'}
                </Button>
              </div>
            </form>
          </Form>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center space-x-2 text-green-600">
              <CheckCircle className="h-5 w-5" />
              <span className="font-medium">教室が正常に登録されました！</span>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">教室情報</CardTitle>
                <CardDescription>
                  以下の情報を教室管理者にお渡しください
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-500">教室名</span>
                  </div>
                  <div className="text-lg font-semibold">{createdClassroom.classroom.name}</div>
                </div>

                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-500">ログインID</span>
                    <Badge variant="secondary">{createdClassroom.credentials.login_id}</Badge>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    塾ID + 教室ID（{createdClassroom.credentials.login_id}）
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-500">教室ID</span>
                    <Badge variant="secondary">{createdClassroom.credentials.classroom_id}</Badge>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-500">初期パスワード</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowCredentials(!showCredentials)}
                    >
                      {showCredentials ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                  <div className="font-mono text-lg">
                    {showCredentials ? createdClassroom.credentials.password : '••••••'}
                  </div>
                </div>

                <div className="p-3 bg-yellow-50 rounded-md">
                  <p className="text-sm text-yellow-800">
                    <strong>重要:</strong> 教室ページへのログインには「ログインID」を使用してください。
                    初期パスワードは教室IDと同じです。
                    セキュリティのため、最初のログイン後にパスワードを変更することをお勧めします。
                  </p>
                </div>

                <Button onClick={handleCopyCredentials} className="w-full">
                  <Copy className="mr-2 h-4 w-4" />
                  認証情報をコピー
                </Button>
              </CardContent>
            </Card>

            <div className="flex justify-end">
              <Button onClick={handleClose}>完了</Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};