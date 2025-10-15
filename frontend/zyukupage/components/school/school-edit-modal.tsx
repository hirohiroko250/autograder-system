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
import { School } from '@/lib/types';

const formSchema = z.object({
  name: z.string().min(1, '塾名は必須です').max(100, '塾名は100文字以内で入力してください'),
  is_active: z.boolean(),
  can_register_students: z.boolean(),
  can_input_scores: z.boolean(),
  can_view_reports: z.boolean(),
});

interface SchoolEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  school: School | null;
}

export const SchoolEditModal: React.FC<SchoolEditModalProps> = ({
  isOpen,
  onClose,
  school,
}) => {
  const queryClient = useQueryClient();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      is_active: true,
      can_register_students: true,
      can_input_scores: true,
      can_view_reports: true,
    },
  });

  useEffect(() => {
    if (school) {
      form.reset({
        name: school.name,
        is_active: school.is_active,
        can_register_students: school.can_register_students ?? school.permissions?.can_register_students ?? true,
        can_input_scores: school.can_input_scores ?? school.permissions?.can_input_scores ?? true,
        can_view_reports: school.can_view_reports ?? school.permissions?.can_view_reports ?? true,
      });
    }
  }, [school, form]);

  const updateSchoolMutation = useMutation({
    mutationFn: async (data: z.infer<typeof formSchema>) => {
      if (!school) throw new Error('学校が選択されていません');
      
      return await schoolApi.updateSchool(school.id, {
        name: data.name,
        is_active: data.is_active,
        can_register_students: data.can_register_students,
        can_input_scores: data.can_input_scores,
        can_view_reports: data.can_view_reports,
      });
    },
    onSuccess: (data) => {
      console.log('School update successful:', data);
      console.log('Updated permissions in response:', data.permissions);
      
      queryClient.invalidateQueries({ queryKey: ['schools'] });
      queryClient.invalidateQueries({ queryKey: ['classrooms'] });
      
      // 現在ログイン中のユーザーが該当学校の管理者または教室管理者の場合、権限情報を即座に更新
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      console.log('Current user for real-time update check:', {
        role: currentUser.role,
        school_id: currentUser.school_id,
        updated_school_id: school?.school_id
      });
      
      if ((currentUser.role === 'school_admin' || currentUser.role === 'classroom_admin') && 
          currentUser.school_id === school?.school_id) {
        
        console.log('Updating current user permissions in real-time');
        console.log('New permissions to apply:', data.permissions);
        
        // 学校の権限をユーザーの権限として設定
        currentUser.permissions = data.permissions || {
          can_register_students: data.can_register_students,
          can_input_scores: data.can_input_scores,
          can_view_reports: data.can_view_reports,
        };
        localStorage.setItem('user', JSON.stringify(currentUser));
        
        // AuthContextの状態も更新（リロードなしで反映）
        window.dispatchEvent(new CustomEvent('user-permissions-updated', {
          detail: { permissions: currentUser.permissions }
        }));
        
        toast.success('学校情報と権限設定を更新しました（即座に反映）');
      } else {
        toast.success('学校情報を更新しました');
      }
      
      onClose();
    },
    onError: (error: any) => {
      console.error('学校更新エラー:', error);
      toast.error('学校情報の更新に失敗しました');
    },
  });

  const onSubmit = (values: z.infer<typeof formSchema>) => {
    updateSchoolMutation.mutate(values);
  };

  const handleClose = () => {
    form.reset();
    onClose();
  };

  if (!school) return null;

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>学校情報を編集</DialogTitle>
          <DialogDescription>
            学校の基本情報と権限設定を変更できます。
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-500">学校ID</div>
              <div className="p-2 bg-gray-50 rounded text-sm font-mono">
                {school.school_id}
              </div>
              <div className="text-xs text-gray-500">
                学校IDは変更できません
              </div>
            </div>

            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>学校名</FormLabel>
                  <FormControl>
                    <Input placeholder="例: 〇〇塾" {...field} />
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
                      学校を有効または無効にします
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

            <div className="space-y-4 pt-4 border-t">
              <div className="text-lg font-medium">教室管理者権限設定</div>
              <div className="text-sm text-muted-foreground">
                この学校の教室管理者が実行できる操作を一括設定します
              </div>
              
              <FormField
                control={form.control}
                name="can_register_students"
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
                name="can_input_scores"
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
                name="can_view_reports"
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
                disabled={updateSchoolMutation.isPending}
              >
                {updateSchoolMutation.isPending ? '更新中...' : '更新'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};