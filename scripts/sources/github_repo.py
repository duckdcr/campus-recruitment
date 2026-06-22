#!/usr/bin/env python3
"""
GitHub 社区维护校招数据源 —— 从开源汇总仓库解析产品类校招岗位

来源:
- 0voice/2026-Computer-Spring-Recruitment-Job-Compilation
- namewyf/Campus2026
"""
import re
from typing import Any

from . import fetch_text, build_job, TIER1_CITIES, PRODUCT_KEYWORDS

# GitHub 原始内容地址
CURATED_REPOS = [
    {
        "name": "0voice/2026春招",
        "url": "https://raw.githubusercontent.com/0voice/2026-Computer-Spring-Recruitment-Job-Compilation/main/README.md",
        "industry": "互联网",
    },
    {
        "name": "Campus2026",
        "url": "https://raw.githubusercontent.com/namewyf/Campus2026/main/README.md",
        "industry": "互联网",
    },
]


def parse_markdown_table(md_content: str) -> list[dict[str, str]]:
    """解析 Markdown 表格中的职位信息"""
    rows = []

    # 匹配 markdown 表格行: | 内容 | 内容 | 内容 |
    table_pattern = re.compile(r"^\|(.+)\|$", re.MULTILINE)
    matches = table_pattern.findall(md_content)

    current_headers = []
    for i, match in enumerate(matches):
        cells = [c.strip() for c in match.split("|")]
        # 跳过表头分隔行 (|---|---|)
        if all(re.match(r"^[-:]+$", c.strip()) for c in cells if c.strip()):
            continue

        if i == 0 or not current_headers:
            # 表头行
            current_headers = cells
            continue

        # 数据行
        row = {}
        for idx, header in enumerate(current_headers):
            if idx < len(cells):
                row[header] = cells[idx]
            else:
                row[header] = ""
        if any(c for c in cells if c.strip()):  # 非空行
            rows.append(row)

    return rows


def is_campus_row(row: dict[str, str]) -> bool:
    """检查表格行是否为校招信息"""
    row_text = " ".join(row.values())
    keywords = ["校招", "应届", "校园", "25届", "26届", "2025", "2026", "campus", "graduate"]
    return any(kw in row_text.lower() for kw in keywords)


def is_product_row(row: dict[str, str]) -> bool:
    """检查表格行是否为产品类职位"""
    row_text = " ".join(row.values())
    return any(kw in row_text for kw in PRODUCT_KEYWORDS)


def extract_jobs_from_row(row: dict[str, str], repo_name: str) -> list[dict[str, Any]]:
    """从表格行中提取职位信息"""
    jobs = []
    row_text = " ".join(row.values())

    # 尝试提取公司名
    company = ""
    for key in ["公司", "企业", "Company", "company", "名称"]:
        if key in row:
            company = row[key]
            break

    if not company:
        # 从链接中提取
        link_match = re.search(r"\[(.+?)\]\(.+?\)", row_text)
        if link_match:
            company = link_match.group(1)

    if not company:
        return []

    # 尝试提取城市
    cities_found = [c for c in TIER1_CITIES if c in row_text]
    if not cities_found:
        cities_found = ["北京"]  # 默认

    # 尝试提取岗位名称
    title = ""
    for key in ["职位", "岗位", "Job", "job", "岗位名称", "Title", "title"]:
        if key in row:
            title = row[key]
            break

    # 尝试提取投递链接
    apply_url = ""
    link_pattern = re.compile(r"\[(.+?)\]\((.+?)\)")
    for match in link_pattern.finditer(row_text):
        url = match.group(2)
        if url.startswith("http"):
            apply_url = url
            break

    for city in cities_found:
        job_title = title if title else f"产品经理（校招）"
        job = build_job(
            title=job_title,
            company=company,
            city=city,
            salary="面议",
            source=f"github/{repo_name}",
            apply_url=apply_url,
            industry="互联网",
        )
        jobs.append(job)

    return jobs


def scrape(verbose: bool = True) -> list[dict[str, Any]]:
    """主入口：从 GitHub 社区维护的汇总仓库解析校招信息"""
    all_jobs: list[dict[str, Any]] = []

    for repo in CURATED_REPOS:
        if verbose:
            print(f"  [GitHub/{repo['name']}] 正在获取...", end=" ", flush=True)

        try:
            content = fetch_text(repo["url"], timeout=20)
            if not content:
                if verbose:
                    print("❌ 获取失败")
                continue

            rows = parse_markdown_table(content)
            if verbose:
                print(f"解析到 {len(rows)} 行表格数据")

            repo_jobs = []
            for row in rows:
                try:
                    jobs = extract_jobs_from_row(row, repo["name"])
                    repo_jobs.extend(jobs)
                except Exception:
                    continue

            all_jobs.extend(repo_jobs)
            if verbose:
                print(f"    → 提取 {len(repo_jobs)} 个职位")

        except Exception as e:
            if verbose:
                print(f"❌ {e}")

    if verbose:
        print(f"  [GitHub] 共获取 {len(all_jobs)} 个职位")

    return all_jobs
