'use client';

import React, { useState, useEffect } from 'react';
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
import { Switch } from '@/components/ui/switch';
import { schoolApi } from '@/lib/api-client';
import { toast } from 'sonner';

const formSchema = z.object({
  name: z.string().min(1, '教室名は必須です').max(100, '教室名は100文字以内で入力してください'),
  is_active: z.boolean(),
  permissions: z.object({
    can_register_students: z.boolean(),
    can_input_scores: z.boolean(),
    can_view_reports: z.boolean(),
  }),
});

interface Classroom {
  id: number;
  name: string;
  classroom_id: string;
  school_name: string;
  student_count: number;
  is_active: boolean;
  permissions?: {
    can_register_students: boolean;
    can_input_scores: boolean;
    can_view_reports: boolean;
  };
}

interface ClassroomEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  classroom: Classroom | null;
}

export const ClassroomEditModal: React.FC<ClassroomEditModalProps> = ({
  isOpen,
  onClose,
  classroom,
}) => {
  const queryClient = useQueryClient();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      is_active: true,
      permissions: {
        can_register_students: false,
        can_input_scores: false,
        can_view_reports: true,
      },
    },
  });

  useEffect(() => {
    if (classroom) {
      form.reset({
        name: classroom.name,
        is_active: classroom.is_active,
        permissions: {
          can_register_students: classroom.permissions?.can_register_students ?? false,
          can_input_scores: classroom.permissions?.can_input_scores ?? false,
          can_view_reports: classroom.permissions?.can_view_reports ?? true,
        },
      });
    }
  }, [classroom, form]);

  const updateClassroomMutation = useMutation({
    mutationFn: async (data: z.infer<typeof formSchema>) => {
      if (!classroom) throw new Error('教室が選択されていません');
      
      // Create the update request with only editable fields
      const updateRequest = {
        name: data.name,
        is_active: data.is_active,
        permissions: data.permissions,
      };
      
      // Call the actual API
      return await schoolApi.updateClassroom(classroom.id, updateRequest);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['classrooms'] });
      
      // 現在ログイン中のユーザーが該当教室の管理者の場合、権限情報を即座に更新
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      if (
        classroom &&
        currentUser.role === 'classroom_admin' &&
        currentUser.classroom_id &&
        parseInt(currentUser.classroom_id) === classroom.id
      ) {
        
        console.log('Updating current user permissions in real-time');
        currentUser.permissions = data.permissions;
        localStorage.setItem('user', JSON.stringify(currentUser));
        
        // AuthContextの状態も更新（リロードなしで反映）
        window.dispatchEvent(new CustomEvent('user-permissions-updated', {
          detail: { permissions: data.permissions }
        }));
        
        toast.success('教室情報と権限設定を更新しました（即座に反映）');
      } else {
        toast.success('教室情報を更新しました');
      }
      
      onClose();
    },
    onError: (error: any) => {
      console.error('教室更新エラー:', error);
      toast.error('教室情報の更新に失敗しました');
    },
  });

  const onSubmit = (values: z.infer<typeof formSchema>) => {
    updateClassroomMutation.mutate(values);
  };

  const handleClose = () => {
    form.reset();
    onClose();
  };

  if (!classroom) return null;

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>教室情報を編集</DialogTitle>
          <DialogDescription>
            教室の基本情報を変更できます。
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-500">教室ID</div>
              <div className="p-2 bg-gray-50 rounded text-sm font-mono">
                {classroom.classroom_id}
              </div>
              <div className="text-xs text-gray-500">
                教室IDは変更できません
              </div>
            </div>

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

            <FormField
              control={form.control}
              name="is_active"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">アクティブ状態</FormLabel>
                    <div className="text-sm text-muted-foreground">
                      教室を有効または無効にします
                    </div>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-500">学校名</div>
              <div className="p-2 bg-gray-50 rounded text-sm">
                {classroom.school_name}
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-500">生徒数</div>
              <div className="p-2 bg-gray-50 rounded text-sm">
                {classroom.student_count || 0}名
              </div>
            </div>

            <div className="space-y-4 pt-4 border-t">
              <div className="text-lg font-medium">教室管理者権限設定</div>
              <div className="text-sm text-muted-foreground">
                この教室の管理者が実行できる操作を設定します
              </div>
              
              <FormField
                control={form.control}
                name="permissions.can_register_students"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">生徒登録権限</FormLabel>
                      <div className="text-sm text-muted-foreground">
                        生徒の新規登録・編集・削除を許可
                      </div>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="permissions.can_input_scores"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">点数入力権限</FormLabel>
                      <div className="text-sm text-muted-foreground">
                        テスト結果の入力・編集を許可
                      </div>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="permissions.can_view_reports"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">結果出力権限</FormLabel>
                      <div className="text-sm text-muted-foreground">
                        テスト結果の表示・ダウンロードを許可
                      </div>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
            </div>

            <div className="flex justify-end space-x-2 pt-4">
              <Button type="button" variant="outline" onClick={handleClose}>
                キャンセル
              </Button>
              <Button 
                type="submit" 
                disabled={updateClassroomMutation.isPending}
              >
                {updateClassroomMutation.isPending ? '更新中...' : '更新'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};
