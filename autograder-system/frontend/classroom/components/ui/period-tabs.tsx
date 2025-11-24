'use client';

import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface PeriodTabsProps {
  value: string;
  onValueChange: (value: string) => void;
}

export function PeriodTabs({ value, onValueChange }: PeriodTabsProps) {
  const periods = [
    { value: 'spring', label: '春期' },
    { value: 'summer', label: '夏期' },
    { value: 'winter', label: '冬期' },
  ];

  return (
    <Tabs value={value} onValueChange={onValueChange}>
      <TabsList className="grid grid-cols-3 w-64 rounded-xl">
        {periods.map(period => (
          <TabsTrigger 
            key={period.value} 
            value={period.value}
            className="rounded-lg text-xs"
          >
            {period.label}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}