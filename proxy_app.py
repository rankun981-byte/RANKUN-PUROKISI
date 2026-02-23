"""
社会クイズ - URLを貼るとそのサイトをプロキシ経由で表示
使い方: python proxy_app.py → http://localhost:5000 を開く
"""

from flask import Flask, request, Response, render_template_string
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import re

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
}

HOME_HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>らんくんプロキシ</title>
  <link href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@400;700;900&family=M+PLUS+Rounded+1c:wght@400;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0f0e17;
      --surface: #1a1828;
      --accent: #ff6b6b;
      --accent2: #ffd93d;
      --accent3: #6bcb77;
      --text: #fffffe;
      --muted: #a7a9be;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'M PLUS Rounded 1c', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      position: relative;
    }

    .bubble {
      position: fixed;
      border-radius: 50%;
      opacity: 0.07;
      animation: float linear infinite;
      pointer-events: none;
    }
    @keyframes float {
      0% { transform: translateY(110vh) scale(0.8); }
      100% { transform: translateY(-20vh) scale(1.2); }
    }

    .container {
      position: relative;
      z-index: 10;
      text-align: center;
      padding: 40px 20px;
      width: 100%;
      max-width: 640px;
    }

    .mascot {
      font-size: 80px;
      animation: bounce 2s ease-in-out infinite;
      display: inline-block;
      margin-bottom: 4px;
    }
    @keyframes bounce {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-12px); }
    }

    h1 {
      font-family: 'Zen Maru Gothic', sans-serif;
      font-weight: 900;
      font-size: clamp(2rem, 6vw, 3.2rem);
      margin-bottom: 8px;
      background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      letter-spacing: -1px;
    }

    .subtitle {
      color: var(--muted);
      font-size: 1rem;
      margin-bottom: 36px;
      font-weight: 400;
    }
    .subtitle span {
      color: var(--accent2);
      font-weight: 700;
    }

    .input-card {
      background: var(--surface);
      border-radius: 24px;
      padding: 28px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.06);
    }

    .input-label {
      text-align: left;
      font-size: 0.85rem;
      color: var(--muted);
      margin-bottom: 10px;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }

    .input-row {
      display: flex;
      gap: 10px;
      margin-bottom: 16px;
    }

    input[type=text] {
      flex: 1;
      background: rgba(255,255,255,0.06);
      border: 2px solid rgba(255,255,255,0.1);
      border-radius: 14px;
      padding: 14px 18px;
      color: var(--text);
      font-family: 'M PLUS Rounded 1c', sans-serif;
      font-size: 0.95rem;
      outline: none;
      transition: border-color 0.2s, background 0.2s;
    }
    input[type=text]::placeholder { color: rgba(167,169,190,0.5); }
    input[type=text]:focus {
      border-color: var(--accent);
      background: rgba(255,107,107,0.06);
    }

    button {
      background: linear-gradient(135deg, var(--accent), #ff8e53);
      border: none;
      border-radius: 14px;
      padding: 14px 22px;
      color: white;
      font-family: 'M PLUS Rounded 1c', sans-serif;
      font-size: 1rem;
      font-weight: 800;
      cursor: pointer;
      transition: transform 0.15s, box-shadow 0.15s;
      box-shadow: 0 4px 16px rgba(255,107,107,0.4);
      white-space: nowrap;
    }
    button:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(255,107,107,0.5);
    }
    button:active { transform: translateY(0); }

    .error-msg {
      background: rgba(255,107,107,0.12);
      border: 1px solid rgba(255,107,107,0.3);
      border-radius: 10px;
      padding: 10px 16px;
      color: var(--accent);
      font-size: 0.88rem;
      margin-bottom: 12px;
      text-align: left;
    }

    .tips {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: center;
      margin-top: 18px;
    }
    .tip-badge {
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 20px;
      padding: 6px 14px;
      font-size: 0.78rem;
      color: var(--muted);
      cursor: pointer;
      transition: background 0.2s;
    }
    .tip-badge:hover {
      background: rgba(255,255,255,0.1);
      color: var(--text);
    }

    .footer {
      margin-top: 32px;
      color: rgba(167,169,190,0.4);
      font-size: 0.75rem;
    }
  </style>
</head>
<body>
  <div class="bubble" style="width:300px;height:300px;background:var(--accent);left:-100px;top:10%;animation-duration:18s;animation-delay:-5s;"></div>
  <div class="bubble" style="width:200px;height:200px;background:var(--accent2);right:-60px;top:40%;animation-duration:14s;animation-delay:-8s;"></div>
  <div class="bubble" style="width:150px;height:150px;background:var(--accent3);left:20%;bottom:0;animation-duration:20s;animation-delay:-2s;"></div>
  <div class="bubble" style="width:80px;height:80px;background:var(--accent);right:25%;top:20%;animation-duration:11s;animation-delay:-6s;"></div>

  <div class="container">
    <div class="mascot">😅</div>
    <h1>らんくんプロキシ</h1>
    <p class="subtitle">みたい<span>リンクを貼ってね</span>！プロキシ経由で開くよ🎉</p>

    <div class="input-card">
      <div class="input-label">🔗 URL を貼り付け</div>
      {% if error %}
      <div class="error-msg">⚠️ {{ error }}</div>
      {% endif %}
      <form method="GET" action="/go">
        <div class="input-row">
          <input type="text" name="url" placeholder="https://example.com" value="{{ url or '' }}" autofocus autocomplete="off" spellcheck="false">
          <button type="submit">開く →</button>
        </div>
      </form>
      <div class="tips">
        <span class="tip-badge" onclick="go('https://www.google.com')">Google</span>
        <span class="tip-badge" onclick="go('https://www.wikipedia.org')">Wikipedia</span>
        <span class="tip-badge" onclick="go('https://news.yahoo.co.jp')">Yahoo!ニュース</span>
        <span class="tip-badge" onclick="go('https://www.nicovideo.jp')">ニコニコ</span>
        <span class="tip-badge" onclick="go('https://script.google.com/macros/s/AKfycbxm0tNsWUp7nhFboWBgldo4diYLQIHKCB1YaCa2OI6gwe50HxuEbRb5wHh53rjaaWwArw/exec')">🎬 しあtube</span>
      </div>
    </div>

    <p class="footer">らんくんプロキシ · サーバー経由でウェブを閲覧できるよ</p>
  </div>

  <script>
    function go(url) {
  window.location.href = '/go?url=' + encodeURIComponent(url);
}
  location.href = '/go?url=' + encodeURIComponent(url);
}
      document.querySelector('input[name=url]').value = url;
      document.querySelector('form').submit();
    }
  </script>
</body>
</html>
"""

PROXY_BAR = """<div id="__ran_bar__" style="
  position:fixed;top:0;left:0;right:0;z-index:2147483647;
  background:linear-gradient(135deg,#0f0e17ee,#1a1828ee);
  backdrop-filter:blur(10px);
  color:#fffffe;padding:8px 14px;
  display:flex;align-items:center;gap:10px;
  font-family:sans-serif;
  font-size:13px;border-bottom:1px solid rgba(255,255,255,0.08);
  box-shadow:0 2px 16px rgba(0,0,0,0.5);">
  <span style="font-weight:800;color:#ff6b6b;white-space:nowrap;font-size:14px;">🐾 らんくん</span>
  <input id="__ran_url__" type="text" value="{CURRENT_URL}"
    style="flex:1;padding:5px 12px;border-radius:8px;
    border:1px solid rgba(255,255,255,0.15);
    background:rgba(255,255,255,0.07);color:#fffffe;
    font-size:12px;outline:none;font-family:monospace;">
  <button onclick="location.href='/go?url='+encodeURIComponent(document.getElementById('__ran_url__').value)"
    style="padding:5px 14px;background:linear-gradient(135deg,#ff6b6b,#ff8e53);
    color:white;border:none;border-radius:8px;cursor:pointer;font-weight:800;
    font-size:12px;white-space:nowrap;">移動</button>
  <a href="/" style="color:#a7a9be;text-decoration:none;white-space:nowrap;font-size:12px;">🏠ホーム</a>
</div>
<div style="height:46px;"></div>"""


def rewrite_html(html, base_url):
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return html

    for tag in soup.find_all("a", href=True):
        h = tag["href"].strip()
        if h.startswith(("javascript:", "#", "mailto:", "tel:")):
            continue
        abs_url = urljoin(base_url, h)
        if abs_url.startswith("http"):
            tag["href"] = f"/go?url={quote(abs_url, safe='')}"

    for tag in soup.find_all("link", href=True):
        h = tag["href"].strip()
        abs_url = urljoin(base_url, h)
        if abs_url.startswith("http"):
            tag["href"] = f"/res?url={quote(abs_url, safe='')}"

    for tag in soup.find_all("img", src=True):
        abs_url = urljoin(base_url, tag["src"].strip())
        if abs_url.startswith("http"):
            tag["src"] = f"/res?url={quote(abs_url, safe='')}"

    for tag in soup.find_all("script", src=True):
        abs_url = urljoin(base_url, tag["src"].strip())
        if abs_url.startswith("http"):
            tag["src"] = f"/res?url={quote(abs_url, safe='')}"

    for tag in soup.find_all("form"):
        action = tag.get("action", "")
        if action and not action.startswith(("javascript:", "#")):
            abs_url = urljoin(base_url, action)
            tag["action"] = f"/go?url={quote(abs_url, safe='')}"

    for tag in soup.find_all("base"):
        tag.decompose()

    bar_html = PROXY_BAR.replace("{CURRENT_URL}", base_url)
    bar_soup = BeautifulSoup(bar_html, "html.parser")

    if soup.body:
        soup.body.insert(0, bar_soup)
    elif soup.html:
        soup.html.insert(0, bar_soup)
    else:
        soup.insert(0, bar_soup)

    return str(soup)


@app.route("/")
def index():
    return render_template_string(HOME_HTML)


@app.route("/go")
def go():
    url = request.args.get("url", "").strip()
    if not url:
        return render_template_string(HOME_HTML, error="URLが空です。URLを貼り付けてね！")

    if not url.startswith(("http://", "https://")):
        url = "https://" + url
        from urllib.parse import urlparse, parse_qs
    parsed = urlparse(url)
    if parsed.hostname and "google" in parsed.hostname:
        params = parse_qs(parsed.query)
        if "q" in params:
            search_query = params["q"][0]
            url = f"https://www.google.com/search?q={quote(search_query)}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        content_type = resp.headers.get("Content-Type", "")

        if "text/html" in content_type:
            rewritten = rewrite_html(resp.text, resp.url)
            return Response(rewritten, content_type="text/html; charset=utf-8")
        else:
            return Response(resp.content, content_type=content_type)

    except requests.exceptions.ConnectionError:
        return render_template_string(HOME_HTML, url=url, error=f"接続できませんでした: {url}")
    except requests.exceptions.Timeout:
        return render_template_string(HOME_HTML, url=url, error="タイムアウトしました。")
    except Exception as e:
        return render_template_string(HOME_HTML, url=url, error=f"エラー: {str(e)}")


@app.route("/res")
def resource():
    url = request.args.get("url", "").strip()
    if not url:
        return Response("", status=400)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        content_type = resp.headers.get("Content-Type", "application/octet-stream")

        if "text/css" in content_type:
            base = url
            css = resp.text
            def replace_url(m):
                inner = m.group(1).strip("'\" ")
                if inner.startswith("data:"):
                    return m.group(0)
                abs_u = urljoin(base, inner)
                return f"url('/res?url={quote(abs_u, safe='')}')"
            css = re.sub(r'url\(([^)]+)\)', replace_url, css)
            return Response(css, content_type=content_type)

        return Response(resp.content, content_type=content_type)
    except Exception:
        return Response("", status=502)


if __name__ == "__main__":
    print("=" * 50)
    print("🐾 らんくんプロキシ 起動！")
    print("👉 http://localhost:5000 を開いてね")
    print("=" * 50)
    app.run(debug=False, host="0.0.0.0", port=5000)
