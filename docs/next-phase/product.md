# Product hypothesis and validation

Status: proposed, unvalidated externally. Tom's selected audience is teams shipping
coding or internal-workflow agents. No buyer interviews, price validation or customer
commitments occurred during this design pass.

## The costly job

“When I change an agent's instructions, model or tools, help me establish that it
still performs the work we rely on, identify regressions, and explain what evidence
is missing, so I can make a release decision.”

The initial user is an engineering or AI lead responsible for an agent already used
by a team. The acceptance owner can approve the workflow's requirements. The likely
budget owner is a head of engineering or AI; that is a hypothesis to test, not a
known buying process. The useful trigger is a real upcoming release or a recent
acceptance failure, not general enthusiasm about agents.

Begin with one PR-review agent: its inputs can be frozen in small repositories,
its findings can be checked against source and independently labeled defects, and
it can run without production write access. The next workflow should come from a
customer's committed pilot, rather than a list of hypothetical integrations.

The current workaround may involve replaying examples, reading tool logs, inspecting
repository changes, and gathering sign-off in a document. Ask teams to show their
last instance of that work. We have not measured how common or costly it is.

For each qualified team record:

| Quantity | Measurement |
|---|---|
| Setup and review burden | Engineer hours for the last actual agent change; separate fixture creation, execution and review |
| Recurrence | Number of comparable releases in the last month |
| Rework | Observed hours/cost following a missed defect or misleading pass |
| Delay | Elapsed time waiting for acceptance, recorded separately from labor |
| Existing solution | Tools and process used, what works, and the specific remaining gap |

Monthly addressable effort = comparable releases × repeatable setup/review hours.
Value estimate = effort actually removed × the buyer's loaded hourly cost, plus
observed avoidable rework. Do not add speculative incident losses or convert release
delay into invented revenue. Track initial onboarding cost separately: if setup costs
more than repeated acceptance saves, the product has not earned its place.

## What already exists

| Existing capability | Primary source, inspected 2026-09-05 | Consequence for this proposal |
|---|---|---|
| Experiments, custom scoring and CI | [Braintrust evaluation](https://www.braintrust.dev/docs/evaluate) | Do not build an undifferentiated experiments dashboard |
| Agent/tool evaluation and simulated environments | [Braintrust agents](https://www.braintrust.dev/docs/best-practices/agents) | Actual tool effects are not a unique feature claim |
| Human annotation, code evaluation and comparison | [Langfuse evaluation](https://langfuse.com/docs/evaluation/overview) | Mixed graders and human review are expected capabilities |
| Customer-operated infrastructure | [Langfuse self-hosting](https://langfuse.com/self-hosting) | Customer control is a requirement, not a moat |
| Local tests, custom providers, assertions and CI | [Promptfoo](https://www.promptfoo.dev/docs/intro/) | Model choice and portable test definitions already exist |

**Differentiation hypothesis:** a team can get from an actual proposed agent change
to useful acceptance evidence materially faster with Ivy than with its current
process or a small configuration of these tools. This depends on the quality of the
workflow pack, harness setup and evidence explanation. It is not an established
technical advantage. Test a thin Promptfoo-backed implementation before owning a new
experiment engine; keep portable manifests and customer-controlled execution either way.

## What the first user does

1. Select one review-agent baseline and changed instruction bundle, with a named owner.
2. Review six representative scenarios and their acceptance requirements. Freeze them
   before either variant runs; keep defect answers in the evaluator's private fixtures.
3. Execute a bounded comparison in an isolated environment using the chosen harness.
4. Inspect regressions, evidence gaps, actual outputs and effort, then record a decision.

The headline is “Meets this benchmark”, “Does not meet this benchmark”, or “Evidence
incomplete”. The scope, repetitions and unresolved checks appear beside it. The
operator records release, hold or request evidence against the exact version tested.
Meeting a small benchmark is not a general claim of safety or approval of a reviewed PR.

## Demand experiments and stop conditions

These thresholds are proposed experiment choices. They are not measured market facts.
Tom handles outreach; this design has sent no messages to potential customers.

| Gate | Evidence required | Stop or change direction when |
|---|---|---|
| Problem | Five qualified conversations about a recent release; at least three show recurring acceptance effort of four or more engineer hours per release, or a documented costly miss | Interest stays hypothetical, the burden is rare, or existing tooling already satisfies the job |
| Commitment | Two teams contribute a pending change, baseline, representative cases and an acceptance owner who will review the result | No real artifacts arrive, or each environment needs days of bespoke reconstruction |
| Value | Two bounded concierge pilots; target at least 50% lower repeatable review/setup effort after separately reporting onboarding, and a decision on an actual change | The report changes no decision, the evidence is not trusted, or total effort exceeds the workaround |
| Commercial | At least one paid follow-on or deposit after the buyer sees its own result, with a repeatable scope | Both decline payment or all value depends on bespoke consulting |

Conduct the problem conversations alongside the two-hour feasibility spike. Before
continuing into the full proof as product validation, require one named external
release owner, a pending change and a timed sample of the current workaround.
Further internal dogfood without that evidence requires Tom's explicit choice. A working local demo
can justify a pilot; it cannot satisfy the demand or payment gates. If the workflow
is valuable but setup remains bespoke, offer a bounded acceptance-testing service
and learn from that before claiming a scalable software product.

## Scope that can earn expansion

The proof has one workflow, two instruction variants and one functioning harness.
A second harness validates the adapter contract only after the first result is useful.
Model changes follow a successful instruction comparison; change one factor at a time.
An external pilot brings its own actual environment and private data policy.

Defer fleet routing, autonomous prompt optimization, hosted multi-tenant execution,
SSO, billing, a connector marketplace and broad governance until a buyer need selects
them. The future enterprise path is customer-operated execution plus a shared review
service if collaboration justifies it. There is no requirement to build a new model.
