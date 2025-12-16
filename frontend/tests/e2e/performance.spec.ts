import { test, expect } from '@playwright/test';

import { BasePage } from './page-objects/BasePage';
import { TestUtils } from './test-utils';

test.describe('Performance Tests', () => {
  test('Core Web Vitals measurement', async ({ page }) => {
    const basePage = new BasePage(page);

    // Navigate to dashboard
    await basePage.goto('/');

    // Measure Core Web Vitals
    const _vitals = await page.evaluate(
      () =>
        new Promise(resolve => {
          const observer = new PerformanceObserver(list => {
            const entries = list.getEntries();
            const vitals: { [key: string]: number } = {};

            entries.forEach(entry => {
              if (entry.entryType === 'paint') {
                vitals[entry.name] = entry.startTime;
              }
              if (entry.entryType === 'navigation') {
                const navEntry = entry as PerformanceNavigationTiming;
                vitals.domContentLoaded =
                  navEntry.domContentLoadedEventEnd -
                  navEntry.domContentLoadedEventStart;
                vitals.loadComplete =
                  navEntry.loadEventEnd - navEntry.loadEventStart;
              }
            });

            resolve(vitals);
          });

          observer.observe({ entryTypes: ['paint', 'navigation'] });

          // Fallback timeout
          setTimeout(() => resolve({}), 5000);
        })
    );

    // Core Web Vitals metrics collected

    // Basic performance assertions
    const loadTime = await TestUtils.measurePageLoadTime(page, '/');
    expect(loadTime).toBeLessThan(5000); // 5 seconds max
  });

  test('Page load times across sections', async ({ page }) => {
    const _basePage = new BasePage(page);
    const sections = [
      { path: '/', name: 'Dashboard' },
      { path: '/members', name: 'Members' },
      { path: '/bills', name: 'Bills' },
      { path: '/votes', name: 'Votes' },
    ];

    const loadTimes: { [key: string]: number } = {};

    for (const section of sections) {
      const loadTime = await TestUtils.measurePageLoadTime(page, section.path);
      loadTimes[section.name] = loadTime;

      console.log(`${section.name} load time: ${loadTime}ms`);

      // Each page should load within 5 seconds
      expect(loadTime).toBeLessThan(5000);
    }

    // Dashboard should be fastest (likely has cached data)
    expect(loadTimes.Dashboard).toBeLessThan(3000);
  });

  test('Memory usage during navigation', async ({ page }) => {
    const basePage = new BasePage(page);

    // Measure memory before navigation
    const initialMemory = await page.evaluate(
      () => (performance as any).memory?.usedJSHeapSize || 0
    );

    const sections = ['/', '/members', '/bills', '/votes', '/'];

    for (const section of sections) {
      await basePage.goto(section);
      await basePage.waitForPageLoad();

      const currentMemory = await page.evaluate(
        () => (performance as any).memory?.usedJSHeapSize || 0
      );

      console.log(
        `Memory usage at ${section}: ${(currentMemory / 1024 / 1024).toFixed(2)} MB`
      );

      // Force garbage collection if available
      await page.evaluate(() => {
        if ((window as any).gc) {
          (window as any).gc();
        }
      });
    }

    const finalMemory = await page.evaluate(
      () => (performance as any).memory?.usedJSHeapSize || 0
    );

    // Memory should not grow excessively
    const memoryGrowth = finalMemory - initialMemory;
    console.log(
      `Total memory growth: ${(memoryGrowth / 1024 / 1024).toFixed(2)} MB`
    );

    // Allow for some memory growth but not excessive
    expect(memoryGrowth).toBeLessThan(50 * 1024 * 1024); // 50MB max growth
  });

  test('Chart rendering performance', async ({ page }) => {
    const basePage = new BasePage(page);
    await basePage.goto('/');

    // Find charts and measure rendering time
    const charts = await page.locator('.recharts-wrapper, svg, canvas').all();

    for (let i = 0; i < Math.min(3, charts.length); i++) {
      const chart = charts[i];

      if (await chart.isVisible()) {
        const startTime = Date.now();

        // Wait for chart to be fully rendered
        await TestUtils.waitForElementToBeStable(
          page,
          '.recharts-wrapper, svg',
          5000
        );

        const renderTime = Date.now() - startTime;
        console.log(`Chart ${i + 1} render time: ${renderTime}ms`);

        // Charts should render within 3 seconds
        expect(renderTime).toBeLessThan(3000);
      }
    }
  });

  test('Large dataset handling', async ({ page }) => {
    const basePage = new BasePage(page);
    await basePage.goto('/members');

    // Measure time to render member list
    const startTime = Date.now();
    await basePage.waitForPageLoad();

    const renderTime = Date.now() - startTime;
    console.log(`Members list render time: ${renderTime}ms`);

    // Test scrolling performance
    const scrollStartTime = Date.now();

    await page.evaluate(() => {
      window.scrollTo(0, document.body.scrollHeight);
    });

    await page.waitForTimeout(500);

    const scrollTime = Date.now() - scrollStartTime;
    console.log(`Scroll to bottom time: ${scrollTime}ms`);

    // Scrolling should be smooth
    expect(scrollTime).toBeLessThan(1000);

    // Test scroll back to top
    await page.evaluate(() => {
      window.scrollTo(0, 0);
    });

    await page.waitForTimeout(500);

    // Page should remain responsive after scrolling
    await expect(page.locator('main')).toBeVisible();
  });

  test('Bundle size impact', async ({ page }) => {
    const basePage = new BasePage(page);

    // Measure network traffic
    let totalBytes = 0;
    let jsBytes = 0;
    let cssBytes = 0;

    page.on('response', async response => {
      const url = response.url();
      const contentLength = parseInt(
        response.headers()['content-length'] || '0',
        10
      );

      if (contentLength > 0) {
        totalBytes += contentLength;

        if (url.endsWith('.js') || url.includes('.js?')) {
          jsBytes += contentLength;
        }
        if (url.endsWith('.css') || url.includes('.css?')) {
          cssBytes += contentLength;
        }
      }
    });

    await basePage.goto('/');
    await basePage.waitForPageLoad();

    console.log(`Total bytes downloaded: ${(totalBytes / 1024).toFixed(2)} KB`);
    console.log(`JavaScript bytes: ${(jsBytes / 1024).toFixed(2)} KB`);
    console.log(`CSS bytes: ${(cssBytes / 1024).toFixed(2)} KB`);

    // Bundle size should be reasonable
    expect(jsBytes).toBeLessThan(2 * 1024 * 1024); // 2MB max for JS
    expect(cssBytes).toBeLessThan(500 * 1024); // 500KB max for CSS
  });

  test('Image loading performance', async ({ page }) => {
    const basePage = new BasePage(page);
    await basePage.goto('/');

    // Find all images
    const images = await page.locator('img').all();
    let loadedImages = 0;
    let failedImages = 0;

    for (const img of images) {
      if (await img.isVisible()) {
        const isLoaded = await img.evaluate(
          (el: HTMLImageElement) => el.complete && el.naturalHeight !== 0
        );

        if (isLoaded) {
          loadedImages++;
        } else {
          failedImages++;
        }
      }
    }

    console.log(`Images loaded: ${loadedImages}, failed: ${failedImages}`);

    // Most images should load successfully
    if (loadedImages + failedImages > 0) {
      const successRate = loadedImages / (loadedImages + failedImages);
      expect(successRate).toBeGreaterThan(0.8); // 80% success rate
    }
  });

  test('API response times', async ({ page }) => {
    const basePage = new BasePage(page);

    const apiTimes: { [key: string]: number } = {};

    page.on('response', async response => {
      const url = response.url();

      if (url.includes('/api/') || url.includes('data/')) {
        const startTime =
          (response.request() as any).timing?.startTime || Date.now();
        const endTime = Date.now();
        const responseTime = endTime - startTime;

        apiTimes[url] = responseTime;
        console.log(`API response time for ${url}: ${responseTime}ms`);
      }
    });

    await basePage.goto('/');
    await basePage.waitForPageLoad();

    // Navigate to different sections to trigger API calls
    await basePage.goto('/members');
    await basePage.waitForPageLoad();

    await basePage.goto('/bills');
    await basePage.waitForPageLoad();

    // Check API response times
    Object.entries(apiTimes).forEach(([url, time]) => {
      // API calls should complete within 5 seconds
      expect(time).toBeLessThan(5000);
    });
  });

  test('Rendering performance under load', async ({ page }) => {
    const basePage = new BasePage(page);

    // Simulate high CPU load by rapidly updating the page
    await basePage.goto('/');

    const startTime = Date.now();

    // Rapid navigation to stress test
    for (let i = 0; i < 5; i++) {
      await basePage.goto('/members');
      await page.waitForTimeout(100);
      await basePage.goto('/bills');
      await page.waitForTimeout(100);
      await basePage.goto('/');
      await page.waitForTimeout(100);
    }

    const totalTime = Date.now() - startTime;
    console.log(`Rapid navigation completed in: ${totalTime}ms`);

    // Should handle rapid navigation gracefully
    expect(totalTime).toBeLessThan(10000); // 10 seconds for all navigation

    // Page should still be responsive
    await expect(page.locator('main')).toBeVisible();
  });

  test('Viewport resize performance', async ({ page }) => {
    const basePage = new BasePage(page);
    await basePage.goto('/');

    const viewports = [
      { width: 1920, height: 1080 },
      { width: 768, height: 1024 },
      { width: 375, height: 812 },
      { width: 1440, height: 900 },
    ];

    for (const viewport of viewports) {
      const startTime = Date.now();

      await page.setViewportSize(viewport);
      await page.waitForTimeout(300); // Allow for responsive changes

      const resizeTime = Date.now() - startTime;
      console.log(
        `Resize to ${viewport.width}x${viewport.height}: ${resizeTime}ms`
      );

      // Viewport changes should be fast
      expect(resizeTime).toBeLessThan(1000);

      // Content should remain visible
      await expect(page.locator('main')).toBeVisible();
    }
  });

  test('Font and asset loading', async ({ page }) => {
    const basePage = new BasePage(page);

    let fontBytes = 0;
    let fontRequests = 0;

    page.on('response', async response => {
      const url = response.url();

      if (
        url.includes('.woff') ||
        url.includes('.woff2') ||
        url.includes('fonts')
      ) {
        fontRequests++;
        const contentLength = parseInt(
          response.headers()['content-length'] || '0',
          10
        );
        fontBytes += contentLength;
      }
    });

    await basePage.goto('/');
    await basePage.waitForPageLoad();

    console.log(`Font requests: ${fontRequests}`);
    console.log(`Font bytes: ${(fontBytes / 1024).toFixed(2)} KB`);

    // Font loading should be efficient
    expect(fontRequests).toBeLessThan(10); // Not too many font files
    expect(fontBytes).toBeLessThan(1024 * 1024); // 1MB max for fonts
  });
});
