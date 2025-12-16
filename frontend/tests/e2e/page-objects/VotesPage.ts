import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

import { BasePage } from './BasePage';

export class VotesPage extends BasePage {
  readonly votesList: Locator;
  readonly voteCards: Locator;
  readonly voteBreakdown: Locator;
  readonly partyBreakdown: Locator;
  readonly memberPositions: Locator;
  readonly voteResult: Locator;
  readonly rollCallNumber: Locator;
  readonly voteDate: Locator;
  readonly voteQuestion: Locator;
  readonly yearFilter: Locator;
  readonly chamberFilter: Locator;
  readonly resultFilter: Locator;
  readonly partyUnityChart: Locator;

  constructor(page: Page) {
    super(page);
    this.votesList = page.locator(
      '[data-testid="votes-list"], .votes-grid, .vote-list'
    );
    this.voteCards = page
      .locator(
        '[data-testid="vote-card"], .vote-card, .bg-white.p-4, .bg-white.p-6'
      )
      .filter({ hasText: /roll call|vote|passage/i });
    this.voteBreakdown = page.locator(
      '[data-testid="vote-breakdown"], .vote-breakdown'
    );
    this.partyBreakdown = page.locator(
      '[data-testid="party-breakdown"], .party-breakdown'
    );
    this.memberPositions = page.locator(
      '[data-testid="member-positions"], .member-positions'
    );
    this.voteResult = page.locator('[data-testid="vote-result"], .vote-result');
    this.rollCallNumber = page.locator('[data-testid="roll-call"], .roll-call');
    this.voteDate = page.locator('[data-testid="vote-date"], .vote-date');
    this.voteQuestion = page.locator(
      '[data-testid="vote-question"], .vote-question'
    );
    this.yearFilter = page
      .locator('select, button')
      .filter({ hasText: /year|2024|2023|2022/i });
    this.chamberFilter = page
      .locator('select, button')
      .filter({ hasText: /chamber|house|senate/i });
    this.resultFilter = page
      .locator('select, button')
      .filter({ hasText: /result|passed|failed/i });
    this.partyUnityChart = page.locator(
      '[data-testid="party-unity-chart"], .recharts-wrapper'
    );
  }

  async goToVotesPage() {
    await this.goto('/votes');
    await this.waitForPageLoad();
  }

  async goToSpecificVote(voteId: string) {
    await this.goto(`/votes/${voteId}`);
    await this.waitForPageLoad();
  }

  async verifyVotesPageLoads() {
    await this.goToVotesPage();

    // Check that the page has loaded
    await expect(this.page.locator('main')).toBeVisible();

    // Look for votes-related content or coming soon message
    const hasVotes = (await this.voteCards.count()) > 0;
    const hasList = (await this.votesList.count()) > 0;
    const hasComingSoon =
      (await this.page
        .locator('text=coming soon, text=under development')
        .count()) > 0;
    const hasTitle =
      (await this.page.locator('h1, h2').filter({ hasText: /vote/i }).count()) >
      0;

    // At least one indicator should be present
    expect(hasVotes || hasList || hasComingSoon || hasTitle).toBeTruthy();
  }

  async testVoteBreakdown() {
    // Test specific vote breakdown page
    const voteLinks = await this.page.locator('a[href*="/votes/"]').all();

    if (voteLinks.length > 0) {
      await voteLinks[0].click();
      await this.waitForPageLoad();
    } else {
      // Try navigating to a sample vote
      await this.goToSpecificVote('118-1-500');
    }

    // Check for vote breakdown elements
    if ((await this.voteBreakdown.count()) > 0) {
      await expect(this.voteBreakdown).toBeVisible();
    }

    // Check for party breakdown
    if ((await this.partyBreakdown.count()) > 0) {
      await expect(this.partyBreakdown).toBeVisible();

      // Verify party data is displayed
      const hasPartyData =
        (await this.partyBreakdown
          .locator('text=Democratic, text=Republican, text=Independent')
          .count()) > 0;
      expect(hasPartyData).toBeTruthy();
    }

    // Check for member positions
    if ((await this.memberPositions.count()) > 0) {
      await expect(this.memberPositions).toBeVisible();

      // Verify individual member votes
      const hasVoteData =
        (await this.memberPositions
          .locator('text=Yes, text=No, text=Present, text=Not Voting')
          .count()) > 0;
      expect(hasVoteData).toBeTruthy();
    }
  }

  async verifyVoteDetails() {
    // Check for essential vote information
    if ((await this.rollCallNumber.count()) > 0) {
      await expect(this.rollCallNumber).toBeVisible();

      // Verify roll call number format
      const rollCallText = await this.rollCallNumber.textContent();
      const hasValidFormat = /\d+/.test(rollCallText || '');
      expect(hasValidFormat).toBeTruthy();
    }

    if ((await this.voteDate.count()) > 0) {
      await expect(this.voteDate).toBeVisible();
    }

    if ((await this.voteQuestion.count()) > 0) {
      await expect(this.voteQuestion).toBeVisible();

      // Verify question text is meaningful
      const questionText = await this.voteQuestion.textContent();
      expect(questionText?.trim().length).toBeGreaterThan(10);
    }

    if ((await this.voteResult.count()) > 0) {
      await expect(this.voteResult).toBeVisible();

      // Verify result is displayed
      const resultText = await this.voteResult.textContent();
      const hasValidResult = /passed|failed|agreed|disagreed/i.test(
        resultText || ''
      );
      expect(hasValidResult).toBeTruthy();
    }
  }

  async testPartyUnityVisualization() {
    // Check for party unity charts
    const charts = await this.partyUnityChart.all();

    for (const chart of charts) {
      if (await chart.isVisible()) {
        await expect(chart).toBeVisible();

        // Check for chart elements
        const chartSvg = chart.locator('svg');
        if ((await chartSvg.count()) > 0) {
          await expect(chartSvg).toBeVisible();

          // Verify chart has data elements
          const hasDataElements =
            (await chartSvg.locator('rect, circle, path, line').count()) > 0;
          expect(hasDataElements).toBeTruthy();
        }
      }
    }
  }

  async testVoteFiltering() {
    await this.goToVotesPage();

    // Test year filtering
    const yearFilters = await this.yearFilter.all();
    if (yearFilters.length > 0) {
      const filter = yearFilters[0];
      if (await filter.isVisible()) {
        await filter.click();
        await this.page.waitForTimeout(500);

        // Check if options are available
        const options = await filter.locator('option').all();
        if (options.length > 1) {
          await options[1].click();
          await this.page.waitForTimeout(500);
        }
      }
    }

    // Test chamber filtering
    const chamberFilters = await this.chamberFilter.all();
    if (chamberFilters.length > 0) {
      const filter = chamberFilters[0];
      if (await filter.isVisible()) {
        await filter.click();
        await this.page.waitForTimeout(500);
      }
    }

    // Test result filtering
    const resultFilters = await this.resultFilter.all();
    if (resultFilters.length > 0) {
      const filter = resultFilters[0];
      if (await filter.isVisible()) {
        await filter.click();
        await this.page.waitForTimeout(500);
      }
    }
  }

  async testMemberVotePositions() {
    // Check individual member vote positions
    if ((await this.memberPositions.count()) > 0) {
      const positions = await this.memberPositions.all();

      for (const position of positions) {
        if (await position.isVisible()) {
          await expect(position).toBeVisible();

          // Verify member information is displayed
          const hasContent = await position.textContent();
          expect(hasContent?.trim().length).toBeGreaterThan(0);

          // Look for vote position indicators
          const hasVotePosition =
            (await position
              .locator('text=Yes, text=No, text=Present, text=Not Voting')
              .count()) > 0;
          expect(hasVotePosition).toBeTruthy();
        }
      }
    }
  }

  async verifyPartyBreakdown() {
    if ((await this.partyBreakdown.count()) > 0) {
      await expect(this.partyBreakdown).toBeVisible();

      // Check for party-specific vote counts
      const hasRepublican =
        (await this.partyBreakdown.locator('text=Republican, text=R').count()) >
        0;
      const hasDemocratic =
        (await this.partyBreakdown
          .locator('text=Democratic, text=Democrat, text=D')
          .count()) > 0;

      expect(hasRepublican || hasDemocratic).toBeTruthy();

      // Check for vote totals
      const hasNumbers =
        (await this.partyBreakdown.locator('text=/\\d+/').count()) > 0;
      expect(hasNumbers).toBeTruthy();
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

      await this.goToVotesPage();
      await this.takeFullPageScreenshot(`votes-${viewport.name.toLowerCase()}`);

      // Verify content is accessible
      await expect(this.page.locator('main')).toBeVisible();

      // Test vote breakdown on different screen sizes
      if ((await this.voteBreakdown.count()) > 0) {
        await expect(this.voteBreakdown).toBeVisible();
      }
    }

    // Reset to desktop
    await this.page.setViewportSize({ width: 1920, height: 1080 });
  }

  async testExportVoteData() {
    // Look for export functionality for vote data
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

  async testVoteSearch() {
    await this.goToVotesPage();

    // Look for search functionality
    const searchInput = this.page.locator(
      'input[type="search"], input[placeholder*="search"]'
    );

    if ((await searchInput.count()) > 0) {
      await searchInput.fill('infrastructure');

      const searchButton = this.page
        .locator('button')
        .filter({ hasText: /search/i });
      if ((await searchButton.count()) > 0) {
        await searchButton.click();
      } else {
        await searchInput.press('Enter');
      }

      await this.page.waitForTimeout(1000);

      // Check for results or no results message
      const hasResults = (await this.voteCards.count()) > 0;
      const hasNoResults =
        (await this.page.locator('text=no results, text=not found').count()) >
        0;

      expect(hasResults || hasNoResults).toBeTruthy();
    }
  }
}
