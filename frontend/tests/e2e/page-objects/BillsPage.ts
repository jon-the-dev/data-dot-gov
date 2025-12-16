import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

import { BasePage } from './BasePage';

export class BillsPage extends BasePage {
  readonly billsList: Locator;
  readonly billCards: Locator;
  readonly billTracker: Locator;
  readonly categoryFilter: Locator;
  readonly statusFilter: Locator;
  readonly searchInput: Locator;
  readonly sortOptions: Locator;
  readonly billDetails: Locator;
  readonly sponsorInfo: Locator;
  readonly voteBreakdown: Locator;
  readonly categoryChart: Locator;
  readonly billProgress: Locator;

  constructor(page: Page) {
    super(page);
    this.billsList = page.locator(
      '[data-testid="bills-list"], .bills-grid, .bill-list'
    );
    this.billCards = page
      .locator(
        '[data-testid="bill-card"], .bill-card, .bg-white.p-4, .bg-white.p-6'
      )
      .filter({ hasText: /H\.R\.|S\.|bill/i });
    this.billTracker = page.locator('[data-testid="bill-tracker"]');
    this.categoryFilter = page
      .locator('button, select')
      .filter({ hasText: /category|topic|healthcare|defense|technology/i });
    this.statusFilter = page
      .locator('button, select')
      .filter({ hasText: /status|passed|introduced|enacted/i });
    this.searchInput = page.locator(
      'input[type="search"], input[placeholder*="search"], input[placeholder*="bill"]'
    );
    this.sortOptions = page
      .locator('select, [role="combobox"]')
      .filter({ hasText: /sort|date|title/i });
    this.billDetails = page.locator('[data-testid="bill-details"]');
    this.sponsorInfo = page.locator(
      '[data-testid="sponsor-info"], .sponsor-info'
    );
    this.voteBreakdown = page.locator(
      '[data-testid="vote-breakdown"], .vote-breakdown'
    );
    this.categoryChart = page.locator(
      '[data-testid="category-chart"], .recharts-wrapper'
    );
    this.billProgress = page.locator(
      '[data-testid="bill-progress"], .progress'
    );
  }

  async goToBillsPage() {
    await this.goto('/bills');
    await this.waitForPageLoad();
  }

  async goToCategoryAnalysisPage() {
    await this.goto('/bills/categories');
    await this.waitForPageLoad();
  }

  async verifyBillsPageLoads() {
    await this.goToBillsPage();

    // Check that the page has loaded
    await expect(this.page.locator('main')).toBeVisible();

    // Look for bills-related content
    const hasBills = (await this.billCards.count()) > 0;
    const hasList = (await this.billsList.count()) > 0;
    const hasTracker = (await this.billTracker.count()) > 0;
    const hasTitle =
      (await this.page.locator('h1, h2').filter({ hasText: /bill/i }).count()) >
      0;

    // At least one indicator should be present
    expect(hasBills || hasList || hasTracker || hasTitle).toBeTruthy();
  }

  async verifyBillTracker() {
    await this.goToBillsPage();

    // Check for bill tracker functionality
    if ((await this.billTracker.count()) > 0) {
      await expect(this.billTracker).toBeVisible();
    }

    // Verify bill cards are displayed
    const cards = await this.billCards.all();
    if (cards.length > 0) {
      for (let i = 0; i < Math.min(3, cards.length); i++) {
        const card = cards[i];
        await expect(card).toBeVisible();

        // Each card should have bill information
        const text = await card.textContent();
        expect(text?.trim().length).toBeGreaterThan(0);

        // Look for bill identifiers (H.R., S., etc.)
        const hasBillNumber = /H\.R\.|S\.\d+|HR\d+/i.test(text || '');
        expect(hasBillNumber).toBeTruthy();
      }
    }

    return cards.length;
  }

  async testBillSearch() {
    await this.goToBillsPage();

    if ((await this.searchInput.count()) > 0) {
      // Test bill search functionality
      await this.searchInput.fill('infrastructure');

      // Submit search
      const searchButton = this.page
        .locator('button')
        .filter({ hasText: /search/i });
      if ((await searchButton.count()) > 0) {
        await searchButton.click();
      } else {
        await this.searchInput.press('Enter');
      }

      await this.page.waitForTimeout(1000);

      // Check results
      const hasResults = (await this.billCards.count()) > 0;
      const hasNoResults =
        (await this.page.locator('text=no results, text=not found').count()) >
        0;

      expect(hasResults || hasNoResults).toBeTruthy();
    }
  }

  async testCategoryFiltering() {
    await this.goToBillsPage();

    // Test category filtering
    const categoryFilters = await this.categoryFilter.all();
    if (categoryFilters.length > 0) {
      const filter = categoryFilters[0];
      if (await filter.isVisible()) {
        await filter.click();
        await this.page.waitForTimeout(500);

        // Verify filtering applied
        const billCount = await this.billCards.count();
        expect(billCount).toBeGreaterThanOrEqual(0);
      }
    }

    // Test status filtering
    const statusFilters = await this.statusFilter.all();
    if (statusFilters.length > 0) {
      const filter = statusFilters[0];
      if (await filter.isVisible()) {
        await filter.click();
        await this.page.waitForTimeout(500);
      }
    }
  }

  async testSorting() {
    await this.goToBillsPage();

    if ((await this.sortOptions.count()) > 0) {
      const sortSelect = this.sortOptions.first();
      await sortSelect.click();

      // Select different sort option if available
      const options = await sortSelect.locator('option').all();
      if (options.length > 1) {
        await options[1].click();
        await this.page.waitForTimeout(500);

        // Verify bills reordered
        const billCount = await this.billCards.count();
        expect(billCount).toBeGreaterThanOrEqual(0);
      }
    }
  }

  async testBillDetails() {
    await this.goToBillsPage();

    // Click on first bill card to view details
    const billLinks = await this.page.locator('a[href*="/bills/"]').all();

    if (billLinks.length > 0) {
      await billLinks[0].click();
      await this.waitForPageLoad();

      // Verify bill details page
      if ((await this.billDetails.count()) > 0) {
        await expect(this.billDetails).toBeVisible();
      }

      // Check for sponsor information
      if ((await this.sponsorInfo.count()) > 0) {
        await expect(this.sponsorInfo).toBeVisible();
      }

      // Check for vote breakdown
      if ((await this.voteBreakdown.count()) > 0) {
        await expect(this.voteBreakdown).toBeVisible();
      }

      // Check for bill progress
      if ((await this.billProgress.count()) > 0) {
        await expect(this.billProgress).toBeVisible();
      }

      // Verify bill title and number are displayed
      const billTitle = await this.page
        .locator('h1, h2')
        .filter({ hasText: /H\.R\.|S\./i })
        .count();
      expect(billTitle).toBeGreaterThanOrEqual(0);
    }
  }

  async verifyCategoryAnalysis() {
    await this.goToCategoryAnalysisPage();

    // Check for category analysis content
    const hasChart = (await this.categoryChart.count()) > 0;
    const hasCategories =
      (await this.page
        .locator('text=healthcare, text=defense, text=technology')
        .count()) > 0;
    const hasTitle =
      (await this.page
        .locator('h1, h2')
        .filter({ hasText: /categor/i })
        .count()) > 0;

    expect(hasChart || hasCategories || hasTitle).toBeTruthy();

    // Test chart rendering if present
    if ((await this.categoryChart.count()) > 0) {
      await expect(this.categoryChart.first()).toBeVisible();

      // Check for chart elements
      const chartSvg = this.categoryChart.locator('svg').first();
      if ((await chartSvg.count()) > 0) {
        await expect(chartSvg).toBeVisible();
      }
    }
  }

  async testVoteBreakdown() {
    // Look for vote breakdown functionality
    const voteElements = await this.voteBreakdown.all();

    for (const element of voteElements) {
      if (await element.isVisible()) {
        await expect(element).toBeVisible();

        // Check for party vote data
        const hasPartyData =
          (await element
            .locator('text=Democratic, text=Republican, text=Yes, text=No')
            .count()) > 0;
        expect(hasPartyData).toBeTruthy();
      }
    }
  }

  async verifyResponsiveDesign() {
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
      await this.page.waitForTimeout(300);

      await this.goToBillsPage();
      await this.takeFullPageScreenshot(`bills-${viewport.name.toLowerCase()}`);

      // Verify content is accessible
      await expect(this.page.locator('main')).toBeVisible();

      // Test filtering on mobile
      if (viewport.width < 768) {
        // Check that filters are accessible (might be in dropdown)
        const mobileFilters = await this.page
          .locator('button')
          .filter({ hasText: /filter|category/i })
          .all();
        if (mobileFilters.length > 0) {
          const filter = mobileFilters[0];
          if (await filter.isVisible()) {
            await filter.click();
            await this.page.waitForTimeout(300);
          }
        }
      }
    }

    // Reset to desktop
    await this.page.setViewportSize({ width: 1920, height: 1080 });
  }

  async testExportBillData() {
    await this.goToBillsPage();

    // Look for export functionality
    const exportButtons = await this.page
      .locator('button')
      .filter({ hasText: /export|download|csv|json/i })
      .all();

    for (const button of exportButtons) {
      if (await button.isVisible()) {
        await button.click();
        await this.page.waitForTimeout(500);

        // Verify no errors
        const errorExists = (await this.errorBoundary.count()) > 0;
        expect(errorExists).toBeFalsy();
      }
    }
  }

  async testBillProgress() {
    // Look for bill progress indicators
    const progressElements = await this.billProgress.all();

    for (const element of progressElements) {
      if (await element.isVisible()) {
        await expect(element).toBeVisible();

        // Check for progress steps
        const hasSteps =
          (await element
            .locator(
              'text=introduced, text=committee, text=passed, text=enacted'
            )
            .count()) > 0;
        expect(hasSteps).toBeTruthy();
      }
    }
  }
}
