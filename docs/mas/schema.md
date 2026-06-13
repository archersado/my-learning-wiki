# MAS Wiki Schema

> How this wiki is structured and maintained. Updated as conventions evolve.

## Directory Layout

```
docs/mas/
├── schema.md          # This file — conventions and structure
├── index.md           # Content-oriented catalog of all pages
├── log.md             # Chronological append-only activity log
├── overview.md        # Single entry-point overview
├── concepts/          # Concept pages (individual ideas, definitions)
├── patterns/          # Architecture patterns (reusable designs)
├── protocols/         # Communication protocol pages
├── failures/          # Failure modes and mitigations
├── production/        # Production engineering practices
├── benchmarks/        # Evaluation benchmarks
├── case-studies/      # Real-world case studies
└── economy/           # Agent economics and incentives
```

## Page Format

Every wiki page follows this structure:

```markdown
# Page Title

> One-sentence summary, sourced from which lesson(s).

## Overview
2-3 paragraph synthesis. Written to stand alone — no need to read source.

## Key Concepts
Definitions, diagrams, mechanisms. Bullet-heavy, not narrative.

## Design Rules
Actionable "when to use / when to avoid" guidance.

## Production Notes
What ships vs what stays academic.

## Related
- [[link to related wiki page]]
- [[link to another related page]]
```

## Conventions

- **Cross-references** use `[[Page Title]]` (Obsidian-style wikilinks)
- **Source attribution** in the `>` blockquote header
- **Code examples** are abbreviated — enough to understand, not to copy-paste
- **Diagrams** use ASCII art (renderable, no external tools needed)
- **Tables** are preferred over prose for comparisons
- **Opinion stated** when there is genuine disagreement in the literature

## Wiki Operations

### Ingest
When a new source arrives:
1. Read the source material
2. Identify new concepts, patterns, or updates to existing pages
3. Create or update pages
4. Update `index.md` with new/changed entries
5. Append to `log.md`

### Lint (periodic)
- Check for broken wikilinks
- Find orphan pages (no inbound links)
- Flag contradictions between pages
- Identify concepts mentioned but lacking their own page
