"""Apply corrected "id|text" files to a raw transcript and write the final outputs.

Usage:
  python finalize.py RAW_SRT OUT_BASE [CORRECTED_1.txt ...] [--glossary glossary.tsv] [--gap 2.0]

--glossary: "heard<TAB>corrected" lines (# comments allowed). Applied as plain find/replace
to every segment NOT present in the corrected files, longest "heard" first. Used for the
parts of very long recordings that get no full correction pass.

Writes:
  OUT_BASE.srt  corrected text with the original timestamps
  OUT_BASE.txt  corrected text as readable paragraphs (new paragraph after a pause >= --gap seconds)
  OUT_BASE.timestamped.txt  "[hh:mm:ss] text" per segment
Ids missing from the corrected files keep their raw text and are reported.
A corrected line whose text is empty ("12|") drops that segment (e.g. a hallucination).
"""
import argparse
import re

ap = argparse.ArgumentParser()
ap.add_argument("raw_srt")
ap.add_argument("out_base")
ap.add_argument("corrected", nargs="*")
ap.add_argument("--glossary", default=None)
ap.add_argument("--gap", type=float, default=2.0)
args = ap.parse_args()


def secs(t):
    h, m, s = re.split(r"[:]", t.replace(",", "."))
    return int(h) * 3600 + int(m) * 60 + float(s)


fixed = {}
for p in args.corrected:
    for line in open(p, encoding="utf-8"):
        if "|" in line:
            i, text = line.rstrip("\n").split("|", 1)
            if i.strip().isdigit():
                fixed[int(i)] = text.strip()

glossary = []
if args.glossary:
    for line in open(args.glossary, encoding="utf-8"):
        if line.strip() and not line.startswith("#") and "\t" in line:
            heard, right = line.rstrip("\n").split("\t", 1)
            if heard:
                glossary.append((heard, right))
    glossary.sort(key=lambda g: len(g[0]), reverse=True)


def apply_glossary(text):
    for heard, right in glossary:
        text = text.replace(heard, right)
    return text


def read_srt(path):
    """Cues as (index, start, end, text). A cue may have no text: Whisper sometimes emits
    an empty segment, and splitting the file on blank lines would then break."""
    lines = open(path, encoding="utf-8-sig").read().splitlines()

    def cue_at(i):
        return lines[i].strip().isdigit() and i + 1 < len(lines) and "-->" in lines[i + 1]

    found, i = [], 0
    while i < len(lines):
        if not cue_at(i):
            i += 1
            continue
        idx = int(lines[i])
        start, end = (x.strip() for x in lines[i + 1].split("-->"))
        i += 2
        text = []
        while i < len(lines) and not cue_at(i):
            text.append(lines[i])
            i += 1
        found.append((idx, start, end, "\n".join(text).strip()))
    return found


cues = [(idx, start, end, fixed[idx] if idx in fixed else apply_glossary(text))
        for idx, start, end, text in read_srt(args.raw_srt)]

missing = [c[0] for c in cues if c[0] not in fixed]
kept = [c for c in cues if c[3]]

with open(args.out_base + ".srt", "w", encoding="utf-8") as f:
    for n, (_, start, end, text) in enumerate(kept, 1):
        f.write(f"{n}\n{start} --> {end}\n{text}\n\n")

with open(args.out_base + ".timestamped.txt", "w", encoding="utf-8") as f:
    for _, start, _, text in kept:
        f.write(f"[{start.split(',')[0]}] {text}\n")

# CJK text joins without spaces; other languages join with one space
cjk = re.compile(r"[぀-ヿ㐀-鿿]")
with open(args.out_base + ".txt", "w", encoding="utf-8") as f:
    para, prev_end = [], None
    for _, start, end, text in kept:
        if prev_end is not None and secs(start) - prev_end >= args.gap and para:
            f.write(("" if cjk.search(para[0]) else " ").join(para) + "\n\n")
            para = []
        para.append(text)
        prev_end = secs(end)
    if para:
        f.write(("" if cjk.search(para[0]) else " ").join(para) + "\n")

label = f"glossary-only ({len(glossary)} entries)" if glossary else "uncorrected"
print(f"{len(cues)} segments, {len(fixed)} corrected lines, {len(cues) - len(kept)} dropped, "
      f"{label}: {len(missing)} {missing[:20] or ''}{' ...' if len(missing) > 20 else ''}")
