---
id: T011
title: Survey ciembor/agent-rules-books
labels: [wayfinder:research]
status: closed
assignee: research-rules-books
blocked-by: []
---

## Question

A different artifact class: rule sets distilled per classic software book (Clean Code, Refactoring, DDD, Designing Data-Intensive Applications, A Philosophy of Software Design, The Pragmatic Programmer, Working Effectively with Legacy Code, Release It, Code Complete...) plus a _rule-workbench/ directory. How are the rules structured and consumed (AGENTS.md rules vs skills?), how does the workbench generate/maintain them, what does loading a rule book cost an agent's context, and which specific books' rules would genuinely improve a greenfield/brownfield flow? Decide-worthy question for us: is the rules-book pattern worth adopting ALONGSIDE skills, and if so, how do the two interact (a skill that says 'consult the clean-code rule book'?

## Resolution

Surveyed ciembor/agent-rules-books (3,139 stars, MIT, v0.6): 14 book-derived rule sets in full/mini/nano sizes, packaged as one Agent Skill per book where SKILL.md is a ~700 B dispatcher that says "read and apply <book>.mini.md" (~950–1.4k tok) with full as deeper reference; nano (~310–560 tok) exists only for always-on budgets. The real asset is _rule-workbench/: an auditable agent-run compression process (decision-equivalent, not sentence-equivalent; rule classification; M*/N* traceability; evidence-required `default` labels; process-bugs fed back into PROCESS.md) plus a 91-pair compatibility matrix (78 ✅ / 11 🔁 / 2 ❌) and a self-scored CRITICISM.md. Verdict: adopt the pattern, not the corpus — skills stay procedures, rule files are swappable decision-pressure payloads linked from skill bodies ("a skill that points at a rule book" is literally their design); vendor WELC-mini (brownfield: characterize-first, smallest seam, no rewrite-as-first-move) and APoSD-mini (greenfield: "prove that it hides more complexity than it adds") as reference files; take the 5-part rule template, the nano model-bias list, byte-level size metrics, and the one-primary-rest-on-demand co-loading policy; skip the 14-book corpus, the pair-doc matrix, and the legal-risky ChatGPT-extracted content (author's own "won't fix" on legal).

Findings: `.scratch/skillset-v1/research/agent-rules-books.md`
