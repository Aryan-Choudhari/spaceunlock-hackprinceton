import { chromium } from "@playwright/test";
const browser = await chromium.launch({
  headless: true,
  args: ["--no-sandbox"],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.goto("http://127.0.0.1:8000");
await page.locator(".property h2").waitFor();
await page
  .getByRole("button", { name: "Find the best plan" })
  .waitFor({ timeout: 90000 });
await page.screenshot({ path: "/tmp/spaceunlock-before.png", fullPage: true });
for (const label of [
  "Continuous access from street to this scanned floor is available",
  "An existing entrance can be activated with owner permission",
  "The measured room can be reassigned",
  "An internal route exists and can be cleared without construction",
  "Operating hours have owner consent",
  "Electricity is available",
])
  await page.getByLabel(label, { exact: true }).check();
await page.getByRole("button", { name: "Find the best plan" }).click();
await page
  .getByText("$9,500", { exact: true })
  .first()
  .waitFor({ timeout: 90000 });
await page.getByRole("button", { name: "Approve draft", exact: true }).click();
await page.getByRole("status").filter({ hasText: "approved_draft" }).waitFor();
await page.screenshot({ path: "/tmp/spaceunlock-plan.png", fullPage: true });
await page.getByRole("button", { name: "Agent trace", exact: true }).click();
await page.getByRole("heading", { name: "Decision workflow" }).waitFor();
await page.getByText("Ollama local tool agent", { exact: false }).waitFor();
await page.getByRole("button", { name: "Evidence", exact: true }).click();
await page.getByRole("heading", { name: "Evidence register" }).waitFor();
await page.screenshot({
  path: "/tmp/spaceunlock-evidence.png",
  fullPage: true,
});
await page.setViewportSize({ width: 390, height: 844 });
await page.getByRole("button", { name: "Planner", exact: true }).click();
await page.screenshot({ path: "/tmp/spaceunlock-mobile.png", fullPage: true });
const overflow = await page.evaluate(
  () => document.documentElement.scrollWidth > window.innerWidth + 1,
);
console.log(JSON.stringify({ errors, mobileOverflow: overflow }));
await browser.close();
if (errors.length || overflow) process.exitCode = 1;
