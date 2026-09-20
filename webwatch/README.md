# 网页变化监测 + 表单预填

## web_monitor.py — 零依赖网页变化监测

```bash
python web_monitor.py --once          # 检测一次
python web_monitor.py --config x.json # 用配置文件
```

- 抓取网页 → MD5 指纹 → 内容变化提醒 → 快照存档
- 纯 Python 标准库，无需 pip 安装
- 支持多目标监控 + 关键词定位

## form_filler.user.js — 油猴表单预填

- 装进 Tampermonkey 后，打开网页一键填充表单
- 只预填、不自动提交（安全）
- 原生 setter 触发 input/change 事件，兼容 React/Vue 受控组件
