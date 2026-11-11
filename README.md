# Software factory: how to use this folder

This folder holds a build prompt, not a factory. You give
[BUILD_PROMPT.md](BUILD_PROMPT.md) to Claude Code inside a project, and Claude
Code generates the factory there, tailored to that project.

Once generated, the factory turns GitHub issues into pull requests: you label an
issue `factory`, run `/factory run`, and agents decide whether to build it, write
a spec, build it, test it with the project's own checks, review it, and open a PR.
It merges what it is sure of and hands you the rest. It can also start a new
project from a spec you wrote.

What happens to each issue, in order:

1. **Intake** decides whether it is worth building, at what size, and how risky
   it is. It may ask you a question or decline.
2. **Spec:** an agent writes exactly what to build and how to tell it works.
3. **Build:** an agent writes the code on its own branch and opens a pull request.
4. **Checks:** your project's own tests, lint and build must pass. If not, the
   builder gets the errors and tries again.
5. **Reviews:** a code reviewer always, plus UX, UI and security reviewers when
   the change needs them. If any asks for changes, the builder fixes them and the
   checks and reviews run again.
6. **Final review:** once all reviewers are satisfied, one more agent rereads the
   whole change from scratch, looking for contradictions, leftovers and anything
   the specialists missed. It can send the job back to the builder too.
7. **Approval:** an approver merges the pull request if it is sure, or hands it
   to you with a specific question.

The factory works with any language or framework. Python is only what the
factory's own three small scripts are written in; your projects can use anything.

## Where to start

Follow these in order. Each step is a section below.

1. **Before you start:** check the tools on your machine.
2. **Generate the factory in a project:** pick a small test project, make it a
   GitHub repo, and let Claude Code build the factory from `BUILD_PROMPT.md`.
3. **Run your first job:** one small issue, to see the whole loop work once.
4. **Start a new project, or a big feature:** when you want the factory to plan
   and build something larger from a spec.

**No project in mind yet?** Do not generate the factory just to have it. It is
generated inside a project and tailored to it, so without a project there is
nothing for it to build or check. Instead, create a small throwaway project
purely to test the factory: it is better to find the factory's problems on a toy
than on a project you care about. Example 1 under
"Example plans, from simple to complex" is a good first one. It exercises the
whole path: plan, skeleton, a few issues, pull requests and the dashboard. For an
empty project like this, do steps 1 and 2, then go straight to step 4.

Two sections are for reference along the way: **How it works on GitHub**, if
GitHub is new to you, and **The dashboard**, for watching the factory work.

The prompt has not been run yet, so the first generation is also its first test.
If something comes out wrong, fix `BUILD_PROMPT.md` in this folder rather than only
the generated project, so the next project gets it right.

## What is in here

| Path | What it is |
|---|---|
| `BUILD_PROMPT.md` | The prompt that generates the factory. It is self-contained: nothing else is needed to generate. Edit it to change the factory. |
| `README.md` | This file. |

## Before you start

You need these on your Windows machine. Run all four commands in PowerShell; they
only check, they change nothing, and each should succeed:

```powershell
git --version
python --version      # 3.10 or later
gh auth status        # logged in to GitHub; if not, run: gh auth login
claude --version      # Claude Code
```

Optional: a browser CLI such as `agent-browser`, if the project has web pages. The
builder and the UX and UI reviewers use it to look at the running app; without it
they review from the code alone and say so.

The project you install the factory into must be a git repo with a GitHub remote.
Every job branches from the GitHub copy of the default branch and ends as a pull
request, so without that nothing can run.

## Generate the factory in a project

Use a small test project the first time. The factory opens and merges real PRs.

1. **Make the project a GitHub repo**, if it is not one already. In the project
   folder:

   ```powershell
   git init
   git add .
   git commit -m "Initial commit"
   gh repo create <name> --private --source . --push
   ```

   In an empty folder there is nothing to add, so use
   `git commit --allow-empty -m "Initial commit"` instead of the two middle lines.

2. **Copy `BUILD_PROMPT.md` into the project root.** Change the loop diagram or
   the example config first if you want a different pipeline.

3. **Open Claude Code in the project root** and ask it:

   ```text
   Follow BUILD_PROMPT.md and build the software factory in this repo.
   ```

   It inspects the project, generates the skill, the agents, the scripts, the
   config and the dashboard, fills in the project's real checks, creates the three
   GitHub labels, verifies the result and commits. It asks before pushing.

4. **Read what it generated, then push** to the default branch. Jobs branch from
   GitHub, so the factory must be there before the first run.

## How it works on GitHub

Most of the time you can stay in Claude Code: almost every action below can be
done by typing to the factory. The same actions can also be done on github.com or
from PowerShell, and those ways are described too. They are alternatives: for any
action you pick one way, never all of them.

One rule explains most of the behaviour: **the factory only acts while you run a
`/factory` command in Claude Code.** It does not watch GitHub. If you answer a
question or merge a pull request on github.com, the factory notices the next time
you run `/factory run`.

### Three things to know

Your repository's page is `https://github.com/<your-user>/<project>`. From the
project folder, `gh repo view --web` opens it in the browser.

- **Issue:** a to-do item with a title and a description, under the **Issues**
  tab. Each issue gets a number, such as #12. For the factory, one issue is one
  thing to build.
- **Label:** a coloured tag you attach to an issue. The factory only builds
  issues tagged `factory`. Anything without that tag is ignored, so you can keep
  ideas and notes as issues without having them built.
- **Pull request (PR):** a proposed change to the code, under the **Pull
  requests** tab. It shows exactly which lines would change. Nothing reaches your
  main code until a PR is merged. The factory produces one PR per issue.

### The labels

It is always the same three labels. They belong to a repository, so they are
created once per project, and the generation step does that for you.

| Label | Who adds it | What it means |
|---|---|---|
| `factory` | you | "Build this." |
| `factory:needs-info` | the factory | It asked a question in a comment on the issue and waits for your answer. |
| `factory:needs-human` | the factory | The PR is ready but it wants your decision before merging. |

You only ever add `factory` yourself. The factory adds and removes the other two.

If the labels are missing in a project (for example because `gh` was not logged in
during generation), create them once. Choose one way:

- **In Claude Code:** not available as a `/factory` command.
- **On github.com:** **Issues** tab, then **Labels**, then **New label**. Type the
  name exactly as in the table and save. Repeat for each of the three.
- **From PowerShell:** run all three lines, one per label.

  ```powershell
  gh label create factory --description "Build this with the software factory"
  gh label create "factory:needs-info" --description "The factory asked a question"
  gh label create "factory:needs-human" --description "The factory needs a human decision"
  ```

### What the factory does on GitHub

For each issue it builds, you will see this on github.com:

1. A comment on the issue saying whether it accepted the request and what exactly
   it will build. If it has a question, it asks there and adds
   `factory:needs-info`. If it declines, it says why and removes `factory`.
2. A pull request linked to the issue, marked **Draft** while work is going on.
3. One of two endings:
   - The factory merges the PR itself. The issue closes automatically.
   - The factory takes the PR out of draft, comments what it needs from you, and
     adds `factory:needs-human` to the issue.

### Each action: choose one way

Each action below can be done in up to three ways. **They are alternatives: pick
one, never all of them.** Whichever you pick, the result on GitHub is the same.
The ways are always listed in the same order:

1. **In Claude Code**, by typing to the factory. Usually the easiest.
2. **On github.com**, by clicking.
3. **From PowerShell**, with the `gh` command.

When a way does not exist for an action, it says "not available". Because the
factory only acts when you run it, the github.com and PowerShell ways often end
with "then run `/factory run` in Claude Code"; that last step belongs to that way.

The examples use issue #12 and pull request #15.

#### Ask for something to be built

Choose one:

- **In Claude Code:** describe it. The factory creates the issue, adds the
  `factory` label and starts building. Nothing else to do.

  ```text
  /factory Add a dark mode toggle to the settings page
  ```

- **On github.com:** create the issue by hand, then start the factory.
  1. Open the repository and click the **Issues** tab.
  2. Click **New issue**.
  3. Write a title and a description.
  4. In the right-hand column, click **Labels** and tick `factory`.
  5. Click the green button to create the issue.
  6. In Claude Code, run `/factory run`.
- **From PowerShell:** create the issue with one command, then start the factory.

  ```powershell
  gh issue create --title "Add a dark mode toggle" --body "On the settings page..." --label factory
  ```

  Then, in Claude Code, run `/factory run`.

Write the description like a request to a colleague: what should happen, where,
and how you would tell it works. One issue should be one small change. For
something bigger, use `/factory plan` (see below).

#### Have an existing issue built

This one has two steps: the issue needs the `factory` label first, then you start
the factory.

Step 1, add the label. Choose one:

- **In Claude Code:** not available. The factory only builds issues that already
  carry the label.
- **On github.com:** open the issue, click **Labels** in the right-hand column,
  tick `factory`, and click outside the list to save.
- **From PowerShell:** `gh issue edit 12 --add-label factory`

Step 2, start the factory. In Claude Code, run `/factory run 12` for that issue
alone, or `/factory run` for everything in the queue.

#### Follow progress

Any of these, whenever you like. They show the same job from different places:

- **In Claude Code:** the factory prints one line each time a job moves a step.
  You can also ask, for example `/factory how is issue 12 going?`, or open the
  dashboard (see "The dashboard").
- **On github.com:** open the issue to read the factory's comments. The pull
  request is linked from the issue; open it to see the code so far.
- **From PowerShell:** `gh issue view 12 --comments` prints the issue with the
  factory's comments.

#### Answer a question from the factory

The issue carries `factory:needs-info`, and the question is in the factory's last
comment on it. Choose one:

- **In Claude Code:** give the answer and say which issue. The factory posts your
  words on the issue and carries on. Nothing else to do.

  ```text
  /factory for issue 12: use the existing blue, not a new colour
  ```

- **On github.com:** open the issue, type your answer in the comment box at the
  bottom, and click **Comment**. Then run `/factory run` in Claude Code.
- **From PowerShell:** post the answer with one command.

  ```powershell
  gh issue comment 12 --body "Use the existing blue, not a new colour"
  ```

  Then run `/factory run` in Claude Code.

#### Approve a pull request that waits for you

The issue carries `factory:needs-human`. Approving always means merging the pull
request; there is no separate approve command. Choose one:

- **In Claude Code:** not available for the merge itself. You can ask why the job
  stopped, for example `/factory why did issue 12 need me?`, then merge with one
  of the two ways below.
- **On github.com:**
  1. Click the **Pull requests** tab and open the pull request.
  2. On the **Conversation** tab, read the factory's comment: it says what it
     needs you to decide.
  3. Click the **Files changed** tab to read the code changes.
  4. Back on **Conversation**, click **Merge pull request**, then **Confirm
     merge**.
- **From PowerShell:** the first line reads the changes, the second approves.

  ```powershell
  gh pr diff 15
  gh pr merge 15 --merge
  ```

With either way, the issue closes by itself, and the next `/factory run` records
the job as merged.

You may merge a pull request by hand at any moment, not only when asked. If it is
still marked **Draft**, take it out of draft first: click **Ready for review** on
github.com, or run `gh pr ready 15` in PowerShell.

#### Ask for changes instead of approving

Only one way exists:

- **In Claude Code:** say what to change and for which issue. Your words go to the
  builder, the job runs another round, and the same pull request is updated.

  ```text
  /factory on issue 12: keep the old button and add the new one next to it
  ```

- **On github.com:** not available. The factory does not read comments you leave
  on a pull request.
- **From PowerShell:** not available, for the same reason.

#### Drop a job

Choose one. The Claude Code way is the tidy one:

- **In Claude Code:** for a job that is waiting for you or for an answer, say so
  with a reason. The factory posts the reason on the issue, removes its labels,
  closes the pull request and cleans up its working files.

  ```text
  /factory reject issue 12: not needed any more
  ```

- **On github.com:** open the issue and untick `factory` under **Labels**, or
  close the issue. If it has a pull request, open it and click **Close pull
  request**. The factory will not pick the issue up again, but the job's working
  files stay on your machine.
- **From PowerShell:** the same as the github.com way, with the same limit. The
  second line is only needed if the issue has a pull request.

  ```powershell
  gh issue edit 12 --remove-label factory
  gh pr close 15
  ```

#### See what waits for you

Choose one:

- **In Claude Code:** `/factory what needs me?`
- **On github.com:** on the **Issues** tab, open the **Labels** filter and choose
  `factory:needs-human` or `factory:needs-info`.
- **From PowerShell:** one line per list; run either or both.

  ```powershell
  gh issue list --label "factory:needs-human"
  gh issue list --label "factory:needs-info"
  ```

## Run your first job

1. Create one small issue with the label `factory`, as described under "Ask for
   something to be built".
2. In Claude Code, from the project root, switch to Sonnet with `/model` and run:

   ```text
   /factory run
   ```

3. Watch it on the dashboard. See "The dashboard" below for how to open it.

4. The job ends in one of four ways:
   - **Merged:** the approver was sure and merged the PR.
   - **Needs human:** the PR is ready for you and the issue is labeled
     `factory:needs-human`. Merge the PR to approve it, or tell the factory what
     to change with `/factory <your feedback>`.
   - **Needs info:** intake asked the issue's author a question. Answer it as
     described under "Answer a question from the factory".
   - **Rejected:** intake said why on the issue and removed the label.

## Start a new project, or a big feature

The factory builds one small pull request per issue. For anything bigger, let it
plan first. Give it a spec file you wrote, or just a sentence. These are two forms
of the same command; use one, not both:

```text
/factory plan docs/spec.md
/factory plan A command-line tool that tracks my reading list, in Python
```

A spec file is the better start. The more it settles (what the product does, the
stack, what is out of scope), the fewer questions and surprises you get.

1. **Plan.** A planner agent writes a plan: the stack and structure (for a new
   project), then an ordered list of small issues. With a spec, it follows the
   spec and lists which issue delivers each requirement. If something is left open
   or contradicts itself, it asks you instead of guessing.
2. **You approve.** You read the plan and approve it or ask for changes. Nothing
   is created on GitHub before you approve.
3. **Skeleton, new projects only.** The factory scaffolds the project with a
   working test setup, writes `AGENTS.md` and fills in the checks. The final
   reviewer checks it against the plan, but look at it yourself too: it is the
   foundation everything else builds on, and the one time the factory commits
   straight to the default branch. It pushes only after you say yes.
4. **Issues.** Once the skeleton is pushed, the factory files the issues in
   order. Run `/factory run` and they are built one after another, each waiting
   until the issues it depends on are closed.

Planning is a conversation in Claude Code; nothing about a plan happens on
github.com until its issues are filed. After `/factory plan`, the factory shows
you the plan or its questions, and you reply in the chat. If you come back later
in a new session, say which plan you mean. The three lines below are separate
examples (answering a question, asking for a change, approving), not a sequence:

```text
/factory for the reading-list plan: use SQLite, and one user only
/factory change the reading-list plan: drop the export feature for now
/factory approve the reading-list plan
```

To start from nothing: create an empty folder, make it a GitHub repo as described
above, generate the factory in it, add your spec file if you have one, then run
`/factory plan <spec file or idea>`.

## Example plans, from simple to complex

Ten ideas you can give to `/factory plan`, ordered from a first test to a real
product. Each one adds something new for the factory to handle. Start at the top:
examples 1 to 3 are meant for testing the factory itself.

1. **Command-line to-do list.** The smallest complete project: no web page, no
   database, easy to check by running it.

   ```text
   /factory plan A command-line to-do list in Python: add, list, complete and delete tasks, saved in a JSON file
   ```

2. **Small library with tests.** Pure functions only, so the checks do most of the
   judging. Good for seeing the test gate at work.

   ```text
   /factory plan A Python library that converts between units of length, weight and temperature, with a test for every conversion
   ```

3. **Tool that reads files and calls the network.** Adds error handling and
   things that can fail outside the program.

   ```text
   /factory plan A command-line tool that scans a folder of Markdown files and reports every broken link, with the file and line number
   ```

4. **Static website.** The first one with something to look at, so the UX and UI
   reviewers run.

   ```text
   /factory plan A personal site in plain HTML and CSS: a home page, an about page and a projects page, readable on a phone
   ```

5. **Single-page app that keeps data in the browser.** Adds interaction and
   state, still with no server.

   ```text
   /factory plan An expense tracker as a single web page: add expenses with a category, see monthly totals and a chart, data kept in the browser
   ```

6. **Web API with a database.** The first one with stored data, which raises the
   risk level of some issues.

   ```text
   /factory plan A REST API for notes in Python with SQLite: create, read, update, delete and search notes, with tests for every endpoint
   ```

7. **API and web page together.** Two parts that must agree with each other,
   which is where ordering between issues starts to matter.

   ```text
   /factory plan A URL shortener: an API that creates and resolves short links with a click count, and a small web page to use it
   ```

8. **Content site with several features.** More issues, and features that build
   on each other.

   ```text
   /factory plan A blog generator: Markdown posts become a static site with tags, an archive by month, search and an RSS feed
   ```

9. **Multi-user app with login.** Accounts bring in the security reviewer, and
   the approver hands you every change that touches login or permissions.

   ```text
   /factory plan docs/spec.md
   ```

   with a spec for a shared task board: sign up and log in, boards with columns,
   cards you can move, and each user seeing only their own boards.

10. **A small real product.** Many issues over several runs, with accounts, data,
    email and an admin area. Expect to make real decisions along the way.

    ```text
    /factory plan docs/spec.md
    ```

    with a spec for a booking app: customers pick a time slot, receive a
    confirmation email and can cancel; the owner sets opening hours and sees the
    bookings in an admin page.

Advice for using them:

- **From example 7 on, write a spec file instead of a sentence.** A sentence
  leaves too many choices open, and the planner will come back with questions.
- **Name the stack if you care about it.** If you do not, the planner proposes
  one and you approve or change it with the plan.
- **Examples 4, 5 and 7 to 10 have web pages.** Install a browser CLI such as
  `agent-browser` first, or the UX and UI reviewers work from the code alone.
- **Examples 9 and 10 will not merge by themselves end to end.** The approver
  always hands you changes that touch login, permissions, email or a new
  dependency. That is intended: those are the decisions a human should see.
- **Keep `concurrency` at 1 for a new project.** Its issues build on each other.

### What a good spec file contains

A spec is a plain Markdown file in the project, for example `docs/spec.md`. One
page is enough for most of the examples above.

- **What it is and who it is for**, in two or three sentences.
- **What it must do**, as a list of behaviours a user would recognise.
- **The stack**, if you have a preference: language, framework, database.
- **What is out of scope** for now. This prevents the plan from growing.
- **Anything already decided**: names, data you must keep, how it is run.

## The dashboard

The dashboard is a web page on your own machine that shows what the factory is
doing. It is for watching, not for controlling: it has no buttons that change
anything. You control the factory with `/factory` commands in Claude Code.

### Open it

1. Open a second PowerShell window, so it does not block Claude Code.
2. Go to the project's `factory` folder and start the small web server:

   ```powershell
   cd <project>\factory
   python -m http.server --bind 127.0.0.1
   ```

3. Open <http://127.0.0.1:8000/dashboard.html> in your browser.
4. Leave the PowerShell window open while you use the page. Press `Ctrl+C` in it
   to stop the server when you are done.

Notes:

- `--bind 127.0.0.1` keeps the page private to your machine. Without it, other
  devices on your network could open it and read the job files.
- If port 8000 is already used by something else, pick another one, for example
  `python -m http.server 8010 --bind 127.0.0.1`, and open
  <http://127.0.0.1:8010/dashboard.html>.
- The page refreshes itself every two seconds. You never need to reload it.
- You can open it at any time, before, during or after a run. It reads the files
  the factory has written, so it also shows finished jobs from earlier runs.

### What you see

**Plans, at the top.** One card per plan made with `/factory plan`. This area only
appears if the project has at least one plan. If you never use `/factory plan`,
the page shows the job board alone.

- The card shows the plan's title and its status:

  | Status | Meaning |
  |---|---|
  | planning | The planner is writing or rewriting the plan. |
  | needs-info | The planner has questions for you. |
  | ready | The plan is written and waits for your approval. |
  | approved | You approved it. For a new project, the skeleton is being set up. |
  | filed | Its issues exist on GitHub. The card shows how many are merged, for example 3 of 8. |

- A plan that waits for you (needs-info or ready) is highlighted.
- Click the card to read your brief, the plan and your notes, and to see each
  issue of the plan with where it stands.

**Jobs, on the board.** One card per issue being built. The columns are the steps
of the loop, from intake on the left to done on the right, and a card moves to the
right as its job advances.

- Each card shows the issue and pull request numbers, the risk level intake gave
  it, the cost so far and the time spent.
- Under that, one row per round shows the result of the checks, of each reviewer
  and of the final review. They fill in as results arrive, so you can see which
  reviewer is still working and which one asked for changes.
- A job that came from a plan shows the plan's name.
- A job that waits for you is highlighted.

**Details, on click.** Click a job card to read every file the job wrote: the
issue, intake's decision, the spec, the build report, each round's checks and
reviews, and the final decision. Each file opens with a short summary, so you can
skim first and read the detail only where it matters.

### How to use it day to day

- **During a run:** keep it open next to Claude Code to see progress without
  reading the chat.
- **When something is highlighted:** click it to see what it needs. For a job,
  the decision file says what you must decide; then approve, ask for changes or
  drop the job as described under "Each action: choose one way". For a plan, read
  the questions or the plan, then answer or approve in Claude Code.
- **To understand a result:** open the job and read the reviews and the decision.
  This is the quickest way to see why a job needed several rounds or why it was
  handed to you.
- **To watch cost:** each card shows its own cost, which tells you which kinds of
  issue are expensive.

If the page says there is nothing to show, no job or plan exists yet in this
project: run `/factory run` or `/factory plan` first.

## Commands

```text
/factory run          work through every open `factory` issue; also resumes unfinished jobs
/factory run <n>      run one issue now
/factory plan <idea | spec file>
                      turn a new project or a big feature into an ordered queue of issues
/factory <anything>   ask about a job, give feedback, answer a question, reject a job,
                      approve or change a plan, or describe a new feature (it files
                      the issue and runs it)
```

## Tuning cost and speed

Everything is in `factory/config.json` in the project, so you never need to
regenerate to change it.

- **`concurrency`** is how many issues are worked on at once. It starts at 1.
  Raise it to 2 once a handful of jobs have merged cleanly, and to 3 only when the
  queued issues touch different parts of the code.
- **`models`, `routing`, `surface_reviewers`** set which model each agent runs on.
  The defaults already use cheaper models where the work allows: low-risk jobs get
  a Sonnet builder, a Haiku code reviewer and a Sonnet final reviewer, and the
  UX, UI and security reviewers only run when the change needs them. The final
  review runs on every job; it is the price of not merging something
  inconsistent.
- **`max_rounds`** is how many build, check and review passes a job gets before it
  is handed to you.
- **`checks`** is the list of commands that must pass before any reviewer runs:
  your project's own test, lint and build commands. You change this list yourself;
  the factory's jobs are not allowed to edit it.

The model of the session that runs `/factory` is separate from the agents' models.
That session only moves jobs along, so Sonnet is the suggested choice.

## Good to know

- The main project folder is never touched while jobs run. Each job works in its
  own copy under `.worktrees/`. That folder, `factory/jobs/` and `factory/plans/`
  are gitignored.
- If Claude Code closes mid-run, nothing is lost. Run `/factory run` again and
  every job continues from where it stopped.
- The factory only pushes `factory/*` branches, merges only through pull requests,
  and never deploys. The one exception is the skeleton of a new project, described
  above.
- The cost shown on the dashboard is an estimate at API prices. On a subscription
  it shows where the usage goes, not what you are billed.
