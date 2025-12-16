const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    await page.goto('https://congress.local.team-skynet.io');
    await page.waitForLoadState('networkidle');

    console.log('Main page loaded. Looking for navigation...');

    // Find all navigation links
    const navLinks = await page.locator('nav a, a').evaluateAll(links =>
      links.map(link => ({
        text: link.textContent?.trim(),
        href: link.href
      })).filter(link => link.text && link.text.length > 0)
    );

    console.log('Navigation links found:', navLinks);

    // Navigate to each major section and look for Party Comparison
    const sections = ['Members', 'Bills Analysis', 'Dashboard'];

    for (const section of sections) {
      const link = page.locator('a').filter({ hasText: section }).first();
      if (await link.count() > 0) {
        console.log(`\n📍 Navigating to ${section}...`);
        await link.click();
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);

        // Take a screenshot
        await page.screenshot({ path: `debug-${section.toLowerCase().replace(' ', '-')}.png` });

        // Look for Party Comparison related content
        const partyContent = await page.evaluate(() => {
          const elements = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6,button,a'));
          return elements
            .map(el => el.textContent?.trim())
            .filter(text => text && (
              text.toLowerCase().includes('party') ||
              text.toLowerCase().includes('comparison') ||
              text.toLowerCase().includes('trends') ||
              text.toLowerCase().includes('voting')
            ))
            .slice(0, 10); // Limit results
        });

        console.log(`Party/Comparison content in ${section}:`, partyContent);

        // Look for tabs specifically
        const tabs = await page.locator('button').evaluateAll(buttons =>
          buttons
            .map(btn => btn.textContent?.trim())
            .filter(text => text && (
              text.toLowerCase().includes('trends') ||
              text.toLowerCase().includes('overview') ||
              text.toLowerCase().includes('voting')
            ))
        );

        console.log(`Tabs found in ${section}:`, tabs);

        // If we find trends tab, try to click it
        const trendsTab = page.locator('button').filter({ hasText: /trends/i }).first();
        if (await trendsTab.count() > 0) {
          console.log(`✅ Found Trends tab in ${section}! Clicking...`);
          await trendsTab.click();
          await page.waitForTimeout(3000);
          await page.screenshot({ path: `trends-found-in-${section.toLowerCase().replace(' ', '-')}.png` });
          break;
        }
      }
    }

  } catch (error) {
    console.error('Error:', error.message);
    await page.screenshot({ path: 'debug-navigation-error.png' });
  }

  await browser.close();
})();