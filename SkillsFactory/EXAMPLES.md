# Skills factory: exercises to try

Six exercises for trying the skills factory, from a first test to an
experiment. Each one says what to put in `input`, what to type, what it
exercises, and what a good result looks like. Set up your machine and your
project as described in [README.md](README.md) first.

None of these has been run yet. When one of them shows a defect, fix
[BUILD_PROMPT.md](BUILD_PROMPT.md), so that the next project gets it right.

Unless an exercise says otherwise, type this in Claude Code:

```text
Follow BUILD_PROMPT.md and build the skills workspace in this folder.
```

| # | Exercise | What it exercises |
|---|---|---|
| 1 | A handful of documents | the whole path, without a search database |
| 2 | Spreadsheets where the formula is the rule | Excel conversion, figures, calculations |
| 3 | Texts with dates and versions | authority, exact quotes, questions that depend on a date |
| 4 | A large set of HTML pages | the search database |
| 5 | Documents in one language, skills in another | the language question |
| 6 | A video with chapters and subtitles (experimental) | a new kind of input, images in skills |

## 1. A handful of documents

The first test. Start here.

- **Input:** five to ten documents on one subject, in mixed formats: a PDF, a
  Word file, a short spreadsheet. Internal procedures or a policy are a good
  choice, because you know what the right answers are.
- **Expect:** no search database, since the library is small; one to three
  packs.
- **A good result:**
  - every file is listed in the conversion summary, converted or skipped with
    a reason;
  - answers name the document and the page;
  - a vague question ("how do I do it?") gets the tips list, not a guess;
  - a question the documents do not answer gets "the documents do not say".

## 2. Spreadsheets where the formula is the rule

- **Input:** two or three Excel files with calculated cells, for example
  indicator definitions, a cost allocation, a budget template, plus the note
  that explains them, if there is one.
- **Ask:** "How is <indicator> calculated?", then "Calculate it for these
  values: ...".
- **A good result:**
  - the page of each sheet shows the formula next to the value;
  - the answer gives the formula with its sheet and cell;
  - the calculation shows its inputs and is run with a tool, not done in the
    head.

## 3. Texts with dates and versions

- **Input:** two versions of the same text (a regulation, a policy, a contract
  template), each in its own sub-folder, with their dates, plus an internal
  note that comments on them.
- **Ask:** a question whose answer changed between the versions, first without
  a date, then with one.
- **A good result:**
  - when planning, Claude proposes which source wins and asks for the validity
    dates it cannot find;
  - without a date, the answer asks for it or states its assumption;
  - where the wording matters, the answer quotes the text exactly and names the
    article;
  - when the note and the text disagree, the answer says so and follows the
    order you approved.

## 4. A large set of HTML pages

- **Input:** a few hundred HTML pages in a sub-folder of `input`, for example
  an online manual saved to disk; or their addresses in `input\urls.txt`, one
  per line. Only use pages you are allowed to copy.
- **Expect:** Claude decides to build the search database and says why, with
  the number of pages.
- **A good result:**
  - one Markdown page per HTML page, without menus or cookie banners;
  - a link between two pages still works between their Markdown pages;
  - a question in everyday words finds the right page in the first three
    results;
  - after a miss, Claude adds a line to the synonyms or the glossary, and the
    same question then finds its page.

## 5. Documents in one language, skills in another

- **Input:** the documents of exercise 1, in French.
- **When asked for the languages:** choose English for the skills.
- **Ask:** the same question once in French and once in English.
- **A good result:**
  - packs are written in English, with the French term in brackets the first
    time a key term appears;
  - quotes stay in French;
  - each answer comes in the language of its question;
  - the workspace's own README is in English.

## 6. A video with chapters and subtitles (experimental)

This one goes beyond what the factory builds today. It turns a training video
into illustrated skills: one pack per chapter, and for each sequence a short
description from the subtitles with an animated image (GIF) made from the
video. A recorded lesson, such as a judo class, is a typical case.

It is run with additions typed after the build sentence. What works will be
folded into the factory afterwards.

**Before you start**

- **The video** has chapters, and its subtitles are a text file (`.srt`).
  Subtitles stored as images inside the video cannot be read.
- **ffmpeg** is installed: `ffmpeg -version` prints a version. If not:
  `winget install --id Gyan.FFmpeg -e`, then open a new PowerShell.
- **Rights:** the subtitles and the images belong to the author of the video.
  Check that you may copy them, even into a private repository.

**Input:** the video and its subtitle file, side by side in `input`.

**Type this,** with your file names:

```text
Follow BUILD_PROMPT.md and build the skills workspace in this folder, with the
additions below for this project. Where they differ from BUILD_PROMPT.md, they
win.

My input is one training video with chapters, input/<name>.mkv, and its
subtitles, input/<name>.srt. Treat the pair as one document.

1. Tools. This needs ffmpeg and ffprobe. Check them with the other tools.
2. Transcript. convert.py reads the chapters with ffprobe and the text from the
   .srt file. It writes one library page per chapter, titled with the chapter's
   name, with the subtitle lines merged into sentences and a time marker,
   <!-- t 00:12:34 -->, at least every 30 seconds. The locator is the chapter's
   time range. A citation reads "<video>, 12:34-13:10", and check.py checks that
   the time lies inside the cited page. The audio is not used.
3. Sequences. Read each chapter and propose its sequences. A sequence is one
   thing the trainer shows or explains, from the first subtitle line about it
   to the last. Cut only where the subtitles show a change of topic. Write them
   to kb/sequences.tsv: chapter, number, start, end, title, and the subtitle
   line that justifies each cut. Show me the table, and cut nothing before I
   approve it.
4. Clips. A new script, clips.py, in the kb skill, reads sequences.tsv and calls
   ffmpeg. For each sequence it writes a silent GIF made of frames sampled
   evenly across the sequence, and three still frames (start, middle, end) as
   JPEG. Starting values, kept in config.json: 480 pixels wide, at most 60
   frames, at most 5 MB per GIF. Make the first three, show me their sizes, and
   wait for my yes before making the rest.
5. Packs. One pack per chapter. SKILL.md lists the chapter's sequences, one line
   each. Each sequence has its own file, references/<nn>-<title>.md, with what
   the trainer says (cited with its time), the key points, and the GIF. The GIF
   and the stills are in the pack's assets/ folder. check.py also checks that
   every sequence has its file and its GIF, and that no GIF passes the size
   limit.
6. What is written. The description of a sequence comes from the subtitles. You
   may add what you see in the three still frames, marked "[seen in the
   frames]". Add nothing about the subject from memory.
7. Git. Add the assets/ folders to .gitignore for now. I decide about committing
   the GIFs once I have seen their total size.
```

**What you get**

```
.claude/skills/
  <name>-library/pages/...          one page per chapter: what is said, with times
  <name>-<chapter>/                 one pack per chapter
    SKILL.md                        the chapter's sequences, one line each
    references/01-<sequence>.md     one sequence: the words, the key points, the GIF
    assets/01-<sequence>.gif        the animated image, and three still frames
kb/sequences.tsv                    the cuts you approved: chapter, start, end, title
```

To see the images, open a sequence file in VS Code, right-click in it, and
choose **Markdown Preview Enhanced: Open Preview to the Side**. The chat
itself shows text only: Claude answers from the subtitles and points to the
file that holds the GIF.

**A good result**

- the table of sequences cuts where you would cut, and each cut is justified by
  a subtitle line;
- each GIF shows the gesture the text describes;
- every description cites its time, and what was read from the still frames is
  marked as such;
- asking "how does the trainer do <gesture>?" leads to the right sequence.

**What to watch**

- **Movement.** Frames sampled evenly over a long sequence may show a fast
  gesture in one or two images only. If so, ask for a short clip at real speed
  of the demonstration itself, located from the subtitles. This is why the
  additions stop after three GIFs.
- **Weight.** GIFs are heavy. Look at the total before committing them. Width,
  number of frames and the size limit are in `kb/config.json`.
- **What Claude sees.** Claude reads the subtitles and looks at still frames.
  It does not watch the movement, so a detail that the trainer does not say and
  that no still frame shows is not in the description.
- **No subtitles.** A video without subtitles would need its speech turned into
  text first. That is a heavier step, not covered here.
