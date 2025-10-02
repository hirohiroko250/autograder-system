'use client';

export const dynamic = 'force-dynamic';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  Upload, 
  FileText, 
  Users, 
  MessageSquare, 
  CalendarCheck, 
  BarChart3,
  Clock,
  CheckCircle,
  AlertTriangle,
  Download,
  History
} from 'lucide-react';
import { toast } from 'sonner';

interface ImportHistory {
  id: string;
  import_type: string;
  status: string;
  total_records: number;
  successful_records: number;
  failed_records: number;
  error_log: string;
  created_at: string;
  created_by_name: string;
}

const IMPORT_TYPES = [
  { value: 'student_data', label: '生徒データ', icon: Users, description: '生徒の基本情報をインポートします' },
  { value: 'score_data', label: 'スコアデータ', icon: BarChart3, description: 'テストスコア・成績データをインポートします' },
  { value: 'comment_data', label: 'コメントデータ', icon: MessageSquare, description: '生徒コメント・評価をインポートします' },
  { value: 'attendance_data', label: '出席データ', icon: CalendarCheck, description: '出席・欠席情報をインポートします' },
  { value: 'test_results', label: 'テスト結果', icon: FileText, description: '詳細なテスト結果をインポートします' },
  { value: 'full_migration', label: '完全移行', icon: Download, description: 'すべてのデータを一括インポートします' }
];

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'completed':
      return <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />完了</Badge>;
    case 'processing':
      return <Badge className="bg-blue-100 text-blue-800"><Clock className="h-3 w-3 mr-1" />処理中</Badge>;
    case 'failed':
      return <Badge className="bg-red-100 text-red-800"><AlertTriangle className="h-3 w-3 mr-1" />失敗</Badge>;
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
};

export default function DataImportPage() {
  const [selectedImportType, setSelectedImportType] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [importNotes, setImportNotes] = useState('');

  // インポート履歴取得
  const { data: importHistory = [], isLoading, refetch } = useQuery({
    queryKey: ['import-history'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/past-data-imports/');
      if (!response.ok) throw new Error('Failed to fetch import history');
      const data = await response.json();
      return data.results || [];
    },
  });

  // データインポート実行
  const importMutation = useMutation({
    mutationFn: async (data: { importType: string; file?: File; notes?: string }) => {
      const formData = new FormData();
      formData.append('import_type', data.importType);
      if (data.file) {
        formData.append('file', data.file);
      }
      if (data.notes) {
        formData.append('notes', data.notes);
      }

      const response = await fetch('http://localhost:8000/api/past-data-imports/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Import failed');
      return response.json();
    },
    onSuccess: () => {
      toast.success('データインポートを開始しました');
      setSelectedImportType('');
      setUploadFile(null);
      setImportNotes('');
      refetch();
    },
    onError: (error: any) => {
      toast.error(`インポートに失敗しました: ${error.message}`);
    },
  });

  const handleImport = () => {
    if (!selectedImportType) {
      toast.error('インポートタイプを選択してください');
      return;
    }

    importMutation.mutate({
      importType: selectedImportType,
      file: uploadFile || undefined,
      notes: importNotes || undefined,
    });
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadFile(file);
    }
  };

  const selectedType = IMPORT_TYPES.find(type => type.value === selectedImportType);

  return (
    <DashboardLayout>
      <div className="space-y-6 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold">過去データインポート</h1>
          <p className="text-muted-foreground mt-1">
            既存システムからのデータ移行・統合を行います
          </p>
        </div>

        <Tabs defaultValue="import" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="import">新規インポート</TabsTrigger>
            <TabsTrigger value="history">インポート履歴</TabsTrigger>
          </TabsList>

          <TabsContent value="import" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  データインポート
                </CardTitle>
                <CardDescription>
                  インポートするデータの種類を選択し、必要に応じてファイルをアップロードしてください
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label>インポートタイプ</Label>
                  <Select value={selectedImportType} onValueChange={setSelectedImportType}>
                    <SelectTrigger>
                      <SelectValue placeholder="インポートタイプを選択してください" />
                    </SelectTrigger>
                    <SelectContent>
                      {IMPORT_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          <div className="flex items-center gap-2">
                            <type.icon className="h-4 w-4" />
                            <div>
                              <div className="font-medium">{type.label}</div>
                              <div className="text-xs text-muted-foreground">{type.description}</div>
                            </div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {selectedType && (
                  <Card className="bg-blue-50 border-blue-200">
                    <CardContent className="pt-4">
                      <div className="flex items-start gap-3">
                        <selectedType.icon className="h-5 w-5 text-blue-600 mt-0.5" />
                        <div>
                          <h4 className="font-medium text-blue-900">{selectedType.label}</h4>
                          <p className="text-sm text-blue-700 mt-1">{selectedType.description}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                <div className="space-y-2">
                  <Label>ファイルアップロード（任意）</Label>
                  <Input
                    type="file"
                    accept=".csv,.xlsx,.json"
                    onChange={handleFileChange}
                    className="file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  />
                  {uploadFile && (
                    <div className="flex items-center gap-2 text-sm text-green-600">
                      <FileText className="h-4 w-4" />
                      {uploadFile.name} ({Math.round(uploadFile.size / 1024)}KB)
                    </div>
                  )}
                  <p className="text-xs text-muted-foreground">
                    CSV, Excel, JSONファイルがサポートされています
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>メモ・備考（任意）</Label>
                  <Textarea
                    value={importNotes}
                    onChange={(e) => setImportNotes(e.target.value)}
                    placeholder="インポートに関するメモや注意事項があれば記入してください"
                    className="min-h-20"
                  />
                </div>

                <Button
                  onClick={handleImport}
                  disabled={!selectedImportType || importMutation.isPending}
                  className="w-full"
                  size="lg"
                >
                  <Upload className="h-4 w-4 mr-2" />
                  {importMutation.isPending ? 'インポート中...' : 'インポート開始'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="history" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <History className="h-5 w-5" />
                  インポート履歴
                </CardTitle>
                <CardDescription>
                  過去のデータインポート実行履歴を確認できます
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="text-center py-8 text-muted-foreground">
                    読み込み中...
                  </div>
                ) : importHistory.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>インポート履歴はありません</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {importHistory.map((item: ImportHistory) => {
                      const importType = IMPORT_TYPES.find(type => type.value === item.import_type);
                      const successRate = item.total_records > 0 
                        ? Math.round((item.successful_records / item.total_records) * 100) 
                        : 0;

                      return (
                        <Card key={item.id} className="hover:shadow-md transition-shadow">
                          <CardContent className="p-4">
                            <div className="space-y-3">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  {importType && <importType.icon className="h-5 w-5" />}
                                  <div>
                                    <h4 className="font-medium">
                                      {importType?.label || item.import_type}
                                    </h4>
                                    <p className="text-sm text-muted-foreground">
                                      {new Date(item.created_at).toLocaleDateString('ja-JP', {
                                        year: 'numeric',
                                        month: 'long',
                                        day: 'numeric',
                                        hour: '2-digit',
                                        minute: '2-digit'
                                      })}
                                    </p>
                                  </div>
                                </div>
                                {getStatusBadge(item.status)}
                              </div>

                              {item.status === 'processing' && (
                                <div className="space-y-2">
                                  <div className="flex justify-between text-sm">
                                    <span>処理中...</span>
                                    <span>{item.successful_records}/{item.total_records}</span>
                                  </div>
                                  <Progress value={successRate} className="h-2" />
                                </div>
                              )}

                              {(item.status === 'completed' || item.status === 'failed') && (
                                <div className="grid grid-cols-3 gap-4 text-sm">
                                  <div className="text-center">
                                    <div className="text-2xl font-bold text-blue-600">
                                      {item.total_records}
                                    </div>
                                    <div className="text-muted-foreground">総件数</div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-2xl font-bold text-green-600">
                                      {item.successful_records}
                                    </div>
                                    <div className="text-muted-foreground">成功</div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-2xl font-bold text-red-600">
                                      {item.failed_records}
                                    </div>
                                    <div className="text-muted-foreground">失敗</div>
                                  </div>
                                </div>
                              )}

                              {item.error_log && (
                                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                                  <h5 className="font-medium text-red-800 mb-2">エラーログ</h5>
                                  <pre className="text-xs text-red-700 whitespace-pre-wrap">
                                    {item.error_log}
                                  </pre>
                                </div>
                              )}

                              <div className="flex items-center justify-between text-xs text-muted-foreground border-t pt-2">
                                <span>実行者: {item.created_by_name || '不明'}</span>
                                {item.status === 'completed' && (
                                  <span className="text-green-600">
                                    成功率: {successRate}%
                                  </span>
                                )}
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
