'use client';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Calendar } from 'lucide-react';

interface YearPickerProps {
  value: string;
  onValueChange: (value: string) => void;
}

export function YearPicker({ value, onValueChange }: YearPickerProps) {
  const years = Array.from({ length: 6 }, (_, i) => (2025 + i).toString());

  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className="w-32">
        <Calendar className="h-4 w-4 mr-2" />
        <SelectValue placeholder="年度" />
      </SelectTrigger>
      <SelectContent>
        {years.map((year) => (
          <SelectItem key={year} value={year}>
            {year}年度
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}