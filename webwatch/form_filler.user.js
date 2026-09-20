// ==UserScript==
// @name         通用表单预填器（样品版）
// @namespace    sample.form-filler
// @version      1.0
// @description  打开网页后，点击悬浮按钮一键预填表单。只预填、不自动提交。
// @match        *://*/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function () {
    'use strict';

    // ============================================================
    // 配置区：按需修改。键是「字段名/placeholder/name/id 的关键词」，
    // 值是预填内容。留空 {} 则只显示按钮不填。
    // ============================================================
    var RULES = {
        // 示例：把名字叫「姓名/name/username」的输入框填成「张三」
        '姓名': '张三',
        'name': '张三',
        'username': 'zhangsan',
        '手机': '13800000000',
        'phone': '13800000000',
        '邮箱': 'test@example.com',
        'email': 'test@example.com',
    };

    var FILL_KEYS = Object.keys(RULES);

    // 悬浮按钮样式（不干扰原页面，纯右下角悬浮）
    var style = document.createElement('style');
    style.textContent =
        '#ff-btn{position:fixed;right:16px;bottom:16px;z-index:2147483647;' +
        'padding:10px 16px;background:#1d9e75;color:#fff;border:none;' +
        'border-radius:8px;font-size:14px;cursor:pointer;font-family:sans-serif;' +
        'box-shadow:0 2px 8px rgba(0,0,0,.2);}' +
        '#ff-btn:hover{background:#0f6e56;}' +
        '#ff-tip{position:fixed;right:16px;bottom:60px;z-index:2147483647;' +
        'background:#333;color:#fff;padding:6px 12px;border-radius:6px;' +
        'font-size:12px;font-family:sans-serif;display:none;}';
    document.head.appendChild(style);

    var btn = document.createElement('button');
    btn.id = 'ff-btn';
    btn.textContent = '一键预填';
    document.body.appendChild(btn);

    var tip = document.createElement('div');
    tip.id = 'ff-tip';
    document.body.appendChild(tip);

    function showTip(msg, ok) {
        tip.textContent = msg;
        tip.style.background = ok ? '#1d9e75' : '#c0392b';
        tip.style.display = 'block';
        setTimeout(function () { tip.style.display = 'none'; }, 2000);
    }

    // 判断一个输入框是否匹配某个规则键
    function matchKey(el, key) {
        var k = key.toLowerCase();
        var hay = [
            el.getAttribute('name'),
            el.getAttribute('id'),
            el.getAttribute('placeholder'),
            el.getAttribute('aria-label'),
            el.className,
        ].join(' ').toLowerCase();
        // 也检查 label 文本
        if (el.labels) {
            for (var i = 0; i < el.labels.length; i++) {
                hay += ' ' + el.labels[i].textContent.toLowerCase();
            }
        }
        return hay.indexOf(k) >= 0;
    }

    function setNativeValue(el, value) {
        // 用原生 setter 触发 React/Vue 的受控组件更新
        var proto = Object.getPrototypeOf(el);
        var desc = Object.getOwnPropertyDescriptor(proto, 'value');
        if (desc && desc.set) {
            desc.set.call(el, value);
        } else {
            el.value = value;
        }
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function fill() {
        var inputs = document.querySelectorAll(
            'input:not([type=hidden]):not([type=submit]):not([type=button])' +
            ':not([type=checkbox]):not([type=radio]), textarea, select');
        var filled = 0, matched = 0;

        for (var i = 0; i < inputs.length; i++) {
            var el = inputs[i];
            var tag = el.tagName.toLowerCase();
            var value = null;

            for (var j = 0; j < FILL_KEYS.length; j++) {
                if (matchKey(el, FILL_KEYS[j])) {
                    value = RULES[FILL_KEYS[j]];
                    break;
                }
            }
            if (value === null) continue;
            matched++;

            try {
                if (tag === 'select') {
                    var opts = el.options;
                    for (var k = 0; k < opts.length; k++) {
                        if (opts[k].text.indexOf(value) >= 0 ||
                            opts[k].value.indexOf(value) >= 0) {
                            el.value = opts[k].value;
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                            filled++;
                            break;
                        }
                    }
                } else {
                    setNativeValue(el, value);
                    filled++;
                }
            } catch (e) { /* 忽略单个失败 */ }
        }

        showTip('已预填 ' + filled + ' 个字段（匹配 ' + matched + ' 个）', filled > 0);
    }

    btn.addEventListener('click', fill);
})();
