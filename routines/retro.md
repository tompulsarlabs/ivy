# Routine: retro

- **Trigger:** `trig_015JhFyeg4kGtrjHFwAi7hbU` (`ivy-retro`), cron `0 8 * * 0` in UTC: Sunday 10:00 in Berlin
  in summer, Sunday 09:00 after the late-October change to CET
- **Model:** `claude-sonnet-5`, set by Tom on the trigger; Ivy never changes
  its own routines' models
- **Connectors:** none

## Prompt

```text
You are Ivy's weekly retro, the Sunday 10:00 run. The tompulsarlabs/ivy repository is checked out here.

Read playbook.md: "Tunable: retro" is your instruction set, and every Immutable section is a hard constraint that only Tom changes. Every commit this run makes is authored ivy-bot <bot@ivy.invalid>, set explicitly per commit.

Finish with one or two lines: what changed and the evidence for it, or why nothing changed.
```

The block above is the prompt the trigger should run: paste it into the
trigger whenever this file changes (a Claude session with the
Claude_Code_Remote tools can update it). `evals/routines/live-prompts/` keeps
the prompts the triggers ran before this version, as the eval's baseline.
Everything else the routine needs lives in `playbook.md`, which is the point:
the retro tunes behaviour there without touching cloud configuration.
