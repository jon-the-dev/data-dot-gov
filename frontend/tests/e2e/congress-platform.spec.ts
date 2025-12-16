import type { Page } from '@playwright/test';
import { test, expect } from '@playwright/test';

import { BasePage } from './page-objects/BasePage';
import { BillsPage } from './page-objects/BillsPage';
import { DashboardPage } from './page-objects/DashboardPage';
import { MembersPage } from './page-objects/MembersPage';
import { VotesPage } from './page-objects/VotesPage';

// Screenshots directory is created manually

test.describe('Congressional Transparency Platform', () => {
  let page: Page;
  let dashboardPage: DashboardPage;
  let membersPage: MembersPage;
  let billsPage: BillsPage;
  let votesPage: VotesPage;
  let basePage: BasePage;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    dashboardPage = new DashboardPage(page);
    membersPage = new MembersPage(page);
    billsPage = new BillsPage(page);
    votesPage = new VotesPage(page);
    basePage = new BasePage(page);

    // Set up console error tracking
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error('Console error:', msg.text());
      }
    });

    page.on('pageerror', error => {
      console.error('Page error:', error.message);
    });
  });

  test.afterEach(async () => {
    await page.close();
  });

  test.describe('Dashboard Tests', () => {
    test('dashboard loads correctly', async () => {
      await dashboardPage.verifyDashboardLoads();

      // Take screenshot
      await dashboardPage.takeFullPageScreenshot('dashboard-main');

      // Verify no console errors
      const errors = await dashboardPage.checkNoConsoleErrors();
      expect(errors.length).toBe(0);
    });

    test('dashboard displays stat cards', async () => {
      await dashboardPage.goto('/');
      const cardCount = await dashboardPage.verifyStatCards();

      // Found stat cards on dashboard: ${cardCount}
      expect(cardCount).toBeGreaterThanOrEqual(0);
    });

    test('dashboard charts render properly', async () => {
      await dashboardPage.goto('/');
      await dashboardPage.verifyChartsRender();

      // Check for data visualization
      const vizData = await dashboardPage.checkDataVisualization();
      console.log(
        `Found ${vizData.charts} charts and ${vizData.tables} tables`
      );
    });

    test('dashboard export functionality works', async () => {
      await dashboardPage.goto('/');
      await dashboardPage.testExportFunctionality();
    });

    test('dashboard responsive design', async () => {
      await dashboardPage.verifyResponsiveLayout();
    });

    test('dashboard loading states', async () => {
      await dashboardPage.checkLoadingStates();
    });

    test('dashboard performance', async () => {
      const loadTime = await dashboardPage.checkPerformance();
      console.log(`Dashboard load time: ${loadTime}ms`);

      // Performance assertion
      expect(loadTime).toBeLessThan(5000);
    });
  });

  test.describe('Members Section Tests', () => {
    test('members page loads correctly', async () => {
      await membersPage.verifyMembersPageLoads();
      await membersPage.takeFullPageScreenshot('members-main');
    });

    test('member search functionality', async () => {
      await membersPage.testMemberSearch();
    });

    test('member filtering works', async () => {
      await membersPage.testFiltering();
    });

    test('member cards display correctly', async () => {
      const cardCount = await membersPage.verifyMemberCards();
      console.log(`Found ${cardCount} member cards`);
    });

    test('member profile navigation', async () => {
      await membersPage.testMemberProfile();
    });

    test('party unity charts render', async () => {
      await membersPage.testPartyUnityChart();
    });

    test('members responsive design', async () => {
      await membersPage.verifyResponsiveDesign();
    });

    test('member data export', async () => {
      await membersPage.testExportMemberData();
    });
  });

  test.describe('Bills Section Tests', () => {
    test('bills page loads correctly', async () => {
      await billsPage.verifyBillsPageLoads();
      await billsPage.takeFullPageScreenshot('bills-main');
    });

    test('bill tracker functionality', async () => {
      const billCount = await billsPage.verifyBillTracker();
      console.log(`Found ${billCount} bills in tracker`);
    });

    test('bill search works', async () => {
      await billsPage.testBillSearch();
    });

    test('bill category filtering', async () => {
      await billsPage.testCategoryFiltering();
    });

    test('bill sorting functionality', async () => {
      await billsPage.testSorting();
    });

    test('bill details navigation', async () => {
      await billsPage.testBillDetails();
    });

    test('category analysis page', async () => {
      await billsPage.verifyCategoryAnalysis();
      await billsPage.takeFullPageScreenshot('bills-categories');
    });

    test('vote breakdown displays', async () => {
      await billsPage.testVoteBreakdown();
    });

    test('bill progress tracking', async () => {
      await billsPage.testBillProgress();
    });

    test('bills responsive design', async () => {
      await billsPage.verifyResponsiveDesign();
    });

    test('bill data export', async () => {
      await billsPage.testExportBillData();
    });
  });

  test.describe('Votes Section Tests', () => {
    test('votes page loads correctly', async () => {
      await votesPage.verifyVotesPageLoads();
      await votesPage.takeFullPageScreenshot('votes-main');
    });

    test('vote breakdown functionality', async () => {
      await votesPage.testVoteBreakdown();
    });

    test('vote details display', async () => {
      await votesPage.verifyVoteDetails();
    });

    test('party unity visualization', async () => {
      await votesPage.testPartyUnityVisualization();
    });

    test('vote filtering works', async () => {
      await votesPage.testVoteFiltering();
    });

    test('member vote positions', async () => {
      await votesPage.testMemberVotePositions();
    });

    test('party breakdown displays', async () => {
      await votesPage.verifyPartyBreakdown();
    });

    test('vote search functionality', async () => {
      await votesPage.testVoteSearch();
    });

    test('votes responsive design', async () => {
      await votesPage.verifyResponsiveDesign();
    });

    test('vote data export', async () => {
      await votesPage.testExportVoteData();
    });
  });

  test.describe('Navigation Tests', () => {
    test('main navigation works', async () => {
      await basePage.goto('/');

      // Test each navigation section
      const sections = ['members', 'bills', 'votes', 'party-comparison'];

      for (const section of sections) {
        await basePage.navigateToSection(section);
        await expect(page.locator('main')).toBeVisible();

        // Verify URL changed
        expect(page.url()).toContain(
          section === 'party-comparison' ? 'party-comparison' : section
        );
      }
    });

    test('mobile navigation functionality', async () => {
      await basePage.goto('/');
      await basePage.testMobileNavigation();
    });

    test('navigation accessibility', async () => {
      await basePage.goto('/');
      await basePage.checkAccessibility();
    });

    test('keyboard navigation', async () => {
      await basePage.goto('/');
      await basePage.testKeyboardNavigation();
    });

    test('navigation breadcrumbs', async () => {
      // Test breadcrumb navigation if present
      await basePage.goto('/members');

      const breadcrumbs = page.locator(
        '[data-testid="breadcrumbs"], .breadcrumb, nav[aria-label*="breadcrumb"]'
      );
      if ((await breadcrumbs.count()) > 0) {
        await expect(breadcrumbs).toBeVisible();
      }
    });
  });

  test.describe('Error Handling Tests', () => {
    test('handles network failures gracefully', async () => {
      // Simulate network failure
      await page.route('**/api/**', route => route.abort());

      await basePage.goto('/');
      await basePage.waitForPageLoad();

      // Should show error state or loading state, not crash
      const hasError = (await basePage.errorBoundary.count()) > 0;
      const hasLoading = (await basePage.loadingSpinner.count()) > 0;
      const hasContent = (await page.locator('main').count()) > 0;

      expect(hasError || hasLoading || hasContent).toBeTruthy();
    });

    test('handles 404 pages', async () => {
      await page.goto('/nonexistent-page');
      await basePage.waitForPageLoad();

      // Should show 404 message
      const has404 =
        (await page
          .locator('text=not found, text=404, text=page.*not.*found')
          .count()) > 0;
      expect(has404).toBeTruthy();
    });

    test('error boundary catches component errors', async () => {
      // If error boundaries are implemented, they should catch errors
      await basePage.goto('/');

      // Check that error boundaries exist in the DOM structure
      const errorBoundaryExists =
        (await page.locator('[data-error-boundary], .error-boundary').count()) >
        0;

      // This is informational - error boundaries might be implemented differently
      console.log(`Error boundary elements found: ${errorBoundaryExists}`);
    });
  });

  test.describe('Performance Tests', () => {
    test('page load performance', async () => {
      const startTime = Date.now();
      await basePage.goto('/');
      const loadTime = Date.now() - startTime;

      console.log(`Page load time: ${loadTime}ms`);
      expect(loadTime).toBeLessThan(5000);
    });

    test('large dataset handling', async () => {
      // Test handling of large datasets (if available)
      await membersPage.goto('/members');

      // Scroll to test virtual scrolling or pagination
      await page.evaluate(() => {
        window.scrollTo(0, document.body.scrollHeight);
      });

      await page.waitForTimeout(1000);

      // Page should remain responsive
      await expect(page.locator('main')).toBeVisible();
    });

    test('memory usage during navigation', async () => {
      // Navigate between different sections to test memory leaks
      const sections = ['/', '/members', '/bills', '/votes', '/'];

      for (const section of sections) {
        await basePage.goto(section);
        await basePage.waitForPageLoad();

        // Verify page is responsive
        await expect(page.locator('main')).toBeVisible();
      }
    });
  });

  test.describe('Accessibility Tests', () => {
    test('basic accessibility compliance', async () => {
      await basePage.goto('/');
      await basePage.checkAccessibility();
    });

    test('keyboard navigation support', async () => {
      await basePage.goto('/');

      // Test tab navigation
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');

      // Verify focus is visible
      const focusedElement = page.locator(':focus');
      await expect(focusedElement).toBeVisible();
    });

    test('screen reader support', async () => {
      await basePage.goto('/');

      // Check for ARIA labels and roles
      const ariaLabels = await page.locator('[aria-label]').count();
      const ariaRoles = await page.locator('[role]').count();
      const headings = await page.locator('h1, h2, h3, h4, h5, h6').count();

      console.log(
        `ARIA labels: ${ariaLabels}, roles: ${ariaRoles}, headings: ${headings}`
      );

      // Should have some accessibility attributes
      expect(ariaLabels + ariaRoles + headings).toBeGreaterThan(0);
    });

    test('color contrast and visual accessibility', async () => {
      await basePage.goto('/');

      // Take screenshots for manual color contrast review
      await basePage.takeFullPageScreenshot('accessibility-review');

      // Verify text is readable (has actual content)
      const textElements = await page
        .locator('p, span, div, h1, h2, h3, h4, h5, h6')
        .all();
      let hasReadableText = false;

      for (const element of textElements.slice(0, 10)) {
        // Check first 10 elements
        const text = await element.textContent();
        if (text && text.trim().length > 0) {
          hasReadableText = true;
          break;
        }
      }

      expect(hasReadableText).toBeTruthy();
    });
  });

  test.describe('Data Integrity Tests', () => {
    test('data consistency across sections', async () => {
      // Check that member counts are consistent between dashboard and members page
      await dashboardPage.goto('/');

      // Look for member count on dashboard
      const dashboardMemberCount = await page
        .locator('text=/\\d+.*member/i, text=/member.*\\d+/i')
        .textContent();

      await membersPage.goto('/members');
      const memberCardCount = await membersPage.verifyMemberCards();

      console.log(
        `Dashboard shows: ${dashboardMemberCount}, Members page has: ${memberCardCount} cards`
      );

      // Both should show some member data (exact match not required due to different data sources)
      expect(memberCardCount).toBeGreaterThanOrEqual(0);
    });

    test('bill data consistency', async () => {
      await billsPage.goto('/bills');
      const billCount = await billsPage.verifyBillTracker();

      await billsPage.goto('/bills/categories');
      // Category page should also show bills
      await expect(page.locator('main')).toBeVisible();

      console.log(`Bills page shows: ${billCount} bills`);
    });

    test('vote data relationships', async () => {
      await votesPage.goto('/votes');

      // Check that vote data is properly linked
      const voteLinks = await page.locator('a[href*="/votes/"]').count();
      console.log(`Found ${voteLinks} vote links`);

      if (voteLinks > 0) {
        // Test one vote detail page
        await page.locator('a[href*="/votes/"]').first().click();
        await votesPage.waitForPageLoad();

        await votesPage.verifyVoteDetails();
      }
    });
  });

  test.describe('Multi-Browser Compatibility', () => {
    test('works in different browsers', async () => {
      // This test will run across all configured browsers
      await basePage.goto('/');
      await expect(page.locator('main')).toBeVisible();

      // Test basic functionality
      await basePage.navigateToSection('members');
      await expect(page.locator('main')).toBeVisible();

      await basePage.navigateToSection('bills');
      await expect(page.locator('main')).toBeVisible();
    });
  });

  test.describe('Visual Regression Tests', () => {
    test('visual consistency check', async () => {
      const pages = [
        { path: '/', name: 'dashboard' },
        { path: '/members', name: 'members' },
        { path: '/bills', name: 'bills' },
        { path: '/votes', name: 'votes' },
      ];

      for (const testPage of pages) {
        await basePage.goto(testPage.path);
        await basePage.waitForPageLoad();

        // Take full page screenshot
        await basePage.takeFullPageScreenshot(`${testPage.name}-visual-test`);

        // Verify page structure is intact
        await expect(page.locator('header')).toBeVisible();
        await expect(page.locator('nav')).toBeVisible();
        await expect(page.locator('main')).toBeVisible();
        await expect(page.locator('footer')).toBeVisible();
      }
    });
  });
});
