#!/usr/bin/env python3
"""
Moka API 数据源 —— 从 Moka 招聘系统获取校招职位

Moka 的职位 API 是公开的，无需认证即可获取职位列表。
端点: GET https://api.mokahr.com/api-platform/v1/jobs/{orgId}?mode=campus
"""
import re
from datetime import datetime, timezone
from typing import Any

from . import fetch_json, build_job, clean_html

# ── 已知使用 Moka 系统的公司及其 orgId ──
# 通过验证各公司招聘官网的 API 请求发现
# 格式: "公司名": "orgId"
MOKA_ORGS: dict[str, str] = {
    # ── 已验证（测试通过，可以正常返回数据） ──
    "知乎": "zhihu",           # ✅
    "滴滴出行": "didiglobal",  # ✅
    "搜狐": "sohu",            # ✅
    "新浪": "sina",            # ✅
    "西山居": "xishanju",      # ✅
    "大疆": "dji",             # ✅
    "月之暗面": "moonshot",    # ✅
    "影石Insta360": "insta360",# ✅
    "众安保险": "zhongan",     # ✅
    "猫眼": "maoyan",          # ✅
    "小鹏汽车": "xiaopeng",    # ✅
    # ── 待验证（orgId 可能映射不对，采集时自动容错） ──
    "美团": "meituan",
    "快手": "kuaishou",
    "小红书": "xiaohongshu",
    "得物": "poizon",
    "哔哩哔哩": "bilibili",
    "理想汽车": "lixiang",
    "蔚来": "nio",
    "keep": "keep",
    "神策数据": "shence",
    "微盟": "weimeng",
    "有赞": "youzan",
    "众安保险": "zhongan",
    "趣加": "funplus",
    "莉莉丝": "lilith",
    "完美世界": "wanmei",
    "唯品会": "vipshop",
    "得到": "dedao",
    "高途": "gaotu",
    "去哪儿": "qunar",
    "安克创新": "ankert",
    "追觅科技": "dreame",
    "旷视科技": "megvii",
    "商汤科技": "sensetime",
    "地平线": "horizon",
    "第四范式": "4paradigm",
    "百川智能": "baichuan",
    "智谱AI": "zhipu",
    "MiniMax": "minimax",
    "零一万物": "lingyi",
}

# 公司补充信息（行业、官网、Logo）
COMPANY_INFO: dict[str, dict[str, str]] = {
    "美团": {"industry": "互联网/本地生活", "website": "https://zhaopin.meituan.com/campus"},
    "快手": {"industry": "互联网/短视频", "website": "https://zhaopin.kuaishou.cn/campus"},
    "小红书": {"industry": "互联网/社区", "website": "https://job.xiaohongshu.com/campus"},
    "滴滴": {"industry": "互联网/出行", "website": "https://talent.didiglobal.com/campus"},
    "知乎": {"industry": "互联网/社区", "website": "https://job.zhihu.com/campus"},
    "得物": {"industry": "互联网/电商", "website": "https://poizon.jobs.feishu.cn/campus"},
    "bilibili": {"industry": "互联网/视频", "website": "https://campus.bilibili.com/"},
    "搜狐": {"industry": "互联网/门户", "website": "https://hr.sohu.com/campus"},
    "新浪": {"industry": "互联网/门户", "website": "https://career.sina.com.cn/campus"},
    "58同城": {"industry": "互联网/分类信息", "website": "https://hr.58.com/campus"},
    "理想汽车": {"industry": "新能源汽车", "website": "https://www.lixiang.com/careers/campus"},
    "蔚来": {"industry": "新能源汽车", "website": "https://nio.jobs.feishu.cn/campus"},
    "小鹏汽车": {"industry": "新能源汽车", "website": "https://campus.xiaopeng.com/"},
    "元气森林": {"industry": "消费品/饮料", "website": "https://job.genki forest.com/campus"},
    "keep": {"industry": "互联网/运动", "website": "https://keep.jobs.feishu.cn/campus"},
    "猫眼": {"industry": "互联网/票务", "website": "https://maoyan.jobs.feishu.cn/campus"},
    "神策数据": {"industry": "企业服务/大数据", "website": "https://www.sensorsdata.cn/campus"},
    "微盟": {"industry": "企业服务/SaaS", "website": "https://career.weimob.com/campus"},
    "有赞": {"industry": "企业服务/SaaS", "website": "https://youzan.jobs.feishu.cn/campus"},
    "众安保险": {"industry": "互联网保险", "website": "https://campus.zhongan.com/"},
    "老虎证券": {"industry": "金融科技", "website": "https://tiger.jobs.feishu.cn/campus"},
    "富途证券": {"industry": "金融科技", "website": "https://futu.jobs.feishu.cn/campus"},
    "趣加": {"industry": "游戏", "website": "https://funplus.jobs.feishu.cn/campus"},
    "莉莉丝": {"industry": "游戏", "website": "https://lilith.jobs.feishu.cn/campus"},
    "叠纸": {"industry": "游戏", "website": "https://papergames.jobs.feishu.cn/campus"},
    "鹰角网络": {"industry": "游戏", "website": "https://hypergryph.jobs.feishu.cn/campus"},
    "完美世界": {"industry": "游戏", "website": "https://campus.wanmei.com/"},
    "西山居": {"industry": "游戏", "website": "https://hr.xishanju.com/campus"},
    "唯品会": {"industry": "互联网/电商", "website": "https://campus.vipshop.com/"},
    "得到": {"industry": "互联网/知识服务", "website": "https://dedao.jobs.feishu.cn/campus"},
    "高途": {"industry": "在线教育", "website": "https://campus.gaotu.cn/"},
    "猿辅导": {"industry": "在线教育", "website": "https://hr.yuanfudao.com/campus"},
    "去哪儿": {"industry": "互联网/旅游", "website": "https://qunar.jobs.feishu.cn/campus"},
    "大疆": {"industry": "硬件/无人机", "website": "https://we.dji.com/campus"},
    "旷视科技": {"industry": "AI/计算机视觉", "website": "https://megvii.jobs.feishu.cn/campus"},
    "商汤科技": {"industry": "AI/计算机视觉", "website": "https://campus.sensetime.com/"},
    "地平线": {"industry": "AI/芯片", "website": "https://horizon.jobs.feishu.cn/campus"},
    "第四范式": {"industry": "AI/企业服务", "website": "https://4paradigm.jobs.feishu.cn/campus"},
    "智谱AI": {"industry": "AI/大模型", "website": "https://zhipu.jobs.feishu.cn/campus"},
    "百川智能": {"industry": "AI/大模型", "website": "https://baichuan.jobs.feishu.cn/campus"},
    "MiniMax": {"industry": "AI/大模型", "website": "https://minimax.jobs.feishu.cn/campus"},
    "月之暗面": {"industry": "AI/大模型", "website": "https://moonshot.jobs.feishu.cn/campus"},
    "零一万物": {"industry": "AI/大模型", "website": "https://lingyi.jobs.feishu.cn/campus"},
    "Insta360": {"industry": "硬件/影像", "website": "https://insta360.jobs.feishu.cn/campus"},
    "安克创新": {"industry": "硬件/消费电子", "website": "https://anker.jobs.feishu.cn/campus"},
    "追觅科技": {"industry": "硬件/机器人", "website": "https://dreame.jobs.feishu.cn/campus"},
    "Momenta": {"industry": "AI/自动驾驶", "website": "https://momenta.jobs.feishu.cn/campus"},
    "流利说": {"industry": "在线教育", "website": "https://liulishuo.jobs.feishu.cn/campus"},
    "易企秀": {"industry": "企业服务/营销", "website": "https://eqxiu.jobs.feishu.cn/campus"},
}


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
                city = loc.get("city", "") or ""

        zhineng = j.get("zhineng", {}) or {}
        if isinstance(zhineng, dict):
            category = zhineng.get("name") or "其他"
        else:
            category = "其他"

        salary_min = j.get("minSalary") or 0
        salary_max = j.get("maxSalary") or 0
        if salary_max and salary_max > 0:
            salary_str = f"{salary_min // 1000}K-{salary_max // 1000}K"
        else:
            salary_str = "面议"

        description = clean_html(j.get("description") or "")
        updated_at = j.get("updatedAt") or j.get("openedAt") or now.isoformat()
        closed_at = j.get("closedAt") or ""

        results.append({
            "title": title,
            "city": city,
            "salary": salary_str,
            "category": category,
            "description": description,
            "education": j.get("education", "本科及以上"),
            "postedAt": updated_at,
            "deadline": closed_at,
            "org_id": org_id,
        })
    return results


def build_moka_jobs(company_name: str, org_id: str) -> list[dict[str, Any]]:
    """获取 Moka 公司职位并转换为标准格式"""
    raw_jobs = fetch_moka_jobs(org_id)
    if not raw_jobs:
        return []

    info = COMPANY_INFO.get(company_name, {"industry": "互联网", "website": ""})
    website = info.get("website", "")
    if not website:
        website = f"https://{org_id}.jobs.f.mioffice.cn/campus"

    jobs = []
    for rj in raw_jobs:
        job = build_job(
            title=rj["title"],
            company=company_name,
            city=rj["city"],
            salary=rj["salary"],
            source="moka",
            apply_url=website,
            description=rj["description"],
            education=rj["education"],
            category="产品" if rj["category"] == "产品类" else rj["category"],
            posted_at=rj["postedAt"],
            deadline=rj["deadline"],
            industry=info.get("industry", "互联网"),
        )
        jobs.append(job)

    return jobs


def scrape(verbose: bool = True) -> list[dict[str, Any]]:
    """主入口：采集所有 Moka 公司的校招职位"""
    all_jobs: list[dict[str, Any]] = []
    errors: list[str] = []

    if verbose:
        print(f"  [Moka] 配置公司数: {len(MOKA_ORGS)}")

    for company_name, org_id in MOKA_ORGS.items():
        if verbose:
            print(f"    正在获取 {company_name} ({org_id})...", end=" ", flush=True)
        try:
            jobs = build_moka_jobs(company_name, org_id)
            all_jobs.extend(jobs)
            if verbose:
                print(f"✅ {len(jobs)} 个职位")
        except Exception as e:
            errors.append(f"{company_name}: {e}")
            if verbose:
                print(f"❌ {e}")

    if verbose:
        print(f"  [Moka] 共获取 {len(all_jobs)} 个职位")
        if errors:
            print(f"  [Moka] ⚠️ {len(errors)} 家公司采集失败")

    return all_jobs
