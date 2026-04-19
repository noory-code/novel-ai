import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.ts"],
  },
  resolve: {
    alias: {
      // The `vscode` module is provided by the host at runtime, not as an
      // npm package. Tests stub it via this alias so importing `vscode` in
      // the source under test resolves to our fake.
      vscode: new URL("./tests/__mocks__/vscode.ts", import.meta.url).pathname,
    },
  },
});
