import { Search, X } from 'lucide-react';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function SearchBar({ value, onChange, placeholder = '搜索公司、职位、关键词...' }: SearchBarProps) {
  return (
    <div className="search-bar">
      <input
        className="search-bar-input"
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        aria-label="搜索校招信息"
      />
      {value && (
        <button className="search-bar-clear" onClick={() => onChange('')} aria-label="清除搜索">
          <X size={16} />
        </button>
      )}
      <span className="search-bar-icon">
        <Search size={18} />
      </span>
    </div>
  );
}
