---
name: LifeOS UI Review
description: Review Life OS frontend work for usability, accessibility, responsive behavior, visual consistency, and offline-friendly implementation.
---

# Life OS UI Review

Use after creating or modifying a page, component, widget, form, or navigation flow.

## Product direction

Life OS should feel like a calm, capable personal command center: clear hierarchy, restrained color, purposeful information density, consistent spacing, and strong readability. Avoid generic template layouts, oversized decorative hero areas, gratuitous gradients, excessive animation, and decorative charts without meaning.

Use the Anthropic `frontend-design` skill for visual design tasks when installed. This local review skill is the quality check; it does not replace that design process.

## Review checklist

- The primary action and page hierarchy are obvious.
- Components use consistent design tokens for color, spacing, radius, typography, and state.
- Semantic HTML is used; buttons/links have correct roles and labels.
- All essential actions are keyboard accessible and focus indicators are visible.
- Contrast is readable and status is not communicated only with color.
- Forms show labels, validation, and actionable error messages.
- Loading, empty, success, and failure states are intentionally designed.
- Layout remains usable on desktop, tablet, and narrow mobile screens.
- Reduced-motion preferences are respected; motion is purposeful and subtle.
- The UI does not depend on remote fonts, image CDNs, or third-party runtime services.
- User-provided note content is rendered as text, never injected as executable HTML.
- Widgets present real data from existing services and do not duplicate business logic.

## Output

List concrete findings with file/line locations where possible, severity, user impact, and the smallest safe correction. Do not invent a WCAG conformance claim without testing against the relevant criteria.
