#!/usr/bin/env python3
"""
猎聘网数据源 —— 从猎聘校园招聘平台获取产品类校招职位

来源: https://campus.liepin.com/
使用猎聘公开 API 搜索产品类校招职位
"""
import json
import time
import random
import urllib.request
from typing import Any

from . import build_job, fetch_json, TIER1_CITIES

# 猎聘搜索 API（web 前端使用的开放接口）
SEARCH_URL = "https://api-c.liepin.com/api/com.liepin.searchfront4c.pc-search-job"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Origin": "https://www.liepin.com",
    "Referer": "https://www.liepin.com/zhaopin/",
}

# 猎聘城市代码
CITY_CODES = {
    "北京": "010",
    "上海": "020",
    "广州": "030",
    "深圳": "040",
}


def search_liepin(keyword: str, city_code: str, page: int = 1) -> list[dict[str, Any]]:
    """搜索猎聘职位"""
    import urllib.parse
    params = (
        f"key={urllib.parse.quote(keyword)}"
        f"&city={city_code}"
        f"&pageNum={page}"
        f"&pageSize=40"
        f"&dq=应届生"
        f"&pubTime="
        f"&workLevel="
        f"&salary="
        f"&compIds="
        f"&industry="
        f"&position="
        f"&compTag="
    )
    url = f"{SEARCH_URL}?{params}"

    data = fetch_json(url, headers=HEADERS)
    if not data:
        return []

    jobs = []
    try:
        card_list = data.get("data", {}).get("cardList", [])
    except (AttributeError, KeyError, TypeError):
        return jobs

    for card in card_list:
        if not isinstance(card, dict):
            continue
        job_info = card.get("job", {})
        if not job_info:
            continue

        title = job_info.get("title", "")
        # 只保留产品类职位
        if not any(kw in title for kw in ["产品", "产品经理", "产品策划", "产品运营"]):
            continue

        company_name = job_info.get("company", {}).get("name", "")
        city = job_info.get("city", {}).get("name", "")
        salary = job_info.get("salary", "")
        education = job_info.get("eduLevel", {}).get("name", "本科及以上")

        # 检查是否为校招
        job_type = job_info.get("jobType", {})
        if isinstance(job_type, dict):
            type_name = job_type.get("name", "")
        else:
            type_name = str(job_type) if job_type else ""

        is_campus = any(kw in type_name for kw in ["校招", "应届", "校园"])
        if not is_campus:
            continue

        create_time = job_info.get("createTime", "")
        position_id = job_info.get("positionId", "")
        apply_url = f"https://www.liepin.com/job/{position_id}.html" if position_id else ""

        description = job_info.get("jobDesc", "")

        job = build_job(
            title=title,
            company=company_name,
            city=city,
            salary=salary,
            source="liepin",
            apply_url=apply_url,
            description=description,
            education=education,
            posted_at=create_time,
            job_id=f"liepin-{position_id}",
        )
        jobs.append(job)

    return jobs


def scrape(verbose: bool = True) -> list[dict[str, Any]]:
    """主入口：从猎聘搜索产品类校招职位"""
    all_jobs: list[dict[str, Any]] = []

    keywords = ["产品经理", "产品策划", "AI产品"]

    if verbose:
        print(f"  [猎聘] 搜索城市: {list(CITY_CODES.keys())}")
        print(f"  [猎聘] 关键词: {keywords}")

    for keyword in keywords:
        for city_name, city_code in CITY_CODES.items():
            if verbose:
                print(f"    搜索 {city_name} 关键词 '{keyword}'...", end=" ", flush=True)
            try:
                jobs = search_liepin(keyword, city_code, page=1)
                all_jobs.extend(jobs)
                if verbose:
                    print(f"✅ {len(jobs)} 个职位")
            except Exception as e:
                if verbose:
                    print(f"❌ {e}")
            # 礼貌延迟
            time.sleep(random.uniform(1.0, 2.0))

    if verbose:
        print(f"  [猎聘] 共获取 {len(all_jobs)} 个产品类校招职位")

    return all_jobs
