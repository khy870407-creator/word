# 영단어 탐험대

초등학교 5·6학년을 위한 영단어 학습 사이트예요. 단어 50개를 소리로 듣고, 카드로 외우고, 퀴즈로 확인할 수 있어요.

## 사용 방법

`index.html`을 브라우저로 열면 바로 시작돼요. 설치할 것도 없고 인터넷도 필요 없어요.

- **📖 단어장**: 뜻, 품사, 예문 보기. 🔊로 발음 듣기, ☆로 외운 단어 표시
- **🃏 카드**: 카드를 눌러 뒤집으며 외우기
- **❓ 뜻 퀴즈**: 4지선다 10문제
- **✏️ 철자**: 뜻을 보고 영어 단어 쓰기 (글자 힌트, 소리 힌트)

주제(학교, 자연, 행동 등 9가지)를 고르면 모든 모드가 그 주제 단어로 바뀌어요.

## 폴더 구성

| 파일 | 설명 |
|---|---|
| `index.html`, `style.css`, `app.js` | 사이트 |
| `words.json` | 단어 원본 데이터 (단어는 여기서 고쳐요) |
| `words.js` | 사이트가 읽는 단어 파일 (자동 생성) |
| `audio/` | 단어·예문 발음 MP3 100개 |
| `icons/` | 단어 그림 SVG 35개와 라이선스 |
| `make_audio.py` | 발음 MP3 생성 + `words.js` 갱신 |
| `make_icons.py` | 그림 내려받기 + `ICON_CREDITS.md`·`words.js` 갱신 |

## 단어 바꾸기

1. `words.json`을 수정해요. 그림을 넣으려면 `"icon": "fluent-emoji-flat:이름"`을 추가해요.
2. Python 3와 edge-tts를 준비해요: `python -m pip install edge-tts`
3. 아래 명령을 실행해요. 새 발음과 그림을 받아 오고 `words.js`를 다시 만들어요.

```bash
python make_icons.py
```

모든 발음을 다시 만들려면 `python make_audio.py --force`를 실행해요.

## 출처

- 발음: [edge-tts](https://github.com/rany2/edge-tts) (Microsoft Edge 온라인 음성, `en-US-JennyNeural`)
- 그림: [Fluent Emoji](https://github.com/microsoft/fluentui-emoji) © Microsoft Corporation, MIT 라이선스, [Iconify](https://iconify.design/) 제공. 자세한 내용은 [ICON_CREDITS.md](ICON_CREDITS.md)를 참고하세요.
