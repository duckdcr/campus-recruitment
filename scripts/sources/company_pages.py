#!/usr/bin/env python3
"""
企业官网直采数据源 —— 从大型公司自有招聘系统获取产品类校招职位

覆盖不使用 Moka 的大厂（腾讯、阿里、字节、百度、京东、华为、网易等）。
各公司招聘系统不同，需要分别适配。
"""
import json
import re
import time
import random
from typing import Any
from datetime import datetime, timezone

from . import build_job, fetch_json, fetch_text, clean_html, TIER1_CITIES, PRODUCT_KEYWORDS

# ── 公司自定义采集器配置 ──
# 每家公司可以有自己的采集函数
# 如果函数返回 None，则跳过

# ── 字节跳动 ──
def scrape_bytedance(verbose: bool) -> list[dict[str, Any]]:
    """字节跳动 - 使用飞书招聘 API"""
    jobs = []
    try:
        # 飞书招聘校招 API
        url = "https://jobs.bytedance.com/api/v1/campus/position/list"
        payload = {
            "limit": 50,
            "offset": 0,
            "job_category_ids": [],
            "keyword": "",
            "city_ids": [],
            "recruitment_type": "graduate",
        }
        data = fetch_json(url)
        if not data:
            return jobs

        positions = data.get("data", {}).get("list", []) if isinstance(data, dict) else []
        for pos in positions:
            if not isinstance(pos, dict):
                continue
            title = pos.get("name", "")
            city = pos.get("city", "")
            salary = pos.get("salary_range", "面议")
            education = pos.get("education", "本科及以上")

            is_product = any(kw in title for kw in PRODUCT_KEYWORDS)
            if not is_product:
                continue

            job = build_job(
                title=title,
                company="字节跳动",
                city=city,
                salary=salary,
                source="bytedance",
                apply_url=f"https://jobs.bytedance.com/campus/position/{pos.get('id', '')}/detail",
                education=education,
                job_id=f"bytedance-{pos.get('id', '')}",
            )
            jobs.append(job)
    except Exception as e:
        if verbose:
            print(f"      [ByteDance] {e}")
    return jobs


# ── 腾讯 ──
def scrape_tencent(verbose: bool) -> list[dict[str, Any]]:
    """腾讯 - 使用腾讯招聘 API"""
    jobs = []
    try:
        url = "https://join.qq.com/api/v1/campus/position/list"
        data = fetch_json(url, timeout=15)
        if not data:
            return jobs

        positions = data.get("data", {}).get("positions", []) if isinstance(data, dict) else []
        for pos in positions:
            if not isinstance(pos, dict):
                continue
            title = pos.get("name", "")
            city = pos.get("cityName", "")
            if not any(c in city for c in TIER1_CITIES):
                continue
            is_product = any(kw in title for kw in PRODUCT_KEYWORDS)
            if not is_product:
                continue

            job = build_job(
                title=title,
                company="腾讯",
                city=city,
                salary="面议",
                source="tencent",
                apply_url=f"https://join.qq.com/campus/position/{pos.get('id', '')}",
                job_id=f"tencent-{pos.get('id', '')}",
            )
            jobs.append(job)
    except Exception as e:
        if verbose:
            print(f"      [Tencent] {e}")
    return jobs


# ── 百度 ──
def scrape_baidu(verbose: bool) -> list[dict[str, Any]]:
    """百度 - 百度招聘 API"""
    jobs = []
    try:
        url = "https://talent.baidu.com/api/v1/campus/list"
        data = fetch_json(url, timeout=15)
        if not data:
            return jobs

        positions = data.get("data", {}).get("list", []) if isinstance(data, dict) else []
        for pos in positions:
            if not isinstance(pos, dict):
                continue
            title = pos.get("postName", "")
            city = pos.get("city", "")
            if not any(c in city for c in TIER1_CITIES):
                continue
            is_product = any(kw in title for kw in PRODUCT_KEYWORDS)
            if not is_product:
                continue

            job = build_job(
                title=title,
                company="百度",
                city=city,
                salary="面议",
                source="baidu",
                apply_url=pos.get("applyUrl", "https://talent.baidu.com/campus"),
                job_id=f"baidu-{pos.get('postId', '')}",
            )
            jobs.append(job)
    except Exception as e:
        if verbose:
            print(f"      [Baidu] {e}")
    return jobs


# ── 京东 ──
def scrape_jd(verbose: bool) -> list[dict[str, Any]]:
    """京东招聘"""
    jobs = []
    try:
        url = "https://campus.jd.com/api/v1/position/list"
        data = fetch_json(url, timeout=15)
        if not data:
            return jobs

        positions = data.get("data", []) if isinstance(data, dict) else data if isinstance(data, list) else []
        for pos in positions:
            if not isinstance(pos, dict):
                continue
            title = pos.get("name", "")
            city = pos.get("workCity", "")
            if not any(c in city for c in TIER1_CITIES):
                continue
            is_product = any(kw in title for kw in PRODUCT_KEYWORDS)
            if not is_product:
                continue
            job = build_job(
                title=title,
                company="京东",
                city=city,
                salary="面议",
                source="jd",
                apply_url="https://campus.jd.com/#/",
            )
            jobs.append(job)
    except Exception as e:
        if verbose:
            print(f"      [JD] {e}")
    return jobs


# ── 阿里巴巴 ──
def scrape_alibaba(verbose: bool) -> list[dict[str, Any]]:
    """阿里巴巴招聘"""
    jobs = []
    try:
        url = "https://talent.alibaba.com/api/campus/position/list"
        data = fetch_json(url, timeout=15)
        if not data:
            return jobs
        positions = data.get("data", {}).get("positions", []) if isinstance(data, dict) else []
        for pos in positions:
            if not isinstance(pos, dict):
                continue
            title = pos.get("name", "")
            city = pos.get("city", "")
            if not any(c in city for c in TIER1_CITIES):
                continue
            is_product = any(kw in title for kw in PRODUCT_KEYWORDS)
            if not is_product:
                continue
            job = build_job(
                title=title,
                company="阿里巴巴",
                city=city,
                salary="面议",
                source="alibaba",
                apply_url="https://talent.alibaba.com/campus",
            )
            jobs.append(job)
    except Exception as e:
        if verbose:
            print(f"      [Alibaba] {e}")
    return jobs


# ── 网易 ──
def scrape_netease(verbose: bool) -> list[dict[str, Any]]:
    """网易招聘"""
    jobs = []
    try:
        url = "https://campus.163.com/api/v1/position/list"
        data = fetch_json(url, timeout=15)
        if not data:
            return jobs
        positions = data.get("data", []) if isinstance(data, dict) else data if isinstance(data, list) else []
        for pos in positions:
            if not isinstance(pos, dict):
                continue
            title = pos.get("title", "")
            city = pos.get("city", "")
            if not any(c in city for c in TIER1_CITIES):
                continue
            is_product = any(kw in title for kw in PRODUCT_KEYWORDS)
            if not is_product:
                continue
            job = build_job(
                title=title,
                company="网易",
                city=city,
                salary="面议",
                source="netease",
                apply_url="https://campus.163.com/",
            )
            jobs.append(job)
    except Exception as e:
        if verbose:
            print(f"      [NetEase] {e}")
    return jobs


# ── 华为 ──
def scrape_huawei(verbose: bool) -> list[dict[str, Any]]:
    """华为招聘"""
    jobs = []
    try:
        url = "https://career.huawei.com/api/campus/v1/position/list"
        data = fetch_json(url, timeout=15)
        if not data:
            return jobs
        positions = data.get("data", {}).get("positions", []) if isinstance(data, dict) else []
        for pos in positions:
            if not isinstance(pos, dict):
                continue
            title = pos.get("name", "")
            city = pos.get("workplace", "")
            if not any(c in city for c in TIER1_CITIES):
                continue
            is_product = any(kw in title for kw in PRODUCT_KEYWORDS)
            if not is_product:
                continue
            job = build_job(
                title=title,
                company="华为",
                city=city,
                salary="面议",
                source="huawei",
                apply_url="https://career.huawei.com/campus",
            )
            jobs.append(job)
    except Exception as e:
        if verbose:
            print(f"      [Huawei] {e}")
    return jobs


# ── 采集器注册表 ──
# 每家公司对应一个采集函数
COMPANY_SCRAPERS: list[dict[str, Any]] = [
    {"name": "字节跳动", "func": scrape_bytedance},
    {"name": "腾讯", "func": scrape_tencent},
    {"name": "百度", "func": scrape_baidu},
    {"name": "京东", "func": scrape_jd},
    {"name": "阿里巴巴", "func": scrape_alibaba},
    {"name": "网易", "func": scrape_netease},
    {"name": "华为", "func": scrape_huawei},
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
                print(f"✅ {len(jobs)} 个职位")
        except Exception as e:
            if verbose:
                print(f"❌ {e}")
        time.sleep(random.uniform(0.5, 1.5))

    if verbose:
        print(f"  [企业官网] 共获取 {len(all_jobs)} 个产品类校招职位")

    return all_jobs
