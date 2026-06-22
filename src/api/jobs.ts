import type { Job } from '../types/job';

// 数据源配置：生产环境使用 public/data/campus-jobs.json（由 GitHub Actions 每日更新）
const DATA_URL = '/data/campus-jobs.json';

/**
 * 获取校招岗位列表
 * 优先从远程 JSON 获取，失败时使用内置样本数据
 */
export async function fetchJobs(): Promise<Job[]> {
  try {
    const res = await fetch(DATA_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data: Job[] = await res.json();
    if (Array.isArray(data) && data.length > 0) {
      return data;
    }
    throw new Error('Empty data');
  } catch (e) {
    console.warn('[jobs] Failed to fetch remote data, using sample data:', e);
    return getSampleJobs();
  }
}

// ─── 内置样本数据 ──────────────────────────────────────────────

export function getSampleJobs(): Job[] {
  // prettier-ignore
  const companies = [
    { name: '字节跳动', logo: '', industry: '互联网' },
    { name: '腾讯', logo: '', industry: '互联网' },
    { name: '阿里巴巴', logo: '', industry: '互联网' },
    { name: '美团', logo: '', industry: '互联网' },
    { name: '百度', logo: '', industry: '互联网' },
    { name: '网易', logo: '', industry: '互联网' },
    { name: '快手', logo: '', industry: '互联网' },
    { name: '京东', logo: '', industry: '互联网' },
    { name: '小红书', logo: '', industry: '互联网' },
    { name: '哔哩哔哩', logo: '', industry: '互联网' },
    { name: '拼多多', logo: '', industry: '互联网' },
    { name: '小米', logo: '', industry: '互联网' },
    { name: '华为', logo: '', industry: '互联网' },
    { name: '滴滴', logo: '', industry: '互联网' },
  ];

  const productTitles = [
    '产品经理（校招）',
    'AI产品经理',
    '产品运营专员',
    '策略产品经理',
    '用户产品经理',
    '增长产品经理',
    '数据产品经理',
    'B端产品经理',
    '电商产品经理',
    '社交产品经理',
    '内容产品经理',
    '商业化产品经理',
    '支付产品经理',
    '搜索产品经理',
    '推荐产品经理',
  ];

  const cities = ['北京', '上海', '深圳', '杭州', '广州'];
  const education = ['本科', '硕士', '本科及以上'];
  const tags = ['校招', '产品', '互联网'];

  const jobs: Job[] = [];

  for (let i = 0; i < 60; i++) {
    const company = companies[i % companies.length];
    const daysAgo = Math.floor(Math.random() * 30);
    const postedAt = new Date(Date.now() - daysAgo * 86400000).toISOString();
    const salaryBase = 15 + Math.floor(Math.random() * 25);
    const salaryMax = salaryBase + 5 + Math.floor(Math.random() * 10);

    jobs.push({
      id: `sample-${i}`,
      title: productTitles[i % productTitles.length],
      company: company.name,
      companyLogo: company.logo,
      industry: company.industry,
      city: cities[i % cities.length],
      location: cities[i % cities.length],
      salary: `${salaryBase}K-${salaryMax}K·14薪`,
      education: education[i % education.length],
      experience: '应届',
      category: '产品',
      postedAt,
      deadline: new Date(Date.now() + (30 - daysAgo) * 86400000).toISOString(),
      description: `负责${company.name}核心产品的规划与设计工作，深入理解用户需求，推动产品持续迭代优化。与工程、设计、运营等团队紧密协作，确保产品高效高质量交付。`,
      requirements: [
        '2026届应届毕业生，本科及以上学历',
        '对互联网产品有浓厚兴趣，有产品实习经验者优先',
        '具备优秀的逻辑思维能力和数据分析能力',
        '良好的跨团队协作能力和沟通表达能力',
        '有较强的用户洞察力和产品感',
      ],
      applyUrl: `https://${company.name.toLowerCase()}.zhaopin.com/campus`,
      source: 'sample',
      type: Math.random() > 0.8 ? 'intern' : 'campus',
      tags: [...tags, company.name],
      featured: Math.random() > 0.85,
    });
  }

  // Sort by postedAt desc
  return jobs.sort((a, b) => new Date(b.postedAt).getTime() - new Date(a.postedAt).getTime());
}
