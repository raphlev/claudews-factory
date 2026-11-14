# Factories

A collection of prompts that build factories with Claude Code. A factory is not
installed from here: each folder holds a prompt that you give to Claude Code
inside your own project, and Claude Code builds the factory there, fitted to
that project.

| Factory | What it builds | Start here |
|---|---|---|
| [SoftwareFactory](SoftwareFactory/) | A factory that turns GitHub issues into pull requests: agents decide whether to build an issue, write a spec, build it, test it with the project's own checks, review it and open a pull request. | [README](SoftwareFactory/README.md) |
| [SkillsFactory](SkillsFactory/) | A skills workspace for one knowledge domain (finance controlling, a body of law, a public-service procedure, technical documentation): your documents become Markdown skills, and Claude answers questions from them, citing its sources. | [README](SkillsFactory/README.md) |

## How to use a factory

1. Open the factory's `README.md`. It says what you need on your machine and
   walks through the steps.
2. Copy the factory's `BUILD_PROMPT.md` into the root of your own project.
3. Open Claude Code in that project and ask it to follow the prompt. The exact
   sentence is in the factory's README.

Each `BUILD_PROMPT.md` is self-contained: nothing else from this repository is
needed in your project.

## What is in each folder

| File | What it is |
|---|---|
| `README.md` | For you: what the factory does, how to set up, how to use the result. |
| `BUILD_PROMPT.md` | For Claude Code: the prompt that builds the factory. Edit it to change the factory. |

If a generated project shows a defect of the factory, fix the `BUILD_PROMPT.md`
here rather than only the generated project, so that the next project gets it
right.
