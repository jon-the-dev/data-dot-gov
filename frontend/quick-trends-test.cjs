const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // Listen for console messages
  page.on('console', msg => console.log('CONSOLE:', msg.text()));

  try {
    console.log('Navigating to Congress platform...');
    await page.goto('https://congress.local.team-skynet.io');
    await page.waitForLoadState('networkidle');

    // Navigate to Party Comparison and click Trends tab
    const membersLink = page.locator('a').filter({ hasText: /members/i }).first();
    if (await membersLink.count() > 0) {
      await membersLink.click();
      await page.waitForLoadState('networkidle');
    }

    // Find and click Trends tab
    const trendsTab = page.locator('button').filter({ hasText: /trends/i }).first();
    if (await trendsTab.count() > 0) {
      console.log('Clicking Trends tab...');
      await trendsTab.click();
      await page.waitForTimeout(5000); // Wait longer to see network requests

      // Take final screenshot
      await page.screenshot({ path: 'quick-trends-test.png', fullPage: true });

      console.log('✅ Test completed, check console for API request details');
    } else {
      console.log('❌ Trends tab not found');
    }

  } catch (error) {
    console.error('Error:', error.message);
  }

  await browser.close();
})();