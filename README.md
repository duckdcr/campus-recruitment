# 校招雷达 🎯

每日更新的互联网校招信息聚合平台。聚焦互联网行业产品类校招/实习岗位，覆盖一线城市。

## 功能

- **搜索** — 按公司、职位、关键词搜索
- **公司筛选** — 多选公司，精准定位
- **城市筛选** — 一线城市全覆盖
- **薪资排序** — 按最新发布/薪资最高/公司名排序
- **职位详情** — 弹窗查看完整信息
- **暗黑模式** — 一键切换
- **响应式设计** — 桌面端和移动端适配
- **订阅推送** — 新职位邮件通知

## 技术栈

| 技术 | 用途 |
|------|------|
| React 19 + TypeScript | 前端框架 |
| Vite 8 | 构建工具 |
| lucide-react | 图标库 |
| date-fns | 日期格式化 |
| GitHub Actions | 每日数据自动采集 + 部署 |
| 阿里云 OSS | 静态网站托管 |

## 数据来源

- **Moka API** — 字节跳动、美团、快手、小红书等互联网公司的校招 API
- 每日北京时间 08:00 自动更新

## 本地开发

```bash
npm install
npm run dev      # 启动开发服务器
npm run build    # 构建
npm run preview  # 预览构建产物
```

## 部署到阿里云 OSS

### 1. 创建 AccessKey

登录 [阿里云 RAM 控制台](https://ram.console.aliyun.com/users) → 创建用户 → 勾选"编程访问" → 添加 AliyunOSSFullAccess 权限 → 保存 AccessKey。

### 2. 创建 OSS Bucket

[OSS 控制台](https://oss.console.aliyun.com/bucket) → 创建 Bucket → ACL 选"公共读" → 开启静态网站托管。

### 3. 一键部署

```bash
python scripts/setup-aliyun.py \
  --access-key-id <你的AccessKey ID> \
  --access-key-secret <你的AccessKey Secret> \
  --bucket campus-recruitment
```

### 4. GitHub Actions 自动部署

在 GitHub Repo → Settings → Secrets → Actions 添加：

| Secret | 值 |
|--------|-----|
| ALIYUN_ACCESS_KEY_ID | AccessKey ID |
| ALIYUN_ACCESS_KEY_SECRET | AccessKey Secret |
| ALIYUN_OSS_BUCKET | Bucket 名称 |
| ALIYUN_OSS_ENDPOINT | oss-cn-hangzhou.aliyuncs.com |

推送 main 分支，自动部署。

### 5. 绑定 CDN 域名（可选）

[CDN 控制台](https://cdn.console.aliyun.com/) → 添加域名 → 源站 OSS → CNAME 解析。

## 项目结构

```
├── .github/workflows/   # GitHub Actions 流水线
├── public/data/          # 校招数据（自动更新）
├── scripts/              # 数据采集 + 部署脚本
├── src/
│   ├── api/hooks/components/styles/
│   ├── types/utils/
│   └── App.tsx + main.tsx
└── index.html
```
