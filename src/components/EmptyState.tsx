import { SearchX } from 'lucide-react';

interface EmptyStateProps {
  hasFilter: boolean;
  onReset: () => void;
}

export function EmptyState({ hasFilter, onReset }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">
        <SearchX size={48} />
      </div>
      <h3 className="empty-state-title">未找到匹配职位</h3>
      <p className="empty-state-desc">
        {hasFilter
          ? '当前筛选条件没有匹配的校招信息，试试调整筛选条件'
          : '暂时没有校招信息，请稍后再来查看'}
      </p>
      {hasFilter && (
        <button className="btn btn-outline" onClick={onReset}>
          清除筛选条件
        </button>
      )}
    </div>
  );
}
