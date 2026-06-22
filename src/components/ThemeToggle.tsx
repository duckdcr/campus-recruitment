import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import { storage } from '../utils';

export function ThemeToggle() {
  const [isDark, setIsDark] = useState(() => {
    const saved = storage.get<'light' | 'dark'>('campus-theme', 'light');
    return saved === 'dark';
  });

  useEffect(() => {
    const theme = isDark ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', theme);
    storage.set('campus-theme', theme);
  }, [isDark]);

  return (
    <button
      className="icon-btn"
      onClick={() => setIsDark((prev) => !prev)}
      aria-label={isDark ? '切换到亮色模式' : '切换到暗黑模式'}
      title={isDark ? '亮色模式' : '暗黑模式'}
    >
      {isDark ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
}
