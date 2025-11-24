import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// 学年表示フォーマット変換関数
export function formatGrade(grade: string | number): string {
  const gradeStr = String(grade);
  
  // 数字のみの場合（1-6は小学生、7-9は中学生）
  if (/^\d+$/.test(gradeStr)) {
    const gradeNum = parseInt(gradeStr);
    if (gradeNum >= 1 && gradeNum <= 6) {
      return `小${gradeNum}`;
    } else if (gradeNum >= 7 && gradeNum <= 9) {
      return `中${gradeNum - 6}`;
    }
  }
  
  // 既にフォーマット済みの場合はそのまま返す
  if (gradeStr.match(/^(小|中)\d+$/)) {
    return gradeStr;
  }
  
  // その他の場合はそのまま返す
  return gradeStr;
}

// 逆変換：表示形式から数値に変換
export function parseGrade(gradeDisplay: string): string {
  if (gradeDisplay.startsWith('小')) {
    return gradeDisplay.replace('小', '');
  } else if (gradeDisplay.startsWith('中')) {
    const middleGrade = parseInt(gradeDisplay.replace('中', ''));
    return String(middleGrade + 6);
  }
  return gradeDisplay;
}
