import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => {
  cleanup();
});

// reactflow renders SVG measurement-driven layouts that require a real DOM
// box model. jsdom doesn't compute layout, so we stub the bare minimum
// reactflow needs for non-visual tests. Visual layout (positions, edges)
// is covered by the pure `buildServiceFlowElements` function which has no
// DOM dependency.
class ResizeObserverMock {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(globalThis as any).ResizeObserver = ResizeObserverMock;

// jsdom does not implement `URL.createObjectURL`; reactflow uses it for some
// internal measurement paths. Stub it to a no-op string.
if (!globalThis.URL.createObjectURL) {
  globalThis.URL.createObjectURL = (): string => "blob:mock";
}

// `DOMMatrix` is used by reactflow's d3 transforms; jsdom doesn't ship it.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
if (!(globalThis as any).DOMMatrix) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (globalThis as any).DOMMatrix = class {
    a = 1;
    b = 0;
    c = 0;
    d = 1;
    e = 0;
    f = 0;
    constructor() {}
  };
}
