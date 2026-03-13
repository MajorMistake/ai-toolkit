---
name: leadership-report
description: Draft concise, findings-driven reports for leadership with clear recommendations. Use this skill whenever the user mentions writing a report for leadership, preparing findings for their manager or director, documenting investigation results, writing up analysis for stakeholders, drafting a Confluence page with recommendations, or preparing any written deliverable that needs to persuade senior people to act. Also trigger when the user mentions writing something for Victor, Nancy, or "leadership" at Cyderes. This skill produces two outputs — the report itself and a Teams hook message to drive readership.
---

# Leadership Report Skill

## Why this skill exists

The hardest part of a leadership report isn't the writing — it's getting anyone to read it and act on it. This skill treats that as a first-class design constraint. Every report produces two artifacts:

1. **The report** (Confluence-ready markdown) — concise, scannable, with a clear "so what"
2. **The Teams hook** — a short message designed to make someone actually click the Confluence link

## When to use this skill

Trigger when the user is:
- Writing up findings from an investigation (e.g., spend analysis, incident review)
- Preparing recommendations for leadership
- Documenting a technical decision or proposal for non-technical stakeholders
- Creating any Confluence page meant to persuade or inform senior people

## Gathering context

Before drafting, collect these essentials. Ask conversationally — don't dump a form.

1. **The headline**: What is the single most important thing leadership should walk away knowing? Force this to one sentence. If the user gives you three things, push back and ask which one matters most. The others become supporting findings.
2. **The ask**: What do you want leadership to *do* after reading this? Be specific. "Be aware" is not an action. "Approve switching to X" or "Prioritize investigation of Y" are actions.
3. **The evidence**: What data, observations, or sources support the headline? Encourage the user to share raw evidence — logs, screenshots, queries, ticket numbers. The skill will help distill.
4. **The audience**: Who specifically will read this? Different people care about different things. A director cares about business impact and risk; a manager cares about feasibility and team load.
5. **Scope boundary**: What is this report explicitly *not* covering? Stating scope prevents the "but what about..." derailment.

## Report structure

Use this structure. Do not add sections unless the user asks. Shorter is better — every sentence should earn its place.

```
# [Descriptive title — not clever, not vague]

## Bottom line
[1-3 sentences. The headline finding and the recommended action. A busy director
should be able to read only this section and know what you found and what you want.]

## Key findings
[2-5 findings, each as a short paragraph or single sentence with supporting evidence.
Use specific numbers, dates, and sources. No filler. Each finding should connect
to the bottom line or to a recommendation.]

### Finding 1: [Concise label]
[Evidence and context. Cite sources inline — link to dashboards, tickets, logs.]

### Finding 2: [Concise label]
[Same pattern.]

## Recommended actions
[Numbered list. Each recommendation should be concrete and assignable.
Include who should own it if known. Include rough effort/complexity if possible.]

1. **[Action]** — [Why, what it addresses, who owns it]
2. **[Action]** — [Why, what it addresses, who owns it]

## Methodology and scope
[Brief — how you investigated, what tools/data you used, what you explicitly
did not examine. This section exists for credibility, not length. 2-4 sentences.]
```

## Writing principles

These matter more than the template:

- **Lead with the conclusion.** Do not build suspense. Leadership reads the first paragraph and maybe skims the rest. Put the answer first.
- **Be specific, not thorough.** "VertexAI spend is $10.2K/month, 73% attributable to Project X" beats "There are several factors contributing to elevated cloud costs across multiple services."
- **Quantify when possible.** Dollars, percentages, dates, counts. Vague findings get vague responses.
- **Name things.** Specific projects, services, teams, dashboards. Not "certain services" or "some teams."
- **Cut the throat-clearing.** No "This report aims to provide an overview of..." — just start with the finding.
- **Show your work without showing all your work.** Cite sources and link to evidence. Don't reproduce every query you ran.
- **Recommendations should be actionable by someone other than you.** "We should investigate further" is weak. "Eng team should audit Project X's Gemini API calls and implement usage caps — estimated 2-3 days" is strong.

## The Teams hook message

After drafting the report, produce a Teams message designed to drive clicks. This is a separate, critical output.

The Teams hook should:
- Be 2-4 sentences max
- Lead with the most compelling or alarming finding (not "I wrote a report about...")
- Include the specific number or fact that makes someone stop scrolling
- End with the Confluence link
- Not try to summarize the whole report — create curiosity, not completeness

**Example pattern:**
> We're spending $10.2K/month on VertexAI and 73% of it traces to a single project's unthrottled API calls. I dug into the attribution and have recommendations for reducing this. Full findings here: [link]

**Anti-pattern:**
> Hi team, I've completed my analysis of our VertexAI spending patterns. The report covers several findings and recommendations. Please review when you get a chance: [link]

The first version gives someone a reason to click. The second is ignorable.

## Output format

Produce two clearly labeled outputs:

1. **Confluence Report** — Full markdown, ready to paste into Confluence. Use Confluence-compatible markdown (headers, tables, numbered lists). Offer to produce this as a file if the user prefers.
2. **Teams Hook Message** — The short Teams message, ready to copy-paste.

## Iteration guidance

After the first draft:
- Ask the user to read the Bottom Line section and verify it captures their actual message
- Ask if any findings should be cut (if in doubt, cut)
- Ask if the recommendations are things leadership can actually say yes/no to
- Check that the Teams hook would make *them* click if they saw it in their feed

## Common failure modes to watch for

- **Scope creep**: The user wants to add "just one more finding." Push back — suggest it goes in a follow-up report or an appendix.
- **Burying the lede**: If the most interesting finding is in Finding 3, move it to Finding 1 and rewrite the Bottom Line.
- **Passive recommendations**: "It might be worth considering..." — rewrite to "We should [X] because [Y]."
- **Missing the audience**: Technical detail that the audience won't parse. Translate to business impact.
