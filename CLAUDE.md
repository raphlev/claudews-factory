# Notes for Claude

This repo is a collection of prompts that build factories. Each factory is a
folder holding two files:

- `README.md`, for the person who will use the factory;
- `BUILD_PROMPT.md`, a self-contained prompt given to Claude Code inside a
  target project, which generates the factory there.

`SkillsFactory/` also has `EXAMPLES.md`: exercises to try the factory. An
experiment that goes beyond the factory lives there, as additions typed with
the build sentence, until a run has shown what is worth moving into
`BUILD_PROMPT.md`.

| Folder | What its prompt builds |
|---|---|
| `SoftwareFactory/` | a factory that turns GitHub issues into pull requests |
| `SkillsFactory/` | a skills workspace that answers questions about one domain from the user's documents |

## Requirements for every factory

- **Readers have mixed experience.** Assume neither a developer nor a beginner:
  the prompt asks the user how familiar they are with the tools and explains as
  much or as little as they chose. A generated project may be shared between
  experienced and inexperienced people, so READMEs stay plain and short, with a
  fast path for those already set up and a step-by-step path for the others.
- **Help with installation.** The prompt checks the machine and helps install or
  update what is missing, with the user's yes. The README covers what is needed
  before Claude Code can run: accounts, VS Code and its extensions, git, Python,
  Claude Code.
- **Latest versions.** Recommend the latest version of each tool, or newer. An
  older version gets an upgrade offer; it does not block.
- **GitHub is optional.** The prompt asks whether to use it. Without GitHub the
  workflow is simpler: git on the machine only, no account, no `gh`, no push.
- **Language is the user's choice.** English and French at least. The prompt
  asks in which language the generated content is written; Claude talks to the
  user in the language they write in. The prompts themselves stay in English.
- **Claude's own practices for skills, tools and agents.** A skill is a folder
  with a short `SKILL.md`, detail in linked reference files one level deep, and
  its scripts beside it. Agents are optional. Check the current Claude Code
  documentation for frontmatter fields and limits instead of relying on memory.
- **Wording in SkillsFactory:** web input is "a set of HTML pages", not "help
  center".

## Working rules

- Notes for this project stay in the project, in this file. Do not write to the
  user-level Claude memory folder (`~/.claude/projects/.../memory/`).
- A root `input/` folder, when present, is gitignored working material. It is
  not part of any factory and is never referenced from one.
- When a generated project shows a defect of a factory, fix the factory's
  `BUILD_PROMPT.md` here, not only the generated project.
- Commit only when asked, and ask before pushing.
