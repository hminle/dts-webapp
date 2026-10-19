import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

/**
 * Testing Library only registers its own cleanup when vitest runs with
 * `globals: true`, which this project deliberately does not. Without this,
 * every rendered tree stays in the document and later queries match elements
 * left behind by earlier tests.
 */
afterEach(cleanup)

/**
 * jsdom implements neither of these, but the sidebar (mobile breakpoint) and
 * Radix popovers (scroll locking) both call them. Real browsers provide them,
 * so stub rather than change the components.
 */
if (!window.matchMedia) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }))
}

// jsdom logs a "not implemented" error for every call; dialogs scroll on open.
window.scrollTo = vi.fn()

// cmdk keeps the highlighted item in view; jsdom has no layout to scroll.
Element.prototype.scrollIntoView = vi.fn()

if (!window.ResizeObserver) {
  window.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
}

// The data grid's scroll area waits for the viewport's transitions to finish
// before it measures. jsdom ships no Web Animations API, and the call happens
// on a timer — so without this the failure surfaces as an unhandled rejection
// after the test that rendered the grid has already passed.
if (!Element.prototype.getAnimations) {
  Element.prototype.getAnimations = () => []
}

/**
 * Radix's Select checks pointer capture before it opens its list. jsdom has no
 * pointer capture at all, so without these the trigger simply never opens and
 * the options cannot be asserted on.
 */
if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false
  Element.prototype.setPointerCapture = () => {}
  Element.prototype.releasePointerCapture = () => {}
}
