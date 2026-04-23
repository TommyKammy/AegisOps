export default {
  testDir: "./apps/operator-ui/e2e",
  fullyParallel: true,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:4173",
    trace: "on-first-retry",
  },
  webServer: {
    command: "npm --prefix apps/operator-ui run dev -- --host 127.0.0.1",
    reuseExistingServer: !process.env.CI,
    url: "http://127.0.0.1:4173/operator",
  },
  projects: [
    {
      name: "chromium",
      use: {
        browserName: "chromium",
        viewport: {
          height: 720,
          width: 1280,
        },
      },
    },
  ],
};
