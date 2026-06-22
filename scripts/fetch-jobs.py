#!/usr/bin/env python3
"""
校招数据采集脚本
从 Moka API + 其他公开来源抓取校招信息，输出 JSON 供前端消费

用法: python scripts/fetch-jobs.py [--output public/data/campus-jobs.json]
"""

import json
import sys
import os
import urllib.request
import urllib.error
import ssl
from datetime import datetime, timezone, timedelta
from typing import Any

# ── 配置 ─────────────────────────────────────────────

# 已知使用 Moka 系统的公司及其 orgId
# 可通过查看公司招聘页面的 API 请求发现
MOKA_ORGS: dict[str, str] = {
    "字节跳动": "bytedance",
    "美团": "meituan",
    "快手": "kuaishou",
    "小红书": "xiaohongshu",
    "网易": "netease",
    "拼多多": "pinduoduo",
    "哔哩哔哩": "bilibili",
    "小米": "xiaomi",
    "滴滴": "didiglobal",
    "知乎": "zhihu",
    "得物": "poizon",
}

# 手动维护的公司招聘官网（当 Moka API 不可用时的备选信息来源）
COMPANY_INFO: dict[str, dict[str, str]] = {
    "字节跳动": {"industry": "互联网", "website": "https://jobs.bytedance.com/campus"},
    "腾讯": {"industry": "互联网", "website": "https://join.qq.com/"},
    "阿里巴巴": {"industry": "互联网", "website": "https://talent.alibaba.com/campus"},
    "美团": {"industry": "互联网", "website": "https://zhaopin.meituan.com/campus"},
    "百度": {"industry": "互联网", "website": "https://talent.baidu.com/campus"},
    "网易": {"industry": "互联网", "website": "https://campus.163.com/"},
    "快手": {"industry": "互联网", "website": "https://zhaopin.kuaishou.cn/campus"},
    "京东": {"industry": "互联网", "website": "https://campus.jd.com/"},
    "小红书": {"industry": "互联网", "website": "https://job.xiaohongshu.com/campus"},
    "哔哩哔哩": {"industry": "互联网", "website": "https://campus.bilibili.com/"},
    "拼多多": {"industry": "互联网", "website": "https://careers.pinduoduo.com/campus"},
    "小米": {"industry": "互联网", "website": "https://xiaomi.jobs.f.mioffice.cn/campus"},
    "华为": {"industry": "互联网", "website": "https://career.huawei.com/campus"},
    "滴滴": {"industry": "互联网", "website": "https://talent.didiglobal.com/campus"},
}

# 产品类职位关键词（用于前端分类）
PRODUCT_KEYWORDS = ["产品", "产品经理", "产品策划", "产品运营", "策略产品", "AI产品"]

# ── 数据获取 ──────────────────────────────────────────

ctx = ssl.create_default_context()


def fetch_json(url: str, timeout: int = 15) -> dict[str, Any] | list[Any] | None:
    """获取 JSON 数据"""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [WARN] Failed to fetch {url}: {e}")
        return None


def fetch_moka_jobs(org_id: str) -> list[dict[str, Any]]:
    """从 Moka API 获取校招职位"""
    url = f"https://api.mokahr.com/api-platform/v1/jobs/{org_id}?mode=campus&limit=100"
    data = fetch_json(url)
    if not data or not isinstance(data, dict):
        return []

    jobs_raw = data.get("jobs", []) if isinstance(data, dict) else []
    if not jobs_raw:
        return []

    now = datetime.now(timezone.utc)
    results = []
    for j in jobs_raw:
        if not isinstance(j, dict):
            continue
        # 只保留开放中的职位
        if j.get("status") != "open":
            continue

        title = j.get("title", "")
        locations = j.get("locations", []) or []
        city = ""
        if locations and isinstance(locations, list) and len(locations) > 0:
            loc = locations[0]
            if isinstance(loc, dict):
                city = loc.get("city", "")

        zhineng = j.get("zhineng", {}) or {}
        if isinstance(zhineng, dict):
            category = zhineng.get("name", "其他")
        else:
            category = "其他"

        salary_min = j.get("minSalary") or 0
        salary_max = j.get("maxSalary") or 0
        if salary_max > 0:
            salary_str = f"{salary_min // 1000}K-{salary_max // 1000}K"
        else:
            salary_str = "面议"

        department = j.get("department", {}) or {}
        if isinstance(department, dict):
            dept_name = department.get("name", "")
        else:
            dept_name = ""

        description = j.get("description", "") or ""
        # 去除 HTML 标签
        import re
        description_clean = re.sub(r"<[^>]+>", "", description).strip()

        updated_at = j.get("updatedAt") or j.get("openedAt") or now.isoformat()

        results.append(
            {
                "id": f"moka-{org_id}-{j.get('id', '')}",
                "title": title,
                "company": "",  # 由调用方填充
                "companyLogo": "",
                "industry": "",
                "city": city,
                "location": city,
                "salary": salary_str,
                "education": j.get("education", "本科及以上"),
                "experience": "应届",
                "category": category,
                "postedAt": updated_at,
                "deadline": j.get("closedAt", ""),
                "description": description_clean[:1000] if description_clean else "",
                "requirements": _parse_requirements(description_clean),
                "applyUrl": f"https://{org_id}.jobs.f.mioffice.cn/campus",
                "source": "moka",
                "type": "campus",
                "tags": ["校招", category],
                "featured": False,
            }
        )
    return results


def _parse_requirements(description: str) -> list[str]:
    """从职位描述中提取任职要求"""
    lines = description.split("\n")
    reqs = []
    in_req_section = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 检测要求/资格/条件相关标题
        if any(kw in line for kw in ["任职要求", "岗位要求", "职位要求", "我们需要", "希望你"]):
            in_req_section = True
            continue
        if any(kw in line for kw in ["工作内容", "岗位职责", "职位描述", "关于我们"]):
            in_req_section = False
            continue
        if in_req_section and len(line) > 4:
            reqs.append(line.strip("·•-*").strip())
    if not reqs:
        # fallback: 取描述中带"要求"关键词的句子
        for line in lines:
            line = line.strip()
            if any(kw in line for kw in ["学历", "专业", "经验", "能力", "熟悉", "掌握", "负责"]):
                reqs.append(line.strip("·•-*").strip()[:120])
    return reqs[:8]  # 最多 8 条


# ── 主流程 ─────────────────────────────────────────────


def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else "public/data/campus-jobs.json"

    all_jobs: list[dict[str, Any]] = []
    errors: list[str] = []

    print(f"[校招雷达] 开始采集数据 ({datetime.now().isoformat()})")
    print(f"[校招雷达] Moka 公司数量: {len(MOKA_ORGS)}")

    for company_name, org_id in MOKA_ORGS.items():
        print(f"  [Moka] 正在获取 {company_name} ({org_id})...", end=" ", flush=True)
        try:
            jobs = fetch_moka_jobs(org_id)
            info = COMPANY_INFO.get(company_name, {})
            for j in jobs:
                j["company"] = company_name
                j["industry"] = info.get("industry", "互联网")
                j["applyUrl"] = info.get("website", j["applyUrl"])
                # 检查是否为产品类
                is_product = any(kw in j["title"] for kw in PRODUCT_KEYWORDS)
                if is_product:
                    j["category"] = "产品"
                    j["tags"] = ["校招", "产品", company_name]
                else:
                    j["tags"] = ["校招", company_name]
            all_jobs.extend(jobs)
            print(f"✅ {len(jobs)} 个职位")
        except Exception as e:
            errors.append(f"{company_name}: {e}")
            print(f"❌ {e}")

    # 去重（按 title + company）
    seen = set()
    unique_jobs = []
    for j in all_jobs:
        key = (j["title"], j["company"])
        if key not in seen:
            seen.add(key)
            unique_jobs.append(j)

    # 按发布时间排序
    unique_jobs.sort(key=lambda j: j.get("postedAt", ""), reverse=True)

    # 写文件
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique_jobs, f, ensure_ascii=False, indent=2)

    print(f"\n[校招雷达] ✅ 采集完成！共 {len(unique_jobs)} 个职位")
    print(f"[校招雷达]   输出文件: {output_path}")

    if errors:
        print(f"\n[校招雷达] ⚠️ 以下公司采集失败:")
        for e in errors:
            print(f"  - {e}")

    # 返回非零状态码如果有严重错误
    # 部分失败是可以接受的
    if len(errors) > len(MOKA_ORGS) // 2:
        print("[校招雷达] ❌ 超过一半的公司采集失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
