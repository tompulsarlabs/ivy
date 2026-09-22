# Workflow decision: portable context, one dispatch authority

22 September 2026. Recommendation for Tom's requested Paperclip release and
workflow evaluation. This proposes operational changes; it does not modify Ivy's
production instructions, schedules, Cockpit or model configuration.

## What the linked article argues

Neema Rashidee's [LinkedIn post](https://www.linkedin.com/posts/neemarashidee_we-have-this-conversation-often-at-notion-share-7507815017367363585-NfZA/)
links Vitoria Lima's [The importance of a (or many) Switzerland(s) in AI](https://www.aiminutes.co/articles/the-importance-of-a-switzerland-in-ai)
(16 September). Its useful argument is that independent tools can choose among
model providers, while a business's durable asset is its accumulated context:
decisions, client knowledge and workflows. It suggests structured, reusable
knowledge instead of repeatedly rebuilding it around whichever model leads.
The Notion comparison is a product direction, not evidence of better outcomes.

## Recommendation

Adopt portable context and replaceable workers. Keep each record authoritative
in one place. Use Paperclip for coordination if its operational controls pass;
retain Ivy's acceptance rules and independent evidence checks. Do not move
everything into Notion or rebuild the existing system to follow the analogy.

| Home | Responsibility | Tradeoff |
| --- | --- | --- |
| GitHub | Code, versioned task contracts, source revisions, PR/CI evidence, accepted technical decisions | Strong history and reproducibility; less pleasant for broad research and collaborative prose |
| Paperclip | Task ownership, queue, review state and the operator's next action | Reuses an existing product; adds a database, auth, updates, backups and integration failure modes |
| Ivy | What work matters, acceptance criteria, independent verification and learning from results | Preserves the useful domain logic; requires discipline about what “verified” means |
| Notion, optionally | Human-authored briefs, research and decisions where collaborators actually write | Easier knowledge work; export/reimport and permissions are weaker substitutes for a versioned execution contract |
| Agent harnesses | Execute bounded tasks against their declared sources | Model choice remains replaceable; authentication, tooling and output formats still need adapter-specific checks |

Notion is worth adding if writing/collaboration there reduces friction. I have
not audited Tom's Notion usage, so migration has no demonstrated benefit yet.
Its [MCP connection](https://www.notion.com/help/notion-mcp) lets external AI tools
use its content, but acts with the connected user's permissions. Its
[exports](https://www.notion.com/help/back-up-your-data) help portability, yet
cannot recreate a workspace simply by re-uploading them. Model choice does not
remove application, permission or data-model dependence.

## The daily workflow

1. Tom chooses the outcome and priority. Use a short brief: context, desired
   result, acceptance evidence and decisions that need Tom.
2. Ivy turns that into one executable task: source commit or document revision,
   allowed actions, expected artifact and concrete checks. Routine small changes
   stay small; don't require an elaborate interview for every task.
3. One dispatcher owns the task. The worker delivers a branch/PR or artifact and
   its observed checks. GitHub remains authoritative for code changes.
4. Independent checks establish what actually passed. Failed or unavailable
   checks remain visible. Tom sees decisions and exceptions that need attention.
5. Capture the accepted outcome and a short reusable lesson. Update a canonical
   brief or policy only when evidence warrants it, with behavior evals for agent
   instruction changes. Link records across tools instead of copying live status.

During adoption the existing Ivy queue remains authoritative. Paperclip starts
with manual board use and isolated replay. Cut over one task class only after
proving ownership/recovery, and disable the former dispatcher for that class.
Running both against the same work would create competing assignments and retries.

## Evidence from Ivy

The current system already separates claimed completion from checked completion
and keeps contracts in Git. That is worth preserving. However, the
`2026-09-09-talentradar-sybilintake-review-01` verification note explicitly says
it could not check referenced paths and used the PR description as corroboration.
That does not satisfy its stated path-existence check. An attractive board would
not repair this evidentiary gap.

For a representative contract, this continuation independently fetched the
`2026-09-10-tomgreenai-planetarymap-review-01` report from GitHub at Ivy main
`59b6eac9c6185ab5aca40c88f091410b00c899cb` and checked its nine linked files against
PR #54 head `ebeeb079eddfdcf3718abf7b16e5b6ef53b99e29`. All files exist, all cited
lines are in range, and GitHub reports successful CI on that source commit.
[The recorded reassessment](evidence/contract-readiness-20260922/assessment.json)
retains source hashes, paths and check URLs.

The original review did not pin its source commit, and the observed CI finished
after the report. This is a present-day source reassessment, not proof of the
original report's correctness, historical acceptance or a Paperclip replay.
No model or judge was run. Future task contracts should pin the reviewed commit.

## Options and decision criteria

| Option | Benefit | Cost / failure mode | Assessment |
| --- | --- | --- | --- |
| Keep everything Git-first | Few moving parts; existing workflow works | Tom still needs to interpret scattered task/agent state | Keep as a baseline |
| Move the workflow into Notion | Shared prose and context become easier to use | Migration, duplicated states, broad integration permissions; execution still needs a reliable coordinator | Insufficient evidence to justify it |
| Add Paperclip, retain Git, use Notion selectively | Reuse coordination UI while keeping source evidence portable | Hosting and integration maintenance; must enforce one dispatch authority | Recommended, staged by task class |

Judge the change on the next representative tasks: time to an accepted useful
result, avoidable interruptions to Tom, first-pass acceptance, rework, actual
spend and whether evidence can be replayed. A green contribution graph can remain
a hygiene signal; it is not enough to measure useful outcomes. No cost or quality
improvement has been measured from Paperclip yet.

The [prepared hosting proposal](../../deploy/paperclip/README.md) estimates
$20–40/month before tax on Railway with a proposed $40 compute shutdown limit.
The app can be hosted without model credentials. Remote worker integration,
isolated authentication and paid model execution are separate unfinished work.
