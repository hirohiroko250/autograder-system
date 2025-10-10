'use client';

import { useState, useEffect, useCallback } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Separator } from '@/components/ui/separator';
import { 
  Search, 
  Filter, 
  X, 
  ChevronDown, 
  ChevronUp,
  Calendar,
  Users,
  GraduationCap,
  Building2,
  Hash
} from 'lucide-react';

interface FilterOption {
  key: string;
  label: string;
  icon?: any;
  type: 'text' | 'select' | 'multiselect' | 'date' | 'number' | 'range';
  options?: Array<{ value: string; label: string }>;
  placeholder?: string;
}

interface SearchFilters {
  [key: string]: any;
}

interface AdvancedSearchProps {
  placeholder?: string;
  filterOptions: FilterOption[];
  onSearch: (query: string, filters: SearchFilters) => void;
  onClear?: () => void;
  defaultSearchValue?: string;
  defaultFilters?: SearchFilters;
  showResultCount?: boolean;
  resultCount?: number;
  className?: string;
}

export function AdvancedSearch({
  placeholder = "検索...",
  filterOptions,
  onSearch,
  onClear,
  defaultSearchValue = '',
  defaultFilters = {},
  showResultCount = false,
  resultCount = 0,
  className = ''
}: AdvancedSearchProps) {
  const [searchQuery, setSearchQuery] = useState(defaultSearchValue);
  const [filters, setFilters] = useState<SearchFilters>(defaultFilters);
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [activeFilterCount, setActiveFilterCount] = useState(0);

  // アクティブなフィルター数を計算
  useEffect(() => {
    const count = Object.values(filters).filter(value => {
      if (Array.isArray(value)) return value.length > 0;
      return value !== '' && value !== null && value !== undefined;
    }).length;
    setActiveFilterCount(count);
  }, [filters]);

  // 検索実行
  const executeSearch = useCallback(() => {
    onSearch(searchQuery, filters);
  }, [searchQuery, filters, onSearch]);

  // 検索クリア
  const clearSearch = () => {
    setSearchQuery('');
    setFilters({});
    setActiveFilterCount(0);
    onClear?.();
  };

  // フィルター値変更
  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // フィルター削除
  const removeFilter = (key: string) => {
    setFilters(prev => {
      const newFilters = { ...prev };
      delete newFilters[key];
      return newFilters;
    });
  };

  // Enterキーでの検索
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      executeSearch();
    }
  };

  // フィルタータイプ別のレンダリング
  const renderFilterInput = (option: FilterOption) => {
    const value = filters[option.key] || '';
    
    switch (option.type) {
      case 'text':
        return (
          <Input
            placeholder={option.placeholder}
            value={value}
            onChange={(e) => handleFilterChange(option.key, e.target.value)}
            onKeyPress={handleKeyPress}
          />
        );
      
      case 'number':
        return (
          <Input
            type="number"
            placeholder={option.placeholder}
            value={value}
            onChange={(e) => handleFilterChange(option.key, e.target.value)}
            onKeyPress={handleKeyPress}
          />
        );
      
      case 'select':
        return (
          <Select value={value || "all"} onValueChange={(newValue) => handleFilterChange(option.key, newValue === "all" ? "" : newValue)}>
            <SelectTrigger>
              <SelectValue placeholder={option.placeholder || `${option.label}を選択`} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">すべて</SelectItem>
              {option.options?.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );
      
      case 'multiselect':
        const selectedValues = Array.isArray(value) ? value : [];
        return (
          <div className="space-y-2">
            <Select 
              value={undefined} 
              onValueChange={(newValue) => {
                if (newValue && !selectedValues.includes(newValue)) {
                  handleFilterChange(option.key, [...selectedValues, newValue]);
                }
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder={option.placeholder || `${option.label}を選択`} />
              </SelectTrigger>
              <SelectContent>
                {option.options?.map((opt) => (
                  <SelectItem 
                    key={opt.value} 
                    value={opt.value}
                    disabled={selectedValues.includes(opt.value)}
                  >
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedValues.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {selectedValues.map((selectedValue: string) => {
                  const selectedOption = option.options?.find(opt => opt.value === selectedValue);
                  return (
                    <Badge key={selectedValue} variant="secondary" className="text-xs">
                      {selectedOption?.label}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-auto p-0 ml-1"
                        onClick={() => {
                          const newValues = selectedValues.filter(v => v !== selectedValue);
                          handleFilterChange(option.key, newValues);
                        }}
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </Badge>
                  );
                })}
              </div>
            )}
          </div>
        );
      
      case 'date':
        return (
          <Input
            type="date"
            value={value}
            onChange={(e) => handleFilterChange(option.key, e.target.value)}
          />
        );
      
      case 'range':
        const rangeValue = value || { min: '', max: '' };
        return (
          <div className="grid grid-cols-2 gap-2">
            <Input
              type="number"
              placeholder="最小"
              value={rangeValue.min || ''}
              onChange={(e) => handleFilterChange(option.key, { ...rangeValue, min: e.target.value })}
              onKeyPress={handleKeyPress}
            />
            <Input
              type="number"
              placeholder="最大"
              value={rangeValue.max || ''}
              onChange={(e) => handleFilterChange(option.key, { ...rangeValue, max: e.target.value })}
              onKeyPress={handleKeyPress}
            />
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* メイン検索バー */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder={placeholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          <Button onClick={executeSearch} className="flex-1 sm:flex-none sm:px-6">
            検索
          </Button>
          <Button
            variant="outline"
            onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
            className="flex-1 sm:flex-none sm:px-4"
          >
            <Filter className="h-4 w-4 sm:mr-2" />
            <span className="hidden sm:inline">フィルター</span>
            {activeFilterCount > 0 && (
              <Badge variant="secondary" className="ml-2 text-xs">
                {activeFilterCount}
              </Badge>
            )}
            {isAdvancedOpen ? (
              <ChevronUp className="h-4 w-4 ml-2" />
            ) : (
              <ChevronDown className="h-4 w-4 ml-2" />
            )}
          </Button>
          {(searchQuery || activeFilterCount > 0) && (
            <Button variant="ghost" onClick={clearSearch} size="sm" className="flex-shrink-0">
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* 結果件数表示 */}
      {showResultCount && (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-sm text-gray-600">
          <span>{resultCount}件の結果</span>
          {(searchQuery || activeFilterCount > 0) && (
            <div className="flex flex-col sm:flex-row sm:items-center gap-2">
              <span className="hidden sm:inline">検索条件:</span>
              <div className="flex flex-wrap items-center gap-2">
                {searchQuery && (
                  <Badge variant="outline">
                    "{searchQuery}"
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-auto p-0 ml-1"
                      onClick={() => setSearchQuery('')}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                )}
                {Object.entries(filters).map(([key, value]) => {
                  if (!value || (Array.isArray(value) && value.length === 0)) return null;
                  const option = filterOptions.find(opt => opt.key === key);
                  if (!option) return null;

                  let displayValue: string;
                  if (Array.isArray(value)) {
                    displayValue = `${value.length}個選択`;
                  } else if (option.type === 'range' && typeof value === 'object' && value !== null) {
                    displayValue = `${value.min || '?'} - ${value.max || '?'}`;
                  } else if (option.options) {
                    const selectedOption = option.options.find(opt => opt.value === value);
                    displayValue = selectedOption?.label || String(value);
                  } else {
                    displayValue = String(value);
                  }

                  return (
                    <Badge key={key} variant="secondary" className="text-xs">
                      {option.label}: {displayValue}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-auto p-0 ml-1"
                        onClick={() => removeFilter(key)}
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </Badge>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 高度なフィルター */}
      <Collapsible open={isAdvancedOpen}>
        <CollapsibleContent>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Filter className="h-4 w-4" />
                詳細フィルター
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {filterOptions.map((option) => (
                  <div key={option.key} className="space-y-2">
                    <Label className="text-sm font-medium flex items-center gap-1">
                      {option.icon && <option.icon className="h-3 w-3" />}
                      {option.label}
                    </Label>
                    {renderFilterInput(option)}
                  </div>
                ))}
              </div>
              <Separator className="my-4" />
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={clearSearch} size="sm">
                  すべてクリア
                </Button>
                <Button onClick={executeSearch} size="sm">
                  フィルター適用
                </Button>
              </div>
            </CardContent>
          </Card>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}

// 事前定義されたフィルターオプション
export const commonFilterOptions = {
  // 生徒関連
  studentGrade: {
    key: 'grade',
    label: '学年',
    icon: GraduationCap,
    type: 'select' as const,
    options: [
      { value: '小学1年生', label: '小学1年生' },
      { value: '小学2年生', label: '小学2年生' },
      { value: '小学3年生', label: '小学3年生' },
      { value: '小学4年生', label: '小学4年生' },
      { value: '小学5年生', label: '小学5年生' },
      { value: '小学6年生', label: '小学6年生' },
      { value: '中学1年生', label: '中学1年生' },
      { value: '中学2年生', label: '中学2年生' },
      { value: '中学3年生', label: '中学3年生' },
    ],
    placeholder: '学年を選択'
  },

  studentStatus: {
    key: 'status',
    label: 'ステータス',
    icon: Users,
    type: 'select' as const,
    options: [
      { value: 'enrolled', label: '入会' },
      { value: 'new', label: '新規' },
      { value: 'withdrawn', label: '退会' },
    ],
    placeholder: 'ステータスを選択'
  },

  // 教室関連
  classroomActive: {
    key: 'is_active',
    label: 'アクティブ状態',
    icon: Building2,
    type: 'select' as const,
    options: [
      { value: 'true', label: 'アクティブ' },
      { value: 'false', label: '非アクティブ' },
    ],
    placeholder: 'アクティブ状態を選択'
  },

  // 年度・期間
  year: {
    key: 'year',
    label: '年度',
    icon: Calendar,
    type: 'select' as const,
    options: [
      { value: '2025', label: '2025年度' },
          { value: '2026', label: '2026年度' },
          { value: '2027', label: '2027年度' },
      
      
    ],
    placeholder: '年度を選択'
  },

  period: {
    key: 'period',
    label: '期間',
    icon: Calendar,
    type: 'select' as const,
    options: [
      { value: 'spring', label: '春期' },
      { value: 'summer', label: '夏期' },
      { value: 'winter', label: '冬期' },
    ],
    placeholder: '期間を選択'
  },

  // 汎用
  studentId: {
    key: 'student_id',
    label: '生徒ID',
    icon: Hash,
    type: 'text' as const,
    placeholder: '生徒IDで検索'
  }
};