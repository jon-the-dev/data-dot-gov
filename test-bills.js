const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // Collect console messages
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('BROWSER ERROR:', msg.text());
    }
  });

  page.on('pageerror', error => {
    console.error('PAGE ERROR:', error.message);
  });

  try {
    console.log('Loading bills page...');
    await page.goto('https://congress.local.team-skynet.io/bills', { waitUntil: 'networkidle' });

    // Wait a bit more for React to render
    await page.waitForTimeout(3000);

    // Check for main elements
    const checks = await page.evaluate(() => {
      return {
        hasHeader: document.querySelector('h2') !== null,
        headerText: document.querySelector('h2')?.textContent || 'Not found',
        statCardCount: document.querySelectorAll('.bg-white.p-6.rounded-lg').length,
        hasCharts: document.querySelector('svg') !== null,
        hasSelects: document.querySelectorAll('select').length,
        bodyText: document.body.innerText.substring(0, 500)
      };
    });

    console.log('\nPage Analysis:');
    console.log('Header found:', checks.hasHeader);
    console.log('Header text:', checks.headerText);
    console.log('Stat cards found:', checks.statCardCount);
    console.log('Charts (SVG) found:', checks.hasCharts);
    console.log('Select elements:', checks.hasSelects);
    console.log('\nBody content preview:');
    console.log(checks.bodyText);

    // Test filtering functionality
    if (checks.hasSelects > 0) {
      console.log('\nTesting status filter...');
      const statusSelect = await page.locator('select').nth(1);
      if (await statusSelect.count() > 0) {
        await statusSelect.selectOption('Enacted');
        await page.waitForTimeout(1000);

        const filteredCount = await page.evaluate(() => {
          const resultText = document.body.innerText;
          const match = resultText.match(/Found (\d+) bills/);
          return match ? match[1] : 'unknown';
        });

        console.log('Filtered bills count (Enacted):', filteredCount);
      }
    }

    await page.screenshot({ path: 'bills-dashboard-final.png' });
    console.log('\nScreenshot saved as bills-dashboard-final.png');

  } catch (error) {
    console.error('Test Error:', error.message);
  }

  await browser.close();
})();