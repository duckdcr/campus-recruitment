#!/usr/bin/env python3
"""
校招数据采集 - 共享工具模块
"""
import json
import re
import sys
import os
import urllib.request
import urllib.error
import ssl
from datetime import datetime, timezone
from typing import Any

ctx = ssl.create_default_context()

# 产品类职位关键词
PRODUCT_KEYWORDS = [
    "产品", "产品经理", "产品策划", "产品运营", "产品设计师",
    "策略产品", "AI产品", "数据产品", "商业化产品", "增长产品",
    "产品实习生", "产品管培生", "产品助理", "产品专家",
    "产品负责人", "产品总监", "电商产品", "后台产品", "B端产品",
    "C端产品", "平台产品", "搜索产品", "推荐产品", "广告产品",
]

# 一线城市列表
TIER1_CITIES = ["北京", "上海", "广州", "深圳"]

# 城市别名映射
CITY_ALIASES = {
    "北京市": "北京",
    "上海": "上海",
    "上海市": "上海",
    "广州": "广州",
    "广州市": "广州",
    "深圳": "深圳",
    "深圳市": "深圳",
    "beijing": "北京",
    "shanghai": "上海",
    "guangzhou": "广州",
    "shenzhen": "深圳",
}

# 职位分类关键词
CATEGORY_KEYWORDS = {
    "产品": ["产品", "产品经理", "产品策划", "产品运营", "策略产品", "AI产品", "数据产品", "UED"],
    "技术": ["开发", "工程师", "算法", "前端", "后端", "全栈", "测试", "运维", "数据", "研发", "技术"],
    "运营": ["运营", "新媒体", "内容", "用户运营", "社区运营", "活动运营"],
    "设计": ["设计", "UI", "UX", "交互", "视觉", "平面"],
    "市场": ["市场", "营销", "商务", "品牌", "公关", "广告", "销售"],
    "职能": ["HR", "人力", "行政", "财务", "法务", "战略", "投资", "管培"],
}


def fetch_json(url: str, timeout: int = 15, headers: dict | None = None) -> dict[str, Any] | list[Any] | None:
    """获取 JSON 数据"""
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    if headers:
        default_headers.update(headers)
    req = urllib.request.Request(url, headers=default_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [WARN] Failed to fetch {url[:80]}: {e}")
        return None


def fetch_text(url: str, timeout: int = 15, headers: dict | None = None) -> str | None:
    """获取文本内容"""
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    if headers:
        default_headers.update(headers)
    req = urllib.request.Request(url, headers=default_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"  [WARN] Failed to fetch text from {url[:80]}: {e}")
        return None


def clean_html(html: str | None) -> str:
    """去除 HTML 标签，安全处理 None 输入"""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_city(city: str) -> str:
    """统一城市名称"""
    city = city.strip()
    for alias, standard in CITY_ALIASES.items():
        if alias.lower() == city.lower() or alias == city:
            return standard
    # 如果包含常见城市名，提取
    for standard in TIER1_CITIES:
        if standard in city:
            return standard
    return city


def detect_category(title: str) -> str:
    """根据职位名称检测分类"""
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in title:
                return category
    return "其他"


def is_product_position(title: str) -> bool:
    """检查是否为产品类职位"""
    title_lower = title.lower()
    for kw in PRODUCT_KEYWORDS:
        if kw.lower() in title_lower:
            return True
    return False


def build_job(
    title: str,
    company: str,
    city: str,
    salary: str,
    source: str,
    apply_url: str = "",
    description: str = "",
    education: str = "本科及以上",
    experience: str = "应届",
    category: str | None = None,
    posted_at: str = "",
    deadline: str = "",
    requirements: list[str] | None = None,
    tags: list[str] | None = None,
    job_id: str = "",
    industry: str = "互联网",
    company_logo: str = "",
    job_type: str = "campus",
    featured: bool = False,
) -> dict[str, Any]:
    """构建标准化的职位对象"""
    if not category:
        category = detect_category(title)
    if is_product_position(title):
        category = "产品"

    if not tags:
        tags = ["校招"]
    if category:
        tags.append(category)
    if company:
        tags.append(company)
    tags = list(set(tags))

    if not job_id:
        import hashlib
        raw = f"{source}-{company}-{title}-{city}"
        job_id = hashlib.md5(raw.encode()).hexdigest()[:12]

    if not posted_at:
        posted_at = datetime.now(timezone.utc).isoformat()

    if not requirements:
        requirements = _parse_requirements(description)

    return {
        "id": job_id,
        "title": title,
        "company": company,
        "companyLogo": company_logo,
        "industry": industry,
        "city": normalize_city(city),
        "location": normalize_city(city),
        "salary": salary,
        "education": education,
        "experience": experience,
        "category": category,
        "postedAt": posted_at,
        "deadline": deadline,
        "description": description[:1000] if description else "",
        "requirements": requirements[:8],
        "applyUrl": apply_url,
        "source": source,
        "type": job_type,
        "tags": tags,
        "featured": featured,
    }


def _parse_requirements(description: str) -> list[str]:
    """从职位描述中提取任职要求"""
    lines = description.split("\n")
    reqs = []
    in_req_section = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(kw in line for kw in ["任职要求", "岗位要求", "职位要求", "我们需要", "希望你"]):
            in_req_section = True
            continue
        if any(kw in line for kw in ["工作内容", "岗位职责", "职位描述", "关于我们"]):
            in_req_section = False
            continue
        if in_req_section and len(line) > 4:
            reqs.append(line.strip("·•-*").strip())
    if not reqs:
        for line in lines:
            line = line.strip()
            if any(kw in line for kw in ["学历", "专业", "经验", "能力", "熟悉", "掌握", "负责"]):
                reqs.append(line.strip("·•-*").strip()[:120])
    return reqs[:8]


def save_jobs(jobs: list[dict[str, Any]], output_path: str) -> int:
    """保存职位数据到 JSON 文件"""
    # 去重
    seen = set()
    unique_jobs = []
    for j in jobs:
        key = (j["title"], j["company"], j["city"])
        if key not in seen:
            seen.add(key)
            unique_jobs.append(j)

    # 按发布时间排序
    unique_jobs.sort(key=lambda j: j.get("postedAt", ""), reverse=True)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique_jobs, f, ensure_ascii=False, indent=2)

    return len(unique_jobs)
