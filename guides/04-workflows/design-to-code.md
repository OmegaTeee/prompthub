# Design-to-Code Workflow with Figma

**Transform Figma designs into production-ready code using Figma + Claude Desktop + AgentHub**

> **What you'll learn:** How to extract design specifications from Figma, generate component code, build design systems, and maintain design-code consistency.

---

## Overview

### What This Guide Covers
- Extracting design specs from Figma (colors, spacing, typography)
- Generating React/Vue/Svelte components from designs
- Building design system documentation
- Converting Figma variables to code tokens
- Maintaining design-code sync

### Prerequisites
- ✅ Figma account with read access to designs
- ✅ Claude Desktop installed
- ✅ AgentHub running ([Quick check](../../_shared/health-checks.md))
- ✅ Figma plugin or screenshot workflow
- ✅ Basic understanding of component frameworks (React, Vue, etc.)

### Estimated Time
- Initial setup: 15 minutes
- Workflow mastery: 3-5 design implementations

---

## Concepts

### The Design-Code Gap

**Traditional workflow problems:**
- ❌ Designers hand off static mockups
- ❌ Developers eyeball spacing and colors
- ❌ Design changes don't propagate to code
- ❌ Design system components drift from Figma

**With AgentHub + AI assistance:**
- ✅ Automated design token extraction
- ✅ Component generation matching design specs
- ✅ Design system documentation sync
- ✅ Consistent implementation patterns

---

### How This Workflow Works

```
Figma Design → Screenshot/Export → Claude Desktop + AgentHub → Generated Code
     ↓                                                              ↓
Design Tokens ────────────────────────────────────────→ Code Tokens
     ↓                                                              ↓
Design System ←──────────────── Documentation ←──────────────────┘
```

**Key insight:** AI can "see" designs and extract specifications with high accuracy.

---

## Step-by-Step: Initial Setup

### 1. Prepare Figma Access

**Option A: Figma Plugin (Recommended)**
1. Install "Figma to Code" plugin in Figma
2. Export components with structured data
3. Copy JSON specifications

**Option B: Screenshot Workflow**
1. Take high-quality screenshots (Command+Shift+4 on macOS)
2. Include full component with spacing indicators
3. Export at 2x resolution for clarity

---

### 2. Configure Claude Desktop

Ensure enhancement is enabled:

```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Should contain:

```json
{
  "mcpServers": {
    "agenthub": {
      "url": "http://localhost:9090",
      "headers": {
        "X-Enhance": "true",
        "X-Client-Name": "claude-desktop"
      }
    }
  }
}
```

---

### 3. Create Project Context

**Create `.design-context.md` in your project:**

```markdown
# Design System Context

## Framework
React 18 + TypeScript

## Styling
- Tailwind CSS 3.x
- CSS-in-JS: styled-components (for complex components)

## Design Tokens Location
`src/tokens/` - Colors, spacing, typography

## Component Structure
- Atomic design principles (Atoms → Molecules → Organisms)
- Props follow Figma component variants
- Stories for each variant

## Naming Convention
- PascalCase for components: `ButtonPrimary`
- camelCase for props: `onClick`, `isDisabled`
- kebab-case for CSS classes: `btn-primary`
```

---

## Understanding the Workflow

### The Design-to-Code Process

```
1. Analyze Design → 2. Extract Tokens → 3. Generate Component → 4. Refine → 5. Document
       ↑                                                                       ↓
       └─────────────────────── Iterate for Variants ←───────────────────────┘
```

---

## Common Use Cases

### Use Case 1: Extract Design Tokens

**Scenario:** Convert Figma color palette and spacing to code.

**Workflow:**

**Step 1:** Provide Figma screenshot or specs

```
Prompt: "Analyze this Figma color palette screenshot and extract design tokens.

[Attach screenshot showing: Primary Blue #2563EB, Secondary Gray #6B7280, etc.]

Generate:
1. TypeScript token definitions
2. Tailwind config extension
3. CSS variables"
```

**Step 2:** Review generated tokens

```typescript
// tokens/colors.ts
export const colors = {
  primary: {
    DEFAULT: '#2563EB',
    light: '#3B82F6',
    dark: '#1E40AF',
  },
  secondary: {
    DEFAULT: '#6B7280',
    light: '#9CA3AF',
    dark: '#4B5563',
  },
} as const;
```

**Step 3:** Generate Tailwind config

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#2563EB',
          light: '#3B82F6',
          dark: '#1E40AF',
        },
        // ...
      }
    }
  }
}
```

**Step 4:** Create CSS variables (optional)

```css
:root {
  --color-primary: #2563EB;
  --color-primary-light: #3B82F6;
  --color-primary-dark: #1E40AF;
}
```

---

### Use Case 2: Component Generation

**Scenario:** Create a Button component matching Figma design.

**Workflow:**

**Step 1:** Provide design specifications

```
Prompt: "Create a React Button component from this Figma design:

[Attach screenshot showing button variants]

Specifications:
- 3 sizes: small (32px h), medium (40px h), large (48px h)
- 3 variants: primary, secondary, outline
- States: default, hover, active, disabled
- Include icon support (left/right)
- Tailwind CSS for styling
- TypeScript types"
```

**Step 2:** Review base component

```typescript
// components/Button.tsx
import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-white hover:bg-primary-dark',
        secondary: 'bg-secondary text-white hover:bg-secondary-dark',
        outline: 'border-2 border-primary text-primary hover:bg-primary hover:text-white',
      },
      size: {
        small: 'h-8 px-3 text-sm',
        medium: 'h-10 px-4 text-base',
        large: 'h-12 px-6 text-lg',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'medium',
    },
  }
);

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant,
  size,
  iconLeft,
  iconRight,
  className,
  ...props
}) => {
  return (
    <button className={buttonVariants({ variant, size, className })} {...props}>
      {iconLeft && <span className="mr-2">{iconLeft}</span>}
      {children}
      {iconRight && <span className="ml-2">{iconRight}</span>}
    </button>
  );
};
```

**Step 3:** Request Storybook stories

```
Prompt: "Generate Storybook stories for this Button component showing all variants and states"
```

---

### Use Case 3: Complex Layout Implementation

**Scenario:** Implement a card layout from Figma with precise spacing.

**Workflow:**

**Step 1:** Analyze layout

```
Prompt: "Analyze this Figma card design and identify:
- Container dimensions
- Internal spacing/padding
- Grid/flexbox layout structure
- Responsive behavior (mobile, tablet, desktop)

[Attach Figma screenshot with spacing indicators visible]"
```

**Step 2:** Generate responsive component

```
Prompt: "Create a ProductCard component implementing this design. Use Tailwind responsive utilities:
- Mobile: single column, full width
- Tablet: 2 columns
- Desktop: 3 columns

Match exact spacing from Figma (16px padding, 12px gaps)"
```

**Step 3:** Refine details

```
Prompt: "The card shadow doesn't match Figma. Figma shows: X: 0, Y: 4, Blur: 12, Spread: 0, Color: #00000014. Generate correct Tailwind shadow utility or custom CSS."
```

---

### Use Case 4: Design System Documentation

**Scenario:** Generate Storybook documentation from Figma components.

**Workflow:**

**Step 1:** Extract component inventory

```
Prompt: "I have 15 Figma components in my design system:
- Buttons (3 variants)
- Input fields (5 types)
- Cards (4 layouts)
- Modals (2 sizes)
- Navigation (header, sidebar)

Generate a Storybook structure with:
- Organized categories
- Story templates for each component
- Documentation MDX files"
```

**Step 2:** Create component documentation

```
Prompt: "Generate MDX documentation for Button component including:
- When to use each variant
- Accessibility guidelines
- Do's and Don'ts
- Code examples
- Props API table"
```

**Step 3:** Add usage guidelines

```
Prompt: "Create design system usage guidelines for spacing:
- Figma uses 4px base unit
- Common spacings: 4, 8, 12, 16, 24, 32, 48, 64
- How to apply in code (Tailwind classes)"
```

---

### Use Case 5: Figma-to-Code Sync

**Scenario:** Figma design was updated, sync code components.

**Workflow:**

**Step 1:** Identify changes

```
Prompt: "Compare:
- Old design: Button height 40px, border-radius 8px
- New design: Button height 44px, border-radius 12px

What code needs to be updated?"
```

**Step 2:** Generate migration script

```
Prompt: "Create a find-and-replace guide to update all Button components:
- Change h-10 to h-11
- Change rounded-lg to rounded-xl
Include files to check: components/, pages/, stories/"
```

**Step 3:** Update design tokens

```
Prompt: "Update design tokens file with new button specifications"
```

---

### Use Case 6: Animation from Figma Prototypes

**Scenario:** Implement animations matching Figma prototype.

**Workflow:**

**Step 1:** Describe animation

```
Prompt: "Figma prototype shows modal with:
- Fade in: 200ms ease-out
- Slide up: 20px to 0px
- Background blur: 0 to 8px

Generate Framer Motion code for React"
```

**Step 2:** Review animation code

```typescript
import { motion } from 'framer-motion';

const modalVariants = {
  hidden: {
    opacity: 0,
    y: 20,
    backdropFilter: 'blur(0px)'
  },
  visible: {
    opacity: 1,
    y: 0,
    backdropFilter: 'blur(8px)',
    transition: {
      duration: 0.2,
      ease: 'easeOut'
    }
  }
};

<motion.div
  variants={modalVariants}
  initial="hidden"
  animate="visible"
>
  {/* Modal content */}
</motion.div>
```

---

## Advanced Techniques

### Technique 1: Automated Token Sync

**Create a token extraction workflow:**

```
Prompt: "Create a Node.js script that:
1. Reads Figma API (using API token)
2. Extracts color, typography, spacing tokens
3. Generates TypeScript token files
4. Updates Tailwind config
5. Commits changes to git"
```

---

### Technique 2: Component Variant Generation

**Generate all variants at once:**

```
Prompt: "For this Button base component, generate all combinations:
- Variants: primary, secondary, outline, ghost
- Sizes: xs, sm, md, lg, xl
- States: default, hover, active, disabled, loading

Show TypeScript types and Tailwind classes for each"
```

---

### Technique 3: Responsive Design Patterns

**Extract responsive behavior:**

```
Prompt: "Analyze this Figma auto-layout and convert to responsive CSS:
- Mobile: Stack vertically, 16px gap
- Tablet: 2 columns, 24px gap
- Desktop: 3 columns, 32px gap
Use Tailwind responsive utilities"
```

---

## Best Practices

### 1. Include Figma Specifications

**Good:**

```
✅ "Button with: height 44px, padding 16px horizontal, border-radius 12px, font-size 16px, font-weight 600"
```

**Bad:**

```
❌ "Create a button"
```

---

### 2. Match Design Tokens Exactly

**Always:**
- Use exact pixel values from Figma
- Match color hex codes precisely
- Preserve spacing ratios
- Maintain typography scale

**Don't:**
- "Round" values ("let's use 50px instead of 44px")
- Approximate colors ("close enough")
- Ignore Figma's spacing system

---

### 3. Request Accessibility Considerations

```
Prompt: "Generate Button component with:
- ARIA labels
- Keyboard navigation support
- Focus states matching Figma focus ring
- Screen reader announcements
- Color contrast ratio >= 4.5:1"
```

---

### 4. Create Design System First

**Before generating individual components:**
1. Extract all design tokens
2. Set up Tailwind/token system
3. Create base component utilities
4. Then build specific components

**This ensures consistency across all components.**

---

### 5. Document Design Decisions

```
Prompt: "Generate comments explaining why we use these values:
- Why 44px button height (touch target size)
- Why 12px border radius (brand guideline)
- Why primary color #2563EB (accessibility + brand)"
```

---

## Troubleshooting

### Issue: Generated code doesn't match design

**Solution:** Provide exact specifications

```
Prompt: "The spacing is wrong. Figma shows:
- Top padding: 16px
- Bottom padding: 20px
- Left/Right padding: 24px
Update the component to match exactly."
```

---

### Issue: Colors look different

**Solution:** Check color profiles

```
Prompt: "Figma uses sRGB color space. Ensure generated CSS uses exact hex values:
- Primary: #2563EB (not #2564EB)
- Verify in browser DevTools"
```

---

### Issue: Typography doesn't match

**Solution:** Extract font details

```
Prompt: "Figma typography settings:
- Font family: Inter
- Font weight: 600
- Font size: 16px
- Line height: 24px (150%)
- Letter spacing: -0.02em

Generate exact CSS/Tailwind classes"
```

---

### Issue: Responsive behavior differs

**Solution:** Clarify breakpoints

```
Prompt: "Figma shows different layouts at:
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

Ensure Tailwind breakpoints match Figma's design"
```

---

## Key Takeaways

- ✅ **Extract tokens first** - Colors, spacing, typography before components
- ✅ **Match specifications exactly** - Don't approximate Figma values
- ✅ **Use design system approach** - Token-based architecture for consistency
- ✅ **Include accessibility** - ARIA labels, keyboard nav, focus states
- ✅ **Generate variants together** - All sizes/states/variants at once for consistency
- ✅ **Document design decisions** - Explain why values are chosen
- ✅ **Maintain sync** - Update code when Figma designs change

**Next steps:**
- Explore [Code Development](code-development.md) for component refinement
- See [Content Creation](content-creation.md) for design system documentation
- Configure [Enhancement Rules](../../02-core-setup/enhancement-rules.md) for custom behavior

---

**Last Updated:** 2026-02-05
**Workflow Difficulty:** Intermediate
**Time to Master:** 3-5 design implementations
**Prerequisites:** Figma access + Claude Desktop + AgentHub + Design system knowledge
