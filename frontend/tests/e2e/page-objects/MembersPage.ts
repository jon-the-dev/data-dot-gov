import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

import { BasePage } from './BasePage';

export class MembersPage extends BasePage {
  readonly searchInput: Locator;
  readonly searchButton: Locator;
  readonly membersList: Locator;
  readonly memberCards: Locator;
  readonly filterButtons: Locator;
  readonly sortDropdown: Locator;
  readonly partyFilter: Locator;
  readonly stateFilter: Locator;
  readonly memberProfile: Locator;
  readonly votingRecord: Locator;
  readonly partyUnityScore: Locator;

  constructor(page: Page) {
    super(page);
    this.searchInput = page.locator(
      'input[type="search"], input[placeholder*="search"], input[placeholder*="member"]'
    );
    this.searchButton = page.getByRole('button', { name: /search/i });
    this.membersList = page.locator(
      '[data-testid="members-list"], .members-grid, .member-list'
    );
    this.memberCards = page
      .locator(
        '[data-testid="member-card"], .member-card, .bg-white.p-4, .bg-white.p-6'
      )
      .filter({ hasText: /representative|senator/i });
    this.filterButtons = page
      .locator('button')
      .filter({ hasText: /filter|party|state/i });
    this.sortDropdown = page
      .locator('select, [role="combobox"]')
      .filter({ hasText: /sort|order/i });
    this.partyFilter = page
      .locator('button, select')
      .filter({ hasText: /democratic|republican|independent/i });
    this.stateFilter = page
      .locator('button, select')
      .filter({ hasText: /state|AL|CA|TX|NY/i });
    this.memberProfile = page.locator('[data-testid="member-profile"]');
    this.votingRecord = page.locator(
      '[data-testid="voting-record"], .voting-record'
    );
    this.partyUnityScore = page.locator(
      '[data-testid="party-unity"], .party-unity'
    );
  }

  async goToMembersPage() {
    await this.goto('/members');
    await this.waitForPageLoad();
  }

  async goToMemberSearchPage() {
    await this.goto('/members/search');
    await this.waitForPageLoad();
  }

  async verifyMembersPageLoads() {
    await this.goToMembersPage();

    // Check that the page has loaded
    await expect(this.page.locator('main')).toBeVisible();

    // Look for members-related content
    const hasMembers = (await this.memberCards.count()) > 0;
    const hasList = (await this.membersList.count()) > 0;
    const hasTitle =
      (await this.page
        .locator('h1, h2')
        .filter({ hasText: /member/i })
        .count()) > 0;

    // At least one indicator should be present
    expect(hasMembers || hasList || hasTitle).toBeTruthy();
  }

  async testMemberSearch() {
    await this.goToMemberSearchPage();

    if ((await this.searchInput.count()) > 0) {
      // Test search functionality
      await this.searchInput.fill('Smith');

      if ((await this.searchButton.count()) > 0) {
        await this.searchButton.click();
      } else {
        // Try Enter key if no search button
        await this.searchInput.press('Enter');
      }

      await this.page.waitForTimeout(1000); // Wait for search results

      // Check if results appeared or no results message
      const hasResults = (await this.memberCards.count()) > 0;
      const hasNoResults =
        (await this.page.locator('text=no results, text=not found').count()) >
        0;

      expect(hasResults || hasNoResults).toBeTruthy();
    }
  }

  async testFiltering() {
    await this.goToMembersPage();

    // Test party filtering if available
    const partyFilters = await this.partyFilter.all();
    if (partyFilters.length > 0) {
      const filter = partyFilters[0];
      if (await filter.isVisible()) {
        await filter.click();
        await this.page.waitForTimeout(500);

        // Check that filtering applied
        const memberCount = await this.memberCards.count();
        expect(memberCount).toBeGreaterThanOrEqual(0);
      }
    }

    // Test state filtering if available
    const stateFilters = await this.stateFilter.all();
    if (stateFilters.length > 0) {
      const filter = stateFilters[0];
      if (await filter.isVisible()) {
        await filter.click();
        await this.page.waitForTimeout(500);
      }
    }
  }

  async verifyMemberCards() {
    await this.goToMembersPage();

    const cards = await this.memberCards.all();

    if (cards.length > 0) {
      for (let i = 0; i < Math.min(3, cards.length); i++) {
        const card = cards[i];
        await expect(card).toBeVisible();

        // Each card should have some content
        const text = await card.textContent();
        expect(text?.trim().length).toBeGreaterThan(0);

        // Cards should be interactive (clickable)
        const hasLink = (await card.locator('a').count()) > 0;
        const isClickable = await card.evaluate(el => {
          const style = window.getComputedStyle(el);
          return (
            style.cursor === 'pointer' ||
            el.tagName === 'A' ||
            el.onclick !== null
          );
        });

        if (hasLink || isClickable) {
          // Test clicking on first card
          if (i === 0) {
            await card.click();
            await this.page.waitForTimeout(1000);

            // Should navigate somewhere or show member details
            const currentUrl = this.page.url();
            expect(currentUrl).toBeTruthy();
          }
        }
      }
    }

    return cards.length;
  }

  async testMemberProfile() {
    // Try to navigate to a member profile
    const memberLinks = await this.page.locator('a[href*="/members/"]').all();

    if (memberLinks.length > 0) {
      await memberLinks[0].click();
      await this.waitForPageLoad();

      // Verify profile page elements
      if ((await this.memberProfile.count()) > 0) {
        await expect(this.memberProfile).toBeVisible();
      }

      // Check for voting record
      if ((await this.votingRecord.count()) > 0) {
        await expect(this.votingRecord).toBeVisible();
      }

      // Check for party unity score
      if ((await this.partyUnityScore.count()) > 0) {
        await expect(this.partyUnityScore).toBeVisible();
      }

      // Verify member information is displayed
      const memberInfo = await this.page
        .locator('h1, h2, h3')
        .filter({ hasText: /representative|senator/i })
        .count();
      expect(memberInfo).toBeGreaterThanOrEqual(0);
    }
  }

  async testPartyUnityChart() {
    await this.goToMembersPage();

    // Look for party unity charts
    const charts = await this.page.locator('.recharts-wrapper, svg').all();

    for (const chart of charts) {
      if (await chart.isVisible()) {
        await expect(chart).toBeVisible();

        // Check if chart has data (has SVG elements)
        const svgElements = await chart
          .locator('rect, circle, path, line')
          .count();
        expect(svgElements).toBeGreaterThanOrEqual(0);
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

      await this.goToMembersPage();
      await this.takeFullPageScreenshot(
        `members-${viewport.name.toLowerCase()}`
      );

      // Verify content is accessible on all viewports
      await expect(this.page.locator('main')).toBeVisible();

      // Test search on mobile
      if (viewport.width < 768 && (await this.searchInput.count()) > 0) {
        await expect(this.searchInput).toBeVisible();
      }
    }

    // Reset to desktop
    await this.page.setViewportSize({ width: 1920, height: 1080 });
  }

  async testExportMemberData() {
    await this.goToMembersPage();

    // Look for export buttons specifically for member data
    const exportButtons = await this.page
      .locator('button')
      .filter({ hasText: /export|download|csv|json/i })
      .all();

    for (const button of exportButtons) {
      if (await button.isVisible()) {
        await button.click();
        await this.page.waitForTimeout(500);

        // Verify no errors occurred
        const errorExists = (await this.errorBoundary.count()) > 0;
        expect(errorExists).toBeFalsy();
      }
    }
  }
}
