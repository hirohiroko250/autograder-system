'use client';

export const dynamic = 'force-dynamic';

import { Suspense } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Download, FileText, CheckCircle, Clock, AlertTriangle, Calendar } from 'lucide-react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';
import { toast } from 'sonner';
import { useState } from 'react';

function TestDownloadContent() {
  const params = useParams();
  const { year } = params;
  const router = useRouter();
  const [selectedYear, setSelectedYear] = useState(year as string);
  const [selectedPeriod, setSelectedPeriod] = useState('spring'); // デフォルトを春期に設定

  const handleYearChange = (newYear: string) => {
    setSelectedYear(newYear);
    router.push(`/tests/${newYear}/download`);
  };

  const handlePeriodChange = (newPeriod: string) => {
    setSelectedPeriod(newPeriod);
    // 期間変更時はURLは変更せず、状態のみ更新
  };

  const getPeriodLabel = (period: string) => {
    switch (period) {
      case 'spring': return '春期';
      case 'summer': return '夏期';
      case 'winter': return '冬期';
      default: return period;
    }
  };

  const { data: testFiles } = useQuery({
    queryKey: ['test-files', selectedYear, selectedPeriod],
    queryFn: async () => {
      try {
        // 実際のAPIエンドポイントに修正
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/tests/${selectedYear}/${selectedPeriod}/files/`);
        if (!response.ok) {
          throw new Error('Failed to fetch test files');
        }
        return await response.json();
      } catch (error) {
        console.error('Error fetching test files:', error);
        // フォールバック用のモックデータ（一部ファイル未準備の例）
        return [
          {
            id: 1,
            name: `${selectedYear}年度${getPeriodLabel(selectedPeriod)}国語問題`,
            type: 'problem',
            subject: '国語',
            size: '2.5MB',
            status: 'available',
            lastUpdated: new Date('2024-07-15'),
            year: selectedYear,
            period: selectedPeriod,
          },
          {
            id: 2,
            name: `${selectedYear}年度${getPeriodLabel(selectedPeriod)}国語解答`,
            type: 'answer',
            subject: '国語',
            size: '未準備',
            status: 'processing',
            lastUpdated: new Date('2024-07-15'),
            year: selectedYear,
            period: selectedPeriod,
          },
          {
            id: 3,
            name: `${selectedYear}年度${getPeriodLabel(selectedPeriod)}算数問題`,
            type: 'problem',
            subject: '算数',
            size: '未準備',
            status: 'processing',
            lastUpdated: new Date('2024-07-15'),
            year: selectedYear,
            period: selectedPeriod,
          },
          {
            id: 4,
            name: `${selectedYear}年度${getPeriodLabel(selectedPeriod)}算数解答`,
            type: 'answer',
            subject: '算数',
            size: '1.8MB',
            status: 'available',
            lastUpdated: new Date('2024-07-16'),
            year: selectedYear,
            period: selectedPeriod,
          },
        ];
      }
    },
  });

  const handleDownload = async (file: any) => {
    try {
      console.log('Downloading file:', file.id);
      console.log('apiClient:', apiClient);
      console.log('typeof apiClient:', typeof apiClient);
      console.log('apiClient.get:', apiClient?.get);
      
      if (!apiClient || typeof apiClient.get !== 'function') {
        throw new Error('API client not properly initialized');
      }
      
      // 一時的にfetchを使用してテスト
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/tests/${selectedYear}/${selectedPeriod}/files/${file.id}/download/`, {
        method: 'GET',
      });
      
      if (!response.ok) {
        throw new Error('Download failed');
      }
      
      const blob = await response.blob();
      
      if (!blob) {
        throw new Error('Download failed');
      }
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${file.name}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      toast.success(`${file.name}をダウンロードしました`);
    } catch (error) {
      console.error('Download error:', error);
      toast.error('ダウンロードに失敗しました');
    }
  };

  const handleBulkDownload = async () => {
    try {
      console.log('Bulk downloading files');

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/tests/${selectedYear}/${selectedPeriod}/files/bulk-download/`, {
        method: 'GET',
      });
      
      if (!response.ok) {
        throw new Error('Bulk download failed');
      }
      
      const blob = await response.blob();
      
      if (!blob) {
        throw new Error('Bulk download failed');
      }
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedYear}年度${getPeriodLabel(selectedPeriod)}テスト_全ファイル.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
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
      case 'error':
        return (
          <Badge className="bg-red-100 text-red-800">
            <AlertTriangle className="h-3 w-3 mr-1" />
            エラー
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">テストファイルダウンロード</h1>
            <p className="text-muted-foreground mt-1">
              {selectedYear}年度 {getPeriodLabel(selectedPeriod)} テスト
            </p>
          </div>
          <Button onClick={handleBulkDownload} className="rounded-xl bg-primary hover:bg-primary/90">
            <Download className="h-4 w-4 mr-2" />
            全ファイル一括ダウンロード
          </Button>
        </div>

        {/* 年度・期間選択セクション */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              年度・期間選択
            </CardTitle>
            <CardDescription>
              ダウンロードしたいテストの年度と期間を選択してください
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">年度</label>
                <Select value={selectedYear} onValueChange={handleYearChange}>
                  <SelectTrigger className="w-40 rounded-xl">
                    <SelectValue placeholder="年度を選択" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="2027">2027年度</SelectItem>
                    <SelectItem value="2026">2026年度</SelectItem>
                    <SelectItem value="2025">2025年度</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">期間</label>
                <Select value={selectedPeriod} onValueChange={handlePeriodChange}>
                  <SelectTrigger className="w-40 rounded-xl">
                    <SelectValue placeholder="期間を選択" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="spring">春期</SelectItem>
                    <SelectItem value="summer">夏期</SelectItem>
                    <SelectItem value="winter">冬期</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">問題ファイル</CardTitle>
              <CardDescription>テスト問題のPDFファイル</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {testFiles?.filter((file: any) => file.type === 'problem').map((file: any) => (
                  <div key={file.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <FileText className="h-4 w-4 text-blue-500" />
                      <div>
                        <p className="font-medium text-sm">{file.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {file.size}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusBadge(file.status)}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDownload(file)}
                        disabled={file.status !== 'available'}
                        className="rounded-lg"
                      >
                        <Download className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">解答ファイル</CardTitle>
              <CardDescription>テスト解答のPDFファイル</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {testFiles?.filter((file: any) => file.type === 'answer').map((file: any) => (
                  <div key={file.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <FileText className="h-4 w-4 text-green-500" />
                      <div>
                        <p className="font-medium text-sm">{file.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {file.size}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusBadge(file.status)}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDownload(file)}
                        disabled={file.status !== 'available'}
                        className="rounded-lg"
                      >
                        <Download className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

      </div>
    </DashboardLayout>
  );
}

export default function TestDownloadPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <TestDownloadContent />
    </Suspense>
  );
}