#!/usr/bin/env python3
"""
拉勾网数据源 —— 搜索产品类校招职位

使用拉勾公开搜索接口，无需登录即可获取职位列表。
端点: POST https://www.lagou.com/jobs/positionAjax.json?city={city}&needAddtionalResult=false
"""
import json
import urllib.request
import urllib.parse
import http.cookiejar
import time
import random
from typing import Any

from . import build_job, normalize_city, TIER1_CITIES, PRODUCT_KEYWORDS

# 拉勾搜索关键词（产品类）
SEARCH_KEYWORDS = [
    "产品经理 校招",
    "产品经理 应届",
    "产品 校招",
    "产品策划 校招",
    "AI产品 校招",
    "数据产品 校招",
]

# Cookie 管理器（先访问首页获取 cookie）
cookie_jar = http.cookiejar.CookieJar()
cookie_handler = urllib.request.HTTPCookieProcessor(cookie_jar)
lagou_opener = urllib.request.build_opener(cookie_handler)

BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def lagou_init_session():
    """初始化拉勾会话：访问首页获取必要 cookie"""
    try:
        req = urllib.request.Request(
            "https://www.lagou.com/",
            headers={**BASE_HEADERS, "Accept": "text/html,application/xhtml+xml"},
        )
        lagou_opener.open(req, timeout=15)
        # 再访问搜索页面以获取 X-Anit-Forge-Token
        search_page_url = "https://www.lagou.com/jobs/list_%E4%BA%A7%E5%93%81%E7%BB%8F%E7%90%86"
        req2 = urllib.request.Request(
            search_page_url,
            headers={**BASE_HEADERS, "Accept": "text/html,application/xhtml+xml"},
        )
        lagou_opener.open(req2, timeout=15)
        return True
    except Exception as e:
        print(f"    [WARN] Lagou session init failed: {e}")
        return False


def search_lagou(keyword: str, city: str, page: int = 1) -> dict[str, Any] | None:
    """搜索拉勾职位"""
    encoded_city = urllib.parse.quote(city)
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://www.lagou.com/jobs/positionAjax.json?city={encoded_city}&needAddtionalResult=false"

    payload = f"first=false&pn={page}&kd={keyword}"

    headers = {
        **BASE_HEADERS,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "X-Anit-Forge-Code": "0",
        "X-Anit-Forge-Token": "None",
        "Referer": f"https://www.lagou.com/jobs/list_{encoded_keyword}",
        "Origin": "https://www.lagou.com",
    }

    req = urllib.request.Request(
        url,
        data=payload.encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        resp = lagou_opener.open(req, timeout=20)
        raw = resp.read().decode("utf-8")
        # 检查是否为 JSON
        if raw.strip().startswith("{"):
            return json.loads(raw)
        else:
            # HTML 响应 → 被反爬拦截
            if len(raw) < 200:
                print(f"    [WARN] Lagou blocked ({keyword}/{city}): {raw[:100]}")
            else:
                print(f"    [WARN] Lagou returned HTML instead of JSON (blocked)")
            return None
    except json.JSONDecodeError:
        print(f"    [WARN] Lagou invalid JSON response ({keyword}/{city})")
        return None
    except Exception as e:
        print(f"    [WARN] Lagou search error ({keyword}/{city}/p{page}): {e}")
        return None


def parse_lagou_result(data: dict[str, Any] | None) -> list[dict[str, Any]]:
    """解析拉勾搜索结果"""
    jobs = []
    if not data:
        return jobs

    try:
        content = data.get("content", {})
        result = content.get("positionResult", {})
        position_list = result.get("result", [])
    except (AttributeError, KeyError, TypeError):
        return jobs

    for pos in position_list:
        if not isinstance(pos, dict):
            continue

        title = pos.get("positionName", "")

        # 检查是否为校招/应届岗位
        work_year = pos.get("workYear", "")
        is_campus = any(kw in work_year for kw in ["应届", "在校", "校招"])
        # 拉勾的校招通常标记为"应届毕业生"或空
        if not is_campus and work_year and "应届" not in work_year and work_year != "在校生":
            continue

        # 薪资解析
        salary_raw = pos.get("salary", "")
        # 拉勾格式: "20k-40k"
        salary = salary_raw if salary_raw else "面议"

        city = pos.get("city", "")
        district = pos.get("district", "")
        location = city
        if district:
            location = f"{city}-{district}"

        company_name = pos.get("companyFullName", "") or pos.get("companyShortName", "")
        company_size = pos.get("companySize", "")
        industry = pos.get("industryField", "")

        education = pos.get("education", "本科及以上")
        if not education:
            education = "本科及以上"

        position_id = pos.get("positionId", "")
        apply_url = f"https://www.lagou.com/wn/jobs/{position_id}.html" if position_id else ""

        # 过滤：只保留产品相关职位
        is_product = any(kw in title for kw in ["产品", "产品经理", "产品策划", "产品运营", "产品设计"])
        if not is_product:
            continue

        # 发布时间
        create_time = pos.get("createTime", "")

        job = build_job(
            title=title,
            company=company_name,
            city=city,
            salary=salary,
            source="lagou",
            apply_url=apply_url,
            education=education,
            industry=industry or "互联网",
            posted_at=create_time,
            job_id=f"lagou-{position_id}",
        )
        jobs.append(job)

    return jobs


def scrape(verbose: bool = True) -> list[dict[str, Any]]:
    """主入口：从拉勾搜索产品类校招职位"""
    all_jobs: list[dict[str, Any]] = []

    if verbose:
        print(f"  [拉勾] 搜索城市: {TIER1_CITIES}")

    # 初始化 Cookie 会话
    if verbose:
        print(f"    初始化浏览器会话...", end=" ", flush=True)
    session_ok = lagou_init_session()
    if verbose:
        print(f"{'✅' if session_ok else '❌'}")

    if not session_ok:
        if verbose:
            print(f"  [拉勾] 会话初始化失败，跳过")
        return []

    keyword = "产品经理"  # 主关键词
    for city in TIER1_CITIES:
        if verbose:
            print(f"    搜索 {city}...", end=" ", flush=True)
        try:
            # 只取第1页
            data = search_lagou(keyword, city, page=1)
            jobs = parse_lagou_result(data)
            all_jobs.extend(jobs)
            if verbose:
                print(f"✅ {len(jobs)} 个职位")
        except Exception as e:
            if verbose:
                print(f"❌ {e}")

        # 礼貌延迟
        time.sleep(random.uniform(1.5, 3.0))

    # 补充搜索其他关键词
    for extra_kw in ["产品 校招", "产品策划 应届"]:
        try:
            data = search_lagou(extra_kw, "北京", page=1)
            jobs = parse_lagou_result(data)
            # 去重
            existing_keys = {(j["title"], j["company"]) for j in all_jobs}
            for j in jobs:
                key = (j["title"], j["company"])
                if key not in existing_keys:
                    all_jobs.append(j)
                    existing_keys.add(key)
            if verbose and jobs:
                print(f"    [拉勾] 关键词 '{extra_kw}' 补充 {len([j for j in jobs if (j['title'], j['company']) not in existing_keys])} 个")
        except Exception:
            pass
        time.sleep(random.uniform(1.0, 2.0))

    if verbose:
        print(f"  [拉勾] 共获取 {len(all_jobs)} 个产品类校招职位")

    return all_jobs
