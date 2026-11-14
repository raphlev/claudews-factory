# Audio transcription with Claude Code

Turns the speech in an audio or video file into clean text. Built for professional meetings, and it works for any recording (lectures, interviews, tutorials).

- **Languages:** French, English, Japanese, Chinese, Portuguese, Italian (and the other languages Whisper supports).
- **The audio stays on your PC:** the speech-to-text step runs locally, with no web service.
- **Context-aware:** after the raw transcription, Claude corrects names, acronyms, jargon and words Whisper misheard, based on what the recording is about.

> **What leaves your PC.** The audio never does. The transcript text does: Claude
> reads it to correct it, write minutes or translate it, so it is sent to Claude
> like anything else in the conversation. If the text of a recording must stay on
> your PC, ask for the raw transcription only: you get Whisper's uncorrected
> files, and Claude does not read them.

## What's in this folder

```
README.md                             this file
.claude/skills/audio-transcribe/      the reusable skill
  SKILL.md                            instructions Claude follows
  scripts/transcribe.py               step 1: speech to raw text (Whisper)
  scripts/finalize.py                 step 3: applies Claude's corrections (and glossary), writes the final files
  scripts/retime_srt.py               optional: re-times subtitles to the detected speech (no cue shown during intros/music)
  requirements.lock.txt               every Python package of the skill's .venv, pinned to the versions last known to work
  requirements.txt                    fallback: only faster-whisper pinned, used when the lock file does not install
  models/                             Whisper model (large-v3-turbo, 1.6 GB), downloaded once   (not in git)
  .venv/                              Python environment with faster-whisper                    (not in git)
input/                                your own recordings and subtitles                         (not in git)
```

The first test was a judo video in Japanese: transcribed in Japanese, re-timed
to the speech, then translated into French subtitles with the same timings.

## Large files not in git

`.gitignore` leaves out the files that are too big for git:

| Not in git | Size | How to get it back |
|---|---|---|
| `.claude/skills/audio-transcribe/models/` | 1.6 GB | Claude downloads it from Hugging Face the first time the skill is used (SKILL.md, step 0). |
| `.claude/skills/audio-transcribe/.venv/` | 290 MB | Claude recreates it from `requirements.lock.txt` the first time the skill is used (about 1 minute). |
| Recordings and videos (`*.mp4`, `*.mp3`, `*.mkv`, `*.wav`, `*.m4a`), `input/`, `*_transcript/` folders | — | Keep them outside git; they are your own data. |

So after a fresh clone, the first transcription takes a few extra minutes for the one-time download (about 1.9 GB). To do it in advance, ask Claude: `Set up the audio-transcribe skill`.

## How to use it

1. Open Claude Code in this folder (`Skills/convert-audio-subtitle` in the repository). The skill is only available from here, or from a project you copied it into (see "Use it in another project").
2. Ask in plain words, for example:
   - `Transcribe D:\Meetings\2026-11-05-weekly.m4a`
   - `/audio-transcribe D:\Rec\call.mp3, meeting in French with Sophie Martin and Kenji Sato about the Atlas project, I also want minutes`
   - `Transcribe interview.mp3 (Portuguese, Brazil) and translate it into English`
3. Claude asks for any context you haven't given: attendees, agenda, project or client names, acronyms, and whether you want minutes. All of it is optional, but it noticeably improves accuracy on names and acronyms.
4. Claude runs the transcription in the background and tells you how long it will take. It then reviews and corrects the text and gives you the results.

### Results

They are written to a `<name>_transcript` folder next to the recording (or wherever you ask):

| File | Content |
|---|---|
| `<name>.txt` | Clean corrected transcript, in paragraphs |
| `<name>.timestamped.txt` | Same text, one line per segment with `[hh:mm:ss]` |
| `<name>.srt` | Same text in subtitle format |
| `<name>.minutes.md` | Minutes, if requested: summary, decisions, action items with time references |
| `<name>.raw.*` | Whisper's uncorrected output, to compare with |
| `<name>.log` | Progress, and the reason when a transcription stops |

While a transcription runs, the folder also holds `<name>.audio.tmp`, the
decoded audio (115 MB per hour). It is deleted at the end.

Claude also lists the main corrections it made ("heard → corrected"), so you can check them.

## How it works

1. **Raw transcription:** `faster-whisper` with the Whisper `large-v3-turbo` model, on the CPU. Silences and music are filtered out to avoid made-up lines. The names and terms you provide are given to Whisper to steer its spelling.
2. **Contextual correction:** Claude reads the transcript, identifies the subject, and builds a list of recurring mistakes, such as the same name spelled several ways or a Japanese/Chinese word written with the wrong characters. It then corrects the text section by section, without rewriting what people said. Invented lines are deleted, and unclear passages are marked `[?]`.
3. **Finalization:** `finalize.py` puts the corrected text back onto the original timestamps and writes the files above.

## Speed and accuracy

- On this laptop (i7-1165G7, no NVIDIA GPU), it runs at about 3× real time: a 1-hour meeting takes about 20 min, and a 2h17 recording took 42 min. Claude's correction pass comes on top of that.
- For the best accuracy (difficult audio, Japanese or Chinese), ask for the `large-v3` model. It is 2–3× slower and downloads another 3 GB into `models/` the first time.

## Very long recordings (4 h, 8 h…)

Transcription handles long files. At the speed above, count about 1 h 20 for 4 h and 2 h 40 for 8 h.

- **Memory does not grow with the length.** The recording is transcribed in windows of about 10 minutes, each ending in a pause, so a 2-hour recording needs no more memory than a 1-hour one: about 0.5 GB in a test with the smallest model, plus the memory of the model you use.
- **An interruption does not lose the work.** If the laptop goes to sleep or the session closes, ask Claude to resume the transcription: it continues from the last completed window. Keeping the laptop plugged in still saves time.

For the correction step, Claude switches to a lighter mode above about 2 h:
- It first shows you a timeline (what was discussed every ~15 min) and asks which parts deserve a full correction, such as decisions or a client discussion.
- The list of corrections it finds is saved in `glossary.tsv` (one line per correction, "heard → corrected"). It is applied automatically to all the other parts, so names and acronyms are right everywhere.
- The meeting context (attendees, projects, acronyms) is saved in `context.md`.
- Minutes are written hour by hour, then merged.

Keep `glossary.tsv` and `context.md`: Claude can reuse them for the next meeting with the same team.

## Limitations

- **No speaker identification.** Whisper doesn't know who is talking. Claude only adds a name when the conversation makes it obvious (for example, someone is addressed by name) and labels it as deduced. Reliable "who said what" would need an extra tool (pyannote); ask Claude if you need it.
- Overlapping voices, poor microphones and background music lower accuracy.
- Very short recordings in an unknown language may be detected wrongly. Tell Claude the language when you know it.

## Use it in another project

Copy the `.claude/skills/audio-transcribe` folder into the other project's `.claude/skills/`. To save space, you can copy it without `models/` and `.venv/`; Claude recreates them the first time (one-time download of about 1.9 GB).

Requirements:

- **Python 3.10 to 3.14.** On 2026-11-14 one of the packages, `onnxruntime`, did not exist yet for Python 3.15 on Windows. If your only Python is 3.15, install 3.14 beside it with `winget install --id Python.Python.3.14 -e`: versions install side by side, and Claude uses 3.14 for this skill only.
- **`ffmpeg` on the PATH.** To install it on Windows: `winget install --id Gyan.FFmpeg -e`, then open a new PowerShell.

## Troubleshooting

- **The skill doesn't start after the folder was moved or renamed:** delete `.claude/skills/audio-transcribe/.venv` and ask Claude to recreate it (about 1 minute). The model doesn't need downloading again.
- **A transcription stops:** the reason is at the end of `<name>.log` in the results folder, including ffmpeg's own message when the file could not be read. Once the cause is fixed, ask Claude to resume it.
- **The setup fails with "No matching distribution found":** your Python is too recent for one of the packages. Install Python 3.14 as described under "Use it in another project", and ask Claude to set up the skill again.
- **The skill isn't offered:** check that Claude Code was opened in this folder. Project skills are only visible from their own project.
