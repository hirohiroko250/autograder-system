'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Upload, Download, FileText, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

interface ExcelImportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onImport: (data: any) => void;
  students: any[];
  selectedSubject: string;
  selectedGrade: string;
  questionCount?: number; // 大問数（デフォルト6問）
}

export function ExcelImportModal({ 
  open, 
  onOpenChange, 
  onImport, 
  students, 
  selectedSubject, 
  selectedGrade,
  questionCount = 6
}: ExcelImportModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        toast.error('Excelファイル(.xlsx, .xls)のみ対応しています');
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleDownloadTemplate = () => {
    // テンプレートダウンロードの処理
    const csvContent = generateTemplate();
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `score_template_${selectedSubject}_${selectedGrade}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('テンプレートをダウンロードしました');
  };

  const generateTemplate = () => {
    const questionHeaders = Array.from({ length: questionCount }, (_, i) => `大問${i + 1}`);
    const headers = ['生徒ID', '生徒名', ...questionHeaders];
    
    const rows = students.map(student => {
      const emptyScores = Array.from({ length: questionCount }, () => '');
      return [
        student.id,
        student.name,
        ...emptyScores
      ];
    });
    
    return [headers, ...rows]
      .map(row => row.join(','))
      .join('\n');
  };

  const handleImport = async () => {
    if (!selectedFile) {
      toast.error('ファイルを選択してください');
      return;
    }

    setIsProcessing(true);
    
    try {
      // Mock処理 - 実際にはファイルを読み込んでパースする
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // サンプルデータを動的に生成
      const mockData: { [key: string]: { [key: string]: string } } = {};
      students.slice(0, 3).forEach((student, index) => {
        const studentScores: { [key: string]: string } = {};
        for (let i = 1; i <= questionCount; i++) {
          // ランダムな点数を生成（15-20点）
          studentScores[`q${i}`] = (15 + Math.floor(Math.random() * 6)).toString();
        }
        mockData[student.id] = studentScores;
      });
      
      onImport(mockData);
      toast.success(`${Object.keys(mockData).length}名分の点数をインポートしました`);
      onOpenChange(false);
      setSelectedFile(null);
    } catch (error) {
      toast.error('インポートに失敗しました');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Excel一括インポート
          </DialogTitle>
          <DialogDescription>
            Excelファイルから点数データを一括で取り込みます
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              対象: {selectedGrade} {selectedSubject} ({students.length}名)
            </AlertDescription>
          </Alert>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label>1. テンプレートをダウンロード</Label>
              <Button
                variant="outline"
                onClick={handleDownloadTemplate}
                className="w-full rounded-xl"
              >
                <Download className="h-4 w-4 mr-2" />
                テンプレートダウンロード (CSV)
              </Button>
              <p className="text-xs text-muted-foreground">
                生徒一覧が入ったテンプレートをダウンロードして、点数を入力してください
              </p>
            </div>

            <div className="space-y-2">
              <Label>2. 点数入力済みファイルを選択</Label>
              <Input
                type="file"
                accept=".xlsx,.xls,.csv"
                onChange={handleFileSelect}
                className="rounded-xl"
              />
              {selectedFile && (
                <p className="text-sm text-green-600">
                  選択されたファイル: {selectedFile.name}
                </p>
              )}
            </div>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium mb-2">ファイル形式について</h4>
            <ul className="text-xs text-gray-600 space-y-1">
              <li>• Excel (.xlsx, .xls) またはCSV (.csv) ファイルに対応</li>
              <li>• 各列: 生徒ID, 生徒名, 大問1〜{questionCount}の点数</li>
              <li>• 点数は0〜20の数値で入力してください</li>
              <li>• 空欄の場合は0点として処理されます</li>
            </ul>
          </div>

          <div className="flex gap-2 pt-4">
            <Button
              onClick={handleImport}
              disabled={!selectedFile || isProcessing}
              className="flex-1 rounded-xl"
            >
              <Upload className="h-4 w-4 mr-2" />
              {isProcessing ? 'インポート中...' : 'インポート実行'}
            </Button>
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="rounded-xl"
            >
              キャンセル
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}