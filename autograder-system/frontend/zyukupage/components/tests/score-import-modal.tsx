'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Upload, Download, FileSpreadsheet, CheckCircle, AlertCircle, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import { testApi } from '@/lib/api-client';

interface ScoreImportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  testId?: number;
}

interface ValidationResult {
  valid: boolean;
  warnings: string[];
  errors: string[];
}

export function ScoreImportModal({ open, onOpenChange, testId }: ScoreImportModalProps) {
  const [step, setStep] = useState<'setup' | 'template' | 'upload' | 'preview' | 'importing' | 'complete'>('setup');
  const [file, setFile] = useState<File | null>(null);
  const [importProgress, setImportProgress] = useState(0);
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [validationResults, setValidationResults] = useState<ValidationResult[]>([]);
  const [year, setYear] = useState<string>('2025');
  const [period, setPeriod] = useState<string>('summer');
  const [isDragOver, setIsDragOver] = useState(false);
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


  // 全学年統合テンプレートダウンロード
  const handleDownloadAllGradesTemplate = async () => {
    try {
      console.log('Starting template download...', { year: parseInt(year), period });
      const response = await testApi.generateAllGradesTemplate({
        year: parseInt(year),
        period: period
      });

      console.log('Template download response:', response);
      console.log('Response type:', typeof response);
      console.log('Response.success:', response?.success);
      console.log('Response.success === true:', response?.success === true);
      console.log('Response.success === false:', response?.success === false);

      if (response && response.success === true) {
        console.log('Showing success toast');
        toast.success('全学年対応テンプレートファイルをダウンロードしました');
      } else if (response && response.success === false) {
        console.error('Template generation failed:', response);
        toast.error(`テンプレート生成に失敗しました: ${response.message || response.error || '不明なエラー'}`);
      } else {
        console.warn('Unexpected response format:', response);
        toast.warning('テンプレートのダウンロード状態が不明です');
      }
    } catch (error: any) {
      console.error('Template download error:', error);
      toast.error(`全学年対応テンプレートのダウンロードに失敗しました: ${error.message || ''}`);
    }
  };


  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      processFile(selectedFile);
    }
  };

  const processFile = (selectedFile: File) => {
    if (!selectedFile.name.toLowerCase().endsWith('.csv')) {
      toast.error('CSVファイルを選択してください');
      return;
    }
    setFile(selectedFile);
    // CSVファイルの解析とプレビュー
    parseCSVFile(selectedFile);
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      processFile(files[0]);
    }
  };

  const parseCSVFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        let csv = e.target?.result as string;
        // BOM文字を除去
        if (csv.charCodeAt(0) === 0xFEFF) {
          csv = csv.slice(1);
        }
        const lines = csv.split('\n');
        const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
        
        // 新しい形式のヘッダーをチェック
        const expectedHeaders = ['塾ID', '塾名', '教室ID', '教室名', '生徒ID', '生徒名', '学年', '年度', '期間', '出席'];
        const hasNewFormat = expectedHeaders.every(header => headers.includes(header));
        
        if (!hasNewFormat) {
          toast.error('CSVファイルの形式が正しくありません。新しいテンプレートを使用してください。');
          return;
        }
        
        const data = lines.slice(1).filter(line => line.trim()).map((line, index) => {
          const values = line.split(',').map(v => v.trim().replace(/^"|"$/g, ''));
          const row: any = {};
          
          // ヘッダーに基づいてデータをマッピング
          headers.forEach((header, i) => {
            row[header] = values[i] || '';
          });
          
          // 教科別大問の得点を抽出
          const questionScores: number[] = [];
          let totalScore = 0;
          
          // 新しい形式: 「全体合計点」列がある場合はそれを使用
          if (headers.includes('全体合計点') && values[headers.indexOf('全体合計点')]) {
            const totalScoreValue = parseInt(values[headers.indexOf('全体合計点')]);
            if (!isNaN(totalScoreValue)) {
              totalScore = totalScoreValue;
            }
          } else {
            // 教科別合計点を集計（国語_合計点、算数_合計点など）
            headers.forEach((header, i) => {
              if (header.includes('_合計点') && values[i]) {
                const score = parseInt(values[i]);
                if (!isNaN(score)) {
                  totalScore += score;
                }
              }
            });
          }
          
          // デバッグ用ログ（最初の5件のみ）
          if (index < 5) {
            console.log(`学生 ${index + 1}: ${row['生徒名']}, 合計点: ${totalScore}, 全体合計点列の値: ${values[headers.indexOf('全体合計点')] || 'なし'}`);
            console.log(`大問別点数:`, questionScores);
            console.log(`国語_合計点: ${values[headers.indexOf('国語_合計点')] || 'なし'}, 算数_合計点: ${values[headers.indexOf('算数_合計点')] || 'なし'}`);
          }
          
          // 大問別点数も抽出（表示用）
          headers.forEach((header, i) => {
            if ((header.includes('_大問') || header.startsWith('大問')) && values[i]) {
              const score = parseInt(values[i]);
              if (!isNaN(score)) {
                questionScores.push(score);
              } else {
                questionScores.push(0);
              }
            }
          });
          
          return {
            rowIndex: index + 1,
            schoolId: row['塾ID'],
            schoolName: row['塾名'],
            classroomId: row['教室ID'],
            classroomName: row['教室名'],
            studentId: row['生徒ID'],
            studentName: row['生徒名'],
            grade: row['学年'],
            year: row['年度'],
            period: row['期間'],
            attendance: row['出席'] === '出席' || row['出席'] === '○' || row['出席'] === '1',
            scores: questionScores,
            totalScore: totalScore
          };
        });
        
        setPreviewData(data);
        validateData(data);
        setStep('preview');
      } catch (error) {
        console.error('CSV parse error:', error);
        toast.error('CSVファイルの解析に失敗しました');
      }
    };
    reader.readAsText(file, 'utf-8');
  };

  const validateData = (data: any[]) => {
    const results: ValidationResult[] = data.map(row => {
      const warnings: string[] = [];
      const errors: string[] = [];
      
      // 学年に基づいて期待される満点を計算
      const grade = row.grade;
      let expectedMaxScore = 100; // デフォルト（1教科）
      
      if (grade) {
        // 小学生（小1-小6）は国語・算数で200点満点
        if (grade.startsWith('小')) {
          expectedMaxScore = 200;
        }
        // 中学生（中1-中3）は英語・数学で200点満点  
        else if (grade.startsWith('中')) {
          expectedMaxScore = 200;
        }
      }
      
      // パターン1: 合計点が期待される満点を大幅に超える場合（1.5倍を閾値とする）
      const threshold = expectedMaxScore * 1.5;
      if (row.totalScore > threshold) {
        warnings.push(`合計点が想定満点（${expectedMaxScore}点）を大幅に超えています: ${row.totalScore}点`);
      }
      
      // パターン2: 出席しているのに得点が未入力の場合
      if (row.attendance && row.scores.some((score: number | null) => score === null)) {
        warnings.push('出席しているのに得点が未入力の項目があります');
      }
      
      return {
        valid: errors.length === 0,
        warnings,
        errors
      };
    });
    
    setValidationResults(results);
  };

  const handleImport = async () => {
    setStep('importing');
    setImportProgress(0);
    
    try {
      if (!file) {
        toast.error('ファイルが選択されていません');
        return;
      }

      // FormDataを作成してファイルをアップロード
      const formData = new FormData();
      formData.append('file', file);
      formData.append('year', year);
      formData.append('period', period);
      
      // 統合テンプレート形式では教科指定不要
      // バックエンドで自動的に統合形式として判定される

      // プログレスバーのシミュレーション
      setImportProgress(20);
      await new Promise(resolve => setTimeout(resolve, 500));

      // バックエンドのimport_scores_from_excelを使用
      const response = await testApi.importScoresFromFile(formData);

      setImportProgress(80);
      await new Promise(resolve => setTimeout(resolve, 500));

      if (response.success) {
        setImportProgress(100);
        
        // 検証エラーと未入力データの表示
        const validationErrorCount = response.validation_errors?.length || 0;
        const missingDataCount = response.missing_data?.length || 0;
        const warningCount = response.warnings?.length || 0;
        
        // 基本メッセージ
        let message = `処理完了: 成功 ${response.success_count}件`;
        if (response.error_count > 0) {
          message += `, エラー ${response.error_count}件`;
        }
        
        if (validationErrorCount === 0 && missingDataCount === 0 && warningCount === 0) {
          toast.success(message);
        } else {
          toast.warning(message + `\n検証問題: ${validationErrorCount + missingDataCount + warningCount}件`);
        }
        
        // 満点超過エラーの表示
        if (response.validation_errors && response.validation_errors.length > 0) {
          console.error('満点超過エラー:', response.validation_errors);
          setImportErrors([
            ...(importErrors || []),
            `⚠️ 満点超過エラー (${response.validation_errors.length}件):`,
            ...response.validation_errors.map((error: any) => 
              `${error.message || `${error.student_name}(${error.student_id}) ${error.subject}${error.question}: ${error.score}点 > 満点${error.max_score}点`}}`
            )
          ]);
          
          // 最初の3件を即座に表示
          response.validation_errors.slice(0, 3).forEach((error: any, index: number) => {
            setTimeout(() => {
              toast.error(`満点超過: ${error.student_name} ${error.subject}${error.question} (${error.score}点 > ${error.max_score}点)`, { 
                duration: 8000 
              });
            }, (index + 1) * 2000);
          });
        }
        
        // 未入力データの表示
        if (response.missing_data && response.missing_data.length > 0) {
          console.warn('未入力データ:', response.missing_data);
          setImportErrors([
            ...(importErrors || []),
            `📝 未入力データ (${response.missing_data.length}件):`,
            ...response.missing_data.map((missing: any) => 
              missing.message || `${missing.student_name}(${missing.student_id}) ${missing.subject}${missing.question}が未入力`
            )
          ]);
          
          // 最初の3件を即座に表示
          response.missing_data.slice(0, 3).forEach((missing: any, index: number) => {
            setTimeout(() => {
              toast.warning(`未入力: ${missing.student_name} ${missing.subject}${missing.question}`, { 
                duration: 6000 
              });
            }, (index + 1) * 1500);
          });
        }
        
        // 成功でも警告やエラーがある場合は表示
        if (response.warnings && response.warnings.length > 0) {
          console.warn('Import warnings:', response.warnings);
          setImportErrors([
            ...(importErrors || []),
            `⚠️ 警告 (${response.warnings.length}件):`,
            ...response.warnings
          ]);
          
          // 最初の5件の警告を個別に表示
          response.warnings.slice(0, 5).forEach((error: string, index: number) => {
            setTimeout(() => {
              toast.warning(`⚠️ ${error}`, { duration: 6000 });
            }, (index + 2) * 1000);
          });
          
          if (response.errors.length > 5) {
            setTimeout(() => {
              toast.warning(`その他 ${response.errors.length - 5} 件の警告があります。完了画面で全てご確認いただけます。`, { 
                duration: 8000 
              });
            }, 8000);
          }
        }
        setStep('complete');
      } else {
        toast.error(`インポートに失敗しました: ${response.error}`);
        
        // エラー詳細があれば表示
        if (response.errors && response.errors.length > 0) {
          console.error('インポートエラー詳細:', response.errors);
          setImportErrors(response.errors); // エラー詳細を保存
          
          // 各エラーを個別にトーストで表示
          response.errors.slice(0, 5).forEach((error: string, index: number) => {
            setTimeout(() => {
              toast.error(`${error}`, { duration: 8000 });
            }, index * 1000);
          });
          if (response.errors.length > 5) {
            setTimeout(() => {
              toast.error(`その他 ${response.errors.length - 5} 件のエラーがあります。詳細はプレビュー画面でご確認ください。`, { duration: 8000 });
            }, 5000);
          }
        }
        
        setStep('preview');
      }
    } catch (error: any) {
      toast.error('インポートに失敗しました');
      console.error('Import error:', error);
      
      // axios エラーの詳細を表示
      if (error.response) {
        console.error('Error response data:', error.response.data);
        console.error('Error status:', error.response.status);
        
        // バックエンドからのエラーメッセージを表示
        if (error.response.data?.error) {
          toast.error(`詳細: ${error.response.data.error}`);
        }
        
        // エラーリストがあれば表示
        if (error.response.data?.errors) {
          console.error('Detailed errors:', error.response.data.errors);
          // 各エラーを個別にトーストで表示
          error.response.data.errors.slice(0, 3).forEach((errorMsg: string, index: number) => {
            setTimeout(() => {
              toast.error(`${errorMsg}`, { duration: 8000 });
            }, index * 1000);
          });
          if (error.response.data.errors.length > 3) {
            setTimeout(() => {
              toast.error(`その他 ${error.response.data.errors.length - 3} 件のエラーがあります`, { duration: 8000 });
            }, 3000);
          }
        }
      }
      
      setStep('preview');
    }
  };

  const resetModal = () => {
    setStep('setup');
    setFile(null);
    setPreviewData([]);
    setValidationResults([]);
    setImportProgress(0);
    setImportErrors([]);
  };

  const handleClose = () => {
    resetModal();
    onOpenChange(false);
  };

  const getStepTitle = () => {
    switch (step) {
      case 'setup': return '設定';
      case 'template': return 'テンプレート';
      case 'upload': return 'アップロード';
      case 'preview': return 'プレビュー';
      case 'importing': return 'インポート中';
      case 'complete': return '完了';
      default: return '';
    }
  };

  const warningCount = validationResults.filter(result => result.warnings.length > 0).length;
  const errorCount = validationResults.filter(result => result.errors.length > 0).length;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[800px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>得点データインポート - {getStepTitle()}</DialogTitle>
          <DialogDescription>
            Excelファイルから教科・出席・点数情報をインポートします
          </DialogDescription>
        </DialogHeader>

        {step === 'setup' && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileSpreadsheet className="h-5 w-5" />
                  インポート設定
                </CardTitle>
                <CardDescription>
                  年度・期間を選択してください
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <p className="text-sm font-medium">年度</p>
                    <Select value={year} onValueChange={setYear}>
                      <SelectTrigger>
                        <SelectValue placeholder="年度を選択" />
                      </SelectTrigger>
                      <SelectContent>
                        {years.map(yearOption => (
                          <SelectItem key={yearOption.value} value={yearOption.value}>
                            {yearOption.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <p className="text-sm font-medium">期間</p>
                    <Select value={period} onValueChange={setPeriod}>
                      <SelectTrigger>
                        <SelectValue placeholder="期間を選択" />
                      </SelectTrigger>
                      <SelectContent>
                        {periods.map(periodOption => (
                          <SelectItem key={periodOption.value} value={periodOption.value}>
                            {periodOption.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* テンプレートダウンロードとインポート */}
                <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-medium text-blue-900 mb-2">📊 得点データテンプレート</h4>
                  <p className="text-sm text-blue-700 mb-3">
                    全学年・全教科（国語・算数・英語・数学）の得点データを管理できます。<br/>
                    生徒一括エクスポートのテンプレートをそのまま使用できます。
                  </p>
                  <div className="flex gap-2">
                    <Button onClick={handleDownloadAllGradesTemplate} variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      テンプレートダウンロード
                    </Button>
                    <Button onClick={() => setStep('upload')} size="sm">
                      <FileSpreadsheet className="h-4 w-4 mr-2" />
                      インポート
                    </Button>
                  </div>
                </div>

              </CardContent>
            </Card>
          </div>
        )}

        {step === 'upload' && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>ファイルアップロード</CardTitle>
                <CardDescription>
                  記入済みのCSVファイルをアップロードしてください
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* アップロード形式の説明 */}
                <div className="mb-4 p-3 bg-gray-50 rounded-md">
                  <p className="text-sm text-gray-700">
                    <strong>対応形式:</strong> ダウンロードしたテンプレートファイルに得点を入力してインポートしてください。
                  </p>
                </div>

                <div 
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    isDragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-300'
                  }`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <Upload className={`h-12 w-12 mx-auto mb-4 ${isDragOver ? 'text-blue-500' : 'text-gray-400'}`} />
                  <p className="text-lg font-medium mb-2">CSVファイルを選択</p>
                  <p className="text-sm text-gray-500 mb-4">
                    または、ファイルをドラッグ＆ドロップしてください
                  </p>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="csv-upload"
                  />
                  <label htmlFor="csv-upload" className="inline-block">
                    <div className="px-4 py-2 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50 transition-colors">
                      ファイルを選択
                    </div>
                  </label>
                </div>
                {file && (
                  <div className="mt-4 p-3 bg-blue-50 rounded-md">
                    <p className="text-sm font-medium">選択されたファイル: {file.name}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {step === 'preview' && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileSpreadsheet className="h-5 w-5" />
                  データプレビュー
                  {warningCount > 0 && (
                    <Badge variant="outline" className="bg-yellow-50 text-yellow-600 border-yellow-200">
                      <AlertTriangle className="h-3 w-3 mr-1" />
                      警告: {warningCount}件
                    </Badge>
                  )}
                  {errorCount > 0 && (
                    <Badge variant="destructive">
                      <AlertCircle className="h-3 w-3 mr-1" />
                      エラー: {errorCount}件
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription>
                  {previewData.length}件のデータが見つかりました
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {previewData.map((row, index) => (
                    <div key={index} className="border rounded-lg p-3">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-medium">{row.studentName} (ID: {row.studentId})</p>
                          <p className="text-sm text-gray-500">
                            {row.grade} | {row.classroomName} | {row.attendance ? '出席' : '欠席'} | 合計: {row.totalScore}点
                          </p>
                        </div>
                        <div className="flex gap-1">
                          {validationResults[index]?.warnings.map((warning, wIndex) => (
                            <Badge key={wIndex} variant="outline" className="bg-yellow-50 text-yellow-600 text-xs">
                              <AlertTriangle className="h-3 w-3 mr-1" />
                              警告
                            </Badge>
                          ))}
                          {validationResults[index]?.errors.map((error, eIndex) => (
                            <Badge key={eIndex} variant="destructive" className="text-xs">
                              <AlertCircle className="h-3 w-3 mr-1" />
                              エラー
                            </Badge>
                          ))}
                        </div>
                      </div>
                      {(validationResults[index]?.warnings.length > 0 || validationResults[index]?.errors.length > 0) && (
                        <div className="mt-2 space-y-1">
                          {validationResults[index]?.warnings.map((warning, wIndex) => (
                            <p key={wIndex} className="text-xs text-yellow-600">⚠️ {warning}</p>
                          ))}
                          {validationResults[index]?.errors.map((error, eIndex) => (
                            <p key={eIndex} className="text-xs text-red-600">❌ {error}</p>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                
                {/* インポートエラー詳細表示（失敗時） */}
                {importErrors.length > 0 && (
                  <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                    <h4 className="font-medium text-red-800 mb-2">❌ エラー詳細 ({importErrors.length}件)</h4>
                    <div className="max-h-32 overflow-y-auto space-y-1">
                      {importErrors.slice(0, 20).map((error, index) => (
                        <p key={index} className="text-xs text-red-700">
                          • {error}
                        </p>
                      ))}
                      {importErrors.length > 20 && (
                        <p className="text-xs text-red-600 font-medium mt-2">
                          その他 {importErrors.length - 20} 件のエラーがあります
                        </p>
                      )}
                    </div>
                    <div className="mt-2 text-xs text-red-600">
                      <strong>対処方法:</strong> CSVファイルの該当行を修正してから再度インポートしてください。
                    </div>
                  </div>
                )}
                
                <div className="flex justify-end space-x-2 mt-4">
                  <Button variant="outline" onClick={() => setStep('upload')}>
                    戻る
                  </Button>
                  <Button onClick={handleImport} disabled={errorCount > 0}>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    インポート実行
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {step === 'importing' && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>インポート中...</CardTitle>
                <CardDescription>
                  データをインポートしています。しばらくお待ちください。
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-primary h-2 rounded-full transition-all duration-300"
                      style={{ width: `${importProgress}%` }}
                    />
                  </div>
                  <p className="text-center text-sm text-gray-500">
                    {importProgress}% 完了
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {step === 'complete' && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  インポート完了
                </CardTitle>
                <CardDescription>
                  得点データのインポートが正常に完了しました
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-green-50 rounded-md">
                    <p className="text-sm font-medium text-green-800">
                      {previewData.length}件のデータが正常にインポートされました
                    </p>
                    {importErrors.length > 0 && (
                      <p className="text-sm text-yellow-600 mt-2">
                        ⚠️ {importErrors.length}件の警告がありました。下記で詳細をご確認ください。
                      </p>
                    )}
                  </div>
                  
                  {/* 警告詳細表示 */}
                  {importErrors.length > 0 && (
                    <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                      <h4 className="font-medium text-yellow-800 mb-2">⚠️ 警告詳細 ({importErrors.length}件)</h4>
                      <div className="max-h-40 overflow-y-auto space-y-1">
                        {importErrors.slice(0, 50).map((error, index) => (
                          <p key={index} className="text-xs text-yellow-700">
                            • {error}
                          </p>
                        ))}
                        {importErrors.length > 50 && (
                          <p className="text-xs text-yellow-600 font-medium mt-2">
                            その他 {importErrors.length - 50} 件の警告があります
                          </p>
                        )}
                      </div>
                      <div className="mt-2 text-xs text-yellow-600">
                        <strong>注意:</strong> 得点が範囲外の場合、データは保存されていません。正しい値に修正して再度インポートしてください。
                      </div>
                    </div>
                  )}
                  <div className="flex justify-end">
                    <Button onClick={handleClose}>
                      閉じる
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}