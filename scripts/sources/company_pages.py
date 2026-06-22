#!/usr/bin/env python3
"""
企业官网直采数据源 —— 直接从大型公司招聘官网获取产品类校招职位

使用 requests + BeautifulSoup4 解析公司招聘页面。
优先尝试已知的 API 端点，失败时回退到 HTML 页面解析。

注意：许多大厂的招聘页面是 SPA（单页应用），数据通过 XHR 动态加载。
      本模块尽力从各渠道获取数据，但不保证覆盖所有公司。
"""
import json
import re
import time
import random
from typing import Any
from datetime import datetime, timezone

from . import build_job, TIER1_CITIES, PRODUCT_KEYWORDS

# ── 尝试使用 requests + BeautifulSoup ──
def _try_import_bs4():
    """尝试导入 BeautifulSoup，失败时返回 None"""
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup
    except ImportError:
        return None


def _fetch_soup(url: str, timeout: int = 15) -> Any | None:
    """获取页面并用 BeautifulSoup 解析"""
    BeautifulSoup = _try_import_bs4()
    if not BeautifulSoup:
        return None
    try:
        import urllib.request
        ctx = __import__('ssl').create_default_context()
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        html = resp.read().decode("utf-8", errors="replace")
        return BeautifulSoup(html, "html.parser")
    except Exception:
        return None


def _extract_json_from_script(soup: Any, pattern_id: str = "__NEXT_DATA__") -> dict | None:
    """从页面 script 标签中提取 JSON 数据"""
    if not soup:
        return None
    script = soup.find("script", id=pattern_id)
    if script and script.string:
        try:
            return json.loads(script.string)
        except json.JSONDecodeError:
            pass
    # Try regex for __NUXT__ or INITIAL_STATE
    for pattern in [
        r'<script>window\.__NUXT__\s*=\s*({.*?})</script>',
        r'<script>window\.__INITIAL_STATE__\s*=\s*({.*?})</script>',
        r'<script id="__NEXT_DATA__"[^>]*>({.*?})</script>',
    ]:
        import re as re_mod
        match = re_mod.search(pattern, str(soup), re_mod.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    return None


def _scrape_page_by_selectors(url: str, selectors: dict[str, str],
                               base_url: str = "",
                               is_product_only: bool = True,
                               campus_keywords: list[str] | None = None) -> list[dict[str, Any]]:
    """
    通用页面解析器：从 HTML 页面中通过 CSS 选择器提取职位信息

    selectors: {
        "container": ".job-list li, .position-item",
        "title": "h3, .title, .name",
        "company": ".company, .company-name",
        "city": ".city, .location",
        "salary": ".salary, .price",
        "link": "a[href]",
    }
    """
    jobs = []
    BeautifulSoup = _try_import_bs4()
    if not BeautifulSoup:
        return jobs

    soup = _fetch_soup(url)
    if not soup:
        return jobs

    containers = soup.select(selectors.get("container", "li, .item, tr"))

    if campus_keywords is None:
        campus_keywords = ["校招", "应届", "校园", "2026", "2025", "graduate", "campus"]

    for item in containers:
        try:
            title_el = item.select_one(selectors.get("title", "h3, .title")) if selectors.get("title") else None
            company_el = item.select_one(selectors.get("company", ".company")) if selectors.get("company") else None
            city_el = item.select_one(selectors.get("city", ".city, .location")) if selectors.get("city") else None
            salary_el = item.select_one(selectors.get("salary", ".salary")) if selectors.get("salary") else None
            link_el = item.select_one(selectors.get("link", "a[href]")) if selectors.get("link") else None

            title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else ""
            city_text = city_el.get_text(strip=True) if city_el else "北京"
            salary = salary_el.get_text(strip=True) if salary_el else "面议"

            if not title or not company:
                continue

            if is_product_only:
                if not any(kw in title for kw in PRODUCT_KEYWORDS):
                    continue

            item_text = item.get_text()
            is_campus = any(kw in item_text for kw in campus_keywords)
            if not is_campus:
                continue

            link = ""
            if link_el:
                link = link_el.get("href", "")
                if link and not link.startswith("http") and base_url:
                    link = base_url.rstrip("/") + "/" + link.lstrip("/")

            job = build_job(
                title=title,
                company=company,
                city=city_text,
                salary=salary,
                source="company_page",
                apply_url=link,
            )
            jobs.append(job)
        except Exception:
            continue

    return jobs


# ── 各公司采集函数 ──

def scrape_jd_direct(verbose: bool) -> list[dict[str, Any]]:
    """京东 - 从校招页面解析职位"""
    jobs = []
    try:
        from . import fetch_json
        # 尝试不同 API 端点
        endpoints = [
            ("https://campus.jd.com/api/v1/position/list", None),
            ("https://campus.jd.com/api/position/list", None),
        ]
        data = None
        for url, params in endpoints:
            data = fetch_json(url)
            if data and data.get("body"):
                break

        if not data:
            # 回退到页面解析
            return _scrape_page_by_selectors(
                "https://campus.jd.com/",
                {
                    "container": ".position-item, .recruit-item, .job-item, tr",
                    "title": "h3, .title, .job-name",
                    "city": ".city, .location",
                },
                base_url="https://campus.jd.com",
            )

        body = data.get("body", {})
        if isinstance(body, dict) and "code" in body:
            # API 返回 code 而非列表，尝试其他方式
            if verbose:
                print("      京东 API 返回 code，尝试页面解析")
            return _scrape_page_by_selectors(
                "https://campus.jd.com/",
                {
                    "container": ".position-item, .recruit-item, .job-item, .list-item",
                    "title": "h3, .title, .job-name, .name",
                    "city": ".city, .location, .place",
                },
                base_url="https://campus.jd.com",
            )

        position_list = []
        if isinstance(body, list):
            position_list = body
        elif isinstance(body, dict):
            for key in ["positions", "list", "items", "data"]:
                if key in body and isinstance(body[key], list):
                    position_list = body[key]
                    break

        for pos in position_list:
            if not isinstance(pos, dict):
                continue
            title = pos.get("name") or pos.get("title") or pos.get("positionName") or ""
            if not any(kw in title for kw in PRODUCT_KEYWORDS):
                continue
            city = pos.get("city") or pos.get("workCity") or pos.get("workPlace") or pos.get("place") or ""
            if not any(c in city for c in TIER1_CITIES):
                continue

            job = build_job(
                title=title,
                company="京东",
                city=city,
                salary=pos.get("salary", "面议"),
                source="jd",
                apply_url="https://campus.jd.com/",
                job_id=f"jd-{pos.get('id', '') or pos.get('positionId', '')}",
            )
            jobs.append(job)
    except Exception as e:
        if verbose:
            print(f"      京东采集失败: {e}")
    return jobs


def scrape_bytedance_page(verbose: bool) -> list[dict[str, Any]]:
    """字节跳动 - 从校招页面提取嵌入式数据"""
    jobs = []
    try:
        soup = _fetch_soup("https://jobs.bytedance.com/campus")
        if not soup:
            return jobs

        # 查找 __NEXT_DATA__
        data = _extract_json_from_script(soup, "__NEXT_DATA__")
        if not data:
            # 尝试从页面文本中查找职位信息
            page_text = str(soup)
            # 查找 JSON 块
            json_blocks = re.findall(r'\{[^{}]*"name"[^{}]*"city"[^{}]*\}', page_text)
            for block in json_blocks[:50]:
                try:
                    item = json.loads(block)
                    title = item.get("name", "")
                    if not any(kw in title for kw in PRODUCT_KEYWORDS):
                        continue
                    city = item.get("city", "")
                    if not any(c in city for c in TIER1_CITIES):
                        continue
                    job = build_job(
                        title=title,
                        company="字节跳动",
                        city=city,
                        salary=item.get("salary", "面议"),
                        source="bytedance",
                        apply_url=f"https://jobs.bytedance.com/campus",
                    )
                    jobs.append(job)
                except (json.JSONDecodeError, Exception):
                    continue
            return jobs

        # 从 __NEXT_DATA__ 中递归查找职位
        def _extract_positions(obj, depth=0):
            results = []
            if depth > 6:
                return results
            if isinstance(obj, dict):
                name = obj.get("name") or obj.get("title") or ""
                if name and ("产品" in name or "产品经理" in name):
                    city = obj.get("city") or obj.get("workPlace") or obj.get("location") or ""
                    if any(c in city for c in TIER1_CITIES):
                        results.append({
                            "title": name,
                            "city": city,
                            "salary": obj.get("salary", "面议"),
                            "id": obj.get("id", ""),
                        })
                for v in obj.values():
                    results.extend(_extract_positions(v, depth + 1))
            elif isinstance(obj, list):
                for item in obj:
                    results.extend(_extract_positions(item, depth + 1))
            return results

        positions = _extract_positions(data)
        for pos in positions:
            job = build_job(
                title=pos["title"],
                company="字节跳动",
                city=pos["city"],
                salary=pos["salary"],
                source="bytedance",
                apply_url="https://jobs.bytedance.com/campus",
            )
            jobs.append(job)
    except Exception as e:
        if verbose:
            print(f"      字节跳动采集失败: {e}")
    return jobs


def scrape_tencent_page(verbose: bool) -> list[dict[str, Any]]:
    """腾讯 - 从校招页面解析"""
    return _scrape_page_by_selectors(
        "https://join.qq.com/campus.html",
        {
            "container": ".position-item, .recruit-item, .job-item, tr, .list-item",
            "title": "h3, .title, .job-name, a",
            "city": ".city, .location, .place",
            "link": "a[href]",
        },
        base_url="https://join.qq.com",
    )


def scrape_baidu_page(verbose: bool) -> list[dict[str, Any]]:
    """百度 - 从校招页面解析"""
    return _scrape_page_by_selectors(
        "https://talent.baidu.com/campus",
        {
            "container": ".position-item, .recruit-item, .job-item, .list-item, .card",
            "title": "h3, .title, .job-name, .name",
            "city": ".city, .location, .place",
        },
        base_url="https://talent.baidu.com",
    )


def scrape_alibaba_page(verbose: bool) -> list[dict[str, Any]]:
    """阿里巴巴 - 从校招页面解析"""
    return _scrape_page_by_selectors(
        "https://talent.alibaba.com/campus",
        {
            "container": ".position-item, .job-item, .list-item, .card, .ant-card",
            "title": "h3, .title, .job-name, .name",
            "city": ".city, .location, .place",
        },
        base_url="https://talent.alibaba.com",
    )


def scrape_netease_page(verbose: bool) -> list[dict[str, Any]]:
    """网易 - 从校招页面解析"""
    return _scrape_page_by_selectors(
        "https://campus.163.com/",
        {
            "container": ".position-item, .job-item, .list-item, tr, .recruit-list li",
            "title": "h3, .title, .job-name, a",
            "city": ".city, .location, span",
        },
        base_url="https://campus.163.com",
    )


def scrape_huawei_page(verbose: bool) -> list[dict[str, Any]]:
    """华为 - 从校招页面解析"""
    return _scrape_page_by_selectors(
        "https://career.huawei.com/campus",
        {
            "container": ".position-item, .job-item, .list-item, .card, .recruit-item",
            "title": "h3, .title, .job-name, .name",
            "city": ".city, .location, .place",
        },
        base_url="https://career.huawei.com",
    )


# ── 采集器注册表 ──
COMPANY_SCRAPERS: list[dict[str, Any]] = [
    {"name": "京东", "func": scrape_jd_direct},
    {"name": "字节跳动", "func": scrape_bytedance_page},
    {"name": "腾讯", "func": scrape_tencent_page},
    {"name": "百度", "func": scrape_baidu_page},
    {"name": "阿里巴巴", "func": scrape_alibaba_page},
    {"name": "网易", "func": scrape_netease_page},
    {"name": "华为", "func": scrape_huawei_page},
]


def scrape(verbose: bool = True) -> list[dict[str, Any]]:
    """主入口：从各大公司自有招聘系统采集产品类校招职位"""
    all_jobs: list[dict[str, Any]] = []

    if verbose:
        print(f"  [企业官网] 配置公司数: {len(COMPANY_SCRAPERS)}")

    for scraper_def in COMPANY_SCRAPERS:
        name = scraper_def["name"]
        func = scraper_def["func"]
        if verbose:
            print(f"    正在获取 {name}...", end=" ", flush=True)
        try:
            jobs = func(verbose)
            all_jobs.extend(jobs)
            if verbose:
                print(f"{'✅' if jobs else '⚠️'} {len(jobs)} 个职位")
        except Exception as e:
            if verbose:
                print(f"❌ {e}")
        time.sleep(random.uniform(0.5, 1.5))

    # 去重
    seen = set()
    unique = []
    for j in all_jobs:
        key = (j["title"], j["company"], j["city"])
        if key not in seen:
            seen.add(key)
            unique.append(j)

    if verbose:
        print(f"  [企业官网] 共获取 {len(unique)} 个产品类校招职位")

    return unique
