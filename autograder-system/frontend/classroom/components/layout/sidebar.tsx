'use client';

import { useState, useEffect } from 'react';
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
    mobileTitle: 'ダッシュ',
    href: '/dashboard',
    icon: BarChart3,
    show: true
  },
  {
    title: '教室管理',
    mobileTitle: '教室',
    href: '/classrooms',
    icon: GraduationCap,
    show: permissions.canRegisterStudents
  },
  {
    title: '生徒管理',
    mobileTitle: '生徒',
    href: '/students',
    icon: Users,
    show: permissions.canRegisterStudents
  },
  {
    title: 'テスト管理',
    mobileTitle: 'テスト',
    icon: FileText,
    show: permissions.canInputScores || permissions.canViewReports,
    children: [
      { title: 'テスト一覧', mobileTitle: '一覧', href: '/tests', icon: FileText, show: permissions.canInputScores },
      { title: 'ダウンロード', mobileTitle: 'DL', href: '/tests/2025/download', icon: Download, show: permissions.canViewReports },
      { title: '結果・データ出力', mobileTitle: '結果', href: '/tests/results', icon: TrendingUp, show: permissions.canViewReports },
    ].filter(child => child.show)
  },
  {
    title: '設定',
    mobileTitle: '設定',
    icon: Settings,
    show: true,
    children: [
      { title: 'テスト日程', mobileTitle: '日程', href: '/settings/test-schedule', icon: Calendar, show: true },
      { title: 'コメントテンプレート', mobileTitle: 'ｺﾒﾝﾄ', href: '/settings/comment-templates', icon: MessageSquare, show: permissions.canInputScores },
    ].filter(child => child.show)
  },
  // 開発環境のみ表示
  /*
  {
    title: 'デバッグ',
    mobileTitle: 'デバッグ',
    href: '/debug',
    icon: Bug,
    show: process.env.NODE_ENV === 'development'
  }
  */
].filter(item => item.show);

interface SidebarProps {
  onClose?: () => void;
}

export function Sidebar({ onClose }: SidebarProps = {}) {
  const [collapsed, setCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const pathname = usePathname();
  const { user } = useAuth();
  const permissions = usePermissions();
  const menuItems = getMenuItems(permissions, user);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleLinkClick = () => {
    // モバイルでメニューをクリックしたら閉じる
    if (onClose) {
      onClose();
    }
  };

  return (
    <div className={cn(
      "flex flex-col h-screen bg-card border-r transition-all duration-300",
      "w-64 md:w-64", // Fixed width for mobile, responsive for desktop
      collapsed ? "md:w-16" : "md:w-64" // Only apply collapse on desktop
    )}>
      <div className="p-3 md:p-4 border-b">
        <div className="flex items-center justify-between">
          {collapsed && !isMobile ? (
            <div className="flex items-center justify-center w-full">
              <img
                src="/logo.png"
                alt="全国学力向上テスト"
                className="h-10 w-auto object-contain"
              />
            </div>
          ) : (
            <>
              <div className="flex items-center gap-2">
                <img
                  src="/logo.png"
                  alt="全国学力向上テスト"
                  className="h-10 w-auto object-contain"
                />
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setCollapsed(!collapsed)}
                className="hover:bg-primary/10 hidden md:flex"
              >
                {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
              </Button>
            </>
          )}
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
                    {!collapsed && <span className="whitespace-nowrap truncate text-xs sm:text-sm">{isMobile ? item.mobileTitle || item.title : item.title}</span>}
                  </div>
                  {!collapsed && (
                    <div className="ml-4 space-y-1">
                      {item.children.map((child) => (
                        <Link
                          key={child.href}
                          href={child.href}
                          onClick={handleLinkClick}
                          className={cn(
                            "flex items-center gap-3 px-3 py-2 text-sm rounded-xl transition-colors",
                            pathname === child.href
                              ? "bg-primary text-primary-foreground"
                              : "hover:bg-accent hover:text-accent-foreground"
                          )}
                        >
                          <child.icon className="w-4 h-4" />
                          <span className="whitespace-nowrap truncate text-xs sm:text-sm">{isMobile ? child.mobileTitle || child.title : child.title}</span>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <Link
                  href={item.href}
                  onClick={handleLinkClick}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-xl transition-colors",
                    collapsed ? "justify-center" : "justify-start",
                    pathname === item.href
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <item.icon className="w-5 h-5" />
                  {!collapsed && <span className="whitespace-nowrap truncate text-xs sm:text-sm">{isMobile ? item.mobileTitle || item.title : item.title}</span>}
                </Link>
              )}
            </div>
          ))}
        </nav>
      </ScrollArea>
    </div>
  );
}