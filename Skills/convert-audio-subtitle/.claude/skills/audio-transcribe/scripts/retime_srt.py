"""Re-time SRT cues to the speech actually heard, so subtitles don't appear during music/intros.

Whisper often stretches a segment's start back over the silence or music before it
(e.g. a cue shown 40 s before the sentence is spoken). This runs Silero VAD (bundled
with faster-whisper) on the media file and, for each cue, moves its start to the first
speech inside it (minus --lead) and its end to the last speech inside it (plus --tail).
Cues are only ever shortened, never moved outside their original range, and
never overlap the previous cue. Cues with no detected speech are left unchanged.

Usage:
  python retime_srt.py MEDIA IN.srt [IN2.srt ...] [--lead 2.0] [--tail 1.0] [--suffix .retimed]
                       [--chunk-min 10]

All the SRT files must share the same timings (e.g. original + translation); each one
is written next to itself as <name><suffix>.srt.

Long recordings: the audio is decoded once to a temporary file next to the first SRT
(115 MB per hour, deleted at the end), and speech is detected in windows of about
--chunk-min minutes, each ending in a pause, so memory use does not grow with the
length of the recording.
"""
import argparse
import os
import subprocess

import numpy as np
from faster_whisper.vad import VadOptions, get_speech_timestamps

RATE = 16000     # samples per second: what the voice detection expects
MARGIN_S = 60.0  # audio read past the wanted end of a window, in which a pause is looked for
SPILL = 1.0      # seconds: shorter overlaps with a cue belong to the neighbouring cue

ap = argparse.ArgumentParser()
ap.add_argument("media")
ap.add_argument("srts", nargs="+")
ap.add_argument("--lead", type=float, default=2.0, help="seconds shown before speech starts")
ap.add_argument("--tail", type=float, default=1.0, help="seconds kept after speech ends")
ap.add_argument("--suffix", default=".retimed")
ap.add_argument("--chunk-min", type=float, default=10.0,
                help="minutes of audio held in memory at a time (0: the whole recording at once)")
args = ap.parse_args()


def secs(t):
    h, m, s = t.strip().replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def ts(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def parse(path):
    """Cues as [index, start, end, text]. A cue may have no text, so the file is read
    cue by cue rather than split on blank lines. utf-8-sig also accepts files with a BOM."""
    lines = open(path, encoding="utf-8-sig").read().splitlines()

    def cue_at(i):
        return lines[i].strip().isdigit() and i + 1 < len(lines) and "-->" in lines[i + 1]

    cues, i = [], 0
    while i < len(lines):
        if not cue_at(i):
            i += 1
            continue
        idx = lines[i].strip()
        a, b = lines[i + 1].split("-->")
        i += 2
        text = []
        while i < len(lines) and not cue_at(i):
            text.append(lines[i])
            i += 1
        cues.append([idx, secs(a), secs(b), "\n".join(text).strip()])
    return cues


def read_window(path, start, length):
    """Samples from START seconds, LENGTH seconds long (None: to the end), as float32 in [-1, 1]."""
    count = -1 if length is None else int(length * RATE)
    audio = np.fromfile(path, dtype=np.int16, count=count, offset=int(start * RATE) * 2).astype(np.float32)
    audio /= 32768.0
    return audio


def detect_speech(pcm_path, total):
    """Speech as (start, end) seconds over the whole recording, detected window by window."""
    opts = VadOptions(min_silence_duration_ms=300)
    chunk = args.chunk_min * 60 if args.chunk_min > 0 else None
    found, pos = [], 0.0
    while pos < total:
        last = chunk is None or pos + chunk + MARGIN_S >= total
        offset = int(pos * RATE) / RATE
        audio = read_window(pcm_path, offset, None if last else chunk + MARGIN_S)
        if not len(audio):
            break
        speech = [(s["start"] / RATE, s["end"] / RATE) for s in get_speech_timestamps(audio, opts)]
        if last:
            found += [(offset + a, offset + b) for a, b in speech]
            break
        # end the window in the pause closest to the wanted length, never before half of it
        ends = [0.0] + [b for _, b in speech]
        starts = [a for a, _ in speech] + [len(audio) / RATE]
        pauses = [(a + b) / 2 for a, b in zip(ends, starts) if b > a and (a + b) / 2 >= chunk / 2]
        cut = min(pauses, key=lambda p: abs(p - chunk)) if pauses else chunk
        found += [(offset + a, offset + b) for a, b in speech if a < cut]
        pos = offset + cut
    return found


# Decode with ffmpeg to a file rather than into memory, so that a recording of several
# hours does not fill the memory.
pcm_path = os.path.splitext(args.srts[0])[0] + ".audio.tmp"
try:
    print("decoding audio...", flush=True)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", args.media, "-vn", "-ac", "1", "-ar", str(RATE),
         "-f", "s16le", pcm_path],
        capture_output=True, check=True,
    )
    total = os.path.getsize(pcm_path) / 2 / RATE  # 2 bytes per sample
    if total <= 0:
        raise SystemExit(f"ffmpeg returned no audio for {args.media}: does the file have an audio stream?")
    print("detecting speech...", flush=True)
    speech = detect_speech(pcm_path, total)
except subprocess.CalledProcessError as e:
    raise SystemExit("ffmpeg could not read the media file: "
                     + (e.stderr or b"").decode("utf-8", "replace").strip())
finally:
    try:
        os.remove(pcm_path)
    except OSError:
        pass

base = parse(args.srts[0])
new_times, changed, prev_end = [], 0, 0.0
for _, start, end, _ in base:
    # speech overlapping the cue; drop short spill-over pieces of speech that belongs
    # mostly to the neighbouring cue (e.g. the previous sentence ending 0.4 s into this cue)
    inside = [(max(a, start), min(b, end)) for a, b in speech if b > start and a < end
              and ((a >= start and b <= end) or min(b, end) - max(a, start) >= SPILL)]
    if inside:
        s = max(start, prev_end, inside[0][0] - args.lead)
        e = min(end, inside[-1][1] + args.tail)
        if e <= s:  # degenerate: keep original
            s, e = start, end
    else:
        s, e = start, end
    if abs(s - start) > 0.05 or abs(e - end) > 0.05:
        changed += 1
    new_times.append((s, e))
    prev_end = e

for path in args.srts:
    cues = parse(path)
    if [c[1:3] for c in cues] != [c[1:3] for c in base]:
        raise SystemExit(f"{path}: timings differ from {args.srts[0]}, not modified")
    out = os.path.splitext(path)[0] + args.suffix + ".srt"
    with open(out, "w", encoding="utf-8") as f:
        for (idx, _, _, text), (s, e) in zip(cues, new_times):
            f.write(f"{idx}\n{ts(s)} --> {ts(e)}\n{text}\n\n")
    print(f"wrote {out}")

moved = sorted(((n[0] - c[1], c[0]) for c, n in zip(base, new_times)), reverse=True)
print(f"{len(base)} cues, {changed} re-timed; biggest start delays: "
      + ", ".join(f"#{i} +{d:.0f}s" for d, i in moved[:8]))
