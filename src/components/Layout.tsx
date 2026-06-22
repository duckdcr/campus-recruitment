import { Bell, Briefcase } from 'lucide-react';
import type { ReactNode } from 'react';
import { ThemeToggle } from './ThemeToggle';

interface LayoutProps {
  children: ReactNode;
  onOpenSubscription: () => void;
}

export function Layout({ children, onOpenSubscription }: LayoutProps) {
  return (
    <>
      <header className="layout-header">
        <div className="layout-header-inner">
          <div className="layout-logo">
            <span className="layout-logo-icon">
              <Briefcase size={18} />
            </span>
            <span>校招雷达</span>
          </div>

          <div className="layout-header-actions">
            <button className="btn btn-sm btn-outline" onClick={onOpenSubscription}>
              <Bell size={14} />
              <span className="icon-btn-label">订阅</span>
            </button>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="layout-main">{children}</main>

      <footer className="layout-footer">
        校招雷达 · 每日更新一线+新一线城市产品类校招信息 · 数据来源：Moka/拉勾/猎聘/企业官网/GitHub社区
      </footer>
    </>
  );
}
