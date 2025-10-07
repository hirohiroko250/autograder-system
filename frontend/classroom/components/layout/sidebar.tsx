'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Image from 'next/image';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { usePermissions } from '@/lib/permissions';
import { useAuth } from '@/lib/auth-context';
import {
  BarChart3,
  Users,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  GraduationCap,
  Calendar,
  Download,
  TrendingUp,
  MessageSquare,
} from 'lucide-react';

const getMenuItems = (permissions: { canRegisterStudents: boolean; canInputScores: boolean; canViewReports: boolean }, user: any) => [
  { 
    title: 'ダッシュボード', 
    href: '/dashboard', 
    icon: BarChart3,
    show: true
  },
  { 
    title: '教室管理', 
    href: '/classrooms', 
    icon: GraduationCap,
    show: permissions.canRegisterStudents
  },
  { 
    title: '生徒管理', 
    href: '/students', 
    icon: Users,
    show: permissions.canRegisterStudents
  },
  {
    title: 'テスト管理',
    icon: FileText,
    show: permissions.canInputScores || permissions.canViewReports,
    children: [
      { title: 'テスト一覧', href: '/tests', icon: FileText, show: permissions.canInputScores },
      { title: 'ダウンロード', href: '/tests/2025/download', icon: Download, show: permissions.canViewReports },
      { title: '結果・データ出力', href: '/tests/results', icon: TrendingUp, show: permissions.canViewReports },
    ].filter(child => child.show)
  },
  {
    title: '設定',
    icon: Settings,
    show: true,
    children: [
      { title: 'テスト日程', href: '/settings/test-schedule', icon: Calendar, show: true },
      { title: 'コメントテンプレート', href: '/settings/comment-templates', icon: MessageSquare, show: permissions.canInputScores },
    ].filter(child => child.show)
  },
].filter(item => item.show);

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();
  const { user } = useAuth();
  const permissions = usePermissions();
  const menuItems = getMenuItems(permissions, user);

  return (
    <div className={cn(
      "flex flex-col h-screen bg-card border-r transition-all duration-300",
      collapsed ? "w-16" : "w-64"
    )}>
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {!collapsed && (
              <img
                src="/logo.png"
                alt="全国学力向上テスト"
                className="h-10 w-auto"
              />
            )}
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCollapsed(!collapsed)}
            className="hover:bg-primary/10"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </Button>
        </div>
      </div>
      
      <ScrollArea className="flex-1 py-4">
        <nav className="space-y-2 px-2">
          {menuItems.map((item) => (
            <div key={item.title}>
              {item.children ? (
                <div className="space-y-1">
                  <div className={cn(
                    "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-xl",
                    collapsed ? "justify-center" : "justify-start"
                  )}>
                    <item.icon className="w-5 h-5" />
                    {!collapsed && <span>{item.title}</span>}
                  </div>
                  {!collapsed && (
                    <div className="ml-4 space-y-1">
                      {item.children.map((child) => (
                        <Link
                          key={child.href}
                          href={child.href}
                          className={cn(
                            "flex items-center gap-3 px-3 py-2 text-sm rounded-xl transition-colors",
                            pathname === child.href
                              ? "bg-primary text-primary-foreground"
                              : "hover:bg-accent hover:text-accent-foreground"
                          )}
                        >
                          <child.icon className="w-4 h-4" />
                          <span>{child.title}</span>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-xl transition-colors",
                    collapsed ? "justify-center" : "justify-start",
                    pathname === item.href
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <item.icon className="w-5 h-5" />
                  {!collapsed && <span>{item.title}</span>}
                </Link>
              )}
            </div>
          ))}
        </nav>
      </ScrollArea>
    </div>
  );
}