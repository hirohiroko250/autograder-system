'use client';

import { useEffect, useState } from 'react';
import { testApi } from '@/lib/api-client';
import { TestSchedule } from '@/lib/types';

interface TestDeadlineProps {
  year?: number;
  period?: string;
  className?: string;
}

export function TestDeadline({ year, period, className = '' }: TestDeadlineProps) {
  const [deadline, setDeadline] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDeadline = async () => {
      try {
        setLoading(true);
        const response = await testApi.getTestSchedules({
          year: year?.toString(),
          period
        });

        if (response.results.length > 0) {
          const schedule = response.results[0];
          setDeadline(schedule.deadline_at);
        } else {
          setDeadline(null);
        }
      } catch (err) {
        console.error('Failed to fetch test schedule:', err);
        setError('スケジュール情報の取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };

    fetchDeadline();
  }, [year, period]);

  const formatDeadline = (deadlineStr: string): string => {
    const date = new Date(deadlineStr);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const hour = date.getHours();
    const minute = date.getMinutes();
    
    return `${year}年${month}月${day}日 ${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
  };

  const isDeadlinePassed = (deadlineStr: string): boolean => {
    return new Date(deadlineStr) < new Date();
  };

  if (loading) {
    return (
      <div className={`text-gray-500 text-sm ${className}`}>
        締切日時を取得中...
      </div>
    );
  }

  if (error) {
    return (
      <div className={`text-red-500 text-sm ${className}`}>
        {error}
      </div>
    );
  }

  if (!deadline) {
    return (
      <div className={`text-gray-500 text-sm ${className}`}>
        締切日時が設定されていません
      </div>
    );
  }

  const passed = isDeadlinePassed(deadline);

  return (
    <div className={`text-sm ${className}`}>
      <span className={passed ? 'text-red-600' : 'text-orange-600'}>
        {passed ? '締切済み' : '締切'}: {formatDeadline(deadline)}
      </span>
    </div>
  );
}

export default TestDeadline;