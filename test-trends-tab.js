const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  // Listen for console messages and errors
  page.on('console', msg => console.log('CONSOLE:', msg.text()));
  page.on('pageerror', error => console.log('ERROR:', error.message));

  try {
    console.log('Navigating to Congress platform...');
    await page.goto('https://congress.local.team-skynet.io');
    await page.waitForLoadState('networkidle');

    console.log('Looking for Party Comparison section...');
    // Navigate to Party Comparison page (assuming it's in navigation)
    const partyLink = page.locator('text=Party Comparison').first();
    if (await partyLink.count() > 0) {
      await partyLink.click();
      await page.waitForLoadState('networkidle');
    } else {
      // Try to find it in the main content area
      const overviewSection = page.locator('text=Party Comparison Analysis').first();
      if (await overviewSection.count() === 0) {
        // Navigate to members page first, then try to find party comparison
        await page.click('text=Members');
        await page.waitForLoadState('networkidle');

        // Look for party comparison within members page
        const partySection = page.locator('text=Party Comparison').first();
        if (await partySection.count() > 0) {
          await partySection.scrollIntoViewIfNeeded();
        }
      }
    }

    // Take screenshot of current state
    await page.screenshot({ path: 'trends-initial.png', fullPage: true });

    console.log('Looking for Trends tab...');
    // Find and click the Trends tab
    const trendsTab = page.locator('button:has-text("Trends")').first();
    if (await trendsTab.count() > 0) {
      console.log('Found Trends tab, clicking...');
      await trendsTab.click();
      await page.waitForTimeout(2000); // Wait for data loading

      // Take screenshot of Trends tab
      await page.screenshot({ path: 'trends-tab-desktop.png', fullPage: true });

      // Test mobile view
      await page.setViewportSize({ width: 375, height: 812 });
      await page.waitForTimeout(1000);
      await page.screenshot({ path: 'trends-tab-mobile.png', fullPage: true });

      // Test tablet view
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.waitForTimeout(1000);
      await page.screenshot({ path: 'trends-tab-tablet.png', fullPage: true });

      console.log('✅ Successfully tested Trends tab functionality');

      // Check for specific trend components
      await page.setViewportSize({ width: 1920, height: 1080 });
      const legislativeActivity = page.locator('text=Legislative Activity Trends').first();
      const bipartisanCooperation = page.locator('text=Bipartisan Cooperation Analysis').first();
      const votingConsistency = page.locator('text=Party Unity & Voting Consistency').first();

      console.log('Checking trend components:');
      console.log('- Legislative Activity:', await legislativeActivity.count() > 0 ? '✅' : '❌');
      console.log('- Bipartisan Cooperation:', await bipartisanCooperation.count() > 0 ? '✅' : '❌');
      console.log('- Voting Consistency:', await votingConsistency.count() > 0 ? '✅' : '❌');

    } else {
      console.log('❌ Trends tab not found');
      // Take screenshot of what we can see
      await page.screenshot({ path: 'trends-not-found.png', fullPage: true });
    }

    const content = await page.evaluate(() => ({
      url: location.href,
      title: document.title,
      hasContent: document.body.children.length > 0,
      trendsTabExists: !!document.querySelector('button:has-text("Trends")'),
      partyComparisonExists: !!document.querySelector(':has-text("Party Comparison")'),
    }));

    console.log('Page Analysis:', content);

  } catch (error) {
    console.error('Error:', error.message);
    await page.screenshot({ path: 'error-trends-test.png' });
  }

  await browser.close();
})();