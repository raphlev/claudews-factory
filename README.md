# Factories and skills for Claude Code

This repository holds two kinds of things:

- **Factories:** prompts that build something inside your own project. A factory
  is not installed from here: you give its prompt to Claude Code in your
  project, and Claude Code builds the factory there, fitted to that project.
- **Ready-made skills:** finished skills that you use as they are, from their
  folder or copied into your own project.

## Factories

| Factory | What it builds | Start here |
|---|---|---|
| [SoftwareFactory](SoftwareFactory/) | A factory that turns GitHub issues into pull requests: agents decide whether to build an issue, write a spec, build it, test it with the project's own checks, review it and open a pull request. | [README](SoftwareFactory/README.md) |
| [SkillsFactory](SkillsFactory/) | A skills workspace for one knowledge domain (finance controlling, a body of law, a public-service procedure, technical documentation): your documents become Markdown skills, and Claude answers questions from them, citing its sources. | [README](SkillsFactory/README.md) |

### How to use a factory

1. Open the factory's `README.md`. It says what you need on your machine and
   walks through the steps.
2. Copy the factory's `BUILD_PROMPT.md` into the root of your own project.
3. Open Claude Code in that project and ask it to follow the prompt. The exact
   sentence is in the factory's README.

Each `BUILD_PROMPT.md` is self-contained: nothing else from this repository is
needed in your project.

### What is in each factory folder

| File | What it is |
|---|---|
| `README.md` | For you: what the factory does, how to set up, how to use the result. |
| `BUILD_PROMPT.md` | For Claude Code: the prompt that builds the factory. Edit it to change the factory. |
| `EXAMPLES.md` | SkillsFactory only: exercises to try the factory. |

If a generated project shows a defect of the factory, fix the `BUILD_PROMPT.md`
here rather than only the generated project, so that the next project gets it
right.

## Ready-made skills

| Skill | What it does | Start here |
|---|---|---|
| [audio-transcribe](Skills/convert-audio-subtitle/) | Turns the speech of an audio or video file into corrected text and subtitles (`.srt`), with optional minutes and translation. The speech-to-text step runs on your machine. | [README](Skills/convert-audio-subtitle/README.md) |

### How to use a ready-made skill

Either open Claude Code in the skill's folder under `Skills/`, or copy its
`.claude/skills/<name>` folder into the `.claude/skills/` folder of your own
project. Its README says what it needs and what it downloads the first time.

The skills can feed the factories. For example, `audio-transcribe` writes the
subtitle file that the video exercise of the skills factory starts from
([SkillsFactory/EXAMPLES.md](SkillsFactory/EXAMPLES.md), exercise 6).
