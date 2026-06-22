import { useState, useEffect, useMemo, useCallback } from 'react';
import type { Job, FilterState } from '../types/job';
import { DEFAULT_FILTER } from '../types/job';
import { fetchJobs } from '../api/jobs';
import { extractSalaryMax, storage } from '../utils';

const STORAGE_KEY = 'campus-recruit-filter';

export function useJobs() {
  const [allJobs, setAllJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterState>(() => ({
    ...DEFAULT_FILTER,
    ...storage.get(STORAGE_KEY, {}),
  }));

  // 加载数据
  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    fetchJobs()
      .then((jobs) => {
        if (!cancelled) {
          setAllJobs(jobs);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  // 持久化筛选条件
  useEffect(() => {
    storage.set(STORAGE_KEY, filter);
  }, [filter]);

  // 提取可用的公司和城市列表（从全部数据）
  const availableCompanies = useMemo(() => {
    const set = new Set(allJobs.map((j) => j.company));
    return Array.from(set).sort();
  }, [allJobs]);

  const availableCities = useMemo(() => {
    const set = new Set(allJobs.map((j) => j.city));
    return Array.from(set).filter(Boolean).sort();
  }, [allJobs]);

  const availableCategories = useMemo(() => {
    const set = new Set(allJobs.map((j) => j.category));
    return Array.from(set).sort();
  }, [allJobs]);

  // 数据统计
  const stats = useMemo(() => {
    const totalCount = allJobs.length;
    const todayCount = allJobs.filter((j) => {
      const days = (Date.now() - new Date(j.postedAt).getTime()) / 86400000;
      return days <= 1;
    }).length;
    const companyCount = availableCompanies.length;
    return { totalCount, todayCount, companyCount };
  }, [allJobs, availableCompanies]);

  // 核心筛选逻辑
  const filteredJobs = useMemo(() => {
    let result = [...allJobs];

    // 关键词搜索
    if (filter.keyword.trim()) {
      const kw = filter.keyword.trim().toLowerCase();
      result = result.filter(
        (j) =>
          j.title.toLowerCase().includes(kw) ||
          j.company.toLowerCase().includes(kw) ||
          j.tags.some((t) => t.toLowerCase().includes(kw)) ||
          j.description.toLowerCase().includes(kw),
      );
    }

    // 公司筛选
    if (filter.companies.length > 0) {
      result = result.filter((j) => filter.companies.includes(j.company));
    }

    // 城市筛选
    if (filter.cities.length > 0) {
      result = result.filter((j) => filter.cities.includes(j.city));
    }

    // 职位分类
    if (filter.categories.length > 0) {
      result = result.filter((j) => filter.categories.includes(j.category));
    }

    // 招聘类型
    if (filter.type !== 'all') {
      result = result.filter((j) => j.type === filter.type);
    }

    // 排序
    switch (filter.sortBy) {
      case 'latest':
        result.sort((a, b) => new Date(b.postedAt).getTime() - new Date(a.postedAt).getTime());
        break;
      case 'salary':
        result.sort((a, b) => extractSalaryMax(b.salary) - extractSalaryMax(a.salary));
        break;
      case 'company':
        result.sort((a, b) => a.company.localeCompare(b.company));
        break;
    }

    return result;
  }, [allJobs, filter]);

  // 分页
  const totalPages = Math.max(1, Math.ceil(filteredJobs.length / filter.pageSize));
  const safePage = Math.min(filter.page, totalPages);

  const pagedJobs = useMemo(() => {
    const start = (safePage - 1) * filter.pageSize;
    return filteredJobs.slice(start, start + filter.pageSize);
  }, [filteredJobs, safePage, filter.pageSize]);

  // 更新筛选条件
  const updateFilter = useCallback((patch: Partial<FilterState>) => {
    setFilter((prev) => ({ ...prev, ...patch }));
  }, []);

  // 重置筛选条件
  const resetFilter = useCallback(() => {
    setFilter(DEFAULT_FILTER);
  }, []);

  // 设置页码（自动重置到第一页当筛选条件变化）
  const setPage = useCallback((page: number) => {
    setFilter((prev) => ({ ...prev, page }));
  }, []);

  // 搜索结果有变化时重置页码到1
  useEffect(() => {
    if (filter.page > totalPages) {
      setFilter((prev) => ({ ...prev, page: totalPages }));
    }
  }, [filteredJobs.length, filter.pageSize]);

  return {
    allJobs,
    filteredJobs,
    pagedJobs,
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
    currentPage: safePage,
  };
}
