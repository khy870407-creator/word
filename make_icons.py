"""words.json의 "icon" 값(예: "fluent-emoji-flat:school")에 해당하는 SVG를 Iconify에서 내려받고,
아이콘 출처/라이선스 기록(ICON_CREDITS.md)과 words.js를 다시 만듭니다.

사용법:
    python make_icons.py           # 없는 아이콘만 내려받기
    python make_icons.py --force   # 모든 아이콘 다시 받기

아이콘이 없는 단어는 "icon" 값을 넣지 않으면 됩니다(사이트에서 아이콘 자리를 비워 둠).
"""
import asyncio
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import make_audio

ROOT = Path(__file__).parent
API = "https://api.iconify.design"
HEADERS = {"User-Agent": "word-explorer-icon-builder"}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def icon_path(icon: str) -> Path:
    prefix, name = icon.split(":", 1)
    return ROOT / "icons" / prefix / f"{name}.svg"


def main() -> None:
    force = "--force" in sys.argv
    words = json.loads((ROOT / "words.json").read_text(encoding="utf-8"))
    used = [w for w in words if w.get("icon")]

    # 1) SVG 내려받기
    made = 0
    for w in used:
        out = icon_path(w["icon"])
        if out.exists() and not force:
            continue
        prefix, name = w["icon"].split(":", 1)
        svg = fetch(f"{API}/{prefix}/{urllib.parse.quote(name)}.svg")
        if not svg.lstrip().startswith(b"<svg"):
            raise RuntimeError(f"{w['icon']} 아이콘을 찾을 수 없습니다")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(svg)
        made += 1

    # 2) 아이콘 세트 라이선스 정보 가져오기
    prefixes = sorted({w["icon"].split(":", 1)[0] for w in used})
    sets = json.loads(fetch(f"{API}/collections?prefixes={','.join(prefixes)}")) if prefixes else {}

    # 3) 출처 기록 작성
    lines = [
        "# 아이콘 출처 및 사용 조건",
        "",
        "이 사이트의 단어 아이콘은 [Iconify](https://iconify.design/)에서 제공하는 오픈소스 아이콘 세트에서 가져왔습니다.",
        "Iconify는 여러 아이콘 세트를 모아 검색·배포하는 서비스이며, 각 아이콘의 사용 조건은 **원래 아이콘 세트의 라이선스**를 따릅니다.",
        "",
        "> 이 파일은 `make_icons.py`가 `words.json`을 바탕으로 자동 생성합니다. 직접 고치지 마세요.",
        "",
        "## 사용한 아이콘 세트",
        "",
    ]
    for p in prefixes:
        info = sets.get(p, {})
        lic = info.get("license", {})
        author = info.get("author", {})

        # 라이선스 전문을 아이콘 폴더에 함께 저장 (GitHub 링크인 경우)
        lic_url = lic.get("url", "")
        lic_file = ROOT / "icons" / p / "LICENSE.txt"
        if lic_url.startswith("https://github.com/") and "/blob/" in lic_url and (force or not lic_file.exists()):
            raw = lic_url.replace("https://github.com/", "https://raw.githubusercontent.com/").replace("/blob/", "/", 1)
            lic_file.write_bytes(fetch(raw))
        lic_rel = lic_file.relative_to(ROOT).as_posix() if lic_file.exists() else None

        lines += [
            f"### {info.get('name', p)} (`{p}`)",
            "",
            f"- 제작: [{author.get('name', '-')}]({author.get('url', '')})",
            f"- 라이선스: [{lic.get('title', '-')}]({lic.get('url', '')})",
            f"- Iconify 페이지: https://icon-sets.iconify.design/{p}/",
        ]
        if lic_rel:
            lines.append(f"- 라이선스 전문: [{lic_rel}]({lic_rel})")
        if lic.get("spdx") == "MIT":
            lines += [
                "- 사용 조건 요약: 개인·교육·상업적 용도 모두 무료로 사용, 수정, 배포할 수 있습니다.",
                "  배포할 때 저작권 표시와 MIT 라이선스 전문을 함께 포함해야 합니다(이 파일과 원본 LICENSE 링크로 표시).",
                "  아이콘은 \"있는 그대로\" 제공되며 제작자는 어떠한 보증도 하지 않습니다.",
            ]
        lines.append("")

    lines += ["## 단어별 아이콘", "", "| 번호 | 단어 | 뜻 | 아이콘 이름 | 파일 |", "|---|---|---|---|---|"]
    for w in used:
        rel = icon_path(w["icon"]).relative_to(ROOT).as_posix()
        lines.append(f"| {w['id']} | {w['word']} | {w['meaning']} | `{w['icon']}` | [{rel}]({rel}) |")
    lines += ["", f"아이콘을 붙인 단어: {len(used)}개 / 전체 {len(words)}개 (알맞은 아이콘이 없는 단어는 비워 둠)", ""]
    (ROOT / "ICON_CREDITS.md").write_text("\n".join(lines), encoding="utf-8")

    # 4) words.js 갱신(음성은 이미 있으면 다시 만들지 않음)
    sys.argv = [sys.argv[0]]
    asyncio.run(make_audio.main())
    print(f"아이콘 {made}개 내려받음 (아이콘 사용 단어 {len(used)}개), ICON_CREDITS.md 갱신 완료")


if __name__ == "__main__":
    main()
