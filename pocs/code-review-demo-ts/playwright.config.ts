import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "tests/ui",
  testMatch: "**/*.spec.ts",
  use: {
    baseURL: "http://localhost:4321",
    headless: true,
  },
  webServer: {
    command: "node tests/ui/test-server.mjs",
    url: "http://localhost:4321",
    reuseExistingServer: !process.env.CI,
  },
  reporter: [["line"]],
});
