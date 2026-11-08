(() => {
  "use strict";

  const QUIZ_LENGTH = 10;
  const STORAGE_KEY = "word-explorer-learned";
  const ALL = "전체";

  const $ = (id) => document.getElementById(id);

  // ---------- 외운 단어 저장 ----------
  let learned = new Set();
  try {
    learned = new Set(JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"));
  } catch (e) { /* 저장소를 쓸 수 없어도 동작 */ }

  function saveLearned() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify([...learned])); } catch (e) {}
  }

  function toggleLearned(id) {
    learned.has(id) ? learned.delete(id) : learned.add(id);
    saveLearned();
    updateProgress();
  }

  function updateProgress() {
    $("learnedCount").textContent = learned.size;
    $("totalCount").textContent = WORDS.length;
    $("progressFill").style.width = (learned.size / WORDS.length) * 100 + "%";
  }

  // ---------- 공통 ----------
  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  // edge-tts로 만든 MP3를 재생하고, 파일이 없거나 실패하면 브라우저 음성으로 대신 읽음
  const player = new Audio();

  function speakFallback(text) {
    if (!("speechSynthesis" in window)) return;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-US";
    u.rate = 0.85;
    speechSynthesis.speak(u);
  }

  function play(src, text) {
    player.pause();
    if ("speechSynthesis" in window) speechSynthesis.cancel();
    if (!src) return speakFallback(text);
    player.src = src;
    // 다른 버튼을 눌러 재생이 중단된 경우(AbortError)는 대체 음성을 쓰지 않음
    player.play().catch((e) => { if (e.name !== "AbortError") speakFallback(text); });
  }
  player.addEventListener("error", () => speakFallback(player.dataset.text || ""));

  const playWord = (w) => { player.dataset.text = w.word; play(w.audio, w.word); };
  const playExample = (w) => { player.dataset.text = w.example; play(w.exampleAudio, w.example); };

  let category = ALL;
  const currentWords = () => category === ALL ? WORDS : WORDS.filter((w) => w.category === category);

  // Iconify 아이콘(icons/세트/이름.svg). 아이콘이 없는 단어는 null
  const iconSrc = (w) => w.icon ? "icons/" + w.icon.replace(":", "/") + ".svg" : null;

  function setIcon(img, w) {
    const src = iconSrc(w);
    img.classList.toggle("hidden", !src);
    if (src) img.src = src;
    else img.removeAttribute("src");
  }

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  // ---------- 주제 필터 ----------
  const select = $("category");
  [ALL, ...new Set(WORDS.map((w) => w.category))].forEach((c) => {
    const opt = el("option", "", c === ALL ? `전체 (${WORDS.length})` : `${c} (${WORDS.filter((w) => w.category === c).length})`);
    opt.value = c;
    select.appendChild(opt);
  });
  select.addEventListener("change", () => {
    category = select.value;
    refreshAll();
  });

  // ---------- 탭 ----------
  let view = "list";
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      view = tab.dataset.view;
      document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t === tab));
      document.querySelectorAll(".view").forEach((v) => v.classList.toggle("active", v.id === "view-" + view));
      if (view === "quiz") startQuiz();
      if (view === "spell") startSpell();
    });
  });

  function refreshAll() {
    renderList();
    flashIndex = 0;
    flashOrder = currentWords();
    renderFlash();
    if (view === "quiz") startQuiz();
    if (view === "spell") startSpell();
  }

  // ---------- 단어장 ----------
  function renderList() {
    const list = $("wordList");
    list.innerHTML = "";
    currentWords().forEach((w) => {
      const li = el("li", "word-item" + (learned.has(w.id) ? " learned" : ""));
      const main = el("div", "word-main");
      const head = el("div", "word-head");
      head.append(el("span", "word-en", w.word), el("span", "word-ko", w.meaning), el("span", "pos", w.partOfSpeech));
      const ex = el("button", "example example-btn", "💬 " + w.example);
      ex.setAttribute("aria-label", "예문 듣기: " + w.example);
      ex.addEventListener("click", () => playExample(w));
      main.append(head, ex, el("span", "example-ko", w.exampleKo));

      const btns = el("div", "item-buttons");
      const sp = el("button", "icon-btn", "🔊");
      sp.setAttribute("aria-label", w.word + " 발음 듣기");
      sp.addEventListener("click", () => playWord(w));
      const star = el("button", "icon-btn" + (learned.has(w.id) ? " on" : ""), learned.has(w.id) ? "⭐" : "☆");
      star.setAttribute("aria-label", "외운 단어 표시");
      star.addEventListener("click", () => {
        toggleLearned(w.id);
        renderList();
      });
      btns.append(sp, star);

      const src = iconSrc(w);
      if (src) {
        const img = el("img", "word-icon");
        img.src = src;
        img.alt = "";
        li.append(img);
      }
      li.append(main, btns);
      list.appendChild(li);
    });
  }

  // ---------- 플래시카드 ----------
  let flashOrder = currentWords();
  let flashIndex = 0;

  function renderFlash() {
    const w = flashOrder[flashIndex];
    if (!w) return;
    $("flashCard").classList.remove("flipped");
    $("flashWord").textContent = w.word;
    $("flashPos").textContent = w.partOfSpeech;
    setIcon($("flashIcon"), w);
    $("flashMeaning").textContent = w.meaning;
    $("flashExample").textContent = w.example;
    $("flashExampleKo").textContent = w.exampleKo;
    $("flashCounter").textContent = `${flashIndex + 1} / ${flashOrder.length}`;
    const btn = $("flashLearn");
    btn.classList.toggle("on", learned.has(w.id));
    btn.textContent = learned.has(w.id) ? "⭐ 외웠어요!" : "☆ 외웠어요";
  }

  $("flashCard").addEventListener("click", () => $("flashCard").classList.toggle("flipped"));
  $("flashPrev").addEventListener("click", () => {
    flashIndex = (flashIndex - 1 + flashOrder.length) % flashOrder.length;
    renderFlash();
  });
  $("flashNext").addEventListener("click", () => {
    flashIndex = (flashIndex + 1) % flashOrder.length;
    renderFlash();
  });
  $("flashSpeak").addEventListener("click", () => playWord(flashOrder[flashIndex]));
  $("flashSpeakExample").addEventListener("click", () => playExample(flashOrder[flashIndex]));
  $("flashLearn").addEventListener("click", () => {
    toggleLearned(flashOrder[flashIndex].id);
    renderFlash();
    renderList();
  });

  // ---------- 결과 화면 ----------
  function showResult(box, resultEl, score, total, wrongList, restart) {
    box.classList.add("hidden");
    resultEl.classList.remove("hidden");
    resultEl.innerHTML = "";
    const ratio = score / total;
    const msg = ratio === 1 ? "🏆 만점! 정말 대단해요!" : ratio >= 0.7 ? "🎉 아주 잘했어요!" : "💪 조금만 더 연습해 봐요!";
    resultEl.append(el("p", "", msg), el("p", "score", `${score} / ${total}`));
    if (wrongList.length) {
      resultEl.append(el("p", "", "다시 볼 단어"));
      const ul = el("ul");
      wrongList.forEach((w) => ul.appendChild(el("li", "", `${w.word} - ${w.meaning}`)));
      resultEl.appendChild(ul);
    }
    const again = el("button", "btn btn-main", "다시 하기");
    again.addEventListener("click", restart);
    resultEl.appendChild(again);
  }

  // ---------- 뜻 퀴즈 ----------
  let quiz = null;

  function startQuiz() {
    const pool = currentWords();
    quiz = { questions: shuffle(pool).slice(0, Math.min(QUIZ_LENGTH, pool.length)), index: 0, score: 0, wrong: [] };
    $("quizBox").classList.remove("hidden");
    $("quizResult").classList.add("hidden");
    renderQuiz();
  }

  function renderQuiz() {
    const w = quiz.questions[quiz.index];
    $("quizCounter").textContent = `${quiz.index + 1} / ${quiz.questions.length}번 문제`;
    $("quizWord").textContent = w.word;
    $("quizFeedback").textContent = "";
    $("quizFeedback").className = "feedback";
    $("quizNext").classList.add("hidden");
    $("quizIcon").classList.add("hidden");

    // 오답 보기는 전체 단어에서 뽑아 주제가 작아도 4지선다 유지
    const others = shuffle(WORDS.filter((x) => x.id !== w.id && x.meaning !== w.meaning)).slice(0, 3);
    const choices = shuffle([w, ...others]);
    const box = $("quizChoices");
    box.innerHTML = "";
    choices.forEach((c) => {
      const b = el("button", "choice", c.meaning);
      b.addEventListener("click", () => answerQuiz(b, c, w));
      box.appendChild(b);
    });
  }

  function answerQuiz(btn, chosen, answer) {
    const buttons = $("quizChoices").querySelectorAll(".choice");
    buttons.forEach((b) => {
      b.disabled = true;
      if (b.textContent === answer.meaning) b.classList.add("correct");
    });
    const fb = $("quizFeedback");
    if (chosen.id === answer.id) {
      quiz.score++;
      fb.textContent = "⭕ 정답이에요!";
      fb.classList.add("good");
    } else {
      btn.classList.add("wrong");
      quiz.wrong.push(answer);
      fb.textContent = `❌ 아쉬워요! 정답은 "${answer.meaning}"`;
      fb.classList.add("bad");
    }
    setIcon($("quizIcon"), answer); // 답을 고른 뒤에만 아이콘 공개
    playWord(answer);
    const next = $("quizNext");
    next.textContent = quiz.index + 1 < quiz.questions.length ? "다음 문제 ▶" : "결과 보기 🏁";
    next.classList.remove("hidden");
  }

  $("quizNext").addEventListener("click", () => {
    quiz.index++;
    if (quiz.index < quiz.questions.length) renderQuiz();
    else showResult($("quizBox"), $("quizResult"), quiz.score, quiz.questions.length, quiz.wrong, startQuiz);
  });
  $("quizSpeak").addEventListener("click", () => playWord(quiz.questions[quiz.index]));

  // ---------- 철자 쓰기 ----------
  let spell = null;

  function startSpell() {
    const pool = currentWords();
    spell = { questions: shuffle(pool).slice(0, Math.min(QUIZ_LENGTH, pool.length)), index: 0, score: 0, wrong: [] };
    $("spellBox").classList.remove("hidden");
    $("spellResult").classList.add("hidden");
    renderSpell();
  }

  function renderSpell() {
    const w = spell.questions[spell.index];
    spell.answered = false;
    spell.hintLevel = 0;
    $("spellCounter").textContent = `${spell.index + 1} / ${spell.questions.length}번 문제`;
    setIcon($("spellIcon"), w);
    $("spellMeaning").textContent = `${w.meaning} (${w.partOfSpeech})`;
    $("spellHint").textContent = "_ ".repeat(w.word.length).trim();
    $("spellFeedback").textContent = "";
    $("spellFeedback").className = "feedback";
    $("spellNext").classList.add("hidden");
    const input = $("spellInput");
    input.value = "";
    input.disabled = false;
    input.focus();
  }

  function showHint() {
    const w = spell.questions[spell.index].word;
    spell.hintLevel = Math.min(spell.hintLevel + 1, w.length - 1);
    $("spellHint").textContent = w.split("").map((ch, i) => (i < spell.hintLevel ? ch : "_")).join(" ");
  }

  $("spellForm").addEventListener("submit", (e) => {
    e.preventDefault();
    if (spell.answered) return;
    const w = spell.questions[spell.index];
    const value = $("spellInput").value.trim().toLowerCase();
    if (!value) return;
    spell.answered = true;
    $("spellInput").disabled = true;
    const fb = $("spellFeedback");
    if (value === w.word.toLowerCase()) {
      spell.score++;
      fb.textContent = "⭕ 정답이에요!";
      fb.classList.add("good");
    } else {
      spell.wrong.push(w);
      fb.textContent = `❌ 정답은 "${w.word}" 이에요`;
      fb.classList.add("bad");
    }
    $("spellHint").textContent = w.word.split("").join(" ");
    playWord(w);
    const next = $("spellNext");
    next.textContent = spell.index + 1 < spell.questions.length ? "다음 문제 ▶" : "결과 보기 🏁";
    next.classList.remove("hidden");
    next.focus();
  });

  $("spellNext").addEventListener("click", () => {
    spell.index++;
    if (spell.index < spell.questions.length) renderSpell();
    else showResult($("spellBox"), $("spellResult"), spell.score, spell.questions.length, spell.wrong, startSpell);
  });
  $("spellSpeak").addEventListener("click", () => playWord(spell.questions[spell.index]));
  $("spellShowHint").addEventListener("click", () => { if (!spell.answered) showHint(); });

  // ---------- 시작 ----------
  updateProgress();
  renderList();
  renderFlash();
})();
