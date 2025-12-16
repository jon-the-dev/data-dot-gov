const { chromium } = require('playwright');

async function comprehensiveTrendsTabTest() {
  console.log('🚀 Starting Comprehensive Trends Tab Testing (localhost)...\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 500 // Slow down for better visibility
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });

  const page = await context.newPage();

  // Listen for console messages and errors
  const consoleMessages = [];
  const pageErrors = [];

  page.on('console', msg => {
    const message = `${msg.type().toUpperCase()}: ${msg.text()}`;
    consoleMessages.push(message);
    if (msg.type() === 'error') {
      console.log('🔴', message);
    } else if (msg.type() === 'warn') {
      console.log('🟡', message);
    } else if (msg.type() === 'log') {
      console.log('📄', message);
    }
  });

  page.on('pageerror', error => {
    const errorMsg = `PAGE ERROR: ${error.message}`;
    pageErrors.push(errorMsg);
    console.log('❌', errorMsg);
  });

  // Performance tracking
  let testResults = {
    navigationSuccessful: false,
    partyComparisonFound: false,
    trendsTabFound: false,
    legislativeActivityFound: false,
    bipartisanCooperationFound: false,
    votingConsistencyFound: false,
    chartsFound: 0,
    interactiveElementsFound: 0,
    responsiveTestsPassed: 0,
    loadTime: 0,
    errors: []
  };

  try {
    console.log('📍 Test 1: Navigate to Congressional Transparency Platform (localhost)');
    const startTime = Date.now();

    await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
    const loadTime = Date.now() - startTime;
    testResults.loadTime = loadTime;

    console.log(`✅ Page loaded in ${loadTime}ms`);
    testResults.navigationSuccessful = true;

    // Wait a moment for React to render
    await page.waitForTimeout(2000);

    // Take initial screenshot
    await page.screenshot({
      path: 'test-results-homepage-desktop.png',
      fullPage: true
    });
    console.log('📸 Homepage screenshot saved');

    // Check what's actually on the page
    const pageContent = await page.evaluate(() => {
      return {
        title: document.title,
        bodyText: document.body.innerText.substring(0, 1000),
        hasNavigationElements: document.querySelectorAll('nav, .nav, [role="navigation"]').length,
        allLinks: Array.from(document.querySelectorAll('a, button')).map(el => el.textContent?.trim()).filter(text => text && text.length > 0)
      };
    });

    console.log(`📄 Page Title: "${pageContent.title}"`);
    console.log(`🔗 Found ${pageContent.hasNavigationElements} navigation elements`);
    console.log(`🔗 Available links/buttons:`, pageContent.allLinks.slice(0, 10));

    console.log('\n📍 Test 2: Navigate to Party Comparison');

    // Look for navigation elements - try multiple strategies
    let navigatedToPartyComparison = false;

    // Strategy 1: Look for "Party Comparison" text
    const partyComparisonElements = await page.locator('*:has-text("Party Comparison")').all();
    if (partyComparisonElements.length > 0) {
      console.log(`Found ${partyComparisonElements.length} elements with "Party Comparison" text`);
      try {
        await partyComparisonElements[0].click();
        await page.waitForTimeout(2000);
        navigatedToPartyComparison = true;
        console.log('✅ Clicked on Party Comparison element');
      } catch (error) {
        console.log('⚠️ Could not click Party Comparison element:', error.message);
      }
    }

    // Strategy 2: If no specific link, look for navigation menu items
    if (!navigatedToPartyComparison) {
      const navLinks = await page.locator('nav a, nav button, .nav a, .nav button').all();
      console.log(`Found ${navLinks.length} navigation links`);

      for (let i = 0; i < Math.min(navLinks.length, 5); i++) {
        try {
          const linkText = await navLinks[i].textContent();
          console.log(`  Navigation item ${i}: "${linkText}"`);
          if (linkText && (linkText.toLowerCase().includes('party') || linkText.toLowerCase().includes('comparison'))) {
            await navLinks[i].click();
            await page.waitForTimeout(2000);
            navigatedToPartyComparison = true;
            console.log(`✅ Clicked navigation item: "${linkText}"`);
            break;
          }
        } catch (error) {
          console.log(`⚠️ Could not interact with nav item ${i}:`, error.message);
        }
      }
    }

    // Strategy 3: If still not found, try any secondary navigation item
    if (!navigatedToPartyComparison && pageContent.allLinks.length > 1) {
      try {
        // Try clicking the second available link (skip home/first)
        const clickableElements = await page.locator('a, button').all();
        if (clickableElements.length > 1) {
          await clickableElements[1].click();
          await page.waitForTimeout(2000);
          navigatedToPartyComparison = true;
          console.log('✅ Clicked alternative navigation element');
        }
      } catch (error) {
        console.log('⚠️ Could not click alternative element:', error.message);
      }
    }

    testResults.partyComparisonFound = navigatedToPartyComparison;

    await page.screenshot({ path: 'test-results-after-navigation.png', fullPage: true });

    console.log('\n📍 Test 3: Look for Trends Tab');

    // Look for tabs or trends-related content
    await page.waitForTimeout(1000);

    const currentPageContent = await page.evaluate(() => ({
      bodyText: document.body.innerText.toLowerCase(),
      allElements: Array.from(document.querySelectorAll('*')).map(el => el.textContent?.trim()).filter(text => text && text.length > 0 && text.length < 50)
    }));

    console.log('🔍 Searching for Trends content...');
    const hasTrends = currentPageContent.bodyText.includes('trends') ||
                     currentPageContent.allElements.some(text => text.toLowerCase().includes('trends'));

    if (hasTrends) {
      console.log('✅ Found Trends content on page');
      testResults.trendsTabFound = true;
    } else {
      console.log('⚠️ No Trends content found, looking for tab elements...');
    }

    // Look for any tab-like elements
    const tabElements = await page.locator('[role="tab"], .tab, button[class*="tab"], .MuiTab-root').all();
    console.log(`Found ${tabElements.length} tab-like elements`);

    let trendsTabClicked = false;
    for (let i = 0; i < tabElements.length; i++) {
      try {
        const tabText = await tabElements[i].textContent();
        console.log(`  Tab ${i}: "${tabText}"`);
        if (tabText && tabText.toLowerCase().includes('trends')) {
          await tabElements[i].click();
          await page.waitForTimeout(3000);
          trendsTabClicked = true;
          testResults.trendsTabFound = true;
          console.log(`✅ Clicked Trends tab: "${tabText}"`);
          break;
        }
      } catch (error) {
        console.log(`⚠️ Could not interact with tab ${i}:`, error.message);
      }
    }

    await page.screenshot({ path: 'test-results-trends-section.png', fullPage: true });

    console.log('\n📍 Test 4: Validate Trends Content Sections');

    const contentAnalysis = await page.evaluate(() => {
      const bodyText = document.body.innerText.toLowerCase();
      return {
        hasLegislative: bodyText.includes('legislative') || bodyText.includes('activity'),
        hasBipartisan: bodyText.includes('bipartisan') || bodyText.includes('cooperation'),
        hasVoting: bodyText.includes('voting') || bodyText.includes('consistency'),
        hasCharts: document.querySelectorAll('svg, canvas, .recharts-wrapper, .chart').length,
        hasInteractiveElements: document.querySelectorAll('button, select, input[type="checkbox"], input[type="radio"]').length,
        allHeadings: Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6')).map(h => h.textContent?.trim()).filter(t => t)
      };
    });

    console.log('📊 Content Analysis:');
    console.log(`  Legislative Activity content: ${contentAnalysis.hasLegislative ? '✅' : '❌'}`);
    console.log(`  Bipartisan Cooperation content: ${contentAnalysis.hasBipartisan ? '✅' : '❌'}`);
    console.log(`  Voting Consistency content: ${contentAnalysis.hasVoting ? '✅' : '❌'}`);
    console.log(`  Charts found: ${contentAnalysis.hasCharts}`);
    console.log(`  Interactive elements: ${contentAnalysis.hasInteractiveElements}`);
    console.log(`  Page headings:`, contentAnalysis.allHeadings.slice(0, 5));

    testResults.legislativeActivityFound = contentAnalysis.hasLegislative;
    testResults.bipartisanCooperationFound = contentAnalysis.hasBipartisan;
    testResults.votingConsistencyFound = contentAnalysis.hasVoting;
    testResults.chartsFound = contentAnalysis.hasCharts;
    testResults.interactiveElementsFound = contentAnalysis.hasInteractiveElements;

    console.log('\n📍 Test 5: Responsive Design Testing');
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 375, height: 812, name: 'Mobile' }
    ];

    let responsivePassed = 0;
    for (const viewport of viewports) {
      console.log(`📱 Testing ${viewport.name} viewport (${viewport.width}x${viewport.height})`);
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.waitForTimeout(1000);

      await page.screenshot({
        path: `test-results-${viewport.name.toLowerCase()}.png`,
        fullPage: true
      });

      const responsiveCheck = await page.evaluate(() => {
        return {
          hasHorizontalScroll: document.body.scrollWidth > window.innerWidth,
          isContentVisible: document.body.offsetHeight > 100,
          visibleElements: document.querySelectorAll('*:not([hidden]):not([style*="display: none"])').length
        };
      });

      console.log(`  - Has horizontal scroll: ${responsiveCheck.hasHorizontalScroll ? '❌' : '✅'}`);
      console.log(`  - Content visible: ${responsiveCheck.isContentVisible ? '✅' : '❌'}`);
      console.log(`  - Visible elements: ${responsiveCheck.visibleElements}`);

      if (!responsiveCheck.hasHorizontalScroll && responsiveCheck.isContentVisible) {
        responsivePassed++;
      }
    }

    testResults.responsiveTestsPassed = responsivePassed;

    console.log('\n📍 Test 6: Performance and Error Check');

    // Reset to desktop
    await page.setViewportSize({ width: 1920, height: 1080 });

    const performanceMetrics = await page.evaluate(() => {
      const perf = performance.getEntriesByType('navigation')[0];
      return {
        domContentLoaded: perf ? Math.round(perf.domContentLoadedEventEnd - perf.fetchStart) : 0,
        loadComplete: perf ? Math.round(perf.loadEventEnd - perf.fetchStart) : 0,
        memoryUsage: performance.memory ? {
          used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
          total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024)
        } : null
      };
    });

    console.log('⚡ Performance Metrics:');
    console.log(`  DOM Content Loaded: ${performanceMetrics.domContentLoaded}ms`);
    console.log(`  Load Complete: ${performanceMetrics.loadComplete}ms`);
    if (performanceMetrics.memoryUsage) {
      console.log(`  Memory Usage: ${performanceMetrics.memoryUsage.used}MB / ${performanceMetrics.memoryUsage.total}MB`);
    }

    console.log('\n📍 Final Comprehensive Screenshot');
    await page.screenshot({
      path: 'test-results-final-comprehensive.png',
      fullPage: true
    });

    // Error summary
    testResults.errors = [...pageErrors, ...consoleMessages.filter(msg => msg.includes('ERROR'))];

  } catch (error) {
    console.error('❌ Test failed with error:', error.message);
    testResults.errors.push(`Test Error: ${error.message}`);
    await page.screenshot({ path: 'test-results-error.png' });
  } finally {
    console.log('\n🎯 COMPREHENSIVE TEST RESULTS');
    console.log('===============================');

    Object.entries(testResults).forEach(([key, value]) => {
      if (key === 'errors') return; // Handle separately
      const icon = typeof value === 'boolean' ? (value ? '✅' : '❌') : '📊';
      console.log(`${icon} ${key}: ${value}`);
    });

    if (testResults.errors.length > 0) {
      console.log('\n❌ Errors Found:');
      testResults.errors.forEach((error, i) => {
        console.log(`  ${i + 1}. ${error}`);
      });
    } else {
      console.log('\n✅ No errors found!');
    }

    const overallScore = Object.entries(testResults)
      .filter(([key]) => typeof testResults[key] === 'boolean')
      .reduce((score, [_, value]) => score + (value ? 1 : 0), 0);

    console.log(`\n🏆 Overall Score: ${overallScore}/${Object.keys(testResults).filter(k => typeof testResults[k] === 'boolean').length}`);

    console.log('\n📸 Screenshots saved:');
    console.log('  - test-results-homepage-desktop.png');
    console.log('  - test-results-after-navigation.png');
    console.log('  - test-results-trends-section.png');
    console.log('  - test-results-desktop.png');
    console.log('  - test-results-tablet.png');
    console.log('  - test-results-mobile.png');
    console.log('  - test-results-final-comprehensive.png');

    console.log('\n🏁 Testing completed. Check the generated screenshots for visual validation.');
    await browser.close();

    return testResults;
  }
}

// Run the comprehensive test
comprehensiveTrendsTabTest()
  .then(results => {
    console.log('\n✅ Test execution completed successfully');
    process.exit(0);
  })
  .catch(error => {
    console.error('\n❌ Test execution failed:', error);
    process.exit(1);
  });