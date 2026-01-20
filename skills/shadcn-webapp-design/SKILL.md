---
name: shadcn-webapp-design
description: Build production-grade Next.js web applications with shadcn/ui, Tailwind CSS, and Framer Motion. Use when building React components, pages, dashboards, landing pages, or any web UI that should use the shadcn/ui component library. Triggers on requests involving shadcn components, Tailwind styling, Framer Motion animations, or when the user wants polished, non-generic UI that avoids "vibecoded" aesthetics.
---

# shadcn/ui Webapp Design

Build distinctive, production-grade web interfaces using the modern React stack: **Next.js 14 + Tailwind CSS + shadcn/ui + Framer Motion**.

## Core Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Framework | Next.js 14 (App Router) | Server components, routing, optimization |
| Styling | Tailwind CSS | Utility-first styling with design tokens |
| Components | shadcn/ui | Accessible, customizable component primitives |
| Animation | Framer Motion | Declarative animations and gestures |

## Design System First

Before writing code, establish design tokens. Use the project's `tailwind.config.ts` and `globals.css` for consistency.

### Required: Check Existing Tokens

```bash
# Always read these files first
cat tailwind.config.ts
cat app/globals.css
cat components.json  # shadcn config
```

### Token Categories

```css
/* globals.css - CSS variables */
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 222.2 47.4% 11.2%;
  --primary-foreground: 210 40% 98%;
  --accent: 210 40% 96.1%;
  --muted: 210 40% 96.1%;
  --radius: 0.5rem;
}
```

## Component Usage

### Import Pattern

Always import from the project's component directory:

```tsx
// Correct - use project components
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"

// Never reinvent these - use shadcn
```

### Available Components

Check what's installed: `ls components/ui/`

Common components: `button`, `card`, `dialog`, `dropdown-menu`, `input`, `label`, `select`, `sheet`, `tabs`, `toast`, `tooltip`

If a component doesn't exist, install it:
```bash
npx shadcn@latest add [component-name]
```

## Animation Patterns

Use Framer Motion for all animations. See [references/framer-motion-patterns.md](references/framer-motion-patterns.md) for complete examples.

### Quick Reference

```tsx
import { motion } from "framer-motion"

// Fade in
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  transition={{ duration: 0.3 }}
/>

// Stagger children
<motion.div
  initial="hidden"
  animate="visible"
  variants={{
    hidden: {},
    visible: { transition: { staggerChildren: 0.1 } }
  }}
>
  {items.map(item => (
    <motion.div
      key={item.id}
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0 }
      }}
    />
  ))}
</motion.div>

// Hover interaction
<motion.button
  whileHover={{ scale: 1.02 }}
  whileTap={{ scale: 0.98 }}
/>
```

## Anti-Patterns to Avoid

### The "AI Purple Curse"

Never default to:
- Purple/violet gradients on white backgrounds
- Inter, Roboto, or system fonts exclusively
- Generic rounded cards with subtle shadows
- Predictable 3-column grids
- Stock gradient buttons

### Instead

- Use the project's existing color tokens
- Match the brand/aesthetic already established
- Create visual hierarchy through spacing, not just color
- Use unexpected layouts when appropriate

## Workflow

1. **Read existing code** - Understand the project's patterns
2. **Check design tokens** - Use established colors/spacing
3. **Use shadcn components** - Never recreate Button, Card, etc.
4. **Add Framer Motion** - For meaningful interactions
5. **Test responsiveness** - Mobile-first with Tailwind breakpoints

## Reference Files

- **[references/shadcn-components.md](references/shadcn-components.md)** - Component patterns and composition
- **[references/framer-motion-patterns.md](references/framer-motion-patterns.md)** - Animation recipes
- **[references/design-tokens.md](references/design-tokens.md)** - Token system and theming
