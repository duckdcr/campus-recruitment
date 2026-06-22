#!/usr/bin/env python3
"""
拉勾网数据源 —— 浏览器自动化搜索产品类校招职位

使用 Playwright 模拟浏览器访问拉勾校园招聘页面。
由于拉勾有阿里云 WAF 保护，直接 HTTP 请求会被拦截，必须使用真实浏览器。

依赖: pip install playwright
首次运行: playwright install chromium
"""
import time
import random
import json
from datetime import datetime, timezone
from typing import Any

from . import build_job, TIER1_CITIES

# 拉勾校园招聘搜索URL
CAMPUS_SEARCH_URL = "https://xiaoyuan.lagou.com/search?"


def search_playwright(keyword: str, city: str, max_pages: int = 3) -> list[dict[str, Any]]:
    """使用 Playwright 在拉勾校园招聘搜索职位"""
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

            # 构建搜索URL
            params = f"keyword={keyword}&city={city}"
            url = CAMPUS_SEARCH_URL + params

            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(2)

            for page_num in range(max_pages):
                # 等待职位列表加载
                try:
                    page.wait_for_selector(".position-list__item, .job-card, .c-search-result", timeout=10000)
                except Exception:
                    pass  # try to parse whatever is on the page

                # 提取职位卡片
                items = page.query_selector_all(
                    ".position-list__item, .job-card, [class*='position'], [class*='job-item'], [class*='search-result-item']"
                )

                if not items:
                    # Try alternative selectors
                    items = page.query_selector_all("a[href*='position'], a[href*='job'], .list-item, tr")

                for item in items:
                    try:
                        title_el = item.query_selector("h3, .title, .job-title, [class*='title']")
                        company_el = item.query_selector(".company, .company-name, [class*='company']")
                        city_el = item.query_selector(".city, .location, [class*='city'], [class*='location']")
                        salary_el = item.query_selector(".salary, [class*='salary'], .money")
                        link_el = item.query_selector("a[href]")

                        title = title_el.inner_text().strip() if title_el else ""
                        company = company_el.inner_text().strip() if company_el else ""
                        city_text = city_el.inner_text().strip() if city_el else city
                        salary = salary_el.inner_text().strip() if salary_el else "面议"
                        link = link_el.get_attribute("href") or "" if link_el else ""

                        if not title or not company:
                            continue

                        # 只保留产品相关
                        if not any(kw in title for kw in ["产品", "产品经理", "产品策划", "产品运营"]):
                            continue

                        # 检查是否校招
                        item_text = item.inner_text()
                        is_campus = any(kw in item_text for kw in ["校招", "应届", " campus", "graduate", "2026", "2025"])
                        if not is_campus and "实习" in item_text:
                            continue

                        if link and not link.startswith("http"):
                            link = "https://xiaoyuan.lagou.com" + link

                        job = build_job(
                            title=title,
                            company=company,
                            city=city_text,
                            salary=salary,
                            source="lagou",
                            apply_url=link,
                        )
                        jobs.append(job)
                    except Exception:
                        continue

                # 翻页
                try:
                    next_btn = page.query_selector(".next, .pagination-next, a:has-text('下一页')")
                    if next_btn and next_btn.is_enabled():
                        next_btn.click()
                        time.sleep(random.uniform(2, 4))
                        page.wait_for_load_state("networkidle", timeout=15000)
                    else:
                        break
                except Exception:
                    break

    except ImportError:
        print("    [拉勾] ⚠️ Playwright 未安装，跳过 (pip install playwright && playwright install chromium)")
        return []
    except Exception as e:
        print(f"    [拉勾] 浏览器自动化错误: {e}")
    finally:
        if browser:
            try:
                browser.close()
            except Exception:
                pass

    return jobs


def scrape(verbose: bool = True) -> list[dict[str, Any]]:
    """主入口：从拉勾校园招聘搜索产品类校招职位"""
    all_jobs: list[dict[str, Any]] = []

    keywords = ["产品经理", "产品策划", "AI产品"]

    if verbose:
        print(f"  [拉勾] 使用浏览器自动化搜索校招职位")
        print(f"  [拉勾] 关键词: {keywords}")
        print(f"  [拉勾] 城市: {TIER1_CITIES[:4]}")

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
        print(f"  [拉勾] 共获取 {len(unique)} 个产品类校招职位")

    return unique
