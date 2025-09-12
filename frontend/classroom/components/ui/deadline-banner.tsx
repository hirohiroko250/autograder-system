'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Clock, AlertTriangle } from 'lucide-react';

interface DeadlineBannerProps {
  deadline?: Date;
}

export function DeadlineBanner({ deadline }: DeadlineBannerProps) {
  const [timeLeft, setTimeLeft] = useState<string>('');
  const [isUrgent, setIsUrgent] = useState(false);

  useEffect(() => {
    if (!deadline) return;

    const updateTimeLeft = () => {
      const now = new Date();
      const diff = deadline.getTime() - now.getTime();

      if (diff <= 0) {
        // 締切が過ぎた場合は非表示にする
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

      setTimeLeft(`${days}日 ${hours}時間 ${minutes}分`);
      setIsUrgent(days <= 2);
    };

    updateTimeLeft();
    const interval = setInterval(updateTimeLeft, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [deadline]);

  if (!deadline) return null;

  // 締切が過ぎている場合は非表示
  const now = new Date();
  if (deadline.getTime() <= now.getTime()) {
    return null;
  }

  return (
    <Card className={`border-2 ${isUrgent ? 'border-danger bg-danger/5' : 'border-warning bg-warning/5'}`}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {isUrgent ? (
              <AlertTriangle className="h-5 w-5 text-danger" />
            ) : (
              <Clock className="h-5 w-5 text-warning" />
            )}
            <div>
              <h3 className="font-semibold">スコア入力締切</h3>
              <p className="text-sm text-muted-foreground">
                {deadline.toLocaleDateString('ja-JP', { 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </p>
            </div>
          </div>
          <Badge variant={isUrgent ? 'destructive' : 'secondary'}>
            残り {timeLeft}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}