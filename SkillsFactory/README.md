# Skills factory: how to use this folder

This folder holds a build prompt, not a finished product. You give
[BUILD_PROMPT.md](BUILD_PROMPT.md) to Claude Code inside a project folder that
contains your documents, and Claude Code builds a **skills workspace** there:
your documents turned into Markdown and organised into skills, so that Claude
answers questions about your domain from your documents and says where each
answer comes from.

It works for any domain that lives in documents: finance controlling, a body of
law, a public-service procedure, a product's technical documentation. It suits
experienced and inexperienced users alike: Claude first asks how familiar you
are with the tools, then either guides you step by step or keeps it short. It
asks before it installs or changes anything.

What happens, in order:

1. **Environment:** Claude asks how familiar you are with the tools and whether
   you want the project on GitHub, checks your machine, and helps you install
   or update what is missing.
2. **Interview:** it asks which domain, who will ask questions, in which
   languages, and how confidential the documents are.
3. **Input:** you put your documents in the `input` folder.
4. **Convert:** a script turns every document into Markdown pages. This is the
   **library**.
5. **Index or not:** Claude decides whether the library is large enough to need a
   search database, and tells you why.
6. **Plan:** it proposes a list of topics. You approve or change it.
7. **Write, check, test:** for each topic it writes a short skill, called a
   **pack**, checks every citation with a script, then tests the pack with
   questions and corrects it from the documents.
8. **Hand-over:** it answers three questions in front of you, then commits.

## Where to start

Follow these in order. Each one is a section below.

1. **Set up your machine,** once.
2. **Create your project and add your documents.**
3. **Generate the skills.**
4. **Ask your first questions.**

After that, **Day to day** shows how to add documents, report a wrong answer and
test the skills.

**Already using VS Code, git and Claude Code?** Run the commands under "Check"
in section 1, then go straight to section 2. **New to them?** Read "Words you
will meet" first, then follow section 1 line by line.

The prompt has not been run yet, so the first generation is also its first test.
If something comes out wrong, fix `BUILD_PROMPT.md` in this folder rather than
only the generated project, so the next project gets it right.

## What is in here

| Path | What it is |
|---|---|
| `BUILD_PROMPT.md` | The prompt that builds the skills workspace. It is self-contained. Edit it to change the factory. |
| `README.md` | This file. |

## Words you will meet

| Word | Meaning |
|---|---|
| PowerShell, terminal | A window where you type commands. Press the Windows key, type `PowerShell`, press Enter. |
| VS Code | The editor where you see your files and talk to Claude. |
| Claude Code | Claude working inside your project: it reads files, runs commands and writes files, and asks you first. |
| Repository (repo) | A project folder whose history is kept by git. |
| Commit, push | A commit saves a version of the project on your machine. A push sends it to GitHub. |
| Private repository | A repository on GitHub that only you, and the people you invite, can see. |
| Markdown | Plain text with simple marks for titles, lists and tables. Files end in `.md`. |
| Skill | A folder of Markdown files that tells Claude how to handle one kind of question. |

## 1. Set up your machine

You do this once. Windows 10 or 11.

### First choice: with GitHub or without

GitHub is an online service that keeps a copy of your project in a private
space of your own in the cloud, called a private repository. Only you, and the
people you invite, can see it. It is optional, and worth it if you intend to
keep and maintain the project:

- **It is saved off your machine.** A lost or broken laptop does not lose it.
- **Every version is kept.** You can go back to an earlier one.
- **You can maintain it over time** from any machine, and later invite
  colleagues to use or improve the skills.

| | With GitHub | Without GitHub |
|---|---|---|
| Where the project lives | on your machine and in your private repository | on your machine only |
| Backup, a second machine, sharing with colleagues | yes | you copy the project folder yourself |
| What you need in addition | a free GitHub account, two-factor authentication, one more tool (`gh`) | nothing |

Without GitHub the set-up is shorter: skip everything marked **GitHub only**
below. Claude asks you the same question when it starts, and you can add GitHub
later by typing `/kb use GitHub`. Either way, git keeps the history of the
project on your machine, so that a change can be undone.

### Accounts

- **Claude:** an account with a plan that includes Claude Code, at
  <https://claude.ai>.
- **GitHub only:** a free account at <https://github.com/signup>, protected by
  two-factor authentication with the Microsoft Authenticator app on your phone:
  1. On github.com, click your profile picture, then **Settings**, then
     **Password and authentication**, then **Enable two-factor authentication**.
     A QR code appears.
  2. In Microsoft Authenticator, tap **+**, choose **Other account**, and scan
     the QR code.
  3. Type the six-digit code from the app into github.com.
  4. Save the recovery codes somewhere safe. They are the only way back in if
     you lose the phone.

### The software

Open PowerShell and paste these lines. Accept the Windows permission windows
that open.

```powershell
winget install --id Microsoft.VisualStudioCode -e
winget install --id Git.Git -e
winget install --id Python.Python.3.15 -e
winget install --id Anthropic.ClaudeCode -e
```

GitHub only, one more line:

```powershell
winget install --id GitHub.cli -e
```

| Tool | What it is for | Version in November 2026 |
|---|---|---|
| VS Code | the editor | 1.146 |
| Git | keeps the history of your project | 2.56 |
| Python | runs the three small scripts of the workspace | 3.15 |
| Claude Code | Claude inside your project | 2.1 |
| GitHub CLI (`gh`), GitHub only | links your machine to your GitHub account | 2.104 |

Use the latest version of each tool. The table shows the versions current when
this was written; anything newer is fine.

- To update a tool you already have, write `upgrade` in place of `install`.
- Each Python release has its own name. `winget search Python.Python.3` lists
  them; take the highest.

Then **close PowerShell and open it again**, so that it finds the new commands.

### Sign in

1. In PowerShell, run `claude`. The first time, it opens a browser page to sign
   in to your Claude account. Type `/exit` to leave afterwards.
2. **GitHub only:** run `gh auth login` and answer: **GitHub.com**, **HTTPS**,
   **Yes**, **Login with a web browser**. Copy the code it shows, press Enter,
   and paste the code in the browser page that opens.

### VS Code extensions

Paste these lines in PowerShell:

```powershell
code --install-extension anthropic.claude-code
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-toolsai.jupyter
code --install-extension shd101wyy.markdown-preview-enhanced
code --install-extension yzane.markdown-pdf
```

| Extension | What it is for |
|---|---|
| Claude Code | talk to Claude inside VS Code |
| Python, Pylance | run and read the scripts |
| Jupyter | open notebooks, if you later explore a spreadsheet or the search database |
| Markdown Preview Enhanced | read the Markdown files as formatted pages |
| Markdown PDF | export an answer to PDF |

### Check

Each of these should print a version:

```powershell
git --version
python --version
claude --version
code --version
```

GitHub only: this one should say that you are logged in.

```powershell
gh auth status
```

- If `python` opens the Microsoft Store instead, open Windows **Settings**,
  search for **App execution aliases**, and switch off the two Python entries.
- If something else fails, carry on as soon as VS Code, Git and Claude Code
  work. The build prompt starts by checking your machine, and Claude helps you
  install or update the rest.

## 2. Create your project and add your documents

1. Create a folder for the project, with an `input` folder inside it, for example
   `Documents\finance-skills\input`.
2. Copy your documents into `input`. Sub-folders are welcome, and their names are
   kept, so use them to group documents by kind:
   `input\policies`, `input\procedures`, `input\training`.
3. Copy `BUILD_PROMPT.md` from this folder into the project folder, next to
   `input`.

You do not need to create the repository yourself, on your machine or on GitHub.
Claude offers to do it in its first step.

What you can put in `input`:

| Document | What happens to it |
|---|---|
| PDF | Converted, with page numbers kept so that answers can cite the page. A scanned PDF has no text: Claude lists it and asks you to run OCR first. |
| Word (`.docx`) | Converted, split by headings. An old `.doc` must be saved as `.docx` first. |
| Excel, CSV | One page per sheet, as a table, with the formulas of calculated cells. |
| PowerPoint | Converted, with slide numbers kept. |
| Text, Markdown | Taken as they are. |
| A set of HTML pages (saved web pages, an exported site or manual) | Put the HTML files in a sub-folder of `input`, or list the pages' addresses in `input\urls.txt`, one per line. Each HTML page becomes one page. Pages behind a login must be saved by hand. |

Good input makes good answers: final versions rather than drafts, one version of
each document, and a date or version on each when rules change over time.

> **Your documents stay in `input`.** That folder is never committed: it is not
> part of the project's history, and it is never sent to GitHub. Keep the
> originals somewhere safe.
>
> **With GitHub,** what is sent is the Markdown text made from your documents
> and the skills written from them. They carry the content of your documents,
> so keep the repository private. If even the converted text must stay on your
> machine, say so when Claude asks about confidentiality: then only the skills
> are sent.
>
> **Without GitHub,** nothing leaves your machine through git, and the backup of
> the project folder is yours to make.

## 3. Generate the skills

1. Open VS Code. Choose **File**, **Open Folder**, and pick your project folder.
2. Open Claude Code: press `Ctrl+Shift+P`, type `Claude Code`, and choose
   **Open in New Tab**.
3. Type:

   ```text
   Follow BUILD_PROMPT.md and build the skills workspace in this folder.
   ```

Then follow the conversation. Claude asks permission before it runs a command
or installs something: read the line, then accept.

What it asks you:

- how familiar you are with VS Code, git and GitHub, so that it explains as
  much or as little as you need;
- whether you want the project on GitHub;
- which domain, and a short name for it;
- who will ask questions, and what they want back: explanations, step-by-step
  procedures, figures, a check of a case against the rules, drafted documents;
- the languages of the documents and of the answers;
- which names must never be written and, with GitHub, whether the converted
  text may be committed;
- later, with the documents converted: which source wins when two disagree,
  whether answers should end with a notice such as "not professional advice",
  and whether the proposed list of topics suits you.

What it decides and tells you: whether to build a search database (see "The
search database").

A large set of documents takes more than one session. Nothing is lost: open
Claude Code again in the project and type `/kb build` to continue.

At the end, Claude answers three questions in front of you, and commits. With
GitHub, say "push" when you want the result online.

## 4. Ask your first questions

Open Claude Code in the project and type your question in plain words.

```text
By which working day must accruals be posted, and who approves them?
What notice period applies after three years of service? Quote the article.
Which documents must be attached to the application, and what is the deadline to appeal a refusal?
```

A good answer names the document and the page, article or section behind each
statement, says which pages were read, and says so plainly when your documents
do not answer the question.

Tips for asking:

- **Name the subject and the situation:** who, what, in which case.
- **Give the date** when rules change over time: the fiscal year, the date of
  the event.
- **Use the documents' words** when you know them. Otherwise describe the
  situation plainly.
- **Say what you want back:** an explanation, the steps, a figure, a check of
  your case, a draft.
- **Name the document** if you know which one holds the answer.
- **Ask for citations** or exact quotes when the wording matters.

## Day to day

| You want to | Do this |
|---|---|
| Add or replace documents | Copy them into `input`, then type `/kb add`. |
| Cover a new topic | `/kb write a pack about <topic>` |
| Report a wrong answer | Say so: "That is wrong: <what you expected>". Claude checks the pages, corrects the skill, and tells you what it changed. |
| Test the skills | `/kb test` puts new questions to the packs and corrects what is wrong. |
| See where things stand | `/kb status` |
| Keep an answer as a document | Ask "write this as a document". It is saved under `Deliverables`. To make a PDF, open the file, right-click in it, and choose **Markdown PDF: Export (pdf)**. |
| Read a Markdown file as a page | Open it, right-click in it, and choose **Markdown Preview Enhanced: Open Preview to the Side**. |
| Save a version of your work | Type "commit". With GitHub, "commit and push" also sends it online. |
| Work on another machine | Set it up as in section 1. With GitHub, clone the repository and copy `input` by hand; `input` is only needed to add or convert documents. Without GitHub, copy the whole project folder. |
| Put the project on GitHub later | `/kb use GitHub` |
| Share the workspace with a colleague | With GitHub, invite them to the private repository: on github.com, open the repository, then **Settings**, **Collaborators**, **Add people**. They set up their machine as in section 1 and clone it. The workspace's own README tells them how to ask questions, whatever their experience. |

## What gets generated

```
CLAUDE.md              the rules Claude follows when it answers
README.md              how to use your workspace
input/                 your documents; never committed
.claude/skills/
  <name>-library/      every document as Markdown pages, with the search
  <name>-<topic>/      one pack per topic: a short overview, and detail files beside it
  kb/                  the /kb commands and the three scripts
.claude/agents/        optional helpers that write and test the packs
kb/                    settings, the list of packs, the log, the test questions
Deliverables/          documents produced as answers
```

The skills follow Claude's own rules for skills. Each is a folder, not one big
file: a short `SKILL.md` that says what the skill covers and where the detail
is, detail files that are read only when needed, and scripts that are run
rather than read. A script checks these rules, and every citation, each time a
pack changes.

## The search database

Claude needs to find the right pages before it can answer.

- **Small library, up to about 200 pages:** no database. Claude reads the list
  of pages and searches the text directly. There is nothing to maintain.
- **Large library,** or one whose words differ from the words people use
  (acronyms, legal terms, another language): Claude builds a search database, a
  single SQLite file. One search then returns the best pages for a question
  asked in plain words, and corrects small spelling mistakes.

The database is only an index. The Markdown pages remain the source of every
answer, and the database rebuilds itself when pages change. It is not committed.
You can force the choice in `kb/config.json` (`index.mode`: `auto`, `on`, `off`).

## Example domains

| Domain | Documents you might put in `input` | Packs you might get |
|---|---|---|
| Finance controlling | closing procedure (Word), chart of accounts and indicator definitions (Excel), group reporting manual (PDF) | month-end closing, accruals, cost centres, indicator definitions |
| Law | codes and decrees (PDF or HTML pages), a collective agreement, internal notes | notice periods, leave, working time, dismissal procedure |
| Public-service procedure | the regulation, forms and guides (PDF), the agency's web pages saved as HTML | eligibility, the application file, deadlines and appeals |
| Technical documentation | a product manual (PDF), an online manual saved as a set of HTML pages | installation, configuration, troubleshooting |

## Commands

```text
/kb status           what the library holds, which packs are built and tested, what waits for you
/kb add              convert what is new or changed in input, then update what it affects
/kb build [<pack>]   write, check and test the next planned pack, or the one named
/kb test [<pack>]    put new questions to the packs, fix what is wrong, log it
/kb <anything>       report a wrong answer, ask for a new pack, change a setting
```

## Settings

Everything is in `kb/config.json` in the project, so you never need to
regenerate to change it.

- **`guidance`** is `guided` (every step explained) or `concise`.
- **`authority`** is the order in which sources win when they disagree.
- **`notice`** is the sentence that ends answers stating a rule. Empty for none.
- **`index.mode`** is `auto`, `on` or `off` for the search database.
- **`questions_per_pack`** is how many questions test each pack. It starts at 5.
- **`models`** sets which model writes and which model tests the packs.
- **`keep_out`** lists names that must never be written in the workspace.

## Good to know

- **Answers are only as good as your documents.** Claude does not complete them
  from memory or from the web. When they do not answer, it says so.
- **This is not professional advice.** The skills restate your documents as of
  their dates. For a decision with legal or financial consequences, check the
  cited page.
- **Your documents are read by Claude.** To convert, write and answer, Claude
  reads their content. Check that your organisation allows this for the
  documents you use.
- **Scripts cost nothing.** Converting, searching and checking are done by
  scripts on your machine. Writing and testing packs is where Claude is used
  most.
- **If Claude Code closes mid-way, nothing is lost.** Progress is kept in files;
  `/kb build` continues.
