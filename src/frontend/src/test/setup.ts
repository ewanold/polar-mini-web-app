import "@testing-library/jest-dom/vitest";

class MatchMediaMock implements MediaQueryList {
  matches = false;
  media = "";
  onchange = null;
  addListener = () => undefined;
  removeListener = () => undefined;
  addEventListener = () => undefined;
  removeEventListener = () => undefined;
  dispatchEvent = () => true;
}

Object.defineProperty(window, "matchMedia", {
  configurable: true,
  value: () => new MatchMediaMock(),
});

beforeEach(() => {
  window.localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
  window.history.replaceState({}, "", "/");
});
