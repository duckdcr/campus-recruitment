import { useState } from 'react';
import { Calendar, Building2, TrendingUp, AlertCircle } from 'lucide-react';
import { useJobs } from './hooks/useJobs';
import { Layout } from './components/Layout';
import { SearchBar } from './components/SearchBar';
import { FilterPanel } from './components/FilterPanel';
import { JobCard } from './components/JobCard';
import { JobDetailModal } from './components/JobDetailModal';
import { Pagination } from './components/Pagination';
import { EmptyState } from './components/EmptyState';
import { SubscriptionModal } from './components/SubscriptionModal';
import type { Job } from './types/job';

function App() {
  const {
    pagedJobs,
    filteredJobs,
    loading,
    error,
    filter,
    updateFilter,
    resetFilter,
    setPage,
    availableCompanies,
    availableCities,
    availableCategories,
    stats,
    totalPages,
    currentPage,
  } = useJobs();

  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [showSubscription, setShowSubscription] = useState(false);

  return (
    <Layout onOpenSubscription={() => setShowSubscription(true)}>
      {/* 数据概览 */}
      <div className="stats-bar">
        <div className="stat-item">
          <Calendar size={18} />
          <div>
            <div className="stat-value">{stats.todayCount}</div>
            <div className="stat-label">今日新增</div>
          </div>
        </div>
        <div className="stat-item">
          <TrendingUp size={18} />
          <div>
            <div className="stat-value">{stats.totalCount}</div>
            <div className="stat-label">在招职位</div>
          </div>
        </div>
        <div className="stat-item">
          <Building2 size={18} />
          <div>
            <div className="stat-value">{stats.companyCount}</div>
            <div className="stat-label">招聘企业</div>
          </div>
        </div>
      </div>

      {/* 搜索框 */}
      <SearchBar
        value={filter.keyword}
        onChange={(v) => updateFilter({ keyword: v, page: 1 })}
      />

      {/* 筛选面板 */}
      <FilterPanel
        filter={filter}
        availableCompanies={availableCompanies}
        availableCities={availableCities}
        availableCategories={availableCategories}
        onFilterChange={updateFilter}
        onReset={resetFilter}
      />

      {/* 排序与计数 */}
      <div className="sort-bar">
        <div className="sort-bar-count">
          共 <strong>{filteredJobs.length}</strong> 个职位
        </div>
        <div className="sort-buttons">
          <button
            className={`sort-btn${filter.sortBy === 'latest' ? ' active' : ''}`}
            onClick={() => updateFilter({ sortBy: 'latest' })}
          >
            最新发布
          </button>
          <button
            className={`sort-btn${filter.sortBy === 'salary' ? ' active' : ''}`}
            onClick={() => updateFilter({ sortBy: 'salary' })}
          >
            薪资最高
          </button>
          <button
            className={`sort-btn${filter.sortBy === 'company' ? ' active' : ''}`}
            onClick={() => updateFilter({ sortBy: 'company' })}
          >
            按公司
          </button>
        </div>
      </div>

      {/* 加载状态 */}
      {loading && (
        <div className="loading-state">
          <div className="loading-spinner" />
          <div className="loading-text">正在加载校招信息...</div>
        </div>
      )}

      {/* 错误状态 */}
      {error && !loading && (
        <div className="error-state">
          <AlertCircle size={48} style={{ color: 'var(--color-danger)', marginBottom: 16 }} />
          <h3 className="error-state-title">数据加载失败</h3>
          <p className="error-state-desc">{error}</p>
          <button className="btn btn-primary" onClick={() => window.location.reload()}>
            重新加载
          </button>
        </div>
      )}

      {/* 职位列表 */}
      {!loading && !error && (
        <>
          {pagedJobs.length > 0 ? (
            <>
              <div className="job-list">
                {pagedJobs.map((job) => (
                  <JobCard key={job.id} job={job} onClick={setSelectedJob} />
                ))}
              </div>

              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={setPage}
              />
            </>
          ) : (
            <EmptyState
              hasFilter={
                filter.keyword !== '' ||
                filter.companies.length > 0 ||
                filter.cities.length > 0 ||
                filter.categories.length > 0 ||
                filter.type !== 'all'
              }
              onReset={resetFilter}
            />
          )}
        </>
      )}

      {/* 职位详情弹窗 */}
      {selectedJob && (
        <JobDetailModal job={selectedJob} onClose={() => setSelectedJob(null)} />
      )}

      {/* 订阅弹窗 */}
      <SubscriptionModal
        isOpen={showSubscription}
        onClose={() => setShowSubscription(false)}
      />
    </Layout>
  );
}

export default App;
