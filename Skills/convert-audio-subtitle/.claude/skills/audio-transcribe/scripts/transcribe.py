"""Transcribe an audio (or video) file with faster-whisper on CPU.

Usage:
  python transcribe.py INPUT OUT_DIR [--lang ja] [--model large-v3-turbo]
                       [--prompt "context sentence / glossary"] [--hotwords "term1 term2"]
                       [--chunk-min 10] [--resume]

Writes to OUT_DIR, named after INPUT:
  <name>.raw.srt       timestamped raw transcript
  <name>.raw.txt       plain raw text, one segment per line
  <name>.segments.txt  "id|text" lines, the format used for contextual correction
  <name>.log           progress log (tail it to follow progress)
  <name>.audio.tmp     the decoded audio (115 MB per hour), deleted when the run ends

Long recordings: the audio is decoded once to the temporary file, then transcribed in
windows of about --chunk-min minutes, so memory use does not grow with the length of
the recording. A window always ends in a pause found by voice detection, never inside
a sentence. A recording shorter than one window is transcribed in one pass.

Interrupted run: run the same command again with --resume. It continues from the end
of the last window that was completed. A recording shorter than one window starts
again from the beginning.

The log always ends with "DONE" or with a "Traceback": a failure at any stage
(ffmpeg missing, unreadable file, model download) is written to it as well.
"""
import argparse
import os
import re
import subprocess
import time
import traceback

import numpy as np
from faster_whisper import WhisperModel
from faster_whisper.vad import VadOptions, get_speech_timestamps

RATE = 16000     # samples per second: what Whisper expects
MARGIN_S = 60.0  # audio read past the wanted end of a window, in which a pause is looked for
WINDOW_DONE = "window done, next starts at"  # log line that --resume reads


def ts(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def secs(t):
    h, m, s = t.strip().replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def read_srt(path):
    """Cues as (start seconds, end seconds, text). A cue may have no text."""
    lines = open(path, encoding="utf-8-sig").read().splitlines()

    def cue_at(i):
        return lines[i].strip().isdigit() and i + 1 < len(lines) and "-->" in lines[i + 1]

    cues, i = [], 0
    while i < len(lines):
        if not cue_at(i):
            i += 1
            continue
        a, b = lines[i + 1].split("-->")
        i += 2
        text = []
        while i < len(lines) and not cue_at(i):
            text.append(lines[i])
            i += 1
        cues.append((secs(a), secs(b), "\n".join(text).strip()))
    return cues


def read_window(path, start, length):
    """Samples from START seconds, LENGTH seconds long (None: to the end), as float32 in [-1, 1]."""
    count = -1 if length is None else int(length * RATE)
    audio = np.fromfile(path, dtype=np.int16, count=count, offset=int(start * RATE) * 2).astype(np.float32)
    audio /= 32768.0
    return audio


def pause_near(audio, target):
    """Where to end a window: seconds from the start of AUDIO, in the middle of the pause
    closest to TARGET. None when AUDIO has no speech at all."""
    speech = get_speech_timestamps(audio, VadOptions(min_silence_duration_ms=500))
    if not speech:
        return None
    ends = [0.0] + [s["end"] / RATE for s in speech]
    starts = [s["start"] / RATE for s in speech] + [len(audio) / RATE]
    # the middle of each pause; a window is never cut to less than half its wanted length
    pauses = [(a + b) / 2 for a, b in zip(ends, starts) if b > a and (a + b) / 2 >= target / 2]
    if not pauses:
        return target  # one unbroken stretch of speech: cut at the wanted length
    return min(pauses, key=lambda p: abs(p - target))


ap = argparse.ArgumentParser()
ap.add_argument("input")
ap.add_argument("out_dir")
ap.add_argument("--lang", default=None, help="fr, en, ja, zh, pt, it ... (omit to auto-detect)")
ap.add_argument("--model", default="large-v3-turbo")
ap.add_argument("--prompt", default=None, help="initial_prompt: context, names, jargon, in the audio's language")
ap.add_argument("--hotwords", default=None, help="space-separated terms to bias recognition toward")
ap.add_argument("--beam", type=int, default=5)
ap.add_argument("--threads", type=int, default=os.cpu_count() or 4)
ap.add_argument("--chunk-min", type=float, default=10.0,
                help="minutes of audio transcribed and held in memory at a time (0: the whole recording at once)")
ap.add_argument("--resume", action="store_true",
                help="continue an interrupted run from the last completed window")
args = ap.parse_args()

os.makedirs(args.out_dir, exist_ok=True)
name = os.path.splitext(os.path.basename(args.input))[0]
base = os.path.join(args.out_dir, name)

# What an interrupted run left behind: the segments of its completed windows are kept, and
# the window it was in is done again. That window starts in a pause, so nothing is cut.
kept, lang, resume_at, already_done = [], args.lang, 0.0, False
if args.resume and os.path.exists(base + ".raw.srt") and os.path.exists(base + ".log"):
    old_log = open(base + ".log", encoding="utf-8").read()
    already_done = old_log.rstrip().endswith("DONE")
    window_ends = re.findall(rf"^{WINDOW_DONE} ([\d.]+) s$", old_log, re.M)
    if window_ends and not already_done:
        resume_at = float(window_ends[-1])
        kept = [c for c in read_srt(base + ".raw.srt") if c[1] <= resume_at + 0.05]
        found = re.search(r"^language=(\w+)", old_log, re.M)
        if lang is None and found:
            lang = found.group(1)

# Opened before anything can fail, so that the log exists and records the failure.
log = open(base + ".log", "a" if resume_at > 0 or already_done else "w", encoding="utf-8")


def say(msg):
    print(msg, flush=True)
    log.write(msg + "\n")
    log.flush()


def transcribe(pcm_path, total):
    # keep downloaded models inside the skill folder, not in the user's home cache
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
    say(f"loading model {args.model} (downloaded into {models_dir} the first time, which takes several minutes)...")
    model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=args.threads,
                         download_root=models_dir)

    language = lang
    chunk = args.chunk_min * 60 if args.chunk_min > 0 else None
    pos = resume_at
    if args.resume:
        say(f"resuming at {ts(pos)}, after segment {len(kept)}" if pos > 0
            else "nothing to resume (no window was completed): starting again from the beginning")

    announced = False
    started = time.time()
    with open(base + ".raw.srt", "w", encoding="utf-8") as srt, \
         open(base + ".raw.txt", "w", encoding="utf-8") as txt, \
         open(base + ".segments.txt", "w", encoding="utf-8") as seg_f:

        def write(i, start, end, text):
            srt.write(f"{i}\n{ts(start)} --> {ts(end)}\n{text}\n\n")
            txt.write(text + "\n")
            seg_f.write(f"{i}|{text}\n")
            for f in (srt, txt, seg_f):
                f.flush()

        for i, (start, end, text) in enumerate(kept, 1):
            write(i, start, end, text)
        i = len(kept)

        while pos < total:
            last = chunk is None or pos + chunk + MARGIN_S >= total
            offset = int(pos * RATE) / RATE
            audio = read_window(pcm_path, offset, None if last else chunk + MARGIN_S)
            if not len(audio):
                break
            if not last:
                cut = pause_near(audio, chunk)
                if cut is None:  # no speech in this window: nothing to transcribe
                    pos = offset + chunk
                    say(f"{WINDOW_DONE} {pos:.3f} s")
                    continue
                audio = audio[: int(cut * RATE)]
            segments, info = model.transcribe(
                audio,
                language=language,
                beam_size=args.beam,
                vad_filter=True,  # skip silence/music: fewer hallucinated lines
                vad_parameters={"min_silence_duration_ms": 500},
                condition_on_previous_text=False,  # avoids repetition loops on long files
                initial_prompt=args.prompt,
                hotwords=args.hotwords,
            )
            if not announced:
                say(f"language={info.language} (p={info.language_probability:.2f}) duration={total:.0f}s model={args.model}")
                announced = True
            language = info.language  # detected once, then the same for every window

            for seg in segments:
                i += 1
                end = offset + seg.end
                write(i, offset + seg.start, end, seg.text.strip())
                say(f"[{ts(end)}] {end / total:5.1%} elapsed={(time.time() - started) / 60:.1f}min")
            if last:
                break
            pos = offset + cut  # in a pause: the next window starts there
            say(f"{WINDOW_DONE} {pos:.3f} s")
    say("DONE")


def main():
    # Decode with ffmpeg ourselves: faster-whisper's PyAV loader breaks with some PyAV versions,
    # and this accepts any audio/video container ffmpeg can read. Decoding to a file rather than
    # into memory is what keeps a recording of several hours from filling the memory.
    pcm_path = base + ".audio.tmp"
    try:
        say("decoding audio with ffmpeg...")
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", args.input, "-vn", "-ac", "1", "-ar", str(RATE),
             "-f", "s16le", pcm_path],
            capture_output=True, check=True,
        )
        total = os.path.getsize(pcm_path) / 2 / RATE  # 2 bytes per sample
        if total <= 0:
            raise RuntimeError(f"ffmpeg returned no audio for {args.input}: does the file have an audio stream?")
        transcribe(pcm_path, total)
    finally:
        try:
            os.remove(pcm_path)
        except OSError:
            pass


try:
    if already_done:
        say("the previous run was complete: nothing to resume")
        say("DONE")
    else:
        main()
except BaseException as e:  # Ctrl+C included: the log must never just stop
    if isinstance(e, subprocess.CalledProcessError) and e.stderr:
        say("ffmpeg: " + e.stderr.decode("utf-8", "replace").strip())
    say(traceback.format_exc())
    raise
finally:
    log.close()
