---
id: 2026-09-22-tomgreenai-hero-01
type: build
state: open
repo: tompulsarlabs/tomgreen.ai
lane: workhorse
pool: anthropic
created: 2026-09-22T14:30:00+02:00
created_by: tom
expires: 2026-09-24T14:30:00+02:00
budget: { wall_minutes: 30 }
---

## Task
Tighten the homepage hero copy to two sentences, keeping the Ivy and Scout
links. Branch from main; open a draft PR; never push to the default branch.

## Definition of done
A draft PR by tompulsarlabs referencing 2026-09-22-tomgreenai-hero-01 changes
only src/app/page.tsx.

## Verification (cloud-checkable)
search_pull_requests finds that draft PR, and its body names the contract id.
