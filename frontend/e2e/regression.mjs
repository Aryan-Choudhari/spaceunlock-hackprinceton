import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
await mkdir("../docs/private", { recursive: true });
const browser = await chromium.launch({
  headless: true,
  args: ["--no-sandbox"],
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
  recordVideo: { dir: "../docs/private", size: { width: 1440, height: 1000 } },
});
const page = await context.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.goto("http://localhost:8000");
await page
  .getByRole("button", { name: "Find the best plan" })
  .waitFor({ timeout: 90000 });
await page
  .getByRole("button", { name: "Try a conditional demo scenario" })
  .click();
await page.getByRole("button", { name: "Find the best plan" }).click();
await page
  .getByText("$12,000", { exact: true })
  .first()
  .waitFor({ timeout: 90000 });
await page.getByRole("button", { name: "Compare budgets" }).click();
await page
  .getByRole("button", { name: "$5,500 1 uses · $5,500 spent" })
  .waitFor({ timeout: 10000 });
await page
  .getByRole("button", { name: "$5,500 1 uses · $5,500 spent" })
  .click();
await page.getByRole("button", { name: "Find the best plan" }).click();
await page.getByText("+1", { exact: true }).waitFor({ timeout: 90000 });
await page.getByRole("button", { name: "Approve draft", exact: true }).click();
await page.getByRole("status").filter({ hasText: "approved_draft" }).waitFor();
const download = page.waitForEvent("download");
await page.getByRole("link", { name: "Markdown", exact: true }).click();
const file = await download;
await file.saveAs("../docs/private/demo-plan.md");
await page.getByRole("button", { name: "Evidence", exact: true }).click();
await page.getByText("Load Vexcel aerial image", { exact: true }).click();
await page.locator('img[alt^="Vexcel"]').evaluate((img) => img.decode());
await page.getByLabel("Withhold matterport evidence", { exact: true }).check();
await page.getByRole("button", { name: "Reassess evidence" }).click();
await page
  .getByText("Community workshop: UNKNOWN", { exact: false })
  .waitFor({ timeout: 90000 });
await page.getByRole("button", { name: "Agent trace", exact: true }).click();
await page.getByText("Ollama local tool agent", { exact: false }).waitFor();
const tools = await page.locator(".trace summary").allTextContents();
if (
  !tools[0].includes("get_property_context") ||
  !tools.some((t) => t.includes("validate_plan"))
)
  throw Error("Incomplete agent ordering");
await page.getByRole("button", { name: "Planner", exact: true }).click();
await page.screenshot({
  path: "/tmp/spaceunlock-final-desktop.png",
  fullPage: true,
});
await page.setViewportSize({ width: 390, height: 844 });
await page.screenshot({
  path: "/tmp/spaceunlock-final-mobile.png",
  fullPage: true,
});
const overflow = await page.evaluate(
  () => document.documentElement.scrollWidth > innerWidth + 1,
);
const video = page.video();
await context.close();
await video.saveAs("../docs/private/spaceunlock-demo.webm");
await browser.close();
console.log(JSON.stringify({ errors, mobileOverflow: overflow, tools }));
if (errors.length || overflow) process.exitCode = 1;
