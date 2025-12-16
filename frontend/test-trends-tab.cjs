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

    console.log('Taking initial screenshot...');
    await page.screenshot({ path: 'trends-initial.png', fullPage: true });

    console.log('Looking for Dashboard or main content...');

    // Check if we're on the dashboard page
    const dashboardTitle = page.locator('h1, h2, h3').filter({ hasText: /dashboard|congress|main/i }).first();
    if (await dashboardTitle.count() > 0) {
      console.log('Found dashboard content');
    }

    // Look for navigation or links to Members/Party Comparison
    console.log('Looking for navigation...');
    const navItems = await page.locator('nav a, .nav a, a').all();
    console.log(`Found ${navItems.length} navigation items`);

    // Try to find Members or Party-related links
    const membersLink = page.locator('a').filter({ hasText: /members|party|comparison/i }).first();
    if (await membersLink.count() > 0) {
      console.log('Found members/party link, clicking...');
      await membersLink.click();
      await page.waitForLoadState('networkidle');
      await page.screenshot({ path: 'after-navigation.png', fullPage: true });
    }

    // Look for Party Comparison or similar components
    console.log('Searching for Party Comparison component...');
    const partyHeaders = await page.locator('h1, h2, h3, h4').filter({ hasText: /party|comparison/i }).all();
    console.log(`Found ${partyHeaders.length} party-related headers`);

    if (partyHeaders.length > 0) {
      // Scroll to the first party-related header
      await partyHeaders[0].scrollIntoViewIfNeeded();
      await page.waitForTimeout(1000);
    }

    // Look for tab navigation (Overview, Voting, Trends)
    console.log('Looking for tab navigation...');
    const tabs = await page.locator('button').filter({ hasText: /overview|voting|trends/i }).all();
    console.log(`Found ${tabs.length} tab buttons`);

    // Look specifically for Trends tab
    const trendsTab = page.locator('button').filter({ hasText: /trends/i }).first();
    if (await trendsTab.count() > 0) {
      console.log('Found Trends tab! Clicking...');
      await trendsTab.click();
      await page.waitForTimeout(3000); // Wait for loading

      // Take screenshots after clicking Trends
      await page.screenshot({ path: 'trends-tab-desktop.png', fullPage: true });

      // Test responsive design
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.waitForTimeout(1000);
      await page.screenshot({ path: 'trends-tab-tablet.png', fullPage: true });

      await page.setViewportSize({ width: 375, height: 812 });
      await page.waitForTimeout(1000);
      await page.screenshot({ path: 'trends-tab-mobile.png', fullPage: true });

      // Reset to desktop
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.waitForTimeout(1000);

      // Check for trend components
      const components = await page.evaluate(() => {
        const getText = (selector) => {
          const el = document.querySelector(selector);
          return el ? el.textContent : null;
        };

        return {
          legislativeActivity: !!document.querySelector(':has-text("Legislative Activity")'),
          bipartisanCooperation: !!document.querySelector(':has-text("Bipartisan")'),
          votingConsistency: !!document.querySelector(':has-text("Voting Consistency")'),
          loadingState: !!document.querySelector('.animate-spin'),
          errorState: !!document.querySelector('.text-red-800'),
          hasCharts: document.querySelectorAll('.recharts-wrapper, svg').length
        };
      });

      console.log('Trend Components Analysis:');
      console.log('- Legislative Activity:', components.legislativeActivity ? '✅' : '❌');
      console.log('- Bipartisan Cooperation:', components.bipartisanCooperation ? '✅' : '❌');
      console.log('- Voting Consistency:', components.votingConsistency ? '✅' : '❌');
      console.log('- Loading State:', components.loadingState ? '⏳' : '✅');
      console.log('- Error State:', components.errorState ? '❌' : '✅');
      console.log('- Charts Present:', components.hasCharts, 'chart elements');

    } else {
      console.log('❌ Trends tab not found');

      // Let's see what's actually on the page
      const pageContent = await page.evaluate(() => {
        return {
          title: document.title,
          url: location.href,
          bodyText: document.body.innerText.substring(0, 1000),
          buttons: Array.from(document.querySelectorAll('button')).map(btn => btn.textContent?.trim()).filter(Boolean),
          headers: Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6')).map(h => h.textContent?.trim()).filter(Boolean)
        };
      });

      console.log('Page Content Analysis:');
      console.log('Title:', pageContent.title);
      console.log('URL:', pageContent.url);
      console.log('Buttons:', pageContent.buttons);
      console.log('Headers:', pageContent.headers);
    }

    await page.screenshot({ path: 'final-state.png', fullPage: true });

  } catch (error) {
    console.error('Error during testing:', error.message);
    await page.screenshot({ path: 'error-state.png' });
  }

  await browser.close();
  console.log('✅ Testing completed');
})();