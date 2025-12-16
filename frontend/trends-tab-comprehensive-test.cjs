const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function comprehensiveTrendsTabTest() {
  console.log('🚀 Starting Comprehensive Trends Tab Testing...\n');

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
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('🔴 Console Error:', msg.text());
    } else if (msg.type() === 'warn') {
      console.log('🟡 Console Warning:', msg.text());
    }
  });

  page.on('pageerror', error => {
    console.log('❌ Page Error:', error.message);
  });

  try {
    console.log('📍 Test 1: Navigate to Congressional Transparency Platform');
    const startTime = Date.now();
    await page.goto('https://congress.local.team-skynet.io');
    await page.waitForLoadState('networkidle', { timeout: 10000 });
    const loadTime = Date.now() - startTime;
    console.log(`✅ Page loaded in ${loadTime}ms`);

    // Take initial screenshot
    await page.screenshot({
      path: 'homepage-desktop.png',
      fullPage: true
    });
    console.log('📸 Homepage screenshot saved');

    console.log('\n📍 Test 2: Navigate to Party Comparison');
    // Wait for navigation to be visible and click Party Comparison
    await page.waitForSelector('nav', { timeout: 5000 });
    const partyComparisonLink = await page.locator('nav a:has-text("Party Comparison"), nav button:has-text("Party Comparison")').first();

    if (await partyComparisonLink.count() > 0) {
      await partyComparisonLink.click();
      console.log('✅ Clicked Party Comparison link');
    } else {
      // Try alternative navigation
      const navLinks = await page.locator('nav a').all();
      console.log('Available navigation links:');
      for (const link of navLinks) {
        const text = await link.textContent();
        console.log(`  - ${text}`);
      }
      // Try clicking the second or third nav item
      if (navLinks.length > 1) {
        await navLinks[1].click();
        console.log('✅ Clicked alternative navigation item');
      }
    }

    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'party-comparison-page.png', fullPage: true });

    console.log('\n📍 Test 3: Access Trends Tab');
    // Look for Trends tab
    await page.waitForTimeout(2000); // Wait for content to load

    const trendsTab = await page.locator('button:has-text("Trends"), a:has-text("Trends"), [role="tab"]:has-text("Trends")').first();

    if (await trendsTab.count() > 0) {
      await trendsTab.click();
      console.log('✅ Clicked Trends tab');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000); // Wait for charts to load
    } else {
      console.log('🔍 Trends tab not found, checking available tabs...');
      const tabs = await page.locator('[role="tab"], button[class*="tab"], .tab').all();
      for (const tab of tabs) {
        const text = await tab.textContent();
        console.log(`  - Found tab: "${text}"`);
      }

      // If no specific Trends tab, look for any tab that might contain trends
      const possibleTrendsElements = await page.locator('*:has-text("trends"), *:has-text("Trends")').all();
      if (possibleTrendsElements.length > 0) {
        await possibleTrendsElements[0].click();
        console.log('✅ Clicked element containing "Trends"');
      }
    }

    await page.screenshot({ path: 'trends-tab-loaded.png', fullPage: true });

    console.log('\n📍 Test 4: Validate Legislative Activity Section');
    const legislativeSection = await page.locator('*:has-text("Legislative Activity")').first();
    if (await legislativeSection.count() > 0) {
      console.log('✅ Legislative Activity section found');

      // Check for specific components
      const components = [
        'sponsorship',
        'policy',
        'sponsors',
        'bipartisan'
      ];

      for (const component of components) {
        const elements = await page.locator(`*:has-text("${component}")`, { includeHidden: false }).count();
        console.log(`  - ${component} elements: ${elements}`);
      }

      // Take screenshot of this section
      const sectionBounds = await legislativeSection.boundingBox();
      if (sectionBounds) {
        await page.screenshot({
          path: 'legislative-activity-section.png',
          clip: {
            x: sectionBounds.x,
            y: sectionBounds.y,
            width: sectionBounds.width,
            height: sectionBounds.height
          }
        });
      }
    } else {
      console.log('❌ Legislative Activity section not found');
    }

    console.log('\n📍 Test 5: Validate Bipartisan Cooperation Section');
    const bipartisanSection = await page.locator('*:has-text("Bipartisan Cooperation")').first();
    if (await bipartisanSection.count() > 0) {
      console.log('✅ Bipartisan Cooperation section found');

      const components = [
        'cooperation',
        'bridge',
        'cross-party',
        'bipartisan policy'
      ];

      for (const component of components) {
        const elements = await page.locator(`*:has-text("${component}")`, { includeHidden: false }).count();
        console.log(`  - ${component} elements: ${elements}`);
      }

      const sectionBounds = await bipartisanSection.boundingBox();
      if (sectionBounds) {
        await page.screenshot({
          path: 'bipartisan-cooperation-section.png',
          clip: {
            x: sectionBounds.x,
            y: sectionBounds.y,
            width: sectionBounds.width,
            height: sectionBounds.height
          }
        });
      }
    } else {
      console.log('❌ Bipartisan Cooperation section not found');
    }

    console.log('\n📍 Test 6: Validate Voting Consistency Section');
    const votingSection = await page.locator('*:has-text("Voting Consistency")').first();
    if (await votingSection.count() > 0) {
      console.log('✅ Voting Consistency section found');

      const components = [
        'party unity',
        'maverick',
        'divisive votes',
        'consistency'
      ];

      for (const component of components) {
        const elements = await page.locator(`*:has-text("${component}")`, { includeHidden: false }).count();
        console.log(`  - ${component} elements: ${elements}`);
      }

      const sectionBounds = await votingSection.boundingBox();
      if (sectionBounds) {
        await page.screenshot({
          path: 'voting-consistency-section.png',
          clip: {
            x: sectionBounds.x,
            y: sectionBounds.y,
            width: sectionBounds.width,
            height: sectionBounds.height
          }
        });
      }
    } else {
      console.log('❌ Voting Consistency section not found');
    }

    console.log('\n📍 Test 7: Responsive Design Testing');
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 375, height: 812, name: 'Mobile' }
    ];

    for (const viewport of viewports) {
      console.log(`📱 Testing ${viewport.name} viewport (${viewport.width}x${viewport.height})`);
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.waitForTimeout(1000); // Wait for reflow

      await page.screenshot({
        path: `trends-tab-${viewport.name.toLowerCase()}.png`,
        fullPage: true
      });

      // Check if charts are visible and readable
      const charts = await page.locator('svg, canvas, .recharts-wrapper').count();
      console.log(`  - Found ${charts} chart elements`);

      // Check for horizontal scrolling issues
      const hasHorizontalScroll = await page.evaluate(() => {
        return document.body.scrollWidth > window.innerWidth;
      });
      if (hasHorizontalScroll) {
        console.log('  ⚠️ Horizontal scrolling detected');
      } else {
        console.log('  ✅ No horizontal scrolling');
      }
    }

    console.log('\n📍 Test 8: Performance and Data Loading Check');
    // Reset to desktop view
    await page.setViewportSize({ width: 1920, height: 1080 });

    // Check for loading states
    const loadingElements = await page.locator('*:has-text("Loading"), *:has-text("loading"), .loading, [aria-busy="true"]').count();
    console.log(`🔄 Found ${loadingElements} loading indicators`);

    // Check for error messages
    const errorElements = await page.locator('*:has-text("Error"), *:has-text("error"), .error, [role="alert"]').count();
    console.log(`❌ Found ${errorElements} error indicators`);

    // Measure chart rendering performance
    const chartStartTime = Date.now();
    await page.waitForSelector('svg, canvas, .recharts-wrapper', { timeout: 10000 });
    const chartLoadTime = Date.now() - chartStartTime;
    console.log(`📊 Charts loaded in ${chartLoadTime}ms`);

    // Check for memory usage (approximate)
    const memoryInfo = await page.evaluate(() => {
      if (performance.memory) {
        return {
          usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize,
          jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
        };
      }
      return null;
    });

    if (memoryInfo) {
      console.log(`🧠 Memory usage: ${Math.round(memoryInfo.usedJSHeapSize / 1024 / 1024)}MB`);
    }

    console.log('\n📍 Test 9: Interactive Features Testing');

    // Test any interactive elements like filters, buttons, etc.
    const interactiveElements = await page.locator('button, select, input[type="checkbox"], input[type="radio"]').count();
    console.log(`🖱️ Found ${interactiveElements} interactive elements`);

    // Try clicking on chart elements if they exist
    const chartElements = await page.locator('.recharts-bar, .recharts-line, .recharts-area').count();
    if (chartElements > 0) {
      console.log(`📊 Found ${chartElements} chart interactive elements`);
      // Click on first chart element to test interactivity
      try {
        await page.locator('.recharts-bar, .recharts-line, .recharts-area').first().click();
        console.log('✅ Chart element clicked successfully');
      } catch (error) {
        console.log('ℹ️ Chart elements may not be interactive');
      }
    }

    console.log('\n📍 Test 10: Final Comprehensive Screenshot');
    await page.screenshot({
      path: 'trends-tab-final-comprehensive.png',
      fullPage: true
    });

    console.log('\n🎯 Test Summary:');

    // Generate comprehensive analysis
    const pageAnalysis = await page.evaluate(() => {
      return {
        title: document.title,
        url: location.href,
        elementCount: document.querySelectorAll('*').length,
        hasCharts: document.querySelectorAll('svg, canvas, .recharts-wrapper').length > 0,
        hasInteractiveElements: document.querySelectorAll('button, select, input').length > 0,
        hasLoadingStates: document.querySelectorAll('*[class*="loading"], *[aria-busy="true"]').length > 0,
        hasErrors: document.querySelectorAll('*[class*="error"], *[role="alert"]').length > 0,
        trendsContent: document.body.innerText.toLowerCase().includes('trends'),
        legislativeContent: document.body.innerText.toLowerCase().includes('legislative'),
        bipartisanContent: document.body.innerText.toLowerCase().includes('bipartisan'),
        votingContent: document.body.innerText.toLowerCase().includes('voting')
      };
    });

    console.log('📊 Page Analysis Results:');
    Object.entries(pageAnalysis).forEach(([key, value]) => {
      const icon = typeof value === 'boolean' ? (value ? '✅' : '❌') : '📄';
      console.log(`  ${icon} ${key}: ${value}`);
    });

  } catch (error) {
    console.error('❌ Test failed with error:', error.message);
    await page.screenshot({ path: 'error-screenshot.png' });
  } finally {
    console.log('\n🏁 Testing completed. Check the generated screenshots for visual validation.');
    await browser.close();
  }
}

// Run the comprehensive test
comprehensiveTrendsTabTest().catch(console.error);