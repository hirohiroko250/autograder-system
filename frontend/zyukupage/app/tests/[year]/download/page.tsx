'use client';

import { Suspense } from 'react';
import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Download, FileText, CheckCircle, Clock, AlertTriangle, Calendar } from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '@/lib/api-client';
import { Label } from '@/components/ui/label';

function getPeriodLabel(period: string) {
  switch (period) {
    case 'spring':
      return '春期';
    case 'summer':
      return '夏期';
    case 'winter':
      return '冬期';
    default:
      return period;
  }
}

function TestDownloadContent() {
  const params = useParams();
  const router = useRouter();
  const year = params.year as string;

  const [selectedYear, setSelectedYear] = useState(year);
  const [selectedPeriod, setSelectedPeriod] = useState('spring');

  const handleYearChange = (newYear: string) => {
    setSelectedYear(newYear);
    router.push(`/tests/${newYear}/download`);
  };

  const handlePeriodChange = (newPeriod: string) => {
    setSelectedPeriod(newPeriod);
  };

  const {
    data: testFiles,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['test-files', selectedYear, selectedPeriod],
    queryFn: async () => {
      try {
        const response = await apiClient.get(`/tests/${selectedYear}/${selectedPeriod}/files/`);
        return response.data ?? [];
      } catch (error) {
        console.error('Error fetching test files:', error);
        toast.error('テストファイルの取得に失敗しました');
        return [];
      }
    },
  });

  const files = Array.isArray(testFiles) ? testFiles : [];
  const hasAvailableFiles = files.some((file: any) => file.status === 'available');

  const downloadBinary = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    window.URL.revokeObjectURL(url);
  };

  const handleDownload = async (file: any) => {
    if (file?.status !== 'available') {
      toast.warning('このファイルは現在ダウンロードできません');
      return;
    }

    try {
      const response = await apiClient.get(
        `/tests/${selectedYear}/${selectedPeriod}/files/${file.id}/download/`,
        { responseType: 'blob' }
      );

      const blob = response?.data;
      if (!blob) throw new Error('空のファイルです');

      downloadBinary(blob, `${file.name}.pdf`);
      toast.success(`${file.name}をダウンロードしました`);
    } catch (error) {
      console.error('Download error:', error);
      toast.error('ダウンロードに失敗しました');
    }
  };

  const handleBulkDownload = async () => {
    if (!hasAvailableFiles) {
      toast.warning('ダウンロード可能なファイルがありません');
      return;
    }

    try {
      const response = await apiClient.get(
        `/tests/${selectedYear}/${selectedPeriod}/files/bulk-download/`,
        { responseType: 'blob' }
      );

      const blob = response?.data;
      if (!blob) throw new Error('空のファイルです');

      downloadBinary(blob, `${selectedYear}年度${getPeriodLabel(selectedPeriod)}テスト_全ファイル.zip`);
      toast.success('全ファイルをZip形式でダウンロードしました');
    } catch (error) {
      console.error('Bulk download error:', error);
      toast.error('一括ダウンロードに失敗しました');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'available':
        return (
          <Badge className="bg-green-100 text-green-800">
            <CheckCircle className="h-3 w-3 mr-1" />
            利用可能
          </Badge>
        );
      case 'processing':
        return (
          <Badge className="bg-orange-100 text-orange-800">
            <Clock className="h-3 w-3 mr-1" />
            処理中
          </Badge>
        );
      case 'missing':
      case 'unavailable':
        return <Badge variant="outline">未登録</Badge>;
      case 'error':
        return (
          <Badge className="bg-red-100 text-red-800">
            <AlertTriangle className="h-3 w-3 mr-1" />
            エラー
          </Badge>
        );
      default:
        return <Badge variant="outline">不明</Badge>;
    }
  };

  const getStatusDescription = (status: string) => {
    switch (status) {
      case 'available':
        return 'ダウンロード可能';
      case 'processing':
        return '現在準備中です';
      case 'missing':
      case 'unavailable':
        return 'ファイルが登録されていません';
      case 'error':
        return 'エラーが発生しました。管理者にお問い合わせください';
      default:
        return 'ステータス不明';
    }
  };

  return (
    <DashboardLayout>
      <div className="py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold">テスト問題ダウンロード</h1>
            <p className="text-muted-foreground mt-1">
              選択した年度・期間のテスト問題と解答をダウンロードできます
            </p>
          </div>
          <Card className="border-primary/10 bg-primary/5">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="rounded-full bg-primary text-primary-foreground p-2">
                <Calendar className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">選択中の年度</p>
                <p className="text-sm font-semibold">{selectedYear}年度</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>ダウンロード条件の選択</CardTitle>
            <CardDescription>年度と期を選択してファイルを確認してください</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap items-center gap-4">
            <div>
              <Label className="text-sm font-medium text-muted-foreground">年度を選択</Label>
              <Select value={selectedYear} onValueChange={handleYearChange}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="年度を選択" />
                </SelectTrigger>
                <SelectContent>
                  {Array.from({ length: 6 }).map((_, index) => {
                    const targetYear = (new Date().getFullYear() - index).toString();
                    return (
                      <SelectItem key={targetYear} value={targetYear}>
                        {targetYear}年度
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-sm font-medium text-muted-foreground">期間を選択</Label>
              <Select value={selectedPeriod} onValueChange={handlePeriodChange}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="期間を選択" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="spring">春期</SelectItem>
                  <SelectItem value="summer">夏期</SelectItem>
                  <SelectItem value="winter">冬期</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              variant="outline"
              className="space-x-2"
              onClick={handleBulkDownload}
              disabled={!hasAvailableFiles}
            >
              <Download className="h-4 w-4" />
              <span>全ファイルを一括ダウンロード</span>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>テストファイル一覧</CardTitle>
            <CardDescription>
              {selectedYear}年度 {getPeriodLabel(selectedPeriod)} のテストファイルを確認し、必要に応じてダウンロードしてください
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading && <p className="text-sm text-muted-foreground">読み込み中...</p>}
            {isError && (
              <p className="text-sm text-red-600">
                ファイル情報を取得できませんでした。時間をおいて再度お試しください。
              </p>
            )}
            {!isLoading && !files.length && (
              <p className="text-sm text-muted-foreground">
                この年度・期間には登録されたファイルがありません。
              </p>
            )}

            {files.map((file: any) => {
              const statusBadge = getStatusBadge(file.status);
              const statusDescription = getStatusDescription(file.status);
              const updatedAt = file.lastUpdated ? new Date(file.lastUpdated) : null;

              return (
                <Card key={`file-${file.id}`} className="border-muted">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-4">
                        <div className="rounded-full bg-primary/10 p-3 text-primary">
                          <FileText className="h-5 w-5" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold">{file.name || '名称未設定'}</h3>
                          <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
                            科目: {file.subject || '不明'} / 種別: {file.type || '不明'}
                          </p>
                          <dl className="grid grid-cols-2 gap-2 mt-3 text-sm text-muted-foreground">
                            <div>
                              <dt>サイズ</dt>
                              <dd>{file.size || (file.status === 'available' ? '-' : '未登録')}</dd>
                            </div>
                            <div>
                              <dt>最終更新</dt>
                              <dd>{updatedAt ? updatedAt.toLocaleDateString('ja-JP') : '不明'}</dd>
                            </div>
                            <div className="col-span-2 flex items-center gap-2">
                              <dt className="font-medium">状態</dt>
                              <dd className="flex items-center gap-2">
                                {statusBadge}
                                <span className="text-xs text-muted-foreground">{statusDescription}</span>
                              </dd>
                            </div>
                          </dl>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          onClick={() => handleDownload(file)}
                          disabled={file.status !== 'available'}
                        >
                          <Download className="h-4 w-4 mr-2" />ダウンロード
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

export default function TestDownloadPage() {
  return (
    <Suspense fallback={<div>読み込み中...</div>}>
      <TestDownloadContent />
    </Suspense>
  );
}
