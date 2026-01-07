---
trigger: model_decision
description: when working on website/frontend
---

# Frontend Style & Architecture Rules

## Stack
- **Framework**: Next.js (App Router).
- **Styling**: Vanilla CSS or Tailwind CSS (per user request).
- **Icons**: Lucide React.
- **Data Fetching**: Prefer Server Components for direct file access to root artifacts.

## Data Access
- **Direct File Access**: Leverage Node's `fs` module in Server Components/Actions to read CSV/JSON data directly from `../artifacts` or `../data`. This avoids data duplication.
- **Parsing**: Use structured parsers like `papaparse` or `csv-parse` on the server side.

## Component Design
- **Rich Aesthetics**: Prioritize modern, premium UI (vibrant colors, glassmorphism, smooth transitions).
- **Animations**: Use subtle micro-animations for interactivity.
- **SEO**: Implement meta tags and semantic HTML on all pages.
