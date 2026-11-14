---
name: audio-transcribe
description: Transcribe an audio or video file (French, English, Japanese, Chinese, Portuguese, Italian, or other Whisper languages) into clean text, using faster-whisper locally on CPU and then a context-aware correction pass that fixes misheard jargon, names and homophones based on the recording's subject. Main use is professional meeting recordings (Teams/Zoom/phone), producing a transcript and optionally minutes with decisions and action items. Use when the user asks to transcribe, get the text of, write down what is said in, or take minutes from an audio/video file (mp3, wav, m4a, mp4, mkv...), optionally translated.
---

**Confidentiality:** recordings of professional meetings are confidential.
- **The audio stays on the machine.** Decoding and Whisper run locally.
- **The transcript text does not.** You read it to correct, summarise or translate it, so it is sent to the model like the rest of the conversation. Tell the user this in one sentence before the first transcription of a session.
- **If the user says the text must stay on the machine,** do steps 0 to 2 only, give them the raw files without reading them, and say that the result is uncorrected.
- Never send the audio or the transcript anywhere else: no web service, artifact, doc connector, email or message unless the user explicitly asks. Write outputs only to local files.

# Audio transcription with contextual correction

Two stages, both required unless the user asks for the raw transcript only:
1. **Raw transcription**: `scripts/transcribe.py` runs Whisper (faster-whisper, int8, CPU) and writes timestamped segments.
2. **Contextual correction**: you read the raw transcript, work out the subject, and fix what Whisper got wrong because it lacked context (domain terms, proper nouns, homophones, garbled lines). This is the step that makes the result usable; never skip it.

`SKILL_DIR` below means the folder containing this file (`<project>/.claude/skills/audio-transcribe`). Keep everything inside it: the venv, and the models in `SKILL_DIR/models`. Don't install or cache anything in the user's home folder.

## 0. Setup (once per machine, and after every fresh git clone)

`SKILL_DIR/.venv/` and `SKILL_DIR/models/` are **not in git** (`.gitignore`): about 290 MB and 1.6 GB. Check both every time the skill is called, before anything else, and recreate whatever is missing.

**Venv.** If `SKILL_DIR/.venv/Scripts/python` (Windows) or `.venv/bin/python` doesn't exist:

```bash
python -m venv "SKILL_DIR/.venv" && "SKILL_DIR/.venv/Scripts/python" -m pip install -q -r "SKILL_DIR/requirements.lock.txt"
```

`requirements.lock.txt` pins every package, including dependencies, to the versions last known to work, so a rebuilt venv matches it exactly. It was generated and tested with Python 3.14.

**Which Python.** The venv needs a Python for which every package has a wheel. On 2026-11-14, `onnxruntime` (required by faster-whisper) had no Windows wheel for Python 3.15, so neither file installs there; 3.14 works. Before creating the venv:
- Check the version of `python`. If it is 3.15 or newer, list the installed versions with `py -0p` and create the venv with the newest one up to 3.14, e.g. `py -3.14 -m venv "SKILL_DIR/.venv"`.
- If none is installed, ask the user to install Python 3.14 beside the other one, `winget install --id Python.Python.3.14 -e`. Versions install side by side, and only this venv uses it.
- To check whether a newer Python has become usable, without installing it: `"SKILL_DIR/.venv/Scripts/python" -m pip download --no-deps --only-binary=:all: --python-version 3.15 --platform win_amd64 -r "SKILL_DIR/requirements.lock.txt" -d <scratch folder>`.

If the lock file fails on a supported Python, install `requirements.txt` instead (only `faster-whisper` is pinned there) and tell the user the versions may differ. After deliberately upgrading packages and checking that a transcription still works, regenerate the lock file with `"SKILL_DIR/.venv/Scripts/python" -m pip freeze > "SKILL_DIR/requirements.lock.txt"`.

**Model.** If `SKILL_DIR/models/models--mobiuslabsgmbh--faster-whisper-large-v3-turbo/snapshots/*/model.bin` doesn't exist, download it now rather than inside the transcription run, so the user sees the download separately (about 1.6 GB; run it in the background and tell the user it is a one-time download):

```bash
"SKILL_DIR/.venv/Scripts/python" -c "import sys; from faster_whisper import download_model; download_model('large-v3-turbo', cache_dir=sys.argv[1])" "SKILL_DIR/models"
```

Use the same command with `large-v3` (about 3 GB) when the user asks for that model.

Two warnings during the download are harmless: one about symlinks on Windows (the files are copied instead, which works) and one about unauthenticated requests to the Hugging Face Hub (no account is needed).

- Use whichever Python actually starts; on Windows the `py -3.x` launcher can point to removed installs, so try plain `python` first.
- If the venv exists but fails to start (for example after the project folder was moved or renamed), delete `SKILL_DIR/.venv` and recreate it with the command above. Models in `SKILL_DIR/models` don't need downloading again.
- `ffmpeg` must be on PATH (check `which ffmpeg`). The script decodes audio with ffmpeg itself, because faster-whisper's own PyAV loader crashes with some PyAV versions (`unexpected keyword argument 'metadata_errors'`).
- If a model is still missing when `transcribe.py` runs, it downloads it from Hugging Face into `SKILL_DIR/models` itself, so the log stays on its `loading model` line for several minutes.

## 1. Inspect the input and gather context

- `ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name -of compact FILE` gives the duration and tells you whether the file has an audio stream. Video files are fine as input.
- Collect context before transcribing. Look at the file and folder names, what the user said, and any notes or documents next to the file. You need the language, the subject, likely proper names (speakers, places, brands) and jargon.
- If the language is unknown, omit `--lang` and the script auto-detects it. For short or mixed-language files, check the detected `language=` line in the log.
- **For a meeting**, if the user hasn't given these, ask in one short question (all optional; skip what they don't know):
  - who attended (names and roles),
  - the topic or agenda,
  - company, product, project or client names, and internal acronyms,
  - whether they want minutes as well as the transcript.

  This is the most valuable context: names and acronyms are what Whisper gets wrong most in meetings. Pass them as `--hotwords`, and use them in a `--prompt` written as a natural sentence in the meeting's language, e.g. `--prompt "Réunion projet Atlas avec Sophie Martin, Kenji Sato et l'équipe SRE : budget Q3, migration AWS, KPI."`.
- **Mixed-language meetings** (e.g. French discussion full of English tech terms): force the main language. Whisper copes with embedded foreign words, and the correction pass fixes their spelling. If whole parts of the meeting are in another language, leave `--lang` unset, or run the script once per part on cut files (`ffmpeg -ss START -to END`).

## 2. Raw transcription

```bash
"SKILL_DIR/.venv/Scripts/python" -u "SKILL_DIR/scripts/transcribe.py" INPUT OUT_DIR --lang ja \
   [--prompt "..."] [--hotwords "..."] [--model large-v3-turbo] [--chunk-min 10] [--resume]
```

`OUT_DIR` defaults to a `<name>_transcript` folder next to the recording, unless the user asks for another location. Put every file of this job there (corrections, glossary, minutes).

Run it in the background for anything longer than a few minutes, then wait for `DONE` or `Traceback` in `OUT_DIR/<name>.log`. The log starts with `decoding audio` and `loading model`, then has one line per segment and a `window done` line after each window; a failure at any stage, including ffmpeg's own error message, is written to it. After the first ~30 segments, read the log to estimate the total time and tell the user.

**Long recordings.** The audio is decoded once to `OUT_DIR/<name>.audio.tmp` (115 MB of disk per hour, deleted at the end) and transcribed in windows of about 10 minutes, each ending in a pause, so memory does not grow with the length. Measured with the `tiny` model on 2026-11-14: about 0.5 GB at peak for both 1 h and 2 h of audio, against 2 GB for 1 h in a single pass; the chosen model adds its own memory on top. Windows cause no loss or duplication at the cuts. A few words may differ from a single pass, as Whisper's output varies with how the audio is grouped.

**Interrupted run** (laptop asleep, closed session, Ctrl+C): run the same command again with `--resume`. It keeps the segments of every completed window and redoes the window that was cut short; in a test the result was identical to an uninterrupted run. A recording shorter than one window starts again from the beginning. A run that had finished is left as it is.

Options:
- `--lang`: `fr`, `en`, `ja`, `zh`, `pt`, `it`. Force it when you know the language: auto-detect on the first 30 s can be wrong (music intros, accents).
- `--prompt`: a short sentence **in the audio's language** that uses the expected vocabulary and the punctuation style you want. Whisper then favours those spellings. Only add it if you already know the context; a wrong prompt can push Whisper towards the wrong words.
- `--hotwords`: names and technical terms that are known in advance, separated by spaces.
- `--model`: `large-v3-turbo` is the default and a good balance. Use `large-v3` for the best accuracy, especially in Japanese and Chinese or on poor-quality audio; it is about 2–3× slower. Use `medium` or `small` only for quick drafts.
- `--chunk-min`: minutes per window (default 10). Lower it on a machine short of memory; `0` transcribes in one pass, which needs about 2 GB per hour of audio.
- `--resume`: continue an interrupted run, see above.

Speed reference: on a 4-core laptop i7, large-v3-turbo int8 ran at about 3× real time (a 2h17 recording took 42 min).

Outputs in `OUT_DIR`: `<name>.raw.srt`, `<name>.raw.txt`, `<name>.segments.txt` (`id|text`), `<name>.log`.

## 3. Contextual correction (the important part)

### 3a. Build the context profile
Read the first ~150 segments plus samples from the middle and the end. Then write down, for yourself:
- **Subject and register**: lecture, interview, meeting, tutorial, podcast… formal or casual, one speaker or several.
- **Glossary of recurring misrecognitions**: the same term transcribed several wrong ways, mapped to the correct form. The clue is a word that is nonsense in context but sounds like a domain term. Typical cases:
  - **Japanese**: wrong kanji with the same reading (e.g. 横仕方 / 横小型目 → 横四方固め; 好転 → 後転; 先行 → 宣告). Katakana garbles of loanwords. Missing punctuation.
  - **Chinese**: homophones with different characters. Simplified and traditional characters mixed together; normalise to whichever the speaker's region uses, or what the user asks for.
  - **French / Italian / Portuguese**: proper nouns, anglicisms, and elision or gender agreement errors from fast speech. In Portuguese, keep pt-BR or pt-PT spelling consistent with the speaker.
  - **English**: proper nouns, acronyms, and homophones (their/there, to/two).
  - **All languages**: numbers, units, names of people and organisations.
- **Hallucinations to delete**: lines Whisper commonly invents on silence or music, such as "ご視聴ありがとうございました", "Sous-titres réalisés par la communauté d'Amara.org", "Thanks for watching", "Legendas pela comunidade Amara.org", "字幕由…提供". Also delete runs of the exact same line repeated over a non-speech gap.

Check for repeated lines quickly (use `PYTHONIOENCODING=utf-8` on Windows, otherwise printing Japanese or Chinese crashes):
```bash
PYTHONIOENCODING=utf-8 python -c "import collections,sys;L=[l.split('|',1)[1].strip() for l in open(sys.argv[1],encoding='utf-8')];print(collections.Counter(L).most_common(15))" OUT_DIR/<name>.segments.txt
```
Short stock phrases repeated across the file (e.g. "let's try again") are normal speech. A suspicious repetition looks like many identical lines in a row, or text placed where there is no speech.

### 3b. Correct chunk by chunk
Read `<name>.segments.txt` in chunks of about 300–350 lines. For each chunk, write `OUT_DIR/corr_NN.txt` with one `id|corrected text` line for **every** id in the chunk.

Rules:
- **Fix, don't rewrite.** Keep the speaker's wording, word order and register. Correct only misrecognised words, the spelling of names and terms, punctuation and capitalisation.
- Apply the glossary consistently across the whole file, and add to it as new terms appear.
- Repair a garbled line only when the meaning is clear from the lines around it or from the subject. If it isn't, keep the closest reading and mark it `[?]`. Don't invent content.
- Fill in light punctuation (。、 in Japanese and Chinese, normal punctuation elsewhere) so the text reads well.
- Keep fillers (えーと, euh, um) only if the user wants a verbatim transcript; by default, remove pure fillers.
- Drop a hallucinated segment by writing `id|` with empty text.
- Keep the same ids and don't merge segments. The timestamps depend on the ids.

### 3c. Finalize
```bash
python "SKILL_DIR/scripts/finalize.py" OUT_DIR/<name>.raw.srt OUT_DIR/<name> OUT_DIR/corr_*.txt
```
This produces `<name>.txt` (clean paragraphs, split at pauses of 2 s or more; change with `--gap`), `<name>.timestamped.txt` (`[hh:mm:ss] text`) and `<name>.srt`. It reports any ids that were not corrected; fix those and run it again. A segment whose text is empty, in the raw transcript or after correction, is left out of the outputs and counted as dropped.

Then delete the `corr_*.txt` files. Keep the `.raw.*` files so the user can compare.

**Subtitle timing (when the user wants an `.srt` to watch with the video).** Whisper often stretches a segment's start back over the music or silence before it, so a cue can appear tens of seconds before it is spoken. Fix this by re-timing to the detected speech; pass the translated `.srt` too so both keep the same timings:
```bash
"SKILL_DIR/.venv/Scripts/python" "SKILL_DIR/scripts/retime_srt.py" INPUT OUT_DIR/<name>.srt [OUT_DIR/<name>.fr.srt] --lead 2 --tail 1
```
This writes `<name>.retimed.srt` next to each input file. Each cue starts `--lead` seconds before its speech and ends `--tail` seconds after it. It works in 10-minute windows like the transcription (`--chunk-min`), with a temporary audio file next to the first `.srt`: about 0.3 GB at peak, and about 1 min per 2 h of audio.

### 3d. Very long recordings (over ~2 h, or more than ~1500 segments)
A full line-by-line pass on 4–8 h costs a lot of time and usage. The conversation will also be summarized partway through, and corrections decided early can be forgotten. So keep the state **on disk**, not in your head:

1. **`OUT_DIR/context.md`**: write the context profile from 3a here (subject, attendees and roles, projects, acronyms, language notes). Re-read it at the start of every section, and after any context summary.
2. **`OUT_DIR/glossary.tsv`**: one `heard<TAB>corrected` line per recurring misrecognition. Add to it as you go; never keep the list only in memory. Only add entries that are safe to replace everywhere: an exact wrong spelling that can't be a legitimate word in another context. If a "heard" form is ambiguous, leave it out and fix it by hand.
3. **Agree on scope with the user.** Before correcting, give the user the timeline: one line per ~15 min of what was being discussed. Ask which parts deserve a full correction pass (e.g. decisions, a client discussion), unless they already said. Default if they don't care: the first ~30 min, to build the glossary, plus any section where decisions or action items appear.
4. **Full pass** (3b rules) on the chosen sections only, writing `corr_NN.txt` and extending `glossary.tsv`.
5. **Everything else gets the glossary only**: `finalize.py` applies it automatically to every segment not in a `corr_*.txt` file:
   ```bash
   python "SKILL_DIR/scripts/finalize.py" OUT_DIR/<name>.raw.srt OUT_DIR/<name> OUT_DIR/corr_*.txt --glossary OUT_DIR/glossary.tsv
   ```
   Before running it, check quickly for the hallucination patterns from 3a across the whole file (the repeated-lines command), and drop them with `id|` lines in a `corr_drop.txt`.
6. In the report, say which time ranges got a full correction pass and which got glossary only. Keep `glossary.tsv` and `context.md` in OUT_DIR: they can be reused for the next meeting with the same team (pass the names as `--hotwords` too).

Minutes for very long meetings: summarize each hour into `OUT_DIR/minutes_part_NN.md` (same sections as step 4, with timestamps) as you go, then merge them into `<name>.minutes.md`. Remove duplicates, and keep a decision only in its final form if it was revised later in the meeting.

### Speakers (meetings)
Whisper does not identify speakers, and this skill has no voice-based speaker separation. Don't invent speaker labels. Only add a label such as `Sophie :` to a segment when the text makes the speaker clear: someone is addressed by name and replies, someone introduces themselves, or a role is obvious ("as your manager…"). Mark these labels as inferred in the report. If the user needs reliable speaker labels, tell them that adding pyannote-audio diarization (it needs a free Hugging Face token and installs PyTorch) is the next step, and offer to set it up.

## 4. Optional meeting minutes

If the user asks for minutes, write `OUT_DIR/<name>.minutes.md` from the **corrected** transcript, in the meeting's language unless they ask for another. Sections:
- **Context**: date if known, attendees, purpose.
- **Summary**: 5–10 bullets.
- **Decisions**
- **Action items**: who, what, deadline if stated. Write "owner not stated" rather than guessing.
- **Open questions / risks**

Every point must be traceable to the transcript; add `[hh:mm:ss]` references for decisions and action items. Don't add conclusions nobody stated.

## 5. Optional translation

Only translate if the user asks. Use the same chunked `id|text` method on the **corrected** text, write `tr_NN.txt` files, and run `finalize.py` again with a different OUT_BASE (e.g. `<name>.fr`). Translate meaning, not word for word. Keep the domain's established terms in the form people in that field use in the target language (some fields keep the original-language terms, e.g. Japanese martial-arts vocabulary in French).

## 6. Report to the user

- Where the output files are (full paths), the detected or forced language, the model used, and how long it took.
- The main contextual corrections you applied: a short glossary of "heard → corrected" pairs, so the user can check them.
- How many segments are marked `[?]` or were dropped as hallucinations.
- Known limits: Whisper doesn't tell speakers apart, and overlapping speech and music beds reduce accuracy.
