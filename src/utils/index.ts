import { parseISO, differenceInDays, format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

/**
 * 格式化日期为相对时间（如：3天前、2周前）
 */
export function formatRelativeDate(dateStr: string): string {
  try {
    const date = parseISO(dateStr);
    const now = new Date();
    const daysDiff = differenceInDays(now, date);

    if (daysDiff === 0) return '今天';
    if (daysDiff === 1) return '昨天';
    if (daysDiff < 7) return `${daysDiff}天前`;
    if (daysDiff < 30) return `${Math.floor(daysDiff / 7)}周前`;
    if (daysDiff < 365) return `${Math.floor(daysDiff / 30)}个月前`;

    return format(date, 'yyyy年M月d日', { locale: zhCN });
  } catch {
    return dateStr;
  }
}

/**
 * 格式化日期为完整日期
 */
export function formatFullDate(dateStr: string): string {
  try {
    const date = parseISO(dateStr);
    return format(date, 'yyyy年M月d日', { locale: zhCN });
  } catch {
    return dateStr;
  }
}

/**
 * 获取发布日期状态
 */
export function getDateStatus(dateStr: string): { label: string; color: string } {
  try {
    const date = parseISO(dateStr);
    const now = new Date();
    const daysDiff = differenceInDays(now, date);

    if (daysDiff <= 0) return { label: '今日发布', color: 'var(--color-success)' };
    if (daysDiff <= 3) return { label: '3日内', color: 'var(--color-primary)' };
    if (daysDiff <= 7) return { label: '本周', color: 'var(--color-warning)' };
    return { label: formatRelativeDate(dateStr), color: 'var(--color-text-tertiary)' };
  } catch {
    return { label: dateStr, color: 'var(--color-text-tertiary)' };
  }
}

/**
 * 数据来源显示名称
 */
const SOURCE_LABELS: Record<string, string> = {
  moka: 'Moka',
  lagou: '拉勾',
  liepin: '猎聘',
  'github/0voice/2026春招': 'GitHub校招汇总',
  'github/Campus2026': 'GitHub校招汇总',
  sample: '样本数据',
  bytedance: '字节跳动',
  tencent: '腾讯',
  baidu: '百度',
  jd: '京东',
  alibaba: '阿里',
  netease: '网易',
  huawei: '华为',
};

export function getSourceLabel(source: string): string {
  return SOURCE_LABELS[source] || source;
}

/**
 * 薪资范围排序用（提取数字）
 */
export function extractSalaryMax(salary: string): number {
  const match = salary.match(/(\d+)K/i);
  if (match) return parseInt(match[1]);
  // handle "20K-35K" or "20k-35k"
  const parts = salary.split('-');
  if (parts.length > 1) {
    const num = parseFloat(parts[1].replace(/[^0-9.]/g, ''));
    return isNaN(num) ? 0 : num;
  }
  return 0;
}

/**
 * 本地存储封装
 */
export const storage = {
  get<T>(key: string, fallback: T): T {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch {
      return fallback;
    }
  },
  set<T>(key: string, value: T): void {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // ignore quota errors
    }
  },
};
