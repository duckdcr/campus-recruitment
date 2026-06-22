#!/usr/bin/env python3
"""
阿里云 OSS 静态网站配置和部署脚本

使用方法:
  1. 在阿里云控制台创建 AccessKey: https://ram.console.aliyun.com/users
     - 创建 RAM 用户 -> 添加 AliyunOSSFullAccess 权限 -> 创建 AccessKey
  2. 运行此脚本:
     python scripts/setup-aliyun.py --access-key-id <your-key> --access-key-secret <your-secret>
  3. 或仅生成部署文件:
     python scripts/setup-aliyun.py --generate-only
"""

import argparse
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="阿里云 OSS 部署配置")
    parser.add_argument("--access-key-id", help="阿里云 AccessKey ID")
    parser.add_argument("--access-key-secret", help="阿里云 AccessKey Secret")
    parser.add_argument("--bucket", default="campus-recruitment", help="OSS Bucket 名称")
    parser.add_argument("--region", default="oss-cn-hangzhou", help="OSS 地域 (默认 oss-cn-hangzhou)")
    parser.add_argument("--generate-only", action="store_true", help="仅生成配置文件，不操作阿里云")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    dist_dir = project_root / "dist"
    config_path = project_root / "deploy-config.json"

    if args.generate_only:
        # 生成部署配置文件
        config = {
            "bucket": args.bucket,
            "endpoint": f"{args.region}.aliyuncs.com",
            "region": args.region,
            "website_index": "index.html",
            "website_error": "index.html",
            "github_secrets_needed": [
                "ALIYUN_ACCESS_KEY_ID",
                "ALIYUN_ACCESS_KEY_SECRET",
                "ALIYUN_OSS_BUCKET",
                "ALIYUN_OSS_ENDPOINT",
            ],
            "instructions": textwrap.dedent("""\
                GitHub Secrets 配置步骤:
                1. 打开 GitHub Repo -> Settings -> Secrets and variables -> Actions
                2. 添加以下 secrets:
                   - ALIYUN_ACCESS_KEY_ID:     你的 AccessKey ID
                   - ALIYUN_ACCESS_KEY_SECRET: 你的 AccessKey Secret
                   - ALIYUN_OSS_BUCKET:        (默认 campus-recruitment)
                   - ALIYUN_OSS_ENDPOINT:      oss-cn-hangzhou.aliyuncs.com
                3. 推送代码到 main 分支，GitHub Actions 将自动部署
            """),
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✅ 配置文件已生成: {config_path}")
        print("\n" + config["instructions"])
        return

    if not args.access_key_id or not args.access_key_secret:
        print("❌ 需要提供 --access-key-id 和 --access-key-secret")
        print("   或者在阿里云控制台创建后重试")
        print("   使用 --generate-only 仅生成配置文件")
        sys.exit(1)

    # ── 使用 ossutil 配置 ──
    ossutil_dir = project_root / "ossutil" / "ossutil-v1.7.19-windows-amd64"
    ossutil_exe = ossutil_dir / "ossutil64.exe"

    if not ossutil_exe.exists():
        print("❌ ossutil 未找到，请先下载到 ossutil/ 目录")
        sys.exit(1)

    endpoint = f"{args.region}.aliyuncs.com"

    def run_ossutil(cmd: list[str]) -> bool:
        full_cmd = [str(ossutil_exe), "-e", endpoint, "-i", args.access_key_id, "-k", args.access_key_secret] + cmd
        result = subprocess.run(full_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ⚠️  {result.stderr[:200]}")
            return False
        print(f"  ✅ {result.stdout[:200]}")
        return True

    # 1. 创建 Bucket
    print(f"📦 创建 OSS Bucket: {args.bucket}")
    run_ossutil(["mb", f"oss://{args.bucket}", "--acl", "public-read"])

    # 2. 配置静态网站托管
    print(f"🌐 配置静态网站托管...")
    website_config = textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <WebsiteConfiguration>
            <IndexDocument><Suffix>index.html</Suffix></IndexDocument>
            <ErrorDocument><Key>index.html</Key></ErrorDocument>
        </WebsiteConfiguration>
    """)
    website_xml = project_root / "_website_config.xml"
    website_xml.write_text(website_config, encoding="utf-8")
    run_ossutil(["ossutil", "api", "put-bucket-website", "--bucket", args.bucket, "--body", str(website_xml)])
    website_xml.unlink(missing_ok=True)

    # 3. 构建前端
    print("🔨 构建前端...")
    subprocess.run(["npm", "run", "build"], cwd=project_root, check=True)

    if not dist_dir.exists():
        print("❌ 构建产物 dist/ 不存在")
        sys.exit(1)

    # 4. 上传到 OSS
    print(f"📤 上传文件到 OSS...")
    run_ossutil(["cp", str(dist_dir), f"oss://{args.bucket}/", "--recursive"])

    # 5. 输出网站 URL
    website_url = f"http://{args.bucket}.{endpoint}"
    print(f"\n🎉 部署完成！")
    print(f"   网站地址: {website_url}")
    print(f"   建议绑定自定义域名并开启 CDN 加速")

    # 6. 输出 GitHub Secrets
    print(f"\n🔑 GitHub Actions Secrets 配置:")
    print(f"   ALIYUN_ACCESS_KEY_ID:     {args.access_key_id}")
    print(f"   ALIYUN_ACCESS_KEY_SECRET: {args.access_key_secret[:4]}...{args.access_key_secret[-4:]}")
    print(f"   ALIYUN_OSS_BUCKET:        {args.bucket}")
    print(f"   ALIYUN_OSS_ENDPOINT:      {endpoint}")


if __name__ == "__main__":
    main()
