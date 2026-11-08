# 영단어 탐험대

초등학교 5·6학년을 위한 영단어 학습 사이트예요. 단어 50개를 소리로 듣고, 카드로 외우고, 퀴즈로 확인할 수 있어요.

## 사용 방법

`index.html`을 브라우저로 열면 바로 시작돼요. 설치할 것도 없고 인터넷도 필요 없어요.

- **📖 단어장**: 뜻, 품사, 예문 보기. 🔊로 발음 듣기, ☆로 외운 단어 표시
- **🃏 카드**: 카드를 눌러 뒤집으며 외우기
- **❓ 뜻 퀴즈**: 4지선다 10문제
- **✏️ 철자**: 뜻을 보고 영어 단어 쓰기 (글자 힌트, 소리 힌트)

주제(학교, 자연, 행동 등 9가지)를 고르면 모든 모드가 그 주제 단어로 바뀌어요.

## 서버로 실행하기 (Unsplash 사진 검색용)

학습 기능은 `index.html`을 더블클릭해도 모두 동작해요. Unsplash 사진 검색은 비밀 키가 필요해서 **서버를 켰을 때만** 동작해요.
키는 서버(`server.py`)만 읽고 브라우저 코드에는 들어가지 않아요.

1. [Unsplash 개발자 페이지](https://unsplash.com/oauth/applications)에서 앱을 만들고 **Access Key**를 복사해요. Secret Key는 필요 없어요.
2. `.env.example`을 복사해 `.env`를 만들고 `UNSPLASH_ACCESS_KEY=` 뒤에 키를 붙여 넣어요. `.env`는 Git에 올라가지 않아요.
3. 서버를 켜요.

   ```bash
   python server.py
   ```

4. 브라우저에서 http://localhost:8000 을 열어요. (`index.html`을 더블클릭해서 열면 사진 검색은 동작하지 않아요.)

| 주소 | 설명 |
|---|---|
| `/api/unsplash/status` | 키가 설정됐는지 확인 (`{"configured": true}`) |
| `/api/unsplash/search?query=school&per_page=6` | 사진 검색. 사진 주소와 사진작가 출처 링크를 돌려줘요 |

- 키를 읽는 순서: 실행할 때의 환경 변수 → `.env.local` → `.env`
- `.env`는 요청할 때마다 다시 읽어서, 키를 바꾼 뒤 서버를 다시 켤 필요가 없어요.
- 서버는 이 컴퓨터(`127.0.0.1`)에서만 접속할 수 있고, `.env`, `.py`, `.git` 같은 파일은 브라우저에 보내지 않아요.
- Unsplash 사진을 화면에 쓸 때는 사진작가 이름과 Unsplash 링크를 함께 보여 줘야 해요(Unsplash API 가이드라인). 검색 결과에 필요한 링크가 들어 있어요.

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
| `server.py` | 로컬 서버 (사이트 제공 + Unsplash 검색 API) |
| `.env.example` | 환경 변수 예시. 복사해서 `.env`로 써요 |

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
