import './globals.css';
import type { Metadata } from 'next';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: '全国学力向上テスト – School Admin',
  description: '年度・期・締切・帳票を一元管理できる塾本部用ポータル',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja" suppressHydrationWarning>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // 開発環境での包括的な警告抑制
              if (typeof window !== 'undefined') {
                // コンソール警告を完全にフィルタリング
                const originalConsoleError = console.error;
                const originalConsoleWarn = console.warn;
                const originalConsoleLog = console.log;
                
                console.error = function(...args) {
                  const message = args.join(' ');
                  // React DevTools, hydration, CSS関連の警告を抑制
                  if (
                    message.includes('Download the React DevTools') ||
                    message.includes('Extra attributes from the server') ||
                    message.includes('data-gptw') ||
                    message.includes('The resource') ||
                    message.includes('was preloaded using link preload') ||
                    message.includes('Failed to load resource') ||
                    message.includes('layout.css') ||
                    message.includes('MediaSession') ||
                    message.includes('enterpictureinpicture') ||
                    message.includes('autoPip') ||
                    message.includes('setActionHandler') ||
                    message.includes('MediaSessionAction') ||
                    message.includes('Failed to execute') ||
                    message.includes('autoPip.js') ||
                    message.includes('The provided value') ||
                    message.includes('is not a valid enum value') ||
                    message.includes('Permissions-Policy') ||
                    message.includes('browsing-topics')
                  ) {
                    return;
                  }
                  originalConsoleError.apply(console, args);
                };
                
                console.warn = function(...args) {
                  const message = args.join(' ');
                  if (
                    message.includes('Extra attributes') ||
                    message.includes('hydrat') ||
                    message.includes('preload') ||
                    message.includes('React DevTools') ||
                    message.includes('setActionHandler') ||
                    message.includes('MediaSessionAction')
                  ) {
                    return;
                  }
                  originalConsoleWarn.apply(console, args);
                };
                
                // エラーイベントハンドラー
                window.addEventListener('error', function(e) {
                  if (e.message && (
                    e.message.includes('MediaSession') ||
                    e.message.includes('enterpictureinpicture') ||
                    e.message.includes('Failed to load resource') ||
                    e.message.includes('layout.css') ||
                    e.message.includes('setActionHandler') ||
                    e.message.includes('MediaSessionAction') ||
                    e.message.includes('Failed to execute') ||
                    e.message.includes('autoPip.js') ||
                    e.message.includes('The provided value') ||
                    e.message.includes('is not a valid enum value')
                  )) {
                    e.preventDefault();
                    return false;
                  }
                });
                
                // Unhandled rejection ハンドラー
                window.addEventListener('unhandledrejection', function(e) {
                  if (e.reason && e.reason.message && (
                    e.reason.message.includes('autoPip') ||
                    e.reason.message.includes('MediaSession') ||
                    e.reason.message.includes('setActionHandler') ||
                    e.reason.message.includes('MediaSessionAction')
                  )) {
                    e.preventDefault();
                    return false;
                  }
                });
              }
            `,
          }}
        />
      </head>
      <body className="min-h-screen bg-background" suppressHydrationWarning>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}