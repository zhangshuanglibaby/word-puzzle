---
name: ui-designer
description: Craft one-of-a-kind, ship-ready frontend interfaces with elevated design quality. Use when Codex needs to build or restyle websites, landing pages, dashboards, web apps, HTML/CSS/JS pages, React components, posters, or any UI where visual quality matters and generic AI styling should be avoided.
---

# UI Designer

Build production-ready frontend interfaces with a single clear visual point of view. Favor memorable design choices, strong typography, disciplined spacing, and implementation quality over safe default patterns.

## Workflow

Before editing code, decide four things and commit to them:

1. Purpose
   Define what the interface is for and who will use it.
2. Tone
   Pick one strong direction such as minimal, editorial, organic, geometric, playful, luxury, brutalist, or soft pastel.
3. Constraints
   Respect the existing stack, performance needs, accessibility requirements, and the user's codebase patterns.
4. Differentiation
   Choose one memorable device that gives the UI identity. This can be a layout move, typography treatment, motion idea, background system, or compositional motif.

State this direction briefly in your own working notes, then execute it consistently.

## Design Rules

- Reject stock AI aesthetics. Do not default to purple gradients, generic SaaS cards, or overused font stacks.
- Match code complexity to the concept. Minimal work needs restraint and precision; expressive work can justify richer visuals and motion.
- Prefer distinctive type pairings. Use display and body type intentionally when the environment allows it.
- Define a coherent theme with CSS variables instead of ad hoc colors.
- Use motion sparingly but deliberately. Favor one or two meaningful transitions over many tiny effects.
- Push composition beyond boilerplate. Use asymmetry, layered depth, editorial spacing, or intentional silence when it supports the concept.
- Respect the host product when editing an existing system. Preserve patterns unless the user asks for a redesign.

## Implementation Expectations

- Produce working, ship-ready code.
- Make desktop and mobile behavior both intentional.
- Keep accessibility in view: readable contrast, visible focus, semantic structure, and usable hit targets.
- For React work, follow the repo's existing conventions before introducing new abstractions.
- Add comments only when a block would otherwise be hard to parse.

## Imagery

When the design benefits from a real image rather than an abstract gradient or code-only solution, use `scripts/find-relevant-image.py`.

Run:

```bash
python scripts/find-relevant-image.py "<description>"
```

The script:

- reads `assets/images.csv`
- scores each asset against the description tags
- writes the best match into `scripts/outputs/`
- prints the saved file path

Use it for hero backgrounds, poster imagery, splash sections, or other visual surfaces where a concrete image improves the result. Skip it when SVG, CSS, or code-native art is the better fit.

## References

- Read [references/visual-directions.md](references/visual-directions.md) when you need examples of design directions and how to translate them into code.
- Read [references/frontend-checklist.md](references/frontend-checklist.md) before final polish to catch common quality misses.
