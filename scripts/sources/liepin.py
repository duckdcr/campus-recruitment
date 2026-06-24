#!/usr/bin/env python3
"""
猎聘网数据源 —— 浏览器自动化搜索产品类校招职位

使用 Playwright 模拟浏览器访问猎聘校园招聘页面。
猎聘的 API 端点已变更，直接 HTTP 请求不可用，必须使用浏览器。

依赖: pip install playwright
首次运行: playwright install chromium
"""
import time
import random
import json
from typing import Any

from . import build_job, TIER1_CITIES


def search_playwright(keyword: str, city: str, max_pages: int = 3) -> list[dict[str, Any]]:
    """使用 Playwright 在猎聘搜索校招职位"""
    jobs = []
    browser = None
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
            )
            page = context.new_page()

            # 先访问校园招聘页面获取 cookie
            page.goto("https://campus.liepin.com/", wait_until="load", timeout=30000)
            time.sleep(2)

            # 搜索职位
            search_url = f"https://www.liepin.com/zhaopin/?key={keyword}&dq=应届生&city={city}"
            page.goto(search_url, wait_until="load", timeout=30000)
            time.sleep(3)

            for page_num in range(max_pages):
                # 等待页面加载
                try:
                    page.wait_for_selector(
                        ".job-list-item, .job-card, [class*='job-item'], .sojo-result, .job-list-box",
                        timeout=15000,
                    )
                except Exception:
                    pass

                # 提取职位卡片 - 尝试多个选择器
                items = page.query_selector_all(
                    ".job-card, .job-list-item, [class*='job-item'], "
                    ".result-list li, .job-list-box .job-item, "
                    "[class*='card'], [class*='position']"
                )

                # 尝试从页面获取嵌入的JSON数据
                try:
                    script_content = page.content()
                    import re
                    # 找 __NUXT__ 或 __NEXT_DATA__ 或 __INITIAL_STATE__
                    for pattern in [
                        r'<script>window\.__NUXT__\s*=\s*({.*?})</script>',
                        r'<script id="__NEXT_DATA__"[^>]*>({.*?})</script>',
                        r'<script>window\.__INITIAL_STATE__\s*=\s*({.*?})</script>',
                    ]:
                        match = re.search(pattern, script_content, re.DOTALL)
                        if match:
                            data = json.loads(match.group(1))
                            # Try to extract job listings from the state
                            job_list = _extract_from_state(data)
                            if job_list:
                                jobs.extend(job_list)
                                break
                except Exception:
                    pass

                # 如果没有从嵌入式数据找到，则从DOM提取
                if not jobs:
                    for item in items:
                        try:
                            title_el = item.query_selector(
                                "h3, .title, .job-name, [class*='title'], a[class*='title']"
                            )
                            company_el = item.query_selector(
                                ".company, .company-name, [class*='company'], a[class*='company']"
                            )
                            salary_el = item.query_selector(
                                ".salary, [class*='salary'], .price, .money"
                            )
                            city_el = item.query_selector(
                                ".city, .location, [class*='city'], [class*='location']"
                            )
                            link_el = item.query_selector("a[href]")

                            title = title_el.inner_text().strip() if title_el else ""
                            company = company_el.inner_text().strip() if company_el else ""
                            salary = salary_el.inner_text().strip() if salary_el else "面议"
                            city_text = city_el.inner_text().strip() if city_el else city
                            link = link_el.get_attribute("href") or "" if link_el else ""

                            if not title or not company:
                                continue

                            # 只保留产品类
                            if not any(kw in title for kw in ["产品", "产品经理", "产品策划", "产品运营"]):
                                continue

                            # 检查校招
                            item_text = item.inner_text()
                            is_campus = any(
                                kw in item_text for kw in ["校招", "应届", "校园", "graduate", "2026", "2025"]
                            )
                            if not is_campus:
                                continue

                            if link and not link.startswith("http"):
                                link = "https://www.liepin.com" + link

                            job = build_job(
                                title=title,
                                company=company,
                                city=city_text,
                                salary=salary,
                                source="liepin",
                                apply_url=link,
                            )
                            jobs.append(job)
                        except Exception:
                            continue

                # 翻页
                try:
                    next_btn = page.query_selector(
                        ".pagination-next, .next, a:has-text('下一页'), a:has-text('>')"
                    )
                    if next_btn and next_btn.is_enabled():
                        next_btn.click()
                        time.sleep(random.uniform(3, 5))
                        page.wait_for_load_state("load", timeout=15000)
                    else:
                        break
                except Exception:
                    break

    except ImportError:
        print("    [猎聘] ⚠️ Playwright 未安装，跳过 (pip install playwright && playwright install chromium)")
        return []
    except Exception as e:
        print(f"    [猎聘] 浏览器自动化错误: {e}")
    finally:
        if browser:
            try:
                browser.close()
            except Exception:
                pass

    return jobs


def _extract_from_state(data: dict) -> list[dict[str, Any]]:
    """从页面状态数据中递归查找职位列表"""
    jobs = []

    def _search(obj, depth=0):
        if depth > 5:
            return
        if isinstance(obj, dict):
            # Check if this dict looks like a job
            if "title" in obj and "company" in obj:
                jobs.append(obj)
            # Search in values
            for v in obj.values():
                _search(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                _search(item, depth + 1)

    _search(data)
    return jobs


def scrape(verbose: bool = True) -> list[dict[str, Any]]:
    """主入口：从猎聘搜索产品类校招职位"""
    all_jobs: list[dict[str, Any]] = []

    keywords = ["产品经理", "产品策划", "AI产品经理"]

    if verbose:
        print(f"  [猎聘] 使用浏览器自动化搜索校招职位")
        print(f"  [猎聘] 关键词: {keywords}")
        print(f"  [猎聘] 城市: {TIER1_CITIES[:4]}")

    for keyword in keywords:
        for city in TIER1_CITIES[:4]:  # 北上广深
            if verbose:
                print(f"    搜索 '{keyword}' @ {city}...", end=" ", flush=True)
            try:
                jobs = search_playwright(keyword, city, max_pages=2)
                all_jobs.extend(jobs)
                if verbose:
                    print(f"{'✅' if jobs else '⚠️'} {len(jobs)} 个职位")
            except Exception as e:
                if verbose:
                    print(f"❌ {e}")
            time.sleep(random.uniform(2, 4))

    # 去重
    seen = set()
    unique = []
    for j in all_jobs:
        key = (j["title"], j["company"], j["city"])
        if key not in seen:
            seen.add(key)
            unique.append(j)

    if verbose:
        print(f"  [猎聘] 共获取 {len(unique)} 个产品类校招职位")

    return unique
