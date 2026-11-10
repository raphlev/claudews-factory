Build a simple, visual "software factory" in this repo using a Claude Code skill,
subagents, three small scripts, and markdown files. Keep it small: a viewer should
understand the whole thing in one sitting. Scripts do what is deterministic (state,
checks, routing, merging); agents do the judgment in between; every step leaves a
file behind.

Inspect the repo first so the factory knows its language, its test, lint, typecheck
and build commands, its default branch, and its conventions. I build and run this
on Windows, so everything the factory runs must work there. Check which Python
command works (`python` or `python3`) and whether `gh` is authenticated for this
repo. If the repo has no project code yet, or is not a GitHub repo, build the
factory anyway in its generic form and list what is left to adapt in your hand-over
(see Finish). An empty repo is a normal case: /factory plan then starts the project
(see Planning).

## The orchestrator

The factory is one skill, /factory. Whichever Claude Code session runs it becomes
the only orchestrator: it works through the queue, runs up to `concurrency` jobs at
once, spawns every agent as a background subagent, and calls the scripts. It never
writes plans, code, specs, reviews or decisions, and it never edits job.json itself.

## The loop (edit this to change the factory)

```
                   ┌──────────────────┐
                   │   GitHub issue   │
                   │ labeled `factory`│
                   └─────────┬────────┘
                             ▼
                   ┌──────────────────┐
                   │      intake      ├──► NEEDS-INFO: ask the author on the issue, park
                   │       opus       ├──► REJECT: say why on the issue, drop the label
                   └─────────┬────────┘
                             ▼ ACCEPT (maybe rescoped) + risk + surfaces
                   ┌──────────────────┐
                   │  route (script)  │    reviewers + models from config.json
                   └─────────┬────────┘
                             ▼
                   ┌──────────────────┐
                   │   spec-writer    │
                   │       opus       │
                   └─────────┬────────┘
                             ▼
                   ┌──────────────────┐
                   │     builder      │◄────────────────────┐
                   │     by risk      │  opens a draft PR   │
                   └─────────┬────────┘                     │
                             ▼                              │
                   ┌──────────────────┐   FAIL: builder     │
                   │  gate (script)   ├─────────────────────┤
                   │  repo's checks   │   gets the log      │
                   └─────────┬────────┘                     │
                             │ PASS: routed reviewers       │
        ┌─────────────┬──────┴──────┬─────────────┐         │
        ▼             ▼             ▼             ▼         │
  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
  │    code   │ │     ux    │ │ ui design │ │  security │   │
  │  by risk  │ │   sonnet  │ │   haiku   │ │    opus   │   │
  │   always  │ │    `ui`   │ │    `ui`   │ │ `security`│   │
  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘   │
        └─────────────┴──────┬──────┴─────────────┘         │
                             ▼                              │
                   ┌──────────────────┐   any CHANGES:      │
                   │   WAIT FOR ALL   ├─────────────────────┘
                   │  routed reviews  │   resume builder
                   └─────────┬────────┘   (max 3 rounds)
                             ▼ all PASS
                   ┌──────────────────┐
                   │     approver     │
                   │       opus       │
                   └─┬───────────────┬┘
             APPROVE │               │ ESCALATE
                     ▼               ▼
              ┌─────────────┐ ┌─────────────┐
              │ sync + gate │ │ needs-human │ ◄── merge the PR yourself, or
              │ gh pr merge │ │  PR ready   │     /factory <feedback>
              └─────────────┘ └─────────────┘
```

Each box names its model. "by risk" means routed from intake's rating: the builder
is sonnet for low risk and opus for medium and high; the code reviewer is haiku for
low risk and sonnet otherwise. The third line of each reviewer box says when it
runs: the code reviewer always, the others only when intake flags that surface. A
round is one build → gate → review pass.

## Planning (new projects and big features)

The loop builds one small PR per issue. /factory plan turns something bigger, a
new project or a large feature, into a queue of such issues. I give it either a
sentence or the path to a spec file I wrote; both are saved as brief.md.

```
idea or spec file → planner (opus) → plan.md → I approve or ask for changes
     → bootstrap (new projects only) → issues filed in order → /factory run
```

- The planner writes plan.md. For a new project it starts with the stack and the
  structure, each choice with a one-line reason. Then comes an ordered list of
  issues, each small enough for one PR and useful on its own, with what it depends
  on. The first line is `PLAN: READY`, or `PLAN: NEEDS-INFO` with questions. Stack
  and product choices the brief leaves open are questions for me, not assumptions.
- When the brief is a spec, the plan follows it. The planner does not re-decide
  what the spec settles, raises gaps and contradictions as questions, and ends
  plan.md with a Coverage list: every requirement in the spec, and the issue that
  delivers it or the reason it was left out.
- The orchestrator shows me the plan's Summary, its issue list and any questions.
  Nothing is filed until I approve. My answers and changes are saved verbatim as
  note-<k>.md, and the planner rewrites the plan from them.
- Bootstrap runs only when the repo has no project code. A builder, given the
  plan folder instead of a job, scaffolds the skeleton in the main checkout on the
  base branch, with a test runner and one passing test. It writes AGENTS.md
  (setup, dev server on a given port, validation commands) and fills `checks` in
  config.json. The checks must pass before it commits. There is nothing to gate or
  review against yet, so I review it myself. This is the one time the factory
  works in the main checkout and commits on the base branch, and it pushes only
  after I say yes.
- Issues are filed only once the bootstrap is on origin, because every job
  branches from there. job.py files them in order with the `factory` label. Each
  body ends with a `Depends on: #a, #b` line where needed, and `queue` holds an
  issue until every issue it depends on is closed. A new project therefore builds
  up in order, even with `concurrency` above 1.

## Target file system

```
.claude/
  skills/factory/SKILL.md          # the orchestrator's instructions
  agents/                          # one file per agent in the loop
    planner.md  intake.md  spec-writer.md  builder.md  approver.md
    reviewer-code.md  reviewer-ux.md  reviewer-ui.md  reviewer-security.md
factory/
  config.json                      # every knob: concurrency, rounds, labels, checks, routing, prices
  bin/job.py                       # the only writer of job.json; refuses illegal moves; merges
  bin/gate.py                      # runs the checks in a job's worktree, writes round-N/checks.md
  bin/route.py                     # risk + surfaces → the job's reviewers and models
  dashboard.html                   # visual board, polls the job folders
  plans/001-todo-app/              # one folder per plan (gitignored runtime state)
    brief.md                       # my idea or my spec file, verbatim
    plan.md                        # the planner's stack, structure and ordered issues
    note-1.md                      # my answers or requested changes
    issues.json                    # the issues filed from this plan
  jobs/003-rate-limiting/          # one folder per job (gitignored runtime state)
    job.json                       # the job's state, drives the dashboard
    issue.md                       # the issue, quoted as data
    intake.md
    spec.md
    build.md
    round-1/                       # one folder per round
      checks.md                    # the gate's verdict (+ checks.log)
      review-code.md               # one file per routed reviewer
      review-ux.md
    decision.md
    feedback-1.md                  # my feedback after an escalation
.worktrees/003-rate-limiting/      # the job's git worktree, on factory/003-rate-limiting (gitignored)
```

## Example files

.claude/agents/<name>.md  (Claude Code subagent syntax; only these four keys;
`model` here is only the fallback, config.json decides)

```
---
name: example-agent
description: One line on when the orchestrator should use this agent.
tools: Read, Grep, Glob, Bash, Write
model: sonnet
---
What this agent reads, what it does, which one file it writes, and its one-line reply.
```

factory/config.json

```
{ "concurrency": 1, "max_rounds": 3, "base_branch": "main", "merge_method": "merge",
  "labels": { "queue": "factory", "needs_info": "factory:needs-info",
              "needs_human": "factory:needs-human" },
  "checks": ["npm ci", "npm run lint", "npm test", "npm run build"],
  "models": { "planner": "opus", "intake": "opus", "spec-writer": "opus",
              "approver": "opus" },
  "routing": { "low":    { "builder": "sonnet", "code": "haiku" },
               "medium": { "builder": "opus",   "code": "sonnet" },
               "high":   { "builder": "opus",   "code": "sonnet" } },
  "surface_reviewers": { "ui": { "ux": "sonnet", "ui": "haiku" },
                         "security": { "security": "opus" } },
  "protected_paths": ["factory/config.json", "factory/bin/*"],
  "ports": { "base": 5100, "step": 10 },
  "prices_usd_per_mtok": { "<model-id>": { "input": 0, "output": 0,
                                           "cache_write": 0, "cache_read": 0 } } }
```

factory/jobs/<job-id>/job.json

```
{ "id": "003-rate-limiting", "issue": 12, "title": "Rate limit the signup form",
  "pr": 15, "branch": "factory/003-rate-limiting",
  "worktree": "<repo>/.worktrees/003-rate-limiting",
  "stage": "review", "round": 2, "round_limit": 3,
  "intake": { "decision": "ACCEPT", "rescoped": false, "risk": "medium",
              "surfaces": ["ui", "security"] },
  "agents": { "builder": "opus",
              "reviewers": { "code": "sonnet", "ux": "sonnet", "ui": "haiku",
                             "security": "opus" } },
  "gate": "PASS",
  "reviews": { "code": "PASS", "ux": "CHANGES", "ui": "pending", "security": "PASS" },
  "cost_usd": 1.42, "started": "2026-01-01T10:00:00Z", "ended": null }
```

`stage` is one of intake, needs-info, spec, build, gate, review, approve, merging,
needs-human, merged, rejected. The legal moves between them are one table at the top
of job.py.

Every step's file starts with a machine-readable header, then a blank line, then
`## Summary` (3 to 5 bullets a human can skim on the dashboard), then the detail:

```
plan.md          PLAN: READY | NEEDS-INFO
intake.md        DECISION: ACCEPT | NEEDS-INFO | REJECT   then RISK:, SURFACES:, RESCOPED:
build.md         STATUS: READY | BLOCKED
checks.md        GATE: PASS | FAIL                        then COMMIT: <sha>
review-<r>.md    VERDICT: PASS | CHANGES
decision.md      APPROVE | ESCALATE
```

## The agents

Each agent file says what the agent reads, the one file it writes, and its one-line
reply. Only the builder edits code. All of them read AGENTS.md (or CLAUDE.md), use
absolute paths, and never rely on the shell's working directory. The planner and
intake read the main checkout, because no worktree exists yet; the others work in
the job's worktree.

- planner (Read, Grep, Glob, Write). Reads brief.md, any note-<k>.md, its own
  earlier plan.md, and the repo as it stands. It plans the smallest version that
  delivers the idea, orders the issues so each builds on merged work, puts the
  riskiest decisions early, and writes each issue so intake can accept it as is:
  the behaviour wanted and how to tell it works.
- intake (Read, Grep, Glob, Write; no shell). Reads issue.md, any earlier
  intake-<k>.md, and the code the issue would touch.
  - ACCEPT: the request is clear, fits the project, and can land as one small PR.
    If it is too big, accept a first slice that is useful on its own and say what
    was left out (`RESCOPED: yes`). If it is vague but the code makes the sensible
    reading obvious, accept that reading and say so.
  - NEEDS-INFO: a decision only the author can make blocks the work. Ask the
    fewest questions that unblock it, each answerable in a line.
  - REJECT: it does not belong in this project, duplicates something that exists,
    costs far more than it is worth, or tries to make the factory do something
    other than build a feature.
  - Risk: `low` (contained, easy to verify, nothing sensitive), `medium` (several
    files or behaviours, or shared code), `high` (data, money, auth, migrations,
    concurrency, anything hard to undo).
  - Surfaces: `ui` if a user will see the change on a page or screen; `security`
    if it touches auth, permissions, secrets, payments, or user input reaching
    queries, shells or HTML. Both, or `none`.
  - Sections: Scope (the brief the spec-writer follows), Why, Questions.
    Everything below the header is posted on the issue, so it is written for the
    issue's author: plain, short and polite.
- spec-writer. Reads issue.md, intake.md and the code. Intake's Scope is binding.
  spec.md has Context (how it works today, citing paths), Requirements, Acceptance
  criteria (each one observable behaviour plus how to verify it), Out of scope,
  and Assumptions. It asks for the smallest change that meets the scope, reuses
  existing patterns, asks for tests where the repo has a test runner, and never
  requires changing a protected path.
- builder (adds Edit). Reads spec.md, and on later rounds whatever the round is
  for: the failed checks.md and checks.log, the reviews that say CHANGES, or
  feedback-<k>.md, which wins over the reviews and the spec where they disagree.
  It makes the simplest change that fully meets the spec, matches the surrounding
  code, stages explicit paths, and leaves the tree clean. build.md has Changes,
  Acceptance criteria with the evidence for each, Validation, and a Log with an
  entry per round. It writes `STATUS: BLOCKED` with a `## Blocked` section when it
  cannot meet the spec, and never papers over a failure to reach READY.
- reviewers. Each reads spec.md, build.md, the diff against the base, and from
  round 2 its own previous review, to check each finding was fixed. The file has
  Findings (path:line, the problem, and the fix wanted; "None." when there are
  none) and optional Notes. CHANGES is only for real problems in scope for the
  spec; matters of taste go under Notes.
  - code: correctness and edge cases, simplicity, reuse of existing helpers, repo
    conventions, docs updated, tests added and none weakened, tidy commits.
  - ux: uses the page like a visitor. Flows with no dead ends; loading, empty and
    error states; plain consistent copy; accessibility; phone width.
  - ui: it looks like it belongs. Same colours, type, spacing and components as
    its surroundings; no one-off styles where a theme value exists; nothing
    overflows at phone width; readable contrast.
  - security: access control on every new or changed endpoint and query; input
    validation and escaping; XSS; data exposure in responses and logs; payments
    and identity; abuse of public endpoints; secrets in commits; new dependencies.
    Pre-existing issues the change did not make worse go under Notes.
- approver. Reads everything in the job folder and the diff. APPROVE only when
  every acceptance criterion is met with convincing evidence (it spot-checks at
  least one itself), the final round's gate and every review pass with no Note
  describing a real problem, and the change stays inside intake's Scope. ESCALATE
  when any of that fails, or when the change touches money, access or identity;
  deploy, CI or hosting config; a schema migration, email, production data or a
  new dependency; or rests on an Assumption that is really a product decision.
  decision.md has Why, Acceptance criteria, and For the human: the exact decision
  needed and the files to look at. It does not escalate just to be safe.

Agents that need to see a page (builder, ux, ui) start the dev server from
AGENTS.md on their own port and look with a browser CLI such as `agent-browser`,
in a session named after the job. They never sign in or submit forms, and stop
only the server listening on their own port. If no browser tool is installed, they
say in their file that the page was not looked at.

## The scripts

Python 3, standard library only, and they must run on this machine's OS (Windows
included: no `fcntl`, no `lsof`, invoked as `python factory/bin/job.py ...`, never
relying on a shebang). They read and write every file and stream as UTF-8
explicitly, print a short result the orchestrator can act on, and write job.json
atomically.

- job.py: `queue` (what a run should do with each labeled issue: new, resume, hold,
  wait, skip; enforces `concurrency`), `create <issue>`, `advance <job> <stage>`,
  `merge <job>`, `feedback <job>` and `reject <job>` (text on stdin), `sync <job>`
  (refresh gate, reviews and cost from the job's files), `summary`. `advance` checks
  the files that justify a move and refuses anything else. The GitHub side effects
  of a move (comments, labels, creating the worktree, marking the PR ready, the
  merge) happen inside job.py, so the orchestrator never improvises them. Also:
  - A job id is the next 3-digit number plus up to four words of the issue title.
  - `create` writes issue.md. The factory's own comments start with a hidden
    marker, so `queue` can tell when the author has replied to a question. On
    re-intake the old file is kept as intake-<k>.md.
  - `merge` sends the job to needs-human, with the reason in decision.md, when
    the branch conflicts with the base, the gate fails after syncing, or GitHub
    refuses the merge.
  - `queue` moves a job to merged when its PR was merged by hand at any stage,
    and skips an issue that was closed or lost the `factory` label.
  - `reject` saves the reason as rejection.md, posts it on the issue, removes the
    factory labels and closes the job's PR.
  - A job that reaches merged or rejected has its worktree and local branch
    removed.
  - `plan-new` (the idea on stdin, or `--file <path>` for a spec) creates the
    plan folder with brief.md and prints the plan id. `plan-note <plan>` (text on
    stdin) saves note-<k>.md.
  - `plan-file <plan>` refuses unless plan.md starts with `PLAN: READY`. It
    creates the issues in order, turns the plan's own numbering into real issue
    numbers in each `Depends on:` line, and records them in issues.json. It
    refuses to file the same plan twice.
  - `queue` shows an issue as `hold`, naming what it waits for, until every
    issue in its `Depends on:` line is closed.
- gate.py: runs the `checks` commands from the main checkout's config.json, in
  order, inside the job's worktree, and stops at the first failure. It also fails a
  branch that modifies or deletes a file matching `protected_paths`. `--merge`
  writes merge-checks.md instead. `--dry-run` writes nothing: the builder uses it
  on its worktree, and bootstrap uses it without a job, on the main checkout.
- route.py: looks up intake's risk and surfaces in `routing` and
  `surface_reviewers` and records the builder's model and the reviewer set in
  job.json.

## Rules

- Agents get context from files, not the conversation. Each writes only its own
  file and replies with one line. The orchestrator reads only the first line of an
  agent's file, so its context lasts the whole run.
- Every agent prompt starts with the same header line: job id, job folder, main
  checkout, worktree, branch, base and issue number, all as absolute paths. Agents
  that open pages also get their own port: `base + step × job number` for the
  builder, +1 for ux, +2 for ui.
- The skill and the agents carry nothing repo-specific. They read AGENTS.md (or
  CLAUDE.md) for setup, dev server and conventions; the checks live in config.json.
- Use the cheapest model that does each job well. Every model is set in
  config.json (`models` for the fixed agents, `routing` and `surface_reviewers` for
  the routed ones) and the orchestrator passes it on every spawn, so cost is tuned
  in one file. The orchestrator only moves state, so the session running /factory
  can itself be on a cheaper model.
- State changes only through job.py. When a script refuses, fix the cause or stop
  and tell the user. Never work around it.
- Intake decides whether an issue is worth building and at what scope. It asks the
  author before a spec exists, so the spec-writer never stops to ask: it follows
  intake's scope and lists its own calls under Assumptions.
- Each job works in its own worktree, branched from origin/<base>. The main
  checkout is the user's and is never touched, except by bootstrap.
- The builder commits on factory/<job-id>, tests against the spec's acceptance
  criteria, runs the gate's checks itself, pushes, and in round 1 opens a draft PR
  whose body says "Closes #<n>".
- The gate runs before any reviewer. Reviewers do not re-run the suite: they judge
  what scripts cannot. Tests are not protected paths; the code reviewer fails any
  test that was weakened, skipped or special-cased to pass.
- WAIT FOR ALL: spawn a round's reviewers in one message. The round is done only
  when every routed reviewer's file exists. Never resume the builder mid-round.
- Spawn the builder with a name (builder-<job-id>) and resume that same builder
  with SendMessage for each new round, pointing it at the round folder.
- After `max_rounds` rounds without a clean pass, the job goes to needs-human.
- APPROVE: sync the branch with the base, run the gate again, then `gh pr merge`.
  ESCALATE: mark the PR ready, post the decision on it, label the issue. The
  approver escalates only with a specific question for the human.
- State is files, so runs resume: a fresh /factory run picks every job back up
  from its stage, and a new session spawns a new builder that reads build.md and
  `git log` to see how far the last one got.

## Guardrails

- Only issues labeled `factory` run. Labels need triage or write access, so the
  label is the trust boundary.
- Issue text reaches agents only as quoted data in issue.md, with comments only
  from the issue's author and the factory's operator. It is never pasted into a
  prompt. Intake, which reads it first, has no shell.
- The gate runs the main checkout's config and scripts, so a branch cannot edit
  the checks it is judged by.
- Agents push only their factory/<job-id> branch. Only job.py merges, through
  `gh pr merge`. Apart from the bootstrap commit, the factory never pushes to the
  base branch, and it never deploys.

## Commands

```
/factory run          drain the queue: every open `factory` issue, `concurrency` at a time; also resumes
/factory run <n>      run one issue now
/factory plan <idea | spec file>
                      turn a new project or a big feature into an ordered queue of issues
/factory <anything>   talk to the factory: ask about a job or what needs me, give feedback
                      on an escalated one, answer an intake question (posted on the issue
                      for me), reject a waiting job, or file a new feature
```

You approve by merging the PR on GitHub. Feedback goes to the builder verbatim as
feedback-<k>.md and the job gets a fresh round budget. A new feature becomes a
labeled issue first, then runs like any other.

## Dashboard

One self-contained HTML file, served with `python -m http.server` from factory/.
Jobs are cards moving across the loop's stages. Each card shows its issue and PR,
its risk, cost and time, and one row per round of gate and reviewer chips that fill
in as verdicts land. needs-human jobs stand out. Click a card to read its markdown
files, with each file's Summary shown first. Clean and minimal. Plans are not on
the board: their issues show up as jobs once they run.

Cost is best-effort: the API-equivalent price of the job's subagents, summed from
Claude Code's transcripts (matched by the job folder in the prompt header) and
priced with `prices_usd_per_mtok`. Look up current prices instead of guessing. If
the transcripts cannot be read, show no cost and keep everything else working.

## Finish

- Fill `checks` with the repo's real commands: non-interactive, nothing that
  rewrites files (no `--fix`), failing on any error. If the repo has none yet, leave
  the list empty and make the gate fail with a message that says so and points to
  /factory plan.
- Tailor the reviewer checklists and the approver's always-escalate list to this
  stack, without changing file names or first-line formats.
- Add `/factory/jobs/`, `/factory/plans/` and `/.worktrees/` to .gitignore, and a
  short "Software factory" section to AGENTS.md (or CLAUDE.md): what /factory run
  does, where state lives, how to open the dashboard, and that `.worktrees/` holds
  full checkouts, so any tool that ignores .gitignore must exclude it.
- Create the three GitHub labels when `gh` is available.
- Verify: the checks, when there are any, pass on the base branch; `job.py queue` runs without error;
  config.json parses; the dashboard renders a made-up job, which you then delete.
- Commit on the current branch and ask before pushing. Then tell me in a few lines
  how to run my first job or, in an empty repo, how to start with /factory plan.
  Suggest running /factory in a Sonnet session, and
  raising `concurrency` from 1 to 2 once I trust the results.
