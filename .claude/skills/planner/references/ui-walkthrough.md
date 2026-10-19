# UI Walkthrough — the app after this ships

The walkthrough is Part 2 of `explainer.html`: a clickable, step-by-step mockup of the
finished feature, drawn to look like the real app. A reader clicks **Next** and watches
the screens change the way they will once the plan is implemented — which button to
press, which dialog opens, what the numbers become.

Why it exists: Part 1 explains the idea with abstract boxes, and Part 3 explains the code.
Neither shows the person who will *use* the feature what their screen will look like.
A mockup that looks like the app they already know answers that in seconds, and it lets
the user catch a wrong flow (a missing step, a confusing label) before any code is written.

## Contents

1. When to include it
2. Get the look from the real app
3. Pick the steps
4. Build the mockup
5. Keep it current
6. Checklist

## 1. When to include it

Include it when the plan changes anything a user sees or clicks: a new page, dialog,
card, table column, button, or a changed number on an existing screen.

Leave it out when the plan is backend-only, tooling, or a refactor with no visible change.
The page then has two parts (plain explanation, developer briefing) — do not add an empty
walkthrough or a "no UI changes" placeholder.

## 2. Get the look from the real app

The mockup must read as *this* app, not as a generic dashboard. Read the sources; never
guess the theme from memory.

| What | Where to read it |
|---|---|
| Color tokens (light and dark) | `frontend/src/styles/globals.css` — the `:root` and `.dark` blocks. Copy the `oklch(...)` values verbatim. |
| Radius, font | `globals.css` — `--radius` (0.625rem) and `--font-sans` (Inter). Load Inter from Google Fonts. |
| Component look | `frontend/src/styles/style-nova.css` — `.cn-card*`, `.cn-button`, `.cn-badge`, `.cn-dialog-content`, and so on. Mirror their padding, border, radius, and text sizes. |
| App shell | `frontend/src/components/layout/app-sidebar.tsx` (inset sidebar: profile switcher on top, a "Menu" group with Overview then the profile's accounts, footer "Local · single user · no login"), `header.tsx`, `main.tsx`. |
| Nav labels | `frontend/src/components/layout/data/sidebar-data.ts` and `nav-accounts.ts`. |
| The screens this plan touches | The actual route in `frontend/src/routes/` and the components it renders in `frontend/src/components/` (existing dialogs such as `loan-payment-dialog.tsx`, cards such as `net-worth-card.tsx`). Copy their real labels, field order, and button text. |
| Icons | lucide (`iconLibrary` in `components.json`). Inline the SVG paths of the icons the real components import. |

Scope the app's tokens to the mockup container, not the whole page:

```css
.mock-app {            /* app tokens copied from globals.css :root */
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --card: oklch(1 0 0);
  /* ...the rest of :root... */
  font-family: "Inter", sans-serif;
  background: var(--background);
  color: var(--foreground);
}
/* the app's .dark block, under the explainer's own dark-mode selectors */
```

The explainer page keeps its own palette around the frame. Inside the frame, only the
app's tokens apply. The mockup follows the page's light/dark theme using the app's own
`.dark` values, so a reader in dark mode sees the app as it looks in dark mode.

## 3. Pick the steps

Write the steps as the user's journey through the finished feature, from where they
start (usually Overview or an account page) to the result they came for.

- **One action per step.** "Click *Record payment*", "Enter 450.00 and pick 2026-10-01",
  "Click *Save*", "See the new balance". A step that needs two sentences is two steps.
- **Four to eight steps.** Fewer means the feature is simple enough that Part 1 covers it;
  more means you are showing several journeys — pick the main one, or split into two
  tabbed journeys (for example, "Set up the loan" and "Record a payment").
- **Show the result, not only the input.** The last step shows the screen after the
  action: the new row in the table, the updated card, the changed total.
- **Real data from the plan.** Use the plan's worked example — its names, amounts,
  currencies, dates — so numbers on screen add up across steps. A balance that drops by
  the payment's principal portion must drop by exactly that amount. Never "Lorem ipsum",
  "$X,XXX", or "Account 1".
- **Show what can go wrong** when the plan defines it: an "unpriced" marker, a validation
  message, a disabled button with its reason. One error step is enough; pick the one a
  user is most likely to hit.
- **Tag each step with the phase that delivers it** ("Ships in Phase 5"). The reader sees
  which parts of the journey arrive when, and the tag becomes "Live" once that phase is ✅.

## 4. Build the mockup

**Frame.** Draw a simple browser-window frame (three dots, an address bar reading
`localhost:5173/...` with the real route path) around the app. Put a small
"Mockup — not the live app" label on the frame. The frame tells the reader this is a
picture, so nobody tries to click through to real data.

**Layout.** Two columns on wide screens: the step list on the left (numbered, current
step highlighted, each with its one-line action and phase tag), the framed app on the
right. On a phone the step list collapses to "Step 3 of 6" above the frame. The frame
scales down; it never causes horizontal page scroll — shrink the mock sidebar to icons
under ~720px, as the real `collapsible='icon'` sidebar does.

**Stepper.** Back / Next buttons, keyboard left/right arrows, and clicking a step in the
list. Each step is a state of *one* mockup, not a separate screenshot: show and hide
elements (a dialog, a new table row, a changed value) with a `data-step` attribute and a
few lines of inline JavaScript. Without JavaScript, render every step stacked in order,
so the content is still readable.

**Highlight.** On each step, draw attention to the one element the user acts on or
looks at: a ring in the app's `--ring` color plus a small numbered callout with the
step's instruction. Dim nothing else — the reader should still see the whole screen.

**Fidelity.** Match the real app where it is visible: sidebar, card borders, button
shapes, badge colors, table density, dialog width. Skip what does not help the story:
no working inputs, no hover menus, no charts beyond a flat shape when a chart is not
the point. A mockup that is 90% accurate and clear beats one that is pixel-perfect and
cluttered.

**New UI.** For screens the plan adds, build them from the same tokens and component
classes the real code will use (the phase doc says which shadcn/ReUI components). The
mockup then previews the UI the executor will actually build.

## 5. Keep it current

- When a phase that changes UI lands, open the shipped screens (run `scripts/dev.sh` and
  `uv run python -m scripts.seed_demo --reset` if needed) and reconcile the mockup with
  them: labels, order of fields, layout. Flip that phase's step tags to "Live".
  Republish the explainer from the same path.
- When a plan revision changes the flow (⚠️ Revised / 🔁 Rework on a UI phase), update the
  affected steps in the same change.
- The mockup shows only the current truth, like every other plan file.

## 6. Checklist

- [ ] Tokens copied from `globals.css` (both `:root` and `.dark`), scoped to `.mock-app`
- [ ] Sidebar, header, and existing screens match the real components' labels
- [ ] 4–8 steps, one action each, ending on the result screen
- [ ] Every number comes from the plan's worked example and adds up across steps
- [ ] Each step tagged with the phase that ships it
- [ ] Back / Next / arrow keys / step list all work; no-JS fallback shows all steps
- [ ] "Mockup — not the live app" label on the frame
- [ ] No horizontal scroll at phone width; works in light and dark
