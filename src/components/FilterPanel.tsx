import type { FilterState } from '../types/job';
import { JOB_CATEGORIES } from '../types/job';

interface FilterPanelProps {
  filter: FilterState;
  availableCompanies: string[];
  availableCities: string[];
  availableCategories: string[];
  onFilterChange: (patch: Partial<FilterState>) => void;
  onReset: () => void;
}

export function FilterPanel({
  filter,
  availableCompanies,
  availableCities,
  availableCategories,
  onFilterChange,
  onReset,
}: FilterPanelProps) {
  const hasActiveFilters =
    filter.companies.length > 0 ||
    filter.cities.length > 0 ||
    filter.categories.length > 0 ||
    filter.type !== 'all';

  const handleMultiSelect = (field: 'companies' | 'cities' | 'categories', value: string) => {
    const current = filter[field];
    const next = current.includes(value)
      ? current.filter((v) => v !== value)
      : [...current, value];
    onFilterChange({ [field]: next, page: 1 });
  };

  return (
    <div className="filter-panel">
      <select
        className="filter-select"
        value={filter.type}
        onChange={(e) =>
          onFilterChange({ type: e.target.value as FilterState['type'], page: 1 })
        }
        aria-label="招聘类型"
      >
        <option value="all">全部类型</option>
        <option value="campus">校招</option>
        <option value="intern">实习</option>
      </select>

      <select
        className="filter-select"
        value=""
        onChange={(e) => {
          if (e.target.value) handleMultiSelect('companies', e.target.value);
        }}
        aria-label="选择公司"
      >
        <option value="">公司（可多选）</option>
        {availableCompanies.map((c) => (
          <option key={c} value={c} disabled={filter.companies.includes(c)}>
            {c} {filter.companies.includes(c) ? '✓' : ''}
          </option>
        ))}
      </select>

      <select
        className="filter-select"
        value=""
        onChange={(e) => {
          if (e.target.value) handleMultiSelect('cities', e.target.value);
        }}
        aria-label="选择城市"
      >
        <option value="">城市（可多选）</option>
        {availableCities.map((c) => (
          <option key={c} value={c} disabled={filter.cities.includes(c)}>
            {c} {filter.cities.includes(c) ? '✓' : ''}
          </option>
        ))}
      </select>

      <div className="filter-chip-group">
        {JOB_CATEGORIES.filter((c) => availableCategories.includes(c)).map((cat) => (
          <button
            key={cat}
            className={`filter-chip${filter.categories.includes(cat) ? ' active' : ''}`}
            onClick={() => handleMultiSelect('categories', cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      {hasActiveFilters && (
        <button className="filter-reset" onClick={onReset}>
          清除筛选
        </button>
      )}
    </div>
  );
}
