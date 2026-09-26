# 管网风险评估界面 · 第一版
本项目采用 Vue 3 + FastAPI。所有管段、分数、解释和位置均为**虚构演示数据**，未读取或改动竞赛原始文件。GIS 占位图不是地理地图，风险分不是概率。模型验证指标保留“待提供”。

## 第一次运行（Windows）
安装 Python 3.10+、Node.js 20.19+ 或 22.12+（本机开发使用 Python 3.13、Node 24）。在此目录打开 PowerShell：
```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
powershell -ExecutionPolicy Bypass -File .\start.ps1
```
打开 http://127.0.0.1:8000 。停止时在启动终端按 Ctrl+C。setup 需要联网下载依赖；安装完成后页面、字体、示意图无外部网络依赖。命令的 ExecutionPolicy 仅作用于本次 PowerShell 进程。
再次启动只需 start.ps1。端口被占用时先停止此前启动的本项目服务，不要结束不认识的进程。

## 边修改边学习
打开两个 PowerShell 终端，都从项目根目录开始。
终端一：
```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
终端二：
```powershell
cd frontend
npm.cmd run dev
```
访问 http://127.0.0.1:5173 。Vue 文件保存后页面自动更新；Vite 将 /api 请求转发到 Python。更新演示 JSON 后重启后端。
最终演示前在 frontend 目录执行 npm.cmd run build，然后重新运行 start.ps1，确保使用最新页面。接口文档：http://127.0.0.1:8000/docs 。

## 关键文件与数据流
- frontend/src/App.vue：请求后端、筛选、选中管段、详情和清单。
- frontend/src/components/PipeMap.vue：独立 SVG 管网占位组件；只负责展示和发出选择事件。
- frontend/src/style.css：深蓝大屏样式、风险颜色、宽屏/窄屏布局。
- backend/main.py：加载样例、筛选、统计、查询和 CSV 导出。
- demo_data/pipes.json：唯一的虚构业务数据来源。
- docs/接口与交接.md：队友交付格式与地图组件约定。
- docs/学习练习.md：数据请求说明和手动练习。

页面请求 /api/dashboard → 后端从 JSON 筛选并统计 → 页面同时更新图、列表和统计。
点击示意管线 → PipeMap 发出 pipe-select（字符串 ID） → App 更新 selectedId → 右侧详情更新。
“应用筛选”才提交筛选条件；导出使用最近成功应用的筛选，已勾选时只导出选中项。筛选会清除不在结果中的已选项。刷新后选择不保留。

## 当前完成范围
风险统计、分布图、管材分布、筛选、示意图/列表选择联动、详情、示例解释和建议、排查清单、UTF-8 BOM CSV 导出、加载/空结果/服务异常状态。
第一版没有真实 GIS、训练模型、实时监控、登录和持久化排查工单。适合本机演示，尚未按公网部署加固。
