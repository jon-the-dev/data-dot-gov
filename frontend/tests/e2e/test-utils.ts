import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';

export class TestUtils {
  static async waitForNetworkIdle(page: Page, timeout = 30000) {
    await page.waitForLoadState('networkidle', { timeout });
  }

  static async takeElementScreenshot(
    page: Page,
    selector: string,
    filename: string
  ) {
    const element = page.locator(selector);
    if ((await element.count()) > 0) {
      await element.screenshot({ path: `tests/screenshots/${filename}.png` });
    }
  }

  static async checkForConsoleErrors(page: Page): Promise<string[]> {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    page.on('pageerror', error => {
      errors.push(error.message);
    });

    return errors;
  }

  static async verifyDataTableStructure(page: Page, tableSelector: string) {
    const table = page.locator(tableSelector);

    if ((await table.count()) > 0) {
      await expect(table).toBeVisible();

      // Check for table headers
      const headers = table.locator('thead th, th');
      const headerCount = await headers.count();

      // Check for table rows
      const rows = table.locator('tbody tr, tr');
      const rowCount = await rows.count();

      return { headers: headerCount, rows: rowCount };
    }

    return { headers: 0, rows: 0 };
  }

  static async verifyChartElements(page: Page, chartSelector: string) {
    const chart = page.locator(chartSelector);

    if ((await chart.count()) > 0) {
      await expect(chart).toBeVisible();

      // Check for SVG elements (Recharts)
      const svg = chart.locator('svg');
      const svgCount = await svg.count();

      // Check for chart data elements
      const dataElements = chart.locator('rect, circle, path, line');
      const dataCount = await dataElements.count();

      return { svg: svgCount, dataElements: dataCount };
    }

    return { svg: 0, dataElements: 0 };
  }

  static async testResponsiveBreakpoints(
    page: Page,
    testFn: () => Promise<void>
  ) {
    const breakpoints = [
      { width: 1920, height: 1080, name: 'desktop-xl' },
      { width: 1440, height: 900, name: 'desktop-lg' },
      { width: 1024, height: 768, name: 'tablet-landscape' },
      { width: 768, height: 1024, name: 'tablet-portrait' },
      { width: 375, height: 812, name: 'mobile-ios' },
      { width: 360, height: 640, name: 'mobile-android' },
    ];

    for (const breakpoint of breakpoints) {
      await page.setViewportSize({
        width: breakpoint.width,
        height: breakpoint.height,
      });

      await page.waitForTimeout(300); // Allow for responsive changes

      // Testing at viewport: ${breakpoint.name} - ${breakpoint.width}x${breakpoint.height}

      await testFn();
    }

    // Reset to desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
  }

  static async verifyAccessibilityAttributes(page: Page) {
    // Check for essential accessibility attributes
    const results = {
      ariaLabels: await page.locator('[aria-label]').count(),
      ariaRoles: await page.locator('[role]').count(),
      headings: await page.locator('h1, h2, h3, h4, h5, h6').count(),
      altTexts: await page.locator('img[alt]').count(),
      formLabels: await page.locator('label').count(),
      buttons: await page.locator('button').count(),
      links: await page.locator('a').count(),
    };

    return results;
  }

  static async simulateSlowNetwork(page: Page) {
    // Simulate slow 3G network
    await page.route('**/*', async route => {
      await new Promise(resolve => setTimeout(resolve, 300)); // 300ms delay
      await route.continue();
    });
  }

  static async simulateNetworkFailure(
    page: Page,
    patterns: string[] = ['**/api/**']
  ) {
    for (const pattern of patterns) {
      await page.route(pattern, route => route.abort());
    }
  }

  static async measurePageLoadTime(page: Page, url: string): Promise<number> {
    const startTime = Date.now();
    await page.goto(url);
    await page.waitForLoadState('networkidle');
    const endTime = Date.now();

    return endTime - startTime;
  }

  static async verifyFormValidation(page: Page, formSelector: string) {
    const form = page.locator(formSelector);

    if ((await form.count()) > 0) {
      // Check for required fields
      const requiredFields = form.locator(
        'input[required], select[required], textarea[required]'
      );
      const requiredCount = await requiredFields.count();

      // Check for validation messages
      const validationMessages = form.locator(
        '.error, .invalid, [role="alert"]'
      );
      const messageCount = await validationMessages.count();

      return {
        requiredFields: requiredCount,
        validationMessages: messageCount,
      };
    }

    return { requiredFields: 0, validationMessages: 0 };
  }

  static async testKeyboardNavigation(page: Page, startSelector?: string) {
    if (startSelector) {
      await page.locator(startSelector).first().focus();
    }

    // Tab through focusable elements
    const focusableElements = [];

    for (let i = 0; i < 10; i++) {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(100);

      const focusedElement = page.locator(':focus');
      if ((await focusedElement.count()) > 0) {
        const tagName = await focusedElement.evaluate(el => el.tagName);
        focusableElements.push(tagName);
      }
    }

    return focusableElements;
  }

  static async verifyLoadingStates(page: Page) {
    // Check for common loading indicators
    const loadingSelectors = [
      '.loading',
      '.spinner',
      '.animate-spin',
      '[data-testid="loading"]',
      '[aria-label*="loading"]',
    ];

    const loadingIndicators = [];

    for (const selector of loadingSelectors) {
      const count = await page.locator(selector).count();
      if (count > 0) {
        loadingIndicators.push({ selector, count });
      }
    }

    return loadingIndicators;
  }

  static async checkDataAttributes(page: Page, selector: string) {
    const element = page.locator(selector);

    if ((await element.count()) > 0) {
      const attributes = await element.evaluate(el => {
        const attrs: { [key: string]: string } = {};
        for (const attr of el.attributes) {
          if (attr.name.startsWith('data-')) {
            attrs[attr.name] = attr.value;
          }
        }
        return attrs;
      });

      return attributes;
    }

    return {};
  }

  static generateTestData() {
    return {
      members: [
        { name: 'John Smith', party: 'Republican', state: 'TX' },
        { name: 'Jane Doe', party: 'Democratic', state: 'CA' },
        { name: 'Bob Johnson', party: 'Independent', state: 'VT' },
      ],
      bills: [
        {
          number: 'H.R. 1234',
          title: 'Infrastructure Investment Act',
          status: 'Passed',
        },
        {
          number: 'S. 5678',
          title: 'Healthcare Reform Bill',
          status: 'In Committee',
        },
        {
          number: 'H.R. 9999',
          title: 'Climate Action Plan',
          status: 'Introduced',
        },
      ],
      votes: [
        {
          rollCall: 123,
          question: 'On Passage of H.R. 1234',
          result: 'Passed',
        },
        {
          rollCall: 456,
          question: 'On Motion to Table S. 5678',
          result: 'Failed',
        },
        {
          rollCall: 789,
          question: 'On Amendment to H.R. 9999',
          result: 'Agreed to',
        },
      ],
    };
  }

  static async validateDataFormat(data: any, expectedFields: string[]) {
    if (!data || typeof data !== 'object') {
      return { valid: false, errors: ['Data is not an object'] };
    }

    const errors = [];
    const missingFields = expectedFields.filter(field => !(field in data));

    if (missingFields.length > 0) {
      errors.push(`Missing fields: ${missingFields.join(', ')}`);
    }

    return { valid: errors.length === 0, errors };
  }

  static async waitForElementToBeStable(
    page: Page,
    selector: string,
    timeout = 5000
  ) {
    const element = page.locator(selector);

    // Wait for element to exist
    await element.waitFor({ timeout });

    // Wait for element to be stable (not moving)
    let previousBoundingBox = await element.boundingBox();

    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
      await page.waitForTimeout(100);
      const currentBoundingBox = await element.boundingBox();

      if (previousBoundingBox && currentBoundingBox) {
        const isStable =
          Math.abs(previousBoundingBox.x - currentBoundingBox.x) < 1 &&
          Math.abs(previousBoundingBox.y - currentBoundingBox.y) < 1;

        if (isStable) {
          return;
        }
      }

      previousBoundingBox = currentBoundingBox;
    }
  }
}
