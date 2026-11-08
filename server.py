"""영단어 탐험대 로컬 서버.

- 사이트 파일(index.html, audio/, icons/ 등)을 제공합니다.
- /api/unsplash/* 요청을 받아 서버에서 Unsplash API를 호출합니다.
  UNSPLASH_ACCESS_KEY는 서버에서만 읽고, 브라우저로 보내지 않습니다.

실행:
    python server.py            # http://localhost:8000
    python server.py --port 9000

키를 읽는 순서 (앞쪽이 우선):
    1. 실행할 때의 환경 변수 UNSPLASH_ACCESS_KEY
    2. .env.local
    3. .env
.env 파일은 API 요청마다 다시 읽으므로, 키를 넣거나 바꾼 뒤 서버를 다시 켤 필요가 없습니다.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_FILES = [ROOT / ".env.local", ROOT / ".env"]  # 앞쪽이 우선
UNSPLASH_API = "https://api.unsplash.com"

# 브라우저에 공개해도 되는 파일만 제공 (.env, .py, .git 등은 절대 제공하지 않음)
PUBLIC_EXTENSIONS = {".html", ".css", ".js", ".json", ".svg", ".mp3", ".txt", ".png", ".jpg", ".ico"}


def read_env_file(path: Path) -> dict[str, str]:
    """KEY=VALUE 형식의 간단한 .env 파서 (주석 #, 따옴표 지원)."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def get_setting(name: str, default: str = "") -> str:
    if os.environ.get(name):
        return os.environ[name].strip()
    for path in ENV_FILES:
        value = read_env_file(path).get(name, "").strip()
        if value:
            return value
    return default


def with_utm(url: str, app_name: str) -> str:
    """Unsplash 가이드라인: 사진작가/Unsplash 링크에 utm 파라미터를 붙여야 함."""
    if not url:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}utm_source={urllib.parse.quote(app_name)}&utm_medium=referral"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    # ---------- 정적 파일 ----------
    def send_head(self):
        path = urllib.parse.urlparse(self.path).path
        parts = [p for p in urllib.parse.unquote(path).split("/") if p]
        # 숨김 파일/폴더(.env, .git, .claude ...)와 상위 폴더 접근 차단
        if any(p.startswith(".") for p in parts):
            self.send_error(HTTPStatus.NOT_FOUND)
            return None
        if parts and Path(parts[-1]).suffix and Path(parts[-1]).suffix.lower() not in PUBLIC_EXTENSIONS:
            self.send_error(HTTPStatus.NOT_FOUND)
            return None
        return super().send_head()

    def list_directory(self, path):  # 폴더 목록 노출 금지
        self.send_error(HTTPStatus.NOT_FOUND)
        return None

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    # ---------- API ----------
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == "/api/unsplash/status":
            return self.send_json(200, {"configured": bool(get_setting("UNSPLASH_ACCESS_KEY"))})
        if url.path == "/api/unsplash/search":
            return self.unsplash_search(urllib.parse.parse_qs(url.query))
        if url.path.startswith("/api/"):
            return self.send_json(404, {"error": "없는 API 주소예요."})
        return super().do_GET()

    def unsplash_search(self, query: dict):
        key = get_setting("UNSPLASH_ACCESS_KEY")
        if not key:
            return self.send_json(503, {
                "error": "UNSPLASH_ACCESS_KEY가 설정되지 않았어요. 프로젝트 폴더의 .env 파일에 키를 넣어 주세요."
            })

        q = (query.get("query", [""])[0]).strip()
        if not q:
            return self.send_json(400, {"error": "검색어(query)를 넣어 주세요."})
        try:
            per_page = max(1, min(int(query.get("per_page", ["6"])[0]), 30))
        except ValueError:
            per_page = 6

        params = {"query": q, "per_page": per_page, "content_filter": "high"}  # 어린이용: 엄격한 필터
        orientation = query.get("orientation", [""])[0]
        if orientation in ("landscape", "portrait", "squarish"):
            params["orientation"] = orientation

        req = urllib.request.Request(
            f"{UNSPLASH_API}/search/photos?{urllib.parse.urlencode(params)}",
            headers={"Authorization": f"Client-ID {key}", "Accept-Version": "v1"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            messages = {
                401: "Unsplash가 키를 거부했어요. .env의 UNSPLASH_ACCESS_KEY가 Access Key가 맞는지 확인해 주세요.",
                403: "Unsplash 요청 한도를 넘었거나 권한이 없어요. 잠시 후 다시 시도해 주세요.",
            }
            return self.send_json(502, {"error": messages.get(e.code, f"Unsplash 오류 ({e.code})")})
        except (urllib.error.URLError, TimeoutError):
            return self.send_json(502, {"error": "Unsplash에 연결하지 못했어요. 인터넷 연결을 확인해 주세요."})

        app = get_setting("UNSPLASH_APP_NAME", "word_explorer")
        photos = [{
            "id": p["id"],
            "alt": p.get("alt_description") or p.get("description") or "",
            "width": p.get("width"),
            "height": p.get("height"),
            "color": p.get("color"),
            "thumb": p["urls"]["thumb"],
            "small": p["urls"]["small"],
            "regular": p["urls"]["regular"],
            "photoPage": with_utm(p["links"]["html"], app),
            "photographer": p["user"]["name"],
            "photographerPage": with_utm(p["user"]["links"]["html"], app),
            "unsplashPage": with_utm("https://unsplash.com/", app),
        } for p in data.get("results", [])]
        return self.send_json(200, {"total": data.get("total", 0), "photos": photos})

    def send_json(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):  # 요청 주소만 기록 (키는 주소에 없음)
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    port = 8000
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    status = "설정됨" if get_setting("UNSPLASH_ACCESS_KEY") else "아직 없음 (.env에 넣어 주세요)"
    print(f"영단어 탐험대: http://localhost:{port}")
    print(f"UNSPLASH_ACCESS_KEY: {status}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
