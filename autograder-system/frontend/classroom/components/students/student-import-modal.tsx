'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
// import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Upload, Download, FileSpreadsheet, CheckCircle, AlertCircle, Calendar } from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '@/lib/api-client';

interface StudentImportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  classroomId?: number;
}

export function StudentImportModal({ open, onOpenChange, classroomId }: StudentImportModalProps) {
  const [step, setStep] = useState<'setup' | 'template' | 'upload' | 'preview' | 'importing' | 'complete'>('setup');
  const [file, setFile] = useState<File | null>(null);
  const [importProgress, setImportProgress] = useState(0);
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [year, setYear] = useState<string>('2025');
  const [period, setPeriod] = useState<string>('summer');
  const [importErrors, setImportErrors] = useState<string[]>([]);

  const years = [
    { value: '2025', label: '2025年度' },
    { value: '2026', label: '2026年度' },
    { value: '2027', label: '2027年度' },


  ];

  const periods = [
    { value: 'spring', label: '春期' },
    { value: 'summer', label: '夏期' },
    { value: 'winter', label: '冬期' },
  ];

  const handleDownloadTemplate = () => {
    const template = [
      ['塾ID', '塾名', '教室ID', '教室名', '生徒ID', '生徒名', '学年', '年度', '期間'],
      ['100001', 'サンプル学習塾', '001001', 'メイン教室', '123456', '田中太郎', '小6', year, period === 'spring' ? '春期' : period === 'summer' ? '夏期' : '冬期'],
      ['100001', 'サンプル学習塾', '001001', 'メイン教室', '123457', '佐藤花子', '小5', year, period === 'spring' ? '春期' : period === 'summer' ? '夏期' : '冬期'],
      ['100001', 'サンプル学習塾', '001001', 'メイン教室', '123458', '高橋次郎', '中1', year, period === 'spring' ? '春期' : period === 'summer' ? '夏期' : '冬期'],
    ];

    const csv = template.map(row => row.join(',')).join('\n');
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `student_import_template_${year}_${period}.csv`;
    link.click();

    toast.success('テンプレートをダウンロードしました');
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = event.target.files?.[0];
    if (uploadedFile) {
      setFile(uploadedFile);

      // Parse CSV file for preview
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          let csv = e.target?.result as string;

          // BOM除去
          if (csv.charCodeAt(0) === 0xFEFF) {
            csv = csv.slice(1);
          }

          const lines = csv.split('\n').filter(line => line.trim());
          if (lines.length === 0) {
            toast.error('CSVファイルが空です');
            return;
          }

          const headers = lines[0].split(',').map(h => h.trim());

          // Check if headers match expected format
          const expectedHeaders = ['塾ID', '塾名', '教室ID', '教室名', '生徒ID', '生徒名', '学年', '年度', '期間'];
          const isValidFormat = expectedHeaders.every(header => headers.includes(header));

          if (!isValidFormat) {
            toast.error(`CSVファイルの形式が正しくありません。\n期待される列: ${expectedHeaders.join(', ')}\n実際の列: ${headers.join(', ')}`);
            return;
          }

          const data = lines.slice(1).map((line, index) => {
            const values = line.split(',').map(v => v?.trim() || '');
            const row: any = {};
            headers.forEach((header, i) => {
              row[header] = values[i] || '';
            });

            // Skip empty rows
            if (!row['生徒ID'] || row['生徒ID'] === '') {
              return null;
            }

            // Basic validation
            const hasError = !row['塾ID'] || !row['生徒ID'] || !row['生徒名'] || !row['学年'];

            return {
              schoolId: row['塾ID'],
              schoolName: row['塾名'],
              classroomId: row['教室ID'],
              classroomName: row['教室名'],
              studentId: row['生徒ID'],
              name: row['生徒名'],
              grade: row['学年'],
              year: row['年度'],
              period: row['期間'],
              status: hasError ? 'error' : 'valid',
              rowIndex: index + 2
            };
          }).filter(row => row !== null); // Remove null rows

          setPreviewData(data);
          setStep('preview');
        } catch (error) {
          console.error('CSV parsing error:', error);
          toast.error('CSVファイルの読み込みに失敗しました');
        }
      };
      reader.readAsText(uploadedFile, 'UTF-8');
    }
  };

  const handleImport = async () => {
    if (!file) {
      toast.error('ファイルを選択してください');
      return;
    }

    setStep('importing');
    setImportProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Progress simulation
      const progressInterval = setInterval(() => {
        setImportProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await apiClient.post('/students/import_excel/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 80) / progressEvent.total);
            setImportProgress(percentCompleted);
          }
        },
      });

      clearInterval(progressInterval);
      setImportProgress(100);

      const result = response.data;

      setStep('complete');

      // エラーがある場合は保存
      if (result.errors && result.errors.length > 0) {
        setImportErrors(result.errors);
        toast.warning(`一部エラーが発生しました: ${result.error_count}件`);
        console.warn('Import errors:', result.errors);

        // Show detailed errors in console for debugging
        result.errors.forEach((error: string, index: number) => {
          console.log(`Error ${index + 1}:`, error);
        });
      } else {
        setImportErrors([]);
      }

      toast.success(`インポート完了: 生徒${result.created_students}名、受講履歴${result.created_enrollments}件を作成しました`);
    } catch (error: any) {
      console.error('Import error:', error);

      // Axios error handling
      let errorMessage = 'インポート処理中にエラーが発生しました';

      if (error.response) {
        // Server responded with an error status
        const { status, data } = error.response;
        if (data?.error) {
          errorMessage = data.error;
        } else if (status === 500) {
          errorMessage = 'サーバーエラーが発生しました';
        } else if (status === 400) {
          errorMessage = 'リクエストが無効です';
        }
      } else if (error.request) {
        // Network error
        errorMessage = 'ネットワークエラーが発生しました';
      }

      toast.error(errorMessage);
      setStep('preview');
    }
  };

  const handleClose = () => {
    setStep('setup');
    setFile(null);
    setPreviewData([]);
    setImportProgress(0);
    setYear('2025');
    setPeriod('summer');
    setImportErrors([]);
    onOpenChange(false);

    // インポートが完了した場合はページをリロード
    if (step === 'complete') {
      window.location.reload();
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>生徒データインポート</DialogTitle>
          <DialogDescription>
            CSVファイルから生徒データを一括インポートします
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {step === 'setup' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  年度・期間選択
                </CardTitle>
                <CardDescription>
                  インポートする生徒データの年度と期間を選択してください
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="year">年度</Label>
                      <Select value={year} onValueChange={setYear}>
                        <SelectTrigger>
                          <SelectValue placeholder="年度を選択" />
                        </SelectTrigger>
                        <SelectContent>
                          {years.map((yearOption) => (
                            <SelectItem key={yearOption.value} value={yearOption.value}>
                              {yearOption.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="period">期間</Label>
                      <Select value={period} onValueChange={setPeriod}>
                        <SelectTrigger>
                          <SelectValue placeholder="期間を選択" />
                        </SelectTrigger>
                        <SelectContent>
                          {periods.map((periodOption) => (
                            <SelectItem key={periodOption.value} value={periodOption.value}>
                              {periodOption.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <Button
                    onClick={() => setStep('template')}
                    className="w-full"
                  >
                    次へ
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {step === 'template' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileSpreadsheet className="h-5 w-5" />
                  テンプレートダウンロード
                </CardTitle>
                <CardDescription>
                  まずはテンプレートファイルをダウンロードして、生徒データを入力してください
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Button
                    onClick={handleDownloadTemplate}
                    className="w-full"
                    variant="outline"
                  >
                    テンプレートをダウンロード
                  </Button>
                  <div className="text-sm text-muted-foreground">
                    <p>テンプレートの列構成：</p>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>塾ID（6桁の数字）</li>
                      <li>塾名</li>
                      <li>教室ID（6桁の数字）</li>
                      <li>教室名</li>
                      <li>生徒ID（6桁の数字）</li>
                      <li>生徒名</li>
                      <li>学年（小1〜小6、中1〜中3形式）</li>
                      <li>年度（{year}年度）</li>
                      <li>期間（{periods.find(p => p.value === period)?.label}）</li>
                    </ul>
                  </div>
                  <Button
                    onClick={() => setStep('upload')}
                    className="w-full"
                  >
                    次へ：ファイルアップロード
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {step === 'upload' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  ファイルアップロード
                </CardTitle>
                <CardDescription>
                  記入済みのCSVファイルをアップロードしてください
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                    <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                    <p className="text-sm text-gray-600 mb-2">
                      CSVファイルをドラッグ&ドロップするか、クリックしてファイルを選択
                    </p>
                    <input
                      type="file"
                      accept=".csv"
                      onChange={handleFileUpload}
                      className="hidden"
                      id="file-upload"
                    />
                    <label
                      htmlFor="file-upload"
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary hover:bg-primary/90 cursor-pointer"
                    >
                      ファイルを選択
                    </label>
                  </div>
                  <Button
                    onClick={() => setStep('template')}
                    variant="outline"
                    className="w-full"
                  >
                    戻る
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {step === 'preview' && (
            <Card>
              <CardHeader>
                <CardTitle>インポート内容確認</CardTitle>
                <CardDescription>
                  {previewData.length}件のデータが見つかりました
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="max-h-64 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2">塾ID</th>
                          <th className="text-left p-2">教室ID</th>
                          <th className="text-left p-2">生徒ID</th>
                          <th className="text-left p-2">生徒名</th>
                          <th className="text-left p-2">学年</th>
                          <th className="text-left p-2">年度・期間</th>
                          <th className="text-left p-2">状態</th>
                        </tr>
                      </thead>
                      <tbody>
                        {previewData.map((row, index) => (
                          <tr key={index} className="border-b">
                            <td className="p-2">{row.schoolId}</td>
                            <td className="p-2">{row.classroomId}</td>
                            <td className="p-2">{row.studentId}</td>
                            <td className="p-2">{row.name}</td>
                            <td className="p-2">{row.grade}</td>
                            <td className="p-2">
                              <Badge variant="outline" className="text-xs">
                                {row.year}年度 {row.period}
                              </Badge>
                            </td>
                            <td className="p-2">
                              {row.status === 'valid' ? (
                                <Badge className="bg-green-100 text-green-800">
                                  <CheckCircle className="h-3 w-3 mr-1" />
                                  正常
                                </Badge>
                              ) : (
                                <Badge className="bg-red-100 text-red-800">
                                  <AlertCircle className="h-3 w-3 mr-1" />
                                  エラー
                                </Badge>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => setStep('upload')}
                      variant="outline"
                      className="flex-1"
                    >
                      戻る
                    </Button>
                    <Button
                      onClick={handleImport}
                      className="flex-1"
                      disabled={previewData.some(row => row.status === 'error')}
                    >
                      インポート実行
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {step === 'importing' && (
            <Card>
              <CardHeader>
                <CardTitle>インポート中...</CardTitle>
                <CardDescription>
                  データをインポートしています。しばらくお待ちください。
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="w-full h-2 bg-gray-200 rounded-full">
                    <div
                      className="h-full bg-primary rounded-full transition-all duration-300"
                      style={{ width: `${importProgress}%` }}
                    />
                  </div>
                  <p className="text-sm text-center text-muted-foreground">
                    {importProgress}% 完了
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {step === 'complete' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-600">
                  <CheckCircle className="h-5 w-5" />
                  インポート完了
                </CardTitle>
                <CardDescription>
                  生徒データのインポートが完了しました
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="bg-green-50 p-4 rounded-lg">
                    <p className="text-sm">
                      {previewData.filter(row => row.status === 'valid').length}件のデータが正常にインポートされました
                    </p>
                  </div>

                  {importErrors.length > 0 && (
                    <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                      <h4 className="font-medium text-yellow-800 mb-2 flex items-center gap-2">
                        <AlertCircle className="h-4 w-4" />
                        インポートエラー詳細 ({importErrors.length}件)
                      </h4>
                      <div className="max-h-40 overflow-y-auto space-y-1">
                        {importErrors.slice(0, 20).map((error, index) => (
                          <div key={index} className="text-sm text-yellow-700 bg-white px-2 py-1 rounded border">
                            {error}
                          </div>
                        ))}
                        {importErrors.length > 20 && (
                          <div className="text-sm text-yellow-700 font-medium">
                            ... 他 {importErrors.length - 20} 件のエラー
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <Button
                    onClick={handleClose}
                    className="w-full"
                  >
                    完了
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}