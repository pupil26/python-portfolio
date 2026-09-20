# -*- coding: utf-8 -*-
"""
web_monitor.py — 网页变化监测脚本（样品版）

功能：
    定时抓取指定网页，比对内容是否发生变化，变化时提示并保存快照。
    纯本地运行，零依赖第三方服务，无需登录、无爬虫逆向。

设计要点：
    1. 只做"变化检测"，不做数据采集，天然合规。
    2. 变化判定用「内容指纹 + 关键文本」双保险：
       - 指纹：页面文本的 MD5，任何字符变化都会触发
       - 关键词：可选，只关心某几个关键字段（如价格、标题）是否变化
    3. 每次检测自动存档快照，可回看历史变化。

用法：
    python web_monitor.py                          # 用内置示例配置跑一遍
    python web_monitor.py --config my.json         # 用自己的配置
    python web_monitor.py --once                   # 只检测一次（适合测试/计划任务）

配置文件格式（JSON）：
    {
      "targets": [
        {
          "name": "示例页面",
          "url": "https://example.com",
          "interval": 60,              // 秒，0 表示只跑一次
          "keywords": ["价格", "¥"],   // 可选，留空则比对全文
          "headless_note": "无需浏览器，纯 HTTP 抓取"
        }
      ],
      "poll": 60                       // 默认轮询间隔（秒）
    }

依赖：仅 Python 标准库（urllib + hashlib + json），无需 pip 安装。
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

# 存档目录
SNAPSHOT_DIR = "snapshots"


# ---------------------------------------------------------------- 抓取

def fetch(url, timeout=20):
    """抓取网页文本。返回 (状态, 文本)。"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            charset = r.headers.get_content_charset() or 'utf-8'
            try:
                text = raw.decode(charset, 'replace')
            except Exception:
                text = raw.decode('utf-8', 'replace')
            return r.status, text
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:
        return -1, str(e)


# ---------------------------------------------------------------- 指纹与判定

def strip_tags(html):
    """去掉 script/style/tag，只留可见文本。"""
    html = re.sub(r'<script[\s\S]*?</script>', ' ', html, flags=re.I)
    html = re.sub(r'<style[\s\S]*?</style>', ' ', html, flags=re.I)
    html = re.sub(r'<[^>]+>', ' ', html)
    html = re.sub(r'\s+', ' ', html)
    return html.strip()


def fingerprint(text):
    """内容指纹（MD5）。"""
    return hashlib.md5(text.encode('utf-8', 'replace')).hexdigest()


def extract_keywords(text, keywords):
    """只关心关键词所在片段，返回命中的上下文。"""
    hits = []
    for kw in keywords:
        for m in re.finditer(re.escape(kw), text):
            s = max(0, m.start() - 20)
            e = min(len(text), m.end() + 40)
            hits.append(text[s:e])
    return hits


# ---------------------------------------------------------------- 存档

def save_snapshot(name, url, fp, text):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    safe = re.sub(r'[^\w\-]+', '_', name)
    ts = time.strftime('%Y%m%d_%H%M%S')
    path = os.path.join(SNAPSHOT_DIR, '%s_%s.txt' % (safe, ts))
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# name: %s\n# url: %s\n# fingerprint: %s\n# at: %s\n\n'
                % (name, url, fp, time.strftime('%Y-%m-%d %H:%M:%S')))
        f.write(text)
    return path


def load_last_state(name):
    """读取上次指纹，文件藏在 snapshots 下。"""
    state = os.path.join(SNAPSHOT_DIR, '.state_%s.txt' % name)
    if os.path.exists(state):
        with open(state, encoding='utf-8') as f:
            return f.read().strip()
    return None


def save_state(name, fp):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    state = os.path.join(SNAPSHOT_DIR, '.state_%s.txt' % name)
    with open(state, 'w', encoding='utf-8') as f:
        f.write(fp)


# ---------------------------------------------------------------- 单次检测

def check_once(target):
    name = target.get('name', target['url'])
    url = target['url']
    keywords = target.get('keywords') or []
    quiet = target.get('quiet', False)

    status, html = fetch(url)
    if status != 200:
        if not quiet:
            print('[%s] 抓取失败 (HTTP %s)，跳过' % (name, status))
        return None

    text = strip_tags(html)
    fp = fingerprint(text)
    last = load_last_state(name)

    changed = last is not None and last != fp
    is_new = last is None

    if changed:
        hits = extract_keywords(text, keywords) if keywords else []
        path = save_snapshot(name, url, fp, text)
        print('=' * 60)
        print('⚠  检测到变化！目标：%s' % name)
        print('   旧指纹 %s' % last)
        print('   新指纹 %s' % fp)
        if keywords:
            print('   关键词命中 %d 处：' % len(hits))
            for h in hits[:5]:
                print('      …%s…' % h.strip())
        print('   快照已存：%s' % path)
        print('=' * 60)
    elif is_new:
        if not quiet:
            print('[%s] 首次检测，已记录基线（指纹 %s）' % (name, fp[:8]))
    else:
        if not quiet:
            print('[%s] 无变化（%s）' % (name, time.strftime('%H:%M:%S')))

    save_state(name, fp)
    return {'name': name, 'changed': changed, 'fp': fp}


# ---------------------------------------------------------------- 主流程

def load_config(path):
    if path and os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    # 内置示例：检测一个真实可访问的静态页
    return {
        'targets': [
            {
                'name': '示例-百度首页标题',
                'url': 'https://www.baidu.com',
                'interval': 0,
                'keywords': ['百度'],
            }
        ],
        'poll': 60,
    }


def main():
    ap = argparse.ArgumentParser(description='网页变化监测脚本')
    ap.add_argument('--config', default=None, help='配置文件路径')
    ap.add_argument('--once', action='store_true', help='只检测一次')
    args = ap.parse_args()

    cfg = load_config(args.config)
    targets = cfg.get('targets', [])
    if not targets:
        print('配置里没有 targets，请检查。')
        sys.exit(1)

    poll = cfg.get('poll', 60)
    print('监测 %d 个目标，默认间隔 %d 秒。Ctrl+C 退出。\n'
          % (len(targets), poll))

    try:
        while True:
            for t in targets:
                check_once(t)
            if args.once:
                break
            interval = t.get('interval') or poll
            time.sleep(interval)
    except KeyboardInterrupt:
        print('\n已停止。')


if __name__ == '__main__':
    main()
