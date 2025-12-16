const { chromium } = require('playwright');

async function testCommitteeDetail() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  // Listen for console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('CONSOLE ERROR:', msg.text());
    }
  });

  page.on('pageerror', error => {
    console.log('PAGE ERROR:', error.message);
  });

  try {
    console.log('🔍 Testing Committee Detail page functionality...');

    // Navigate to committees page first
    console.log('📋 Navigating to committees page...');
    await page.goto('http://localhost:5173/committees');
    await page.waitForLoadState('networkidle');

    // Take a screenshot of the committees list
    await page.screenshot({ path: 'committee-list-test.png', fullPage: true });
    console.log('✅ Committees list page loaded');

    // Try to find and click on a committee
    const committeeCards = await page.locator('.committee-card, [data-testid="committee-card"], a[href*="/committees/"]').all();

    if (committeeCards.length > 0) {
      console.log(`📊 Found ${committeeCards.length} committee cards`);

      // Click on the first committee
      await committeeCards[0].click();
      await page.waitForLoadState('networkidle');

      // Wait for committee detail content to load
      await page.waitForSelector('h1, .committee-name, [data-testid="committee-name"]', { timeout: 10000 });

      console.log('✅ Committee detail page loaded');

      // Check for key elements
      const elements = await page.evaluate(() => {
        return {
          hasHeader: !!document.querySelector('h1'),
          hasMembers: !!document.querySelector('[data-testid="committee-members"], .member-roster, .member-card'),
          hasBills: !!document.querySelector('[data-testid="committee-bills"], .bill-card'),
          hasTimeline: !!document.querySelector('[data-testid="committee-timeline"], .timeline'),
          hasLoadingStates: !!document.querySelector('.animate-spin, .animate-pulse'),
          hasErrorStates: !!document.querySelector('.bg-red-50, .text-red-'),
          url: location.href,
          title: document.title,
          headerText: document.querySelector('h1')?.textContent || 'No header found'
        };
      });

      console.log('📝 Page Analysis:', elements);

      // Take screenshots at different viewports
      await page.screenshot({ path: 'committee-detail-desktop.png', fullPage: true });

      // Test mobile view
      await page.setViewportSize({ width: 375, height: 812 });
      await page.screenshot({ path: 'committee-detail-mobile.png', fullPage: true });

      // Test tablet view
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.screenshot({ path: 'committee-detail-tablet.png', fullPage: true });

      console.log('📸 Screenshots captured for all viewports');

      // Test member roster functionality
      await page.setViewportSize({ width: 1920, height: 1080 });

      // Look for member search and filters
      const searchInput = await page.locator('input[placeholder*="Search"], input[type="search"]').first();
      if (await searchInput.count() > 0) {
        console.log('🔍 Testing member search...');
        await searchInput.fill('John');
        await page.waitForTimeout(1000);
        await page.screenshot({ path: 'committee-members-search.png' });
        await searchInput.clear();
      }

      // Test party filters if available
      const partyFilter = await page.locator('select[aria-label*="party"], select:has-text("Party")').first();
      if (await partyFilter.count() > 0) {
        console.log('🏛️ Testing party filter...');
        await partyFilter.selectOption({ index: 1 }); // Select first non-"all" option
        await page.waitForTimeout(1000);
        await page.screenshot({ path: 'committee-members-filtered.png' });
      }

      console.log('✅ Committee detail page testing completed successfully');

    } else {
      console.log('❌ No committee cards found on committees page');

      // Try navigating directly to a committee
      console.log('🔄 Trying direct committee URL...');
      await page.goto('http://localhost:5173/committees/hsap00'); // House Appropriations Committee
      await page.waitForLoadState('networkidle');
      await page.screenshot({ path: 'committee-detail-direct.png', fullPage: true });

      const directElements = await page.evaluate(() => {
        return {
          url: location.href,
          title: document.title,
          hasContent: document.body.children.length > 0,
          hasError: !!document.querySelector('.bg-red-50, .text-red-'),
          bodyText: document.body.innerText.substring(0, 500)
        };
      });

      console.log('📊 Direct navigation result:', directElements);
    }

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    await page.screenshot({ path: 'committee-test-error.png' });
  } finally {
    await browser.close();
  }
}

// Run the test
testCommitteeDetail().catch(console.error);