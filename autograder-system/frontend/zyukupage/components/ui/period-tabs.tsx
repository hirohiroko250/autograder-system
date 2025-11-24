'use client';

import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface PeriodTabsProps {
  value: string;
  onValueChange: (value: string) => void;
}

export function PeriodTabs({ value, onValueChange }: PeriodTabsProps) {
  return (
    <Tabs value={value} onValueChange={onValueChange}>
      <TabsList className="grid w-full grid-cols-3">
        <TabsTrigger value="spring">春期</TabsTrigger>
        <TabsTrigger value="summer">夏期</TabsTrigger>
        <TabsTrigger value="winter">冬期</TabsTrigger>
      </TabsList>
    </Tabs>
  );
}