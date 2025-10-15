'use client';

import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from '@/components/ui/form';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { schoolApi } from '@/lib/api-client';
import { toast } from 'sonner';
import { useAuth } from '@/lib/auth-context';
import { Shield, Users, FileText, BarChart, AlertTriangle } from 'lucide-react';

const formSchema = z.object({
  allow_classroom_student_management: z.boolean(),
  default_permissions: z.object({
    can_register_students: z.boolean(),
    can_input_scores: z.boolean(),
    can_view_reports: z.boolean(),
  }),
});

export default function PermissionsSettingsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      allow_classroom_student_management: true,
      default_permissions: {
        can_register_students: false,
        can_input_scores: false,
        can_view_reports: true,
      },
    },
  });

  // 学校設定を取得
  const { data: schoolSettings } = useQuery({
    queryKey: ['school-settings', user?.school_id],
    queryFn: async () => {
      const response = await schoolApi.getSchoolSettings();
      return response;
    },
    enabled: !!user && user.role === 'school_admin',
  });

  // フォームに設定を反映
  useEffect(() => {
    if (schoolSettings) {
      form.reset({
        allow_classroom_student_management: schoolSettings.allow_classroom_student_management ?? true,
        default_permissions: {
          can_register_students: schoolSettings.default_permissions?.can_register_students ?? false,
          can_input_scores: schoolSettings.default_permissions?.can_input_scores ?? false,
          can_view_reports: schoolSettings.default_permissions?.can_view_reports ?? true,
        },
      });
    }
  }, [schoolSettings, form]);

  // 設定更新のミューテーション
  const updateSettingsMutation = useMutation({
    mutationFn: async (data: z.infer<typeof formSchema>) => {
      return await schoolApi.updateSchoolSettings(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['school-settings'] });
      toast.success('権限設定を更新しました');
    },
    onError: (error: any) => {
      console.error('設定更新エラー:', error);
      toast.error('権限設定の更新に失敗しました');
    },
  });

  const onSubmit = (values: z.infer<typeof formSchema>) => {
    updateSettingsMutation.mutate(values);
  };

  if (user?.role !== 'school_admin') {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <Card className="w-full max-w-md">
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <CardTitle>アクセス権限がありません</CardTitle>
              <CardDescription>
                この設定には学校管理者権限が必要です。
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold">権限設定</h1>
          <p className="text-muted-foreground">
            学校全体および教室管理者の権限を設定します
          </p>
        </div>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* 学校全体設定 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  学校全体設定
                </CardTitle>
                <CardDescription>
                  学校全体での権限制御を設定します
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <FormField
                  control={form.control}
                  name="allow_classroom_student_management"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                      <div className="space-y-0.5">
                        <FormLabel className="text-base">教室ごとの生徒管理を許可</FormLabel>
                        <FormDescription>
                          オフにすると、すべての教室管理者の生徒登録・編集権限が無効になります。
                          学校管理者のみが生徒管理を行えます。
                        </FormDescription>
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

                {!form.watch('allow_classroom_student_management') && (
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                    <div className="flex items-center gap-2 text-amber-800 mb-2">
                      <AlertTriangle className="h-4 w-4" />
                      <span className="font-medium">注意</span>
                    </div>
                    <p className="text-sm text-amber-700">
                      この設定をオフにすると、すべての教室管理者が生徒の登録・編集を行えなくなります。
                      生徒管理は学校管理者のみが行えます。
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* 教室管理者デフォルト権限 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  教室管理者デフォルト権限
                </CardTitle>
                <CardDescription>
                  新しい教室を作成した際の、教室管理者のデフォルト権限を設定します
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <FormField
                  control={form.control}
                  name="default_permissions.can_register_students"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                      <div className="space-y-0.5">
                        <FormLabel className="text-base flex items-center gap-2">
                          <Users className="h-4 w-4" />
                          生徒登録権限（デフォルト）
                        </FormLabel>
                        <FormDescription>
                          生徒の新規登録・編集・削除を許可
                        </FormDescription>
                      </div>
                      <FormControl>
                        <Switch
                          checked={field.value && form.watch('allow_classroom_student_management')}
                          onCheckedChange={field.onChange}
                          disabled={!form.watch('allow_classroom_student_management')}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="default_permissions.can_input_scores"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                      <div className="space-y-0.5">
                        <FormLabel className="text-base flex items-center gap-2">
                          <FileText className="h-4 w-4" />
                          点数入力権限（デフォルト）
                        </FormLabel>
                        <FormDescription>
                          テスト結果の入力・編集を許可
                        </FormDescription>
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
                  name="default_permissions.can_view_reports"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                      <div className="space-y-0.5">
                        <FormLabel className="text-base flex items-center gap-2">
                          <BarChart className="h-4 w-4" />
                          結果出力権限（デフォルト）
                        </FormLabel>
                        <FormDescription>
                          テスト結果の表示・ダウンロードを許可
                        </FormDescription>
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

                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-700">
                    <strong>注意:</strong> これらの設定は新しい教室を作成した際のデフォルト権限です。
                    既存の教室の権限は個別に変更する必要があります。
                  </p>
                </div>
              </CardContent>
            </Card>

            <div className="flex justify-end">
              <Button 
                type="submit" 
                disabled={updateSettingsMutation.isPending}
                className="px-8"
              >
                {updateSettingsMutation.isPending ? '保存中...' : '設定を保存'}
              </Button>
            </div>
          </form>
        </Form>
      </div>
    </DashboardLayout>
  );
}