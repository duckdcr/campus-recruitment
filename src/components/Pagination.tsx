import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  const getVisiblePages = (): (number | 'ellipsis')[] => {
    const pages: (number | 'ellipsis')[] = [];
    const delta = 2;
    const start = Math.max(2, currentPage - delta);
    const end = Math.min(totalPages - 1, currentPage + delta);

    pages.push(1);
    if (start > 2) pages.push('ellipsis');
    for (let i = start; i <= end; i++) pages.push(i);
    if (end < totalPages - 1) pages.push('ellipsis');
    if (totalPages > 1) pages.push(totalPages);

    return pages;
  };

  return (
    <div className="pagination">
      <button
        className="pagination-btn"
        disabled={currentPage <= 1}
        onClick={() => onPageChange(currentPage - 1)}
        aria-label="上一页"
      >
        <ChevronLeft size={16} />
      </button>

      {getVisiblePages().map((page, idx) =>
        page === 'ellipsis' ? (
          <span key={`e-${idx}`} className="pagination-ellipsis">
            ...
          </span>
        ) : (
          <button
            key={page}
            className={`pagination-btn${currentPage === page ? ' active' : ''}`}
            onClick={() => onPageChange(page)}
          >
            {page}
          </button>
        ),
      )}

      <button
        className="pagination-btn"
        disabled={currentPage >= totalPages}
        onClick={() => onPageChange(currentPage + 1)}
        aria-label="下一页"
      >
        <ChevronRight size={16} />
      </button>
    </div>
  );
}
