# Routine: scout

- **Trigger:** `trig_01P42rzh3kFT9yVTW1E6WoXW` (`ivy-scout`), cron `0 7 * * *` in UTC: 09:00 in Berlin
  in summer, 08:00 after the late-October change to CET
- **Model:** `claude-sonnet-5`, set by Tom on the trigger; Ivy never changes
  its own routines' models
- **Connectors:** none

## Prompt

```text
You are Ivy's scout, the 09:00 run of the daily ladder. The tompulsarlabs/ivy repository is checked out here.

Read playbook.md: "Rules every run follows" and "Scout" under "Tunable: the daily ladder" are your instructions, and every Immutable section is a hard constraint. This run's commits are system bookkeeping, so each one is authored ivy-bot <bot@ivy.invalid>, set explicitly per commit.

Finish with one line: how many candidates, the top pick, and any blocker or nudge.
```

The block above is the prompt the trigger should run: paste it into the
trigger whenever this file changes (a Claude session with the
Claude_Code_Remote tools can update it). `evals/routines/live-prompts/` keeps
the prompts the triggers ran before this version, as the eval's baseline.
Everything else the routine needs lives in `playbook.md`, which is the point:
the retro tunes behaviour there without touching cloud configuration.
