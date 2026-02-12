# Crafting interface and graphics design prompts for draw things and comfyui

You can treat UI/UX prompts as “design briefs to a junior designer”: clear subject, structure, constraints, and style, not just adjectives.[^1][^2]

## Core structure for UI prompts

For both Draw Things and ComfyUI, a solid baseline structure:

> subject + layout/structure + platform + style + color/typography + constraints

Example (app dashboard):

> “clean SaaS analytics dashboard UI, 2‑column layout with left sidebar nav and main content area, desktop web app, light mode, lots of white space, subtle grid, primary accent in electric blue, modern flat design, minimal icons, no 3D, no glassmorphism, highly legible typography, focus on charts and tables”

Key pieces to always include:

- Subject: “mobile banking app login screen”, “landing page hero section”, “design system components grid”.[^1]
- Layout: “3‑card pricing section in a single row”, “centered modal over dimmed background”, “top nav + hero + 3‑feature columns”.[^1]
- Platform: web app, marketing website, iOS app, watch app, etc.[^1]
- Style: “material‑inspired”, “flat UI”, “brutalist web design”, “neumorphism”, “Swiss graphic design”.[^1]
- Constraints: “no people”, “no device frame”, “no logo text”, “no mockup perspective, straight‑on view”.[^1]

## Draw Things specifics

Draw Things mostly follows Stable Diffusion conventions, so you can lean on normal SD prompt syntax plus BREAK for structure.[^3][^1]

Prompt pattern for interfaces:

- Positive prompt:
  - “minimalist mobile banking app home screen UI, iOS app, 3 card layout, bottom navigation bar with 4 icons, white background, accent color teal, simple flat icons, high contrast text, clean spacing, Figma style, product design, uiux, dribbble, behance”
- Negative prompt:
  - “3d render, illustration, character, hands, photorealistic, noisy, cluttered, text logo, lorem ipsum, distorted text, perspectives, skewed angle”

Tips in Draw Things:

- Use multi‑line/BREAK to separate conceptual chunks: subject vs layout vs style.[^3]
- Save good “style templates” as base prompts and only swap the subject/layout fragments (DT’s style templates system is made for this).[^4]
- For multiple screens on one canvas, describe segments explicitly: “three smartphone screens side by side, each showing a different app screen UI, centered, equal spacing, white background”.[^1]

## ComfyUI: how to wire and phrase prompts

In ComfyUI, the key is the CLIP text‑encode nodes; the text field itself is the same SD prompt language, but you can modularize.[^5][^2]

Basic pattern:

- One `CLIPTextEncode` (or ADV_CLIP) for positive: your full design prompt.[^6][^2]
- One `CLIPTextEncode` for negative: all the “do not want” traits.[^2]

Suggested positive text for `ClipTextEncode`:

> “web app dashboard UI, straight‑on view, 12‑column layout, left sidebar navigation, top header bar, main content with charts and tables, light mode, white background, subtle grey dividers, accent color \#3B82F6 blue, flat design, Figma mockup, modern product design, crisp vector look, no 3d”

Negative text:

> “people, faces, illustration, 3d render, grain, blur, low contrast, neon colors, glassmorphism, perspective tilt, skewed, logo text, long paragraphs, distorted text”

Useful ComfyUI‑specific techniques:

- Use ADV_CLIP or similar nodes when you want A1111‑style weighting and parentheses control; e.g. `(flat ui:1.3), (clean layout:1.2)` to push design language.[^6][^2]
- Exploit multi‑line prompts in ClipTextEncode to mimic BREAK: put subject on first line, layout on second, style on third, negative in its own node.[^2]
- For FLUX nodes (like `CLIPTextEncodeFlux`), you can feed “tag‑ish” text into clip_l and more natural description into t5xxl; keep the design brief in normal language in t5xxl.[^7]

## Prompt snippets for common UI tasks

You can paste these into Draw Things or ComfyUI ClipTextEncode and iterate.

1. Mobile app screen (iOS/Android):
   Positive:
   > “minimal mobile fitness app home screen UI, iOS app, top greeting, centered daily stats card, 3 rounded rectangular buttons, bottom tab bar, white background, pastel accent colors, flat icons, high contrast text, Figma shot, dribbble uiux”
   > Negative:
   > “photo, illustration, character, 3d, perspective, device frame, text logo, noisy background, gradients everywhere, neon, glassmorphism”
2. Marketing landing hero:
   Positive:
   > “saas marketing website hero section, full width, top navigation bar, large headline text on left, call to action buttons, product screenshot frame on right, light mode, lots of white space, soft blue accent, flat web design, swiss graphic design, clean typography”
   > Negative:
   > “3d mascot, people, stock photo, dark mode, heavy gradients, clutter, excessive icons, noisy texture”
3. Design system / components sheet:
   Positive:
   > “ui design system components on white canvas, buttons, inputs, dropdowns, toggles, checkbox, tabs, cards, light mode, simple flat style, neutral grey and blue palette, labeled sections, top‑down view, Figma components page, neat spacing”
   > Negative:
   > “3d, perspective, skewed, dark background, illustration, device frame, content screenshots, text blocks”

## Graphics / icon and illustration accents

To get supporting graphics for UI (icons, spot illustrations, backgrounds), keep prompts constrained and flat:[^1]

- Icons:
  - “set of 16 flat line icons, monochrome dark grey, consistent stroke width, simple shapes, for mobile app navigation, on white background”
- Dashboard decorations:
  - “abstract geometric background for web dashboard, subtle overlapping rounded rectangles, light greys and one accent blue, flat minimal design, no text, no icons”

For both tools, think in systems: keep a small library of reusable style fragments (“flat material‑like ui, subtle shadows, light mode, high contrast, Figma style”) and concatenate with specific layout/subject per shot.[^2][^1]

If you tell me which base models you’re using in Draw Things and which ComfyUI workflows/nodes (SDXL vs FLUX vs SD1.5, etc.), I can rewrite these into model‑tuned prompt presets and a couple of ready‑to‑drop Comfy graphs that mirror your actual stack.
<span style="display:none">[^10][^11][^12][^13][^14][^15][^8][^9]</span>

<div align="center">⁂</div>

[^1]: <https://stable-diffusion-art.com/prompt-guide/>

[^2]: <https://docs.comfy.org/built-in-nodes/ClipTextEncode>

[^3]: <https://www.reddit.com/r/drawthingsapp/comments/1i4s9ed/best_practice_prompting_multiple_persons/>

[^4]: <https://www.youtube.com/watch?v=uJoGQA5oXRU>

[^5]: <https://comfyui-wiki.com/en/comfyui-nodes/conditioning/clip-text-encode>

[^6]: <https://www.runcomfy.com/comfyui-nodes/ComfyUI_ADV_CLIP_emb>

[^7]: <https://comfyui-wiki.com/en/comfyui-nodes/advanced/conditioning/flux/clip-text-encode-flux>

[^8]: <https://www.reddit.com/r/StableDiffusion/comments/z5tnjj/is_there_a_properly_comprehensive_guide_on_prompt/>

[^9]: <https://drawthings.ai/downloads/>

[^10]: <https://www.facebook.com/groups/wombodreamai/posts/5625677674225922/>

[^11]: <https://www.reddit.com/r/drawthingsapp/>

[^12]: <https://www.reddit.com/r/StableDiffusion/comments/10gmvqe/lets_use_stable_diffusion_for_ux_ui_and_web_design/>

[^13]: <https://docs.midjourney.com/hc/en-us/articles/32023408776205-Prompt-Basics>

[^14]: <https://stablediffusionweb.com/prompts/ui-design>

[^15]: <https://drawthings.ai>
