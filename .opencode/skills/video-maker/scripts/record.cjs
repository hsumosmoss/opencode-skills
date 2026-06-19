const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({
    args: ['--autoplay-policy=no-user-gesture-required'],
  });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
    recordVideo: { dir: path.join(__dirname, 'renders'), size: { width: 1920, height: 1080 } },
  });
  const page = await context.newPage();
  const fileUrl = 'file:///' + path.join(__dirname, 'index.html').replace(/\\/g, '/');
  console.log('Loading:', fileUrl);
  await page.goto(fileUrl);
  await page.waitForTimeout(800);
  await page.evaluate(() => { startPlay(); });
  console.log('Recording 165s...');
  await page.waitForTimeout(165000);
  await context.close();
  await browser.close();
  console.log('Done.');
})();
