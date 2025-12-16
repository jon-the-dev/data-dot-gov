import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

export class BasePage {
  readonly page: Page;
  readonly header: Locator;
  readonly navigation: Locator;
  readonly mobileMenuButton: Locator;
  readonly loadingSpinner: Locator;
  readonly errorBoundary: Locator;
  readonly exportButton: Locator;
  readonly searchButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.header = page.locator('header');
    this.navigation = page.locator('nav');
    this.mobileMenuButton = page.getByRole('button', { name: /menu/i });
    this.loadingSpinner = page.locator('.animate-spin');
    this.errorBoundary = page.locator('.bg-red-50');
    this.exportButton = page.getByRole('button', { name: /export data/i });
    this.searchButton = page.getByRole('button', { name: /search/i });
  }

  async goto(path = '/') {
    await this.page.goto(path);
    await this.waitForPageLoad();
  }

  async waitForPageLoad() {
    // Wait for navigation to complete
    await this.page.waitForLoadState('networkidle');

    // Wait for any loading spinners to disappear
    try {
      await this.loadingSpinner.waitFor({ state: 'hidden', timeout: 10000 });
    } catch {
      // Loading spinner might not exist, that's ok
    }
  }

  async takeFullPageScreenshot(name: string) {
    await this.page.screenshot({
      path: `tests/screenshots/${name}.png`,
      fullPage: true,
    });
  }

  async checkNoConsoleErrors() {
    const errors: string[] = [];

    const consoleHandler = (msg: any) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    };

    const pageErrorHandler = (error: Error) => {
      errors.push(error.message);
    };

    this.page.on('console', consoleHandler);
    this.page.on('pageerror', pageErrorHandler);

    return errors;
  }

  async navigateToSection(section: string) {
    const navigationLinks = {
      dashboard: '/',
      members: '/members',
      'member-search': '/members/search',
      bills: '/bills',
      'bill-categories': '/bills/categories',
      votes: '/votes',
      lobbying: '/lobbying',
      'party-comparison': '/party-comparison',
    };

    const path = navigationLinks[section as keyof typeof navigationLinks];
    if (!path) {
      throw new Error(`Unknown section: ${section}`);
    }

    await this.page.goto(path);
    await this.waitForPageLoad();
  }

  async testMobileNavigation() {
    // Test mobile menu functionality
    await this.page.setViewportSize({ width: 375, height: 812 });

    // Menu should be closed initially
    await expect(this.mobileMenuButton).toBeVisible();

    // Open menu
    await this.mobileMenuButton.click();
    await this.page.waitForTimeout(300); // Animation

    // Menu should be open
    await expect(this.page.locator('.lg\\:hidden .border-t')).toBeVisible();

    // Test navigation link
    await this.page
      .getByRole('link', { name: /dashboard/i })
      .first()
      .click();
    await this.waitForPageLoad();

    // Reset viewport
    await this.page.setViewportSize({ width: 1920, height: 1080 });
  }

  async checkAccessibility() {
    // Check for basic accessibility attributes
    const headerElements = await this.page
      .locator('h1, h2, h3, h4, h5, h6')
      .all();
    for (const header of headerElements) {
      await expect(header).toBeVisible();
    }

    // Check navigation has proper roles
    await expect(this.navigation).toHaveAttribute('role', 'navigation');

    // Check buttons have accessible names
    const buttons = await this.page.locator('button').all();
    for (const button of buttons) {
      if (await button.isVisible()) {
        const ariaLabel = await button.getAttribute('aria-label');
        const text = await button.textContent();
        expect(ariaLabel || text).toBeTruthy();
      }
    }
  }

  async testKeyboardNavigation() {
    // Test tab navigation through interactive elements
    await this.page.keyboard.press('Tab');
    await this.page.waitForTimeout(100);

    // Verify focus is visible (should have focus styles)
    const focusedElement = await this.page.locator(':focus').first();
    await expect(focusedElement).toBeVisible();
  }

  async checkPerformance() {
    const startTime = Date.now();
    await this.page.reload();
    await this.waitForPageLoad();
    const loadTime = Date.now() - startTime;

    // Basic performance check - page should load in under 5 seconds
    expect(loadTime).toBeLessThan(5000);

    return loadTime;
  }
}
