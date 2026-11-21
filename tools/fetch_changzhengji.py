#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取人民网《长征记》全书连载（曲爱国/张从田著，华夏出版社授权人民网发布）。
用途：本地研究+结构化事实抽取。页面声明"请勿转载"——因此只存 research_private，
不发布原文到项目前端；仅提取"事件-时间-地点-人物"事实要素并注明出处引用。

章节目录来自 https://dangshi.people.com.cn/GB/146570/406330/index.html
每章 URL 形如 https://dangshi.people.com.cn/n1/2016/0804/c406330-28612048.html
"""
import re
import subprocess
import time
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "research_private" / "ebooks" / "changzhengji_people"
INDEX = "https://dangshi.people.com.cn/GB/146570/406330/index.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def fetch(url: str, retries: int = 3) -> str:
    # 人民网证书 hostname 不匹配，urllib 会报 CERTIFICATE_VERIFY_FAILED；
    # curl -k 可正常抓取（与 WebFetch/浏览器一致），故用 subprocess 调 curl。
    for attempt in range(retries):
        try:
            r = subprocess.run(
                ["curl", "-sL", "-k", "--max-time", "30", "-A", HEADERS["User-Agent"], url],
                capture_output=True, timeout=40,
            )
            raw = r.stdout
            # 人民网老页面为 GBK/GB2312；先按 UTF-8 试，失败或乱码则按 GBK
            try:
                text = raw.decode("utf-8")
                if "\ufffd" in text or "Ķ" in text[:500]:  # 乱码特征
                    text = raw.decode("gbk", errors="ignore")
            except UnicodeDecodeError:
                text = raw.decode("gbk", errors="ignore")
            if len(text) > 1000:
                return text
        except Exception:
            pass
        if attempt == retries - 1:
            raise RuntimeError(f"抓取失败: {url}")
        time.sleep(1.5 * (attempt + 1))
    return ""


def clean(html: str) -> str:
    # 去脚本样式
    html = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.I)
    html = re.sub(r"<style[\s\S]*?</style>", "", html, flags=re.I)
    # 取正文容器（人民网正文在 .show_text 或 rm_txt_con）
    m = re.search(r'<div[^>]*class="[^"]*(?:show_text|rm_txt_con|content)[^"]*"[^>]*>([\s\S]*?)</div>\s*</div>', html, re.I)
    body = m.group(1) if m else html
    # 去标签、留段落
    body = re.sub(r"<br\s*/?>", "\n", body, flags=re.I)
    body = re.sub(r"</p>", "\n", body, flags=re.I)
    body = re.sub(r"<[^>]+>", "", body)
    body = (body.replace("&nbsp;", " ").replace("&ldquo;", "“").replace("&rdquo;", "”")
                .replace("&mdash;", "—").replace("&lsquo;", "‘").replace("&rsquo;", "’")
                .replace("&amp;", "&"))
    lines = [ln.strip() for ln in body.split("\n") if ln.strip()]
    return "\n".join(lines)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    html = fetch(INDEX)
    # 目录页链接为相对路径 /n1/2016/.../c406330-xxxx.html，补全域名
    links = re.findall(r'href="(/n1/2016/[^"]*c406330[^"]*\.html)"', html)
    links += re.findall(r'href="(https?://dangshi\.people\.com\.cn/n1/2016/[^"]*c406330[^"]*\.html)"', html)
    seen, urls = set(), []
    for u in links:
        full = u if u.startswith("http") else "https://dangshi.people.com.cn" + u
        if full not in seen:
            seen.add(full); urls.append(full)
    print(f"目录页发现 {len(urls)} 个章节链接")

    manifest = []
    for i, url in enumerate(urls, 1):
        try:
            page = fetch(url)
            text = clean(page)
            # 标题：从 <title> 提取
            tm = re.search(r"<title>([^<]+)</title>", page)
            title = tm.group(1).strip() if tm else f"第{i}章"
            if len(text) < 500:
                print(f"  [{i}] {title} 正文过短({len(text)}字)，跳过")
                continue
            fn = f"ch{i:02d}.txt"
            (OUT / fn).write_text(f"# {title}\n来源: {url}\n\n{text}", encoding="utf-8")
            manifest.append({"no": i, "title": title, "url": url, "file": fn, "chars": len(text)})
            print(f"  [{i}] {title[:30]} {len(text)}字")
        except Exception as e:
            print(f"  [{i}] 失败 {url}: {e}")
        time.sleep(0.6)

    import json
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"完成：{len(manifest)} 章 -> {OUT}")


if __name__ == "__main__":
    main()
