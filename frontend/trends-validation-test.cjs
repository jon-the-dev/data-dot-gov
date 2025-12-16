const { chromium } = require('playwright');

async function validateTrendsImplementation() {
  console.log('🚀 Starting Focused Trends Tab Validation...\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 300
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  try {
    console.log('📍 Step 1: Navigate to Congressional Transparency Platform');
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    console.log('📍 Step 2: Navigate to Party Comparison page directly');
    // Try to navigate using React Router
    await page.goto('http://localhost:5173/party-comparison');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Check current page content
    let pageContent = await page.evaluate(() => ({
      url: location.href,
      title: document.title,
      hasPartyComparison: document.body.innerText.toLowerCase().includes('party comparison analysis'),
      hasTabButtons: document.querySelectorAll('button').length > 0,
      allButtonTexts: Array.from(document.querySelectorAll('button')).map(btn => btn.textContent?.trim()).filter(text => text)
    }));

    console.log(`Current URL: ${pageContent.url}`);
    console.log(`Has Party Comparison content: ${pageContent.hasPartyComparison ? '✅' : '❌'}`);
    console.log(`Button count: ${pageContent.hasTabButtons ? pageContent.allButtonTexts.length : 0}`);

    // If not on party comparison page, try clicking the navigation link
    if (!pageContent.hasPartyComparison) {
      console.log('📍 Step 2b: Clicking Party Comparison in navigation');
      await page.goto('http://localhost:5173');
      await page.waitForTimeout(2000);

      const partyCompButton = await page.locator('text="Party Comparison"').first();
      if (await partyCompButton.count() > 0) {
        await partyCompButton.click();
        await page.waitForTimeout(3000);
      }
    }

    console.log('📍 Step 3: Look for View Selector Tabs');
    await page.screenshot({ path: 'trends-validation-before-tab-click.png', fullPage: true });

    // Look for the tab buttons specifically
    const tabButtons = await page.locator('button:has-text("Trends"), button:has-text("trends")').all();
    console.log(`Found ${tabButtons.length} Trends tab buttons`);

    if (tabButtons.length > 0) {
      console.log('✅ Trends tab button found! Clicking...');
      await tabButtons[0].click();
      await page.waitForTimeout(5000); // Wait for trend data to load

      console.log('📍 Step 4: Validate Trends Tab Content');
      await page.screenshot({ path: 'trends-validation-after-tab-click.png', fullPage: true });

      // Check for the three main sections
      const trendsValidation = await page.evaluate(() => {
        const bodyText = document.body.innerText.toLowerCase();
        return {
          hasLegislativeActivity: bodyText.includes('legislative activity'),
          hasBipartisanCooperation: bodyText.includes('bipartisan cooperation'),
          hasVotingConsistency: bodyText.includes('voting consistency') || bodyText.includes('party unity'),
          hasLoadingState: bodyText.includes('loading trend analysis'),
          hasErrorState: bodyText.includes('error loading trend data'),
          hasDataNotAvailable: bodyText.includes('trend analysis data is not available') || bodyText.includes('data not available'),
          hasCharts: document.querySelectorAll('svg, canvas, .recharts-wrapper').length,
          hasTrendSpecificContent: bodyText.includes('monthly') || bodyText.includes('bridge builders') || bodyText.includes('maverick'),
          trendsTabActive: Array.from(document.querySelectorAll('button')).some(btn =>
            btn.textContent?.toLowerCase().includes('trends') &&
            (btn.classList.contains('bg-white') || btn.classList.contains('text-blue-600'))
          )
        };
      });

      console.log('\n🔍 TRENDS CONTENT VALIDATION:');
      console.log(`✅ Trends tab active: ${trendsValidation.trendsTabActive}`);
      console.log(`📊 Legislative Activity section: ${trendsValidation.hasLegislativeActivity ? '✅' : '❌'}`);
      console.log(`🤝 Bipartisan Cooperation section: ${trendsValidation.hasBipartisanCooperation ? '✅' : '❌'}`);
      console.log(`🎯 Voting Consistency section: ${trendsValidation.hasVotingConsistency ? '✅' : '❌'}`);
      console.log(`📈 Charts found: ${trendsValidation.hasCharts}`);
      console.log(`🔄 Loading state: ${trendsValidation.hasLoadingState ? '⏳' : '⏭'}`);
      console.log(`❌ Error state: ${trendsValidation.hasErrorState ? '🔴' : '✅'}`);
      console.log(`📭 Data not available: ${trendsValidation.hasDataNotAvailable ? '⚠️' : '✅'}`);
      console.log(`📊 Trend-specific content: ${trendsValidation.hasTrendSpecificContent ? '✅' : '❌'}`);

      // Take screenshots of specific sections if they exist
      const sections = await page.locator('div:has-text("Legislative Activity"), div:has-text("Bipartisan Cooperation"), div:has-text("Voting Consistency")').all();
      console.log(`\nFound ${sections.length} trend sections to capture`);

      for (let i = 0; i < sections.length; i++) {
        try {
          const sectionText = await sections[i].textContent();
          const sectionName = sectionText?.substring(0, 30).replace(/[^a-zA-Z0-9]/g, '') || `section${i}`;
          await sections[i].screenshot({ path: `trends-section-${sectionName}.png` });
          console.log(`📸 Captured: trends-section-${sectionName}.png`);
        } catch (error) {
          console.log(`⚠️ Could not capture section ${i}: ${error.message}`);
        }
      }

      return {
        success: true,
        trendsTabFound: true,
        ...trendsValidation
      };

    } else {
      // Look for any tabs at all
      const allButtons = await page.locator('button').all();
      console.log('\nAll buttons found:');
      for (let i = 0; i < Math.min(allButtons.length, 10); i++) {
        const buttonText = await allButtons[i].textContent();
        console.log(`  Button ${i}: "${buttonText}"`);
      }

      return {
        success: false,
        trendsTabFound: false,
        error: 'Trends tab button not found'
      };
    }

  } catch (error) {
    console.error('❌ Validation failed:', error.message);
    await page.screenshot({ path: 'trends-validation-error.png' });
    return {
      success: false,
      error: error.message
    };
  } finally {
    await browser.close();
    console.log('\n🏁 Trends validation completed.');
  }
}

// Run the validation
validateTrendsImplementation()
  .then(result => {
    console.log('\n📋 FINAL VALIDATION RESULT:');
    console.log(JSON.stringify(result, null, 2));
    process.exit(result.success ? 0 : 1);
  })
  .catch(error => {
    console.error('\n💥 Validation crashed:', error);
    process.exit(1);
  });