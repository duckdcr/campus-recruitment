export interface Job {
  id: string;
  /** 职位名称 */
  title: string;
  /** 公司名称 */
  company: string;
  /** 公司 Logo URL */
  companyLogo?: string;
  /** 公司行业 */
  industry: string;
  /** 工作城市 */
  city: string;
  /** 工作地点（详细） */
  location?: string;
  /** 薪资范围（展示用，如 "20K-35K"） */
  salary: string;
  /** 学历要求 */
  education: string;
  /** 经验要求 */
  experience: string;
  /** 职位类型：产品/技术/运营等 */
  category: string;
  /** 发布时间（ISO 字符串） */
  postedAt: string;
  /** 截止时间 */
  deadline?: string;
  /** 职位描述 */
  description: string;
  /** 职位要求 */
  requirements: string[];
  /** 投递链接 */
  applyUrl: string;
  /** 数据来源 */
  source: string;
  /** 招聘类型：校招/实习 */
  type: 'campus' | 'intern';
  /** 标签 */
  tags: string[];
  /** 是否紧急/推荐 */
  featured?: boolean;
}

export interface FilterState {
  /** 搜索关键词 */
  keyword: string;
  /** 选中的公司 */
  companies: string[];
  /** 选中的城市 */
  cities: string[];
  /** 职位分类 */
  categories: string[];
  /** 招聘类型 */
  type: 'all' | 'campus' | 'intern';
  /** 排序方式 */
  sortBy: 'latest' | 'salary' | 'company';
  /** 当前页码 */
  page: number;
  /** 每页条数 */
  pageSize: number;
}

export const DEFAULT_FILTER: FilterState = {
  keyword: '',
  companies: [],
  cities: [],
  categories: [],
  type: 'all',
  sortBy: 'latest',
  page: 1,
  pageSize: 20,
};

export const TIER_1_CITIES = ['北京', '上海', '广州', '深圳'];

export const JOB_CATEGORIES = ['产品', '技术', '运营', '设计', '市场', '销售', '职能'];
