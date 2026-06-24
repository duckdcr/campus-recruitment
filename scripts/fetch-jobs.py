#!/usr/bin/env python3
"""
校招数据采集 —— 多源聚合采集器

从多个数据源采集产品类校招信息，合并去重后输出 JSON。
支持数据源:
  1. Moka API       - 使用 Moka 招聘系统的公司
  2. 拉勾网          - 产品类校招职位搜索
  3. 猎聘校园        - 产品类校招职位搜索
  4. GitHub 社区仓库  - 校招汇总信息
  5. 企业官网直采    - 大厂自有招聘系统

用法:
  python scripts/fetch-jobs.py --output public/data/campus-jobs.json
  python scripts/fetch-jobs.py --output public/data/campus-jobs.json --sources moka,lagou
  python scripts/fetch-jobs.py --output public/data/campus-jobs.json --sample  (生成样本数据)
"""
import sys
import os
import json
import time
import argparse
import concurrent.futures
from datetime import datetime, timezone
from typing import Any

# 确保 sources 包可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sources import save_jobs

# ── 数据源注册表 ──
# 每个数据源导出 scrape(verbose) -> list[dict]
SOURCES: dict[str, dict[str, Any]] = {}


def register_sources():
    """注册所有可用数据源"""
    try:
        from sources import moka
        SOURCES["moka"] = {
            "name": "Moka API",
            "module": moka,
            "enabled": True,
            "weight": 1,
        }
    except Exception as e:
        print(f"  [WARN] Moka 模块加载失败: {e}")

    try:
        from sources import github_repo
        SOURCES["github"] = {
            "name": "GitHub 校招汇总",
            "module": github_repo,
            "enabled": True,
            "weight": 1,
        }
    except Exception as e:
        print(f"  [WARN] GitHub 模块加载失败: {e}")

    # ── 以下源需要浏览器环境（Playwright），CI 中会自动安装 ──
    # 缺失 Playwright 时模块会自行降级返回空列表，不会崩溃

    try:
        from sources import lagou
        SOURCES["lagou"] = {
            "name": "拉勾网 (Playwright)",
            "module": lagou,
            "enabled": True,
            "weight": 2,
        }
    except Exception as e:
        print(f"  [WARN] 拉勾模块加载失败: {e}")

    try:
        from sources import liepin
        SOURCES["liepin"] = {
            "name": "猎聘校园 (Playwright)",
            "module": liepin,
            "enabled": True,
            "weight": 2,
        }
    except Exception as e:
        print(f"  [WARN] 猎聘模块加载失败: {e}")

    # 企业官网直采（requests + BeautifulSoup，无需浏览器）
    try:
        from sources import company_pages
        SOURCES["company"] = {
            "name": "企业官网直采",
            "module": company_pages,
            "enabled": True,
            "weight": 3,
        }
    except Exception as e:
        print(f"  [WARN] 企业官网模块加载失败: {e}")


def generate_sample_data() -> list[dict[str, Any]]:
    """生成样本数据（当正式采集不可用时使用）"""
    sample = []

    companies_data = [
        {"name": "字节跳动", "industry": "互联网/短视频"},
        {"name": "腾讯", "industry": "互联网/社交"},
        {"name": "阿里巴巴", "industry": "互联网/电商"},
        {"name": "美团", "industry": "互联网/本地生活"},
        {"name": "百度", "industry": "互联网/搜索"},
        {"name": "京东", "industry": "互联网/电商"},
        {"name": "网易", "industry": "互联网/游戏"},
        {"name": "快手", "industry": "互联网/短视频"},
        {"name": "小红书", "industry": "互联网/社区"},
        {"name": "哔哩哔哩", "industry": "互联网/视频"},
        {"name": "拼多多", "industry": "互联网/电商"},
        {"name": "小米", "industry": "互联网/硬件"},
        {"name": "滴滴", "industry": "互联网/出行"},
        {"name": "知乎", "industry": "互联网/社区"},
        {"name": "得物", "industry": "互联网/电商"},
        {"name": "理想汽车", "industry": "新能源汽车"},
        {"name": "蔚来", "industry": "新能源汽车"},
        {"name": "大疆", "industry": "硬件/无人机"},
        {"name": "旷视科技", "industry": "AI/计算机视觉"},
        {"name": "商汤科技", "industry": "AI/计算机视觉"},
        {"name": "智谱AI", "industry": "AI/大模型"},
        {"name": "MiniMax", "industry": "AI/大模型"},
        {"name": "月之暗面", "industry": "AI/大模型"},
        {"name": "百川智能", "industry": "AI/大模型"},
        {"name": "零一万物", "industry": "AI/大模型"},
        {"name": "趣加", "industry": "游戏"},
        {"name": "莉莉丝", "industry": "游戏"},
        {"name": "唯品会", "industry": "互联网/电商"},
        {"name": "猿辅导", "industry": "在线教育"},
        {"name": "得到", "industry": "互联网/知识服务"},
        {"name": "去哪儿", "industry": "互联网/旅游"},
        {"name": "微盟", "industry": "企业服务/SaaS"},
        {"name": "有赞", "industry": "企业服务/SaaS"},
        {"name": "众安保险", "industry": "互联网保险"},
        {"name": "老虎证券", "industry": "金融科技"},
        {"name": "富途证券", "industry": "金融科技"},
        {"name": "搜狐", "industry": "互联网/门户"},
        {"name": "新浪", "industry": "互联网/门户"},
        {"name": "完美世界", "industry": "游戏"},
        {"name": "西山居", "industry": "游戏"},
    ]

    product_titles = [
        "产品经理", "高级产品经理", "产品策划", "产品运营", "AI产品经理",
        "数据产品经理", "商业化产品经理", "策略产品经理", "B端产品经理",
        "C端产品经理", "平台产品经理", "增长产品经理", "电商产品经理",
        "搜索产品经理", "推荐产品经理", "产品管培生", "产品实习生（校招）",
    ]

    cities_order = ["北京", "上海", "广州", "深圳"]
    salary_ranges = [
        "15K-25K", "18K-30K", "20K-35K", "15K-20K", "20K-40K",
        "12K-20K", "25K-45K", "15K-30K", "面议", "20K-28K",
    ]

    now = datetime.now(timezone.utc)
    for idx, company in enumerate(companies_data):
        name = company["name"]
        industry = company["industry"]
        # 每家公司 1-3 个产品岗位
        num_jobs = (hash(name) % 3) + 1
        for j in range(num_jobs):
            title = product_titles[(idx + j) % len(product_titles)]
            city = cities_order[(idx + j) % len(cities_order)]
            salary = salary_ranges[(idx + j) % len(salary_ranges)]

            job = {
                "id": f"sample-{idx}-{j}",
                "title": title,
                "company": name,
                "companyLogo": "",
                "industry": industry,
                "city": city,
                "location": city,
                "salary": salary,
                "education": "本科及以上",
                "experience": "应届",
                "category": "产品",
                "postedAt": now.isoformat(),
                "deadline": "",
                "description": f"{name} 2026届校园招聘 - {title}岗位。负责产品规划、需求分析、产品设计等工作。",
                "requirements": ["本科及以上学历", "计算机、设计或相关专业", "有产品相关实习经验优先", "具有较强的逻辑思维和沟通能力"],
                "applyUrl": f"https://www.example.com/campus/{name.lower()}",
                "source": "sample",
                "type": "campus",
                "tags": ["校招", "产品", name],
                "featured": idx < 5,  # 前5家公司标记推荐
            }
            sample.append(job)

    return sample


def main():
    parser = argparse.ArgumentParser(description="校招数据多源采集器")
    parser.add_argument("--output", default="public/data/campus-jobs.json",
                        help="输出 JSON 文件路径")
    parser.add_argument("--sources", default="",
                        help="要启用的数据源，逗号分隔，默认全部")
    parser.add_argument("--sample", action="store_true",
                        help="仅生成样本数据（跳过网络采集）")
    parser.add_argument("--no-verbose", action="store_true",
                        help="安静模式")
    args = parser.parse_args()

    verbose = not args.no_verbose

    start_time = time.time()

    if args.sample:
        print(f"[校招雷达] 生成样本数据...")
        jobs = generate_sample_data()
        count = save_jobs(jobs, args.output)
        elapsed = time.time() - start_time
        print(f"[校招雷达] ✅ 已生成 {count} 条样本数据 → {args.output} ({elapsed:.1f}s)")
        return

    # 注册数据源
    register_sources()

    # 筛选启用的数据源
    if args.sources:
        enabled = set(s.strip() for s in args.sources.split(",") if s.strip())
        for key in SOURCES:
            SOURCES[key]["enabled"] = key in enabled

    enabled_sources = [k for k, v in SOURCES.items() if v["enabled"]]

    if not enabled_sources:
        print("[校招雷达] ❌ 没有启用的数据源")
        sys.exit(1)

    print(f"[校招雷达] 多源采集启动 ({datetime.now().isoformat()})")
    print(f"[校招雷达] 数据源: {', '.join(SOURCES[s]['name'] for s in enabled_sources)}")
    print("=" * 60)

    all_jobs: list[dict[str, Any]] = []
    source_stats: dict[str, int] = {}

    def run_with_timeout(fn, timeout_sec=180):
        """运行函数并设置超时，超时时返回空列表"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(fn)
            try:
                return fut.result(timeout=timeout_sec)
            except concurrent.futures.TimeoutError:
                print(f"  ⏰ 超时 (>={timeout_sec}s)，跳过此数据源")
                return []
            except Exception as e:
                print(f"  ❌ 采集异常: {e}")
                return []

    for source_key in enabled_sources:
        source_info = SOURCES[source_key]
        try:
            print(f"\n▶ 数据源: {source_info['name']}")
            jobs = run_with_timeout(
                lambda sk=source_key: SOURCES[sk]["module"].scrape(verbose=verbose),
                timeout_sec=180,
            )
            all_jobs.extend(jobs)
            source_stats[source_info["name"]] = len(jobs)
        except Exception as e:
            print(f"\n▶ 数据源: {source_info['name']}")
            print(f"  ❌ 采集失败: {e}")
            source_stats[source_info["name"]] = 0

    # 合并去重并保存
    print("\n" + "=" * 60)
    dedup_count = save_jobs(all_jobs, args.output)

    elapsed = time.time() - start_time

    print(f"\n[校招雷达] ✅ 采集完成！统计:")
    print(f"  ⏱  耗时: {elapsed:.1f}s")
    for name, count in source_stats.items():
        print(f"  📦 {name}: {count} 个")
    print(f"  ─────────────────")
    print(f"  📊 合计: {len(all_jobs)} 个 (去重后 {dedup_count} 个)")
    print(f"  📁 输出: {args.output}")
    print(f"  🕐 时间: {datetime.now().isoformat()}")

    # 如果有数据就不降级，仅当全部源都为空时才用样本
    if dedup_count == 0:
        print("[校招雷达] ⚠️ 所有数据源均未返回数据，使用样本数据备用...")
        sample_jobs = generate_sample_data()
        save_jobs(sample_jobs, args.output)
        print(f"[校招雷达] ✅ 已切换到样本数据 ({len(sample_jobs)} 条)")


if __name__ == "__main__":
    main()
