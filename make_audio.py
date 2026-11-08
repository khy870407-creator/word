"""words.json을 읽어 edge-tts로 단어/예문 MP3를 만들고 words.js를 다시 생성합니다.

사용법:
    python make_audio.py           # 없는 파일만 새로 만들기
    python make_audio.py --force   # 모든 음성 다시 만들기
"""
import asyncio
import json
import sys
from pathlib import Path

import edge_tts

ROOT = Path(__file__).parent
VOICE = "en-US-JennyNeural"
WORD_RATE = "-15%"     # 단어는 조금 천천히
EXAMPLE_RATE = "-10%"
CONCURRENCY = 4


def audio_paths(word: str) -> tuple[Path, Path]:
    name = word.lower().replace(" ", "_") + ".mp3"
    return ROOT / "audio" / "word" / name, ROOT / "audio" / "example" / name


async def synth(text: str, rate: str, out: Path, force: bool, sem: asyncio.Semaphore) -> bool:
    if out.exists() and not force:
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    async with sem:
        for attempt in range(3):
            try:
                await edge_tts.Communicate(text, VOICE, rate=rate).save(str(out))
                return True
            except Exception as e:  # 네트워크 오류 시 재시도
                if attempt == 2:
                    raise RuntimeError(f"'{text}' 생성 실패: {e}") from e
                await asyncio.sleep(1 + attempt)


def write_words_js(words: list[dict]) -> None:
    body = json.dumps(words, ensure_ascii=False, indent=2)
    (ROOT / "words.js").write_text(
        "// make_audio.py가 words.json에서 자동 생성한 파일입니다. 직접 고치지 말고 words.json을 수정하세요.\n"
        f"const WORDS = {body};\n",
        encoding="utf-8",
    )


async def main() -> None:
    force = "--force" in sys.argv
    words = json.loads((ROOT / "words.json").read_text(encoding="utf-8"))
    sem = asyncio.Semaphore(CONCURRENCY)

    tasks = []
    for w in words:
        word_mp3, example_mp3 = audio_paths(w["word"])
        w["audio"] = word_mp3.relative_to(ROOT).as_posix()
        w["exampleAudio"] = example_mp3.relative_to(ROOT).as_posix()
        tasks.append(synth(w["word"], WORD_RATE, word_mp3, force, sem))
        tasks.append(synth(w["example"], EXAMPLE_RATE, example_mp3, force, sem))

    made = sum(await asyncio.gather(*tasks))
    write_words_js(words)
    print(f"음성 {made}개 생성 (전체 {len(tasks)}개), words.js 갱신 완료")


if __name__ == "__main__":
    asyncio.run(main())
