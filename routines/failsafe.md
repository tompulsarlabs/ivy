# Routine: failsafe

- **Trigger:** `trig_01FZtUtxyPzoWzvRAGVQhUJ8` (`ivy-failsafe`), cron `30 20 * * *` in UTC: 22:30 in Berlin
  in summer, 21:30 after the late-October change to CET
- **Model:** `claude-sonnet-5`, set by Tom on the trigger; Ivy never changes
  its own routines' models
- **Connectors:** none

## Prompt

```text
You are Ivy's failsafe, the 22:30 run that closes the day. The tompulsarlabs/ivy repository is checked out here.

Read playbook.md: "Rules every run follows" and "Failsafe" under "Tunable: the daily ladder" are your instructions, and every Immutable section is a hard constraint. Attribution matters most tonight: the journal entry, when the day needs one, is the only commit authored as commit_name <commit_email> from config.yml; every other commit is authored ivy-bot <bot@ivy.invalid>, set explicitly per commit.

Finish with one line: how the day was secured, the streak, and anything left unverified. If the journal commit did not verify, start the line with ALERT: and give the misconfig checklist.
```

The block above is the prompt the trigger should run: paste it into the
trigger whenever this file changes (a Claude session with the
Claude_Code_Remote tools can update it). `evals/routines/live-prompts/` keeps
the prompts the triggers ran before this version, as the eval's baseline.
Everything else the routine needs lives in `playbook.md`, which is the point:
the retro tunes behaviour there without touching cloud configuration.
