import React from 'react';
import Image from 'next/image';

export interface SubjectItem {
  number: number;
  name: string;
  score: number;
  maxScore: number;
  average: number;
  correctRate: number;
}

export interface ReportData {
  issueDate: string;
  year: number;
  period: string;
  periodNumber: number;
  grade: string;
  schoolId: string;
  schoolName: string;
  studentId: string;
  examId: string;
  studentGrade: string;
  studentName: string;

  // 得点・偏差値・順位
  math: {
    score: number;
    deviation: number;
    nationalRank: number;
    nationalTotal: number;
    schoolRank: number;
    schoolTotal: number;
    maxScoreNational: number;
    maxScoreSchool: number;
    minScoreNational: number;
    minScoreSchool: number;
    averageNational: number;
    averageSchool: number;
  };
  japanese: {
    score: number;
    deviation: number;
    nationalRank: number;
    nationalTotal: number;
    schoolRank: number;
    schoolTotal: number;
    maxScoreNational: number;
    maxScoreSchool: number;
    minScoreNational: number;
    minScoreSchool: number;
    averageNational: number;
    averageSchool: number;
  };
  total: {
    score: number;
    deviation: number;
    nationalRank: number;
    nationalTotal: number;
    schoolRank: number;
    schoolTotal: number;
    maxScoreNational: number;
    maxScoreSchool: number;
    minScoreNational: number;
    minScoreSchool: number;
    averageNational: number;
    averageSchool: number;
  };

  // 出題項目別の成績
  mathItems: SubjectItem[];
  japaneseItems: SubjectItem[];

  // 教科ごとの総評
  mathComment: string;
  japaneseComment: string;

  // 塾長からのコメント
  mathTeacherComment: string;
  japaneseTeacherComment: string;

  // 成績の推移
  history: {
    all: Array<{ round: number; score: number; deviation: number }>;
    math: Array<{ round: number; score: number; deviation: number }>;
    japanese: Array<{ round: number; score: number; deviation: number }>;
  };
}

const getPeriodLabel = (period: string) => {
  switch (period) {
    case 'spring': return '春期';
    case 'summer': return '夏期';
    case 'winter': return '冬期';
    default: return period;
  }
};

export const StudentReport: React.FC<{ data: ReportData }> = ({ data }) => {
  return (
    <div id="student-report" className="w-[210mm] h-[297mm] bg-white text-black p-8 print:p-8" style={{ fontFamily: 'sans-serif' }}>
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="w-32 h-16 border border-gray-300 flex items-center justify-center">
            <Image src="/logo.png" alt="Logo" width={120} height={60} className="object-contain" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">全国学力向上テスト 個人成績表</h1>
          </div>
        </div>
        <div className="text-right">
          <p className="text-sm">発行日：{data.issueDate}</p>
          <p className="text-lg font-bold">{data.year} 年度 第 {data.periodNumber} 回 学年 {data.grade}</p>
        </div>
      </div>

      {/* 生徒情報 */}
      <div className="grid grid-cols-6 gap-2 mb-4 text-sm border border-gray-300">
        <div className="p-1 bg-gray-100 border-r border-gray-300">塾ID</div>
        <div className="p-1 border-r border-gray-300">{data.schoolId}</div>
        <div className="p-1 bg-gray-100 border-r border-gray-300">塾名</div>
        <div className="p-1 border-r border-gray-300">{data.schoolName}</div>
        <div className="p-1 bg-gray-100 border-r border-gray-300">生徒ID</div>
        <div className="p-1">{data.studentId}</div>
      </div>
      <div className="grid grid-cols-6 gap-2 mb-6 text-sm border border-gray-300 border-t-0">
        <div className="p-1 bg-gray-100 border-r border-gray-300">受験ID</div>
        <div className="p-1 border-r border-gray-300">{data.examId}</div>
        <div className="p-1 bg-gray-100 border-r border-gray-300">学年</div>
        <div className="p-1 border-r border-gray-300">{data.studentGrade}</div>
        <div className="p-1 bg-gray-100 border-r border-gray-300">生徒氏名</div>
        <div className="p-1 font-bold">{data.studentName}</div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* 左カラム */}
        <div>
          {/* 得点・偏差値・順位 */}
          <h2 className="text-sm font-bold mb-2 flex items-center gap-1">
            <span className="text-blue-600">◆</span>得点・偏差値・順位
          </h2>
          <table className="w-full text-xs mb-4 border-collapse">
            <thead>
              <tr>
                <th className="border border-gray-300 bg-gray-100 p-1">教科</th>
                <th className="border border-gray-300 bg-green-600 text-white p-1">算数</th>
                <th className="border border-gray-300 bg-orange-500 text-white p-1">国語</th>
                <th className="border border-gray-300 bg-blue-500 text-white p-1">合計</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border border-gray-300 bg-gray-100 p-1">得点</td>
                <td className="border border-gray-300 text-center text-2xl font-bold text-red-600 p-1">{data.math.score}点</td>
                <td className="border border-gray-300 text-center text-2xl font-bold text-red-600 p-1">{data.japanese.score}点</td>
                <td className="border border-gray-300 text-center text-2xl font-bold text-red-600 p-1">{data.total.score}点</td>
              </tr>
              <tr>
                <td className="border border-gray-300 bg-gray-100 p-1">偏差値</td>
                <td className="border border-gray-300 text-center text-xl font-bold p-1">{data.math.deviation}</td>
                <td className="border border-gray-300 text-center text-xl font-bold p-1">{data.japanese.deviation}</td>
                <td className="border border-gray-300 text-center text-xl font-bold p-1">{data.total.deviation}</td>
              </tr>
              <tr>
                <td className="border border-gray-300 bg-gray-100 p-1 text-[10px]">全国順位(受験者数)</td>
                <td className="border border-gray-300 text-center p-1">{data.math.nationalRank}位({data.math.nationalTotal}人中)</td>
                <td className="border border-gray-300 text-center p-1">{data.japanese.nationalRank}位({data.japanese.nationalTotal}人中)</td>
                <td className="border border-gray-300 text-center p-1">{data.total.nationalRank}位({data.total.nationalTotal}人中)</td>
              </tr>
              <tr>
                <td className="border border-gray-300 bg-gray-100 p-1 text-[10px]">塾内順位(受験者数)</td>
                <td className="border border-gray-300 text-center p-1">{data.math.schoolRank}位({data.math.schoolTotal}人中)</td>
                <td className="border border-gray-300 text-center p-1">{data.japanese.schoolRank}位({data.japanese.schoolTotal}人中)</td>
                <td className="border border-gray-300 text-center p-1">{data.total.schoolRank}位({data.total.schoolTotal}人中)</td>
              </tr>
              <tr>
                <td className="border border-gray-300 bg-gray-100 p-1">最高点(全国)</td>
                <td className="border border-gray-300 text-center p-1">{data.math.maxScoreNational}点</td>
                <td className="border border-gray-300 text-center p-1">{data.japanese.maxScoreNational}点</td>
                <td className="border border-gray-300 text-center p-1">{data.total.maxScoreNational}点</td>
              </tr>
              <tr>
                <td className="border border-gray-300 bg-gray-100 p-1">最高点(塾内)</td>
                <td className="border border-gray-300 text-center p-1">{data.math.maxScoreSchool}点</td>
                <td className="border border-gray-300 text-center p-1">{data.japanese.maxScoreSchool}点</td>
                <td className="border border-gray-300 text-center p-1">{data.total.maxScoreSchool}点</td>
              </tr>
              <tr>
                <td className="border border-gray-300 bg-gray-100 p-1">平均点(全国)</td>
                <td className="border border-gray-300 text-center p-1">{data.math.averageNational}点</td>
                <td className="border border-gray-300 text-center p-1">{data.japanese.averageNational}点</td>
                <td className="border border-gray-300 text-center p-1">{data.total.averageNational}点</td>
              </tr>
              <tr>
                <td className="border border-gray-300 bg-gray-100 p-1">平均点(塾内)</td>
                <td className="border border-gray-300 text-center p-1">{data.math.averageSchool}点</td>
                <td className="border border-gray-300 text-center p-1">{data.japanese.averageSchool}点</td>
                <td className="border border-gray-300 text-center p-1">{data.total.averageSchool}点</td>
              </tr>
            </tbody>
          </table>

          {/* 成績の推移 */}
          <h2 className="text-sm font-bold mb-2 flex items-center gap-1">
            <span className="text-blue-600">◆</span>成績の推移
          </h2>
          <div className="space-y-2 text-[10px]">
            {/* 全教科 */}
            <div className="border border-gray-300 p-2">
              <div className="bg-blue-500 text-white text-center py-1 mb-2">全教科</div>
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="border border-gray-300 bg-gray-100 p-1">回数</th>
                    <th className="border border-gray-300 bg-gray-100 p-1">得点</th>
                    <th className="border border-gray-300 bg-gray-100 p-1">偏差値</th>
                  </tr>
                </thead>
                <tbody>
                  {data.history.all.map((item) => (
                    <tr key={item.round}>
                      <td className="border border-gray-300 text-center p-1">{item.round}</td>
                      <td className="border border-gray-300 text-center p-1">{item.score}</td>
                      <td className="border border-gray-300 text-center p-1">{item.deviation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 算数 */}
            <div className="border border-gray-300 p-2">
              <div className="bg-green-600 text-white text-center py-1 mb-2">算数</div>
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="border border-gray-300 bg-gray-100 p-1">回数</th>
                    <th className="border border-gray-300 bg-gray-100 p-1">得点</th>
                    <th className="border border-gray-300 bg-gray-100 p-1">偏差値</th>
                  </tr>
                </thead>
                <tbody>
                  {data.history.math.map((item) => (
                    <tr key={item.round}>
                      <td className="border border-gray-300 text-center p-1">{item.round}</td>
                      <td className="border border-gray-300 text-center p-1">{item.score}</td>
                      <td className="border border-gray-300 text-center p-1">{item.deviation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 国語 */}
            <div className="border border-gray-300 p-2">
              <div className="bg-orange-500 text-white text-center py-1 mb-2">国語</div>
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="border border-gray-300 bg-gray-100 p-1">回数</th>
                    <th className="border border-gray-300 bg-gray-100 p-1">得点</th>
                    <th className="border border-gray-300 bg-gray-100 p-1">偏差値</th>
                  </tr>
                </thead>
                <tbody>
                  {data.history.japanese.map((item) => (
                    <tr key={item.round}>
                      <td className="border border-gray-300 text-center p-1">{item.round}</td>
                      <td className="border border-gray-300 text-center p-1">{item.score}</td>
                      <td className="border border-gray-300 text-center p-1">{item.deviation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* 右カラム */}
        <div>
          {/* 出題項目別の成績 - 算数 */}
          <h2 className="text-sm font-bold mb-2 flex items-center gap-1">
            <span className="text-blue-600">◆</span>出題項目別の成績
          </h2>
          <div className="border border-gray-300 mb-3">
            <div className="bg-green-600 text-white text-center py-1 text-xs font-bold">算数</div>
            <p className="text-[9px] px-2 py-1">は出題項目別の正答率です。★は全国の平均正答率です。</p>
            <table className="w-full text-[10px]">
              <thead>
                <tr>
                  <th className="border border-gray-300 bg-gray-100 p-1 w-8">大問</th>
                  <th className="border border-gray-300 bg-gray-100 p-1">出題項目名</th>
                  <th className="border border-gray-300 bg-gray-100 p-1 w-16">得点/配点</th>
                  <th className="border border-gray-300 bg-gray-100 p-1 w-16">全国平均点</th>
                  <th className="border border-gray-300 bg-gray-100 p-1 w-16">正答率</th>
                </tr>
              </thead>
              <tbody>
                {data.mathItems.map((item) => (
                  <tr key={item.number}>
                    <td className="border border-gray-300 text-center p-1">{item.number}</td>
                    <td className="border border-gray-300 p-1">{item.name}</td>
                    <td className="border border-gray-300 text-center p-1">{item.score}/{item.maxScore}点</td>
                    <td className="border border-gray-300 text-center p-1">{item.average}点</td>
                    <td className="border border-gray-300 text-center p-1">{item.correctRate}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 出題項目別の成績 - 国語 */}
          <div className="border border-gray-300 mb-3">
            <div className="bg-orange-500 text-white text-center py-1 text-xs font-bold">国語</div>
            <p className="text-[9px] px-2 py-1">は出題項目別の正答率です。★は全国の平均正答率です。</p>
            <table className="w-full text-[10px]">
              <thead>
                <tr>
                  <th className="border border-gray-300 bg-gray-100 p-1 w-8">大問</th>
                  <th className="border border-gray-300 bg-gray-100 p-1">出題項目名</th>
                  <th className="border border-gray-300 bg-gray-100 p-1 w-16">得点/配点</th>
                  <th className="border border-gray-300 bg-gray-100 p-1 w-16">全国平均点</th>
                  <th className="border border-gray-300 bg-gray-100 p-1 w-16">正答率</th>
                </tr>
              </thead>
              <tbody>
                {data.japaneseItems.map((item) => (
                  <tr key={item.number}>
                    <td className="border border-gray-300 text-center p-1">{item.number}</td>
                    <td className="border border-gray-300 p-1">{item.name}</td>
                    <td className="border border-gray-300 text-center p-1">{item.score}/{item.maxScore}点</td>
                    <td className="border border-gray-300 text-center p-1">{item.average}点</td>
                    <td className="border border-gray-300 text-center p-1">{item.correctRate}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 教科ごとの総評 */}
          <h2 className="text-sm font-bold mb-2 flex items-center gap-1">
            <span className="text-blue-600">◆</span>教科ごとの総評
          </h2>
          <div className="space-y-2 mb-3">
            <div className="border border-gray-300">
              <div className="bg-green-600 text-white text-center py-1 text-xs font-bold">算数</div>
              <p className="text-[10px] p-2 leading-relaxed">{data.mathComment}</p>
            </div>
            <div className="border border-gray-300">
              <div className="bg-orange-500 text-white text-center py-1 text-xs font-bold">国語</div>
              <p className="text-[10px] p-2 leading-relaxed">{data.japaneseComment}</p>
            </div>
          </div>

          {/* 塾長からのコメント */}
          <h2 className="text-sm font-bold mb-2 flex items-center gap-1">
            <span className="text-blue-600">◆</span>塾長からのコメント
          </h2>
          <div className="space-y-2">
            <div className="border border-gray-300">
              <div className="bg-green-600 text-white text-center py-1 text-xs font-bold">算数</div>
              <p className="text-[10px] p-2 leading-relaxed">{data.mathTeacherComment}</p>
            </div>
            <div className="border border-gray-300">
              <div className="bg-orange-500 text-white text-center py-1 text-xs font-bold">国語</div>
              <p className="text-[10px] p-2 leading-relaxed">{data.japaneseTeacherComment}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
