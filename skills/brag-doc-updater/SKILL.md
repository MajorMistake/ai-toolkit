---
name: brag-doc-updater
description: Capture and format professional accomplishments into a structured brag doc. Use this skill whenever the user mentions updating their brag doc, logging an accomplishment, documenting work they're proud of, reviewing sprint tickets for achievements, preparing for a performance review, updating their resume, prepping talking points for a 1:1, or when they describe completing something significant and you think it's worth capturing. Also trigger when the user says things like "I should probably write this down" or "this would be good for my brag doc" or describes a win at work. Produces markdown output for Obsidian.
---

# Brag Doc Updater

## Purpose

Capture accomplishments in a structured format that serves three audiences:
1. **Performance reviews** — evidence of impact with business context
2. **Resume/job search** — translated, portable descriptions of what you did and why it mattered
3. **1:1 talking points** — concise reminders of what to surface with your manager

Every entry is stored in STAR format with two layers: a **technical version** (preserving specific tools, systems, and implementation details) and a **translated version** (abstracting to impact and transferable skills for non-technical or external audiences).

## Two modes of operation

### Mode 1: Fresh capture

The user just finished something and wants to log it. They'll describe what they did in natural language, often casually. Your job is to extract the STAR structure and ask targeted questions to fill gaps.

### Mode 2: Sprint review (batch processing)

The user is reviewing tickets from a sprint/period and wants to identify brag-worthy items. They may paste ticket titles, descriptions, or a list of completed work. Your job is to:
1. Help triage — not everything is brag-worthy, and the user shouldn't dilute their doc with routine work
2. Identify which items have real impact worth capturing
3. Draft entries for the ones that matter

**Triage guidance for batch mode:** An accomplishment is brag-worthy when it involves at least one of: solving a problem others couldn't or didn't, measurable impact (cost savings, time savings, risk reduction), building something new or significantly improving something existing, influence beyond your immediate scope, overcoming a meaningful constraint or blocker, or demonstrating growth into new areas. Routine ticket completion, bug fixes without broader context, and "did my job" items generally don't belong unless there's a story behind them.

## STAR entry format

Each entry should follow this markdown template:

```markdown
## [Short descriptive title]
**Date:** [YYYY-MM or date range]
**Tags:** [comma-separated — e.g., ci-cd, cost-savings, cross-team, infrastructure]

### Technical version
**Situation:** [What was the context? What problem existed? Why did it matter?
Include specific systems, tools, team context.]

**Task:** [What were you specifically responsible for? What was your role
vs. others involved?]

**Action:** [What did you actually do? Be specific — name the technologies,
approaches, decisions. This is where implementation detail lives.
Include key decisions and why you made them.]

**Result:** [What happened? Quantify where possible — time saved, cost reduced,
reliability improved, scope of impact. Include both immediate results
and downstream effects if known.]

### Translated version
**One-liner:** [A single sentence suitable for a resume bullet point.
Format: "[Action verb] [what you did], [resulting in/achieving] [measurable outcome]"]

**Narrative:** [2-3 sentences telling the story without jargon. A non-technical
manager or recruiter should understand the impact. Focus on the problem
you solved and why the solution mattered.]

### 1:1 talking points
- [1-2 bullet points — what to mention to your manager about this work.
  Focus on what they care about: reliability, cost, risk, velocity, visibility.]
```

## Gathering context

### For fresh capture

When the user describes an accomplishment, map what they say to STAR components. Then ask about what's missing. Common gaps:

- **Situation is vague**: "What was broken/expensive/slow before you did this? Who was affected?"
- **Task ownership is unclear**: "Were you the sole owner or part of a team? What was specifically yours?"
- **Action lacks specificity**: "What tools/approaches did you use? Were there alternatives you considered and rejected?"
- **Result isn't quantified**: "Do you have numbers? How many people/systems/dollars were affected? If you don't have exact numbers, can you estimate the order of magnitude?"

Don't interrogate — weave these into conversation. If the user doesn't have numbers, note that as a gap they could fill later rather than blocking the entry.

### For sprint review

Ask the user to share their completed tickets (titles, descriptions, or just a list). Then:
1. Present a quick triage: "Here are the ones I think are brag-worthy and why. The rest look like solid routine work. Agree?"
2. For each brag-worthy item, ask for the context the ticket title doesn't capture
3. Draft entries, noting where you're guessing and what details are missing

## Writing principles

- **Be specific, not grandiose.** "Migrated jira-all-projects-collector from Jenkins to GitHub Actions with ArgoCD deployment" is better than "Led transformative CI/CD modernization initiative." The technical version should sound like an engineer talking to engineers. The translated version should sound like a competent professional explaining impact to a smart non-expert.
- **Quantify, but don't fabricate.** If the user doesn't have metrics, say so: "Result: Eliminated manual deployment steps (estimated time savings TBD)" is honest. Don't invent percentages.
- **Capture decisions, not just actions.** "Chose GitHub Actions over CircleCI because [reason]" is more valuable than "set up GitHub Actions." Decisions show judgment; task completion shows... task completion.
- **The translated version is not a dumbed-down version.** It's a reframing that emphasizes business impact over implementation detail. Replace tool names with what those tools accomplish. "Automated the data collection pipeline" vs. "Built a Python script using the Jira REST API with pagination handling."
- **Tags should be useful for filtering later.** Think about categories that matter at review time: cost-savings, reliability, cross-team, new-capability, process-improvement, mentoring, etc.

## Output format

Produce clean markdown ready to paste into Obsidian. Use the template above exactly — the user can adjust formatting preferences later, but consistency across entries matters more than any particular style choice.

When producing multiple entries in batch mode, separate each with a horizontal rule (`---`).

## Example

Here's what a good entry looks like (based on a real accomplishment):

```markdown
## Migrated jira-all-projects-collector to GitHub Actions/ArgoCD
**Date:** 2026-01
**Tags:** ci-cd, infrastructure, migration, jenkins-deprecation

### Technical version
**Situation:** The jira-all-projects-collector pipeline was running on Jenkins,
which the team was actively deprecating. The Jenkins instance had reliability
issues and lacked integration with the team's evolving GitOps workflow.

**Task:** Own the full migration of this pipeline from Jenkins to GitHub Actions
with ArgoCD-based deployment, including testing and validation that data
collection continued uninterrupted.

**Action:** Rebuilt the pipeline as a GitHub Actions workflow with ArgoCD
deployment manifests. Handled credential migration, scheduling configuration,
and validated output parity between old and new pipelines. Documented the
migration pattern for other pipelines still on Jenkins.

**Result:** Pipeline successfully migrated with zero data collection gaps.
Established a reusable migration pattern for remaining Jenkins pipelines.
Reduced dependency on deprecated infrastructure.

### Translated version
**One-liner:** Migrated critical data pipeline from legacy to modern CI/CD
infrastructure, establishing a reusable pattern for remaining migrations.

**Narrative:** Our team was moving off an aging automation platform, but several
key data pipelines still depended on it. I migrated one of the more complex
ones — a collector that aggregates project data across the organization — to
our modern deployment stack, validated continuity, and documented the pattern
so future migrations would be faster.

### 1:1 talking points
- Completed the jira-all-projects-collector migration — one less thing on
  Jenkins, and the pattern I documented should accelerate the remaining ones.
- Good candidate to highlight as a concrete infrastructure improvement when
  discussing team velocity and technical debt reduction.
```

## After drafting

- Ask if any entries feel inflated or understated — calibration matters more than polish
- Flag entries where the Result section is thin and suggest the user revisit after more time has passed (sometimes impact becomes clearer weeks later)
- If in batch mode, confirm the triage — did the user agree with what was and wasn't brag-worthy?
- Offer to tag entries by likely use (perf-review, resume, 1:1) if the user wants that layer
