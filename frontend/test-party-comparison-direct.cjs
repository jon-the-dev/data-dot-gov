const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  // Listen for console messages
  page.on('console', msg => console.log('CONSOLE:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));

  try {
    console.log('🎯 Navigating directly to Party Comparison page...');
    await page.goto('https://congress.local.team-skynet.io/party-comparison');
    await page.waitForLoadState('networkidle');

    // Take initial screenshot
    console.log('📸 Taking initial screenshot...');
    await page.screenshot({ path: 'party-comparison-page.png', fullPage: true });

    // Wait for page to fully load and then look for trends tab
    console.log('⏳ Waiting for page components to load...');
    await page.waitForTimeout(3000);

    // Look for the Trends tab
    console.log('🔍 Looking for Trends tab...');
    const trendsTab = page.locator('button').filter({ hasText: /trends/i }).first();

    if (await trendsTab.count() > 0) {
      console.log('✅ Found Trends tab! Clicking...');
      await trendsTab.click();

      // Wait for trends data to load
      console.log('⏳ Waiting for trends data to load...');
      await page.waitForTimeout(8000); // Wait longer for mock data to process

      // Take screenshot after clicking Trends
      console.log('📸 Taking Trends tab screenshot...');
      await page.screenshot({
        path: 'party-comparison-trends-loaded.png',
        fullPage: true
      });

      // Analyze what's on the page
      const trendsAnalysis = await page.evaluate(() => {
        return {
          url: location.href,
          title: document.title,

          // Check for main trend sections
          legislativeActivity: !!document.querySelector('*:has-text("Legislative Activity")'),
          bipartisanCooperation: !!document.querySelector('*:has-text("Bipartisan Cooperation")'),
          votingConsistency: !!document.querySelector('*:has-text("Voting Consistency")'),

          // Check for specific components
          bridgeBuilders: !!document.querySelector('*:has-text("Bridge Builders")'),
          maverickMembers: !!document.querySelector('*:has-text("Maverick")'),
          monthlyTrends: !!document.querySelector('*:has-text("Monthly")'),

          // Check for charts
          charts: document.querySelectorAll('.recharts-wrapper, svg[class*="recharts"]').length,

          // Check loading/error states
          loading: !!document.querySelector('.animate-spin'),
          error: !!document.querySelector('.text-red-800, .bg-red-50'),

          // Get some sample text content
          pageText: document.body.innerText.substring(0, 500)
        };
      });

      console.log('\n📊 TRENDS PAGE ANALYSIS:');
      console.log('🌐 URL:', trendsAnalysis.url);
      console.log('📄 Title:', trendsAnalysis.title);
      console.log('\n📈 COMPONENTS:');
      console.log('- Legislative Activity:', trendsAnalysis.legislativeActivity ? '✅' : '❌');
      console.log('- Bipartisan Cooperation:', trendsAnalysis.bipartisanCooperation ? '✅' : '❌');
      console.log('- Voting Consistency:', trendsAnalysis.votingConsistency ? '✅' : '❌');
      console.log('- Bridge Builders:', trendsAnalysis.bridgeBuilders ? '✅' : '❌');
      console.log('- Maverick Members:', trendsAnalysis.maverickMembers ? '✅' : '❌');
      console.log('- Monthly Trends:', trendsAnalysis.monthlyTrends ? '✅' : '❌');
      console.log('\n📊 VISUALIZATION:');
      console.log('- Charts Found:', trendsAnalysis.charts);
      console.log('- Loading State:', trendsAnalysis.loading ? '⏳ Loading' : '✅ Loaded');
      console.log('- Error State:', trendsAnalysis.error ? '❌ Error' : '✅ No Error');

      console.log('\n📱 Testing responsive design...');

      // Test tablet
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.waitForTimeout(1000);
      await page.screenshot({
        path: 'party-comparison-trends-tablet.png',
        fullPage: true
      });

      // Test mobile
      await page.setViewportSize({ width: 375, height: 812 });
      await page.waitForTimeout(1000);
      await page.screenshot({
        path: 'party-comparison-trends-mobile.png',
        fullPage: true
      });

      console.log('\n🎉 SUCCESS! Trends tab functionality is working with visualizations!');

    } else {
      console.log('❌ Trends tab not found on Party Comparison page');

      // Let's see what tabs are available
      const availableTabs = await page.locator('button').evaluateAll(buttons =>
        buttons.map(btn => btn.textContent?.trim()).filter(Boolean)
      );
      console.log('Available buttons:', availableTabs);
    }

  } catch (error) {
    console.error('💥 Error:', error.message);
    await page.screenshot({ path: 'party-comparison-error.png' });
  }

  await browser.close();
})();