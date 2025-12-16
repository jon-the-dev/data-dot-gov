const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  // Listen for console messages
  page.on('console', msg => console.log('CONSOLE:', msg.text()));

  try {
    console.log('🚀 Testing Trends Tab with Mock Data');

    console.log('📡 Navigating to Congress platform...');
    await page.goto('https://congress.local.team-skynet.io');
    await page.waitForLoadState('networkidle');

    console.log('🔍 Looking for Party Comparison...');
    // Navigate to Members first, then find Party Comparison
    const membersLink = page.locator('a').filter({ hasText: /members/i }).first();
    if (await membersLink.count() > 0) {
      console.log('👥 Clicking Members link...');
      await membersLink.click();
      await page.waitForLoadState('networkidle');
    }

    // Find and click Trends tab
    console.log('📊 Looking for Trends tab...');
    const trendsTab = page.locator('button').filter({ hasText: /trends/i }).first();
    if (await trendsTab.count() > 0) {
      console.log('✅ Found Trends tab, clicking...');
      await trendsTab.click();

      // Wait longer for data loading and rendering
      console.log('⏳ Waiting for data to load...');
      await page.waitForTimeout(5000);

      // Take desktop screenshot
      console.log('📸 Taking desktop screenshot...');
      await page.screenshot({
        path: 'trends-with-mock-data-desktop.png',
        fullPage: true
      });

      // Check if charts are rendered
      const chartElements = await page.locator('.recharts-wrapper, svg[class*="recharts"]').count();
      console.log(`📈 Found ${chartElements} chart elements`);

      // Test tablet view
      console.log('📱 Testing tablet view...');
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.waitForTimeout(1000);
      await page.screenshot({
        path: 'trends-with-mock-data-tablet.png',
        fullPage: true
      });

      // Test mobile view
      console.log('📱 Testing mobile view...');
      await page.setViewportSize({ width: 375, height: 812 });
      await page.waitForTimeout(1000);
      await page.screenshot({
        path: 'trends-with-mock-data-mobile.png',
        fullPage: true
      });

      // Back to desktop for final analysis
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.waitForTimeout(1000);

      // Analyze what components are visible
      const componentAnalysis = await page.evaluate(() => {
        const components = {
          legislativeActivity: {
            present: !!document.querySelector(':has-text("Legislative Activity")'),
            charts: document.querySelectorAll('.recharts-wrapper').length
          },
          bipartisanCooperation: {
            present: !!document.querySelector(':has-text("Bipartisan")'),
            bridgeBuilders: !!document.querySelector(':has-text("Bridge Builders")')
          },
          votingConsistency: {
            present: !!document.querySelector(':has-text("Voting Consistency")'),
            mavericks: !!document.querySelector(':has-text("Maverick")')
          },
          totalCharts: document.querySelectorAll('svg[class*="recharts"], .recharts-wrapper').length,
          loadingSpinner: !!document.querySelector('.animate-spin'),
          errorMessage: !!document.querySelector('.text-red-800')
        };
        return components;
      });

      console.log('\n📊 COMPONENT ANALYSIS:');
      console.log('- Legislative Activity:', componentAnalysis.legislativeActivity.present ? '✅' : '❌');
      console.log('- Bipartisan Cooperation:', componentAnalysis.bipartisanCooperation.present ? '✅' : '❌');
      console.log('- Voting Consistency:', componentAnalysis.votingConsistency.present ? '✅' : '❌');
      console.log('- Bridge Builders:', componentAnalysis.bipartisanCooperation.bridgeBuilders ? '✅' : '❌');
      console.log('- Maverick Members:', componentAnalysis.votingConsistency.mavericks ? '✅' : '❌');
      console.log('- Total Charts:', componentAnalysis.totalCharts);
      console.log('- Loading State:', componentAnalysis.loadingSpinner ? '⏳ Still Loading' : '✅ Loaded');
      console.log('- Error State:', componentAnalysis.errorMessage ? '❌ Error Present' : '✅ No Errors');

      console.log('\n🎉 TRENDS TAB TESTING COMPLETE!');

    } else {
      console.log('❌ Trends tab not found');
      await page.screenshot({ path: 'trends-tab-not-found.png' });
    }

  } catch (error) {
    console.error('💥 Error during testing:', error.message);
    await page.screenshot({ path: 'trends-test-error.png' });
  }

  await browser.close();
})();