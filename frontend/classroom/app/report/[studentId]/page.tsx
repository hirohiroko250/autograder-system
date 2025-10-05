'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { StudentReport, ReportData } from '@/components/report/student-report';
import { Button } from '@/components/ui/button';
import { Printer } from 'lucide-react';

export default function ReportPage() {
  const params = useParams();
  const studentId = params.studentId as string;

  // TODO: API から生徒の成績データを取得
  const { data: reportData, isLoading } = useQuery<ReportData>({
    queryKey: ['student-report', studentId],
    queryFn: async () => {
      // ダミーデータ（実際はAPIから取得）
      await new Promise(resolve => setTimeout(resolve, 100)); // 小さな遅延
      return {
        issueDate: '2025年00月00日',
        year: 2025,
        period: 'summer',
        periodNumber: 3,
        grade: '小6',
        schoolId: 'S001',
        schoolName: '〇〇塾',
        studentId: studentId,
        examId: 'E001',
        studentGrade: '小6',
        studentName: '山田太郎',
        math: {
          score: 89,
          deviation: 60.0,
          nationalRank: 178,
          nationalTotal: 1000,
          schoolRank: 31,
          schoolTotal: 100,
          maxScoreNational: 100,
          maxScoreSchool: 100,
          minScoreNational: 7,
          minScoreSchool: 7,
          averageNational: 68.8,
          averageSchool: 68.8,
        },
        japanese: {
          score: 89,
          deviation: 60.0,
          nationalRank: 178,
          nationalTotal: 1000,
          schoolRank: 31,
          schoolTotal: 100,
          maxScoreNational: 100,
          maxScoreSchool: 100,
          minScoreNational: 7,
          minScoreSchool: 7,
          averageNational: 68.8,
          averageSchool: 68.8,
        },
        total: {
          score: 89,
          deviation: 60.0,
          nationalRank: 178,
          nationalTotal: 1000,
          schoolRank: 31,
          schoolTotal: 100,
          maxScoreNational: 100,
          maxScoreSchool: 100,
          minScoreNational: 7,
          minScoreSchool: 7,
          averageNational: 68.8,
          averageSchool: 68.8,
        },
        mathItems: [
          { number: 1, name: '計算', score: 14, maxScore: 14, average: 10.2, correctRate: 100 },
          { number: 2, name: '比', score: 24, maxScore: 28, average: 18.8, correctRate: 86 },
          { number: 3, name: '拡大と縮小', score: 12, maxScore: 12, average: 7.3, correctRate: 100 },
          { number: 4, name: '比例と反比例', score: 16, maxScore: 20, average: 16.0, correctRate: 80 },
          { number: 5, name: '資料の調べ方', score: 14, maxScore: 14, average: 8.9, correctRate: 100 },
          { number: 6, name: 'いろいろな問題', score: 9, maxScore: 12, average: 7.5, correctRate: 75 },
        ],
        japaneseItems: [
          { number: 1, name: '漢字の読み取り', score: 14, maxScore: 14, average: 10.2, correctRate: 100 },
          { number: 2, name: '漢字の書き取り', score: 24, maxScore: 28, average: 18.8, correctRate: 86 },
          { number: 3, name: '読み取り①', score: 12, maxScore: 12, average: 7.3, correctRate: 100 },
          { number: 4, name: '読み取り②', score: 16, maxScore: 20, average: 16.0, correctRate: 80 },
        ],
        mathComment: '今回のテストでは、基礎力をしっかり身につけている生徒が多く見られました。特に算数では、文章題への理解力が向上している様子がうかがえます。一方で、国語の記述問題では、もう一歩深く考える力が求められます。日々の学習を積み重ねて、次回のテストでも力を発揮できるようにしましょう！',
        japaneseComment: '今回のテストでは、基礎力をしっかり身につけている生徒が多く見られました。特に算数では、文章題への理解力が向上している様子がうかがえます。一方で、国語の記述問題では、もう一歩深く考える力が求められます。日々の学習を積み重ねて、次回のテストでも力を発揮できるようにしましょう！',
        mathTeacherComment: '今回の結果は、未来へのヒントです。今の努力が、これからの可能性を広げていきます。小学生の今こそ、学ぶ力を育てる大切な時期です。一歩ずつ進みましょう。',
        japaneseTeacherComment: '今回の結果は、未来へのヒントです。今の努力が、これからの可能性を広げていきます。小学生の今こそ、学ぶ力を育てる大切な時期です。一歩ずつ進みましょう。',
        history: {
          all: [
            { round: 1, score: 142, deviation: 54.3 },
            { round: 2, score: 99, deviation: 42.3 },
            { round: 3, score: 171, deviation: 59.3 },
          ],
          math: [
            { round: 1, score: 71, deviation: 54.3 },
            { round: 2, score: 45, deviation: 42.3 },
            { round: 3, score: 89, deviation: 59.3 },
          ],
          japanese: [
            { round: 1, score: 71, deviation: 54.3 },
            { round: 2, score: 45, deviation: 42.3 },
            { round: 3, score: 89, deviation: 59.3 },
          ],
        },
      };
    },
  });

  const handlePrint = () => {
    window.print();
  };

  if (isLoading) {
    return <div className="flex items-center justify-center h-screen">読み込み中...</div>;
  }

  if (!reportData) {
    return <div className="flex items-center justify-center h-screen">データが見つかりません</div>;
  }

  return (
    <div>
      {/* 印刷ボタン（印刷時は非表示） */}
      <div className="fixed top-4 right-4 print:hidden z-10">
        <Button onClick={handlePrint} className="gap-2">
          <Printer className="h-4 w-4" />
          PDF出力
        </Button>
      </div>

      {/* 帳票 */}
      <StudentReport data={reportData} />

      {/* 印刷用スタイル */}
      <style jsx global>{`
        @media print {
          @page {
            size: A4;
            margin: 0;
          }
          body {
            margin: 0;
            padding: 0;
          }
          .print\\:hidden {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
}
