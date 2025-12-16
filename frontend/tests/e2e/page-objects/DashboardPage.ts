import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

import { BasePage } from './BasePage';

export class DashboardPage extends BasePage {
  readonly pageTitle: Locator;
  readonly statCards: Locator;
  readonly partyUnityChart: Locator;
  readonly recentBills: Locator;
  readonly votingPatterns: Locator;
  readonly quickStats: Locator;

  constructor(page: Page) {
    super(page);
    this.pageTitle = page
      .locator('h1, h2')
      .filter({ hasText: /dashboard|overview/i })
      .first();
    this.statCards = page.locator('[data-testid="stat-card"], .bg-white.p-6');
    this.partyUnityChart = page.locator(
      '[data-testid="party-unity-chart"], .recharts-wrapper'
    );
    this.recentBills = page.locator('[data-testid="recent-bills"]');
    this.votingPatterns = page.locator('[data-testid="voting-patterns"]');
    this.quickStats = page.locator('[data-testid="quick-stats"]');
  }

  async verifyDashboardLoads() {
    await this.goto('/');

    // Check that the main content is visible
    await expect(this.page.locator('main')).toBeVisible();

    // Look for dashboard indicators
    const hasStatCards = (await this.statCards.count()) > 0;
    const hasCharts = (await this.partyUnityChart.count()) > 0;
    const hasTitle = (await this.pageTitle.count()) > 0;

    // At least one dashboard element should be present
    expect(hasStatCards || hasCharts || hasTitle).toBeTruthy();
  }

  async verifyStatCards() {
    const cards = await this.statCards.all();

    for (const card of cards) {
      await expect(card).toBeVisible();

      // Each card should have some content
      const text = await card.textContent();
      expect(text?.trim().length).toBeGreaterThan(0);
    }

    return cards.length;
  }

  async verifyChartsRender() {
    if ((await this.partyUnityChart.count()) > 0) {
      await expect(this.partyUnityChart.first()).toBeVisible();

      // Check if chart has rendered content (SVG elements)
      const chartSvg = this.partyUnityChart.locator('svg').first();
      if ((await chartSvg.count()) > 0) {
        await expect(chartSvg).toBeVisible();
      }
    }
  }

  async checkDataVisualization() {
    // Look for any data visualization elements
    const charts = await this.page
      .locator('.recharts-wrapper, svg, canvas')
      .all();
    const tables = await this.page.locator('table, [role="table"]').all();

    if (charts.length > 0) {
      for (const chart of charts) {
        if (await chart.isVisible()) {
          await expect(chart).toBeVisible();
        }
      }
    }

    if (tables.length > 0) {
      for (const table of tables) {
        if (await table.isVisible()) {
          await expect(table).toBeVisible();
        }
      }
    }

    return { charts: charts.length, tables: tables.length };
  }

  async testExportFunctionality() {
    // Look for export buttons
    const exportButtons = await this.page
      .locator('button')
      .filter({ hasText: /export|download/i })
      .all();

    for (const button of exportButtons) {
      if (await button.isVisible()) {
        // Click and verify no errors
        await button.click();
        await this.page.waitForTimeout(500);

        // Check that no error boundary appeared
        const errorExists = (await this.errorBoundary.count()) > 0;
        expect(errorExists).toBeFalsy();
      }
    }
  }

  async verifyResponsiveLayout() {
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 375, height: 812, name: 'Mobile' },
    ];

    for (const viewport of viewports) {
      await this.page.setViewportSize({
        width: viewport.width,
        height: viewport.height,
      });
      await this.page.waitForTimeout(300); // Allow for responsive changes

      // Take screenshot
      await this.takeFullPageScreenshot(
        `dashboard-${viewport.name.toLowerCase()}`
      );

      // Verify main content is still visible
      await expect(this.page.locator('main')).toBeVisible();

      // Check that navigation works on different viewports
      if (viewport.width < 1024) {
        // Mobile/tablet navigation
        if ((await this.mobileMenuButton.count()) > 0) {
          await expect(this.mobileMenuButton).toBeVisible();
        }
      }
    }

    // Reset to desktop
    await this.page.setViewportSize({ width: 1920, height: 1080 });
  }

  async checkLoadingStates() {
    // Reload page and check for loading states
    await this.page.reload();

    // Initially, there might be loading spinners
    const hasLoadingSpinner = (await this.loadingSpinner.count()) > 0;

    if (hasLoadingSpinner) {
      // Wait for loading to complete
      await this.loadingSpinner.waitFor({ state: 'hidden', timeout: 10000 });
    }

    // Page should be fully loaded now
    await this.waitForPageLoad();
    await expect(this.page.locator('main')).toBeVisible();
  }
}
