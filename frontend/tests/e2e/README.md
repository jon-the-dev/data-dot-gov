# E2E Test Suite for Congressional Transparency Platform

This comprehensive Playwright test suite validates all major functionality of the Congressional Transparency Platform frontend running on http://localhost:5173.

## Test Coverage

### Core Functionality Tests
- **Dashboard Tests**: Homepage loading, stat cards, charts, export functionality
- **Members Section**: Member search, filtering, profile navigation, party unity charts
- **Bills Section**: Bill tracker, search, filtering, category analysis, vote breakdown
- **Votes Section**: Vote details, party breakdown, member positions
- **Navigation**: Multi-level navigation, mobile menu, accessibility
- **Export Functionality**: CSV/JSON export, download validation, error handling

### Quality Assurance Tests
- **Performance**: Page load times, memory usage, chart rendering performance
- **Accessibility**: WCAG compliance, keyboard navigation, screen reader support
- **Responsive Design**: Mobile/tablet/desktop layouts, viewport testing
- **Error Handling**: Network failures, 404 pages, component errors
- **Visual Regression**: Screenshot comparisons, layout consistency

### Browser Compatibility
- Chrome (Desktop & Mobile)
- Firefox
- Safari (Desktop & Mobile)
- Microsoft Edge

## Quick Start

### Prerequisites
1. Frontend application running on http://localhost:5173
2. Node.js and pnpm installed
3. Playwright browsers installed

### Setup
```bash
# Install dependencies
cd frontend
pnpm install

# Install Playwright browsers
pnpm run test:install
```

### Running Tests

#### All Tests
```bash
# Run all tests (headless)
pnpm run test:e2e

# Run tests with UI (interactive)
pnpm run test:e2e:ui

# Run tests in headed mode (see browser)
pnpm run test:e2e:headed
```

#### Specific Test Suites
```bash
# Run main platform tests
npx playwright test congress-platform.spec.ts

# Run export functionality tests
npx playwright test export-functionality.spec.ts

# Run performance tests
npx playwright test performance.spec.ts
```

#### Debug Mode
```bash
# Debug a specific test
pnpm run test:e2e:debug

# Debug with specific test file
npx playwright test congress-platform.spec.ts --debug
```

#### Generate Reports
```bash
# View HTML report
pnpm run test:e2e:report

# Run tests and open report
npx playwright test --reporter=html
```

## Test Structure

### Page Object Models
- `BasePage.ts`: Common functionality and utilities
- `DashboardPage.ts`: Dashboard-specific actions and assertions
- `MembersPage.ts`: Members section functionality
- `BillsPage.ts`: Bills section functionality
- `VotesPage.ts`: Votes section functionality

### Test Utilities
- `test-utils.ts`: Helper functions for common test operations
- `TestUtils.waitForNetworkIdle()`: Wait for network requests to complete
- `TestUtils.testResponsiveBreakpoints()`: Test across multiple viewport sizes
- `TestUtils.verifyAccessibilityAttributes()`: Check accessibility compliance

### Test Categories

#### Functional Tests (`congress-platform.spec.ts`)
- Dashboard loading and functionality
- Member search and filtering
- Bill tracking and categorization
- Vote breakdown and analysis
- Navigation and user flows
- Data consistency across sections

#### Export Tests (`export-functionality.spec.ts`)
- CSV export validation
- JSON export validation
- Download verification
- Export button accessibility
- Cross-device export testing
- Error handling during exports

#### Performance Tests (`performance.spec.ts`)
- Core Web Vitals measurement
- Page load time analysis
- Memory usage monitoring
- Chart rendering performance
- Large dataset handling
- Bundle size impact analysis

## Configuration

### Playwright Config (`playwright.config.ts`)
- **Browsers**: Chrome, Firefox, Safari, Edge, Mobile devices
- **Base URL**: http://localhost:5173
- **Timeouts**: 30s test, 10s expect, 10s action
- **Retries**: 2 retries in CI, 0 locally
- **Screenshots**: On failure only
- **Videos**: Retain on failure
- **Traces**: On first retry

### Test Data
Tests use a combination of:
- Live data from the running application
- Generated test data from `TestUtils.generateTestData()`
- Mock data for error condition testing

## Screenshots and Visual Testing

Screenshots are automatically captured in `tests/screenshots/`:
- Full page screenshots for each major section
- Responsive design screenshots (desktop/tablet/mobile)
- Error state screenshots
- Visual regression reference images

## Continuous Integration

### CI Environment Setup
```bash
# Install dependencies
pnpm install

# Install Playwright browsers
pnpm run test:install

# Run tests
pnpm run test:e2e --reporter=html
```

### Environment Variables
- `CI=true`: Enables CI-specific settings (retries, parallel execution)
- `PLAYWRIGHT_HTML_REPORT`: Custom report location

## Debugging Failed Tests

### Common Issues

1. **Application Not Running**
   - Ensure `pnpm run dev` is running on localhost:5173
   - Check for build errors in the application

2. **Timeout Errors**
   - Increase timeout in playwright.config.ts
   - Check for slow network requests
   - Verify loading states are properly handled

3. **Element Not Found**
   - Check if component structure changed
   - Update selectors in page object models
   - Verify data is loading correctly

4. **Flaky Tests**
   - Add proper wait conditions
   - Use `waitForLoadState('networkidle')`
   - Increase stability timeouts

### Debug Commands
```bash
# Run specific test with debugging
npx playwright test congress-platform.spec.ts --grep "dashboard loads" --debug

# Generate and view trace
npx playwright test --trace on
npx playwright show-trace trace.zip

# Take screenshot during test
await page.screenshot({ path: 'debug.png' });
```

## Test Maintenance

### Updating Tests
1. **Component Changes**: Update page object models if component structure changes
2. **New Features**: Add corresponding test cases in appropriate spec files
3. **API Changes**: Update test data and expectations
4. **Design Changes**: Update visual regression screenshots

### Performance Monitoring
- Monitor test execution times
- Update performance thresholds as application grows
- Track memory usage patterns
- Optimize test data and setup

## Custom Test Utilities

### Network Simulation
```javascript
// Simulate slow network
await TestUtils.simulateSlowNetwork(page);

// Simulate network failure
await TestUtils.simulateNetworkFailure(page, ['**/api/**']);
```

### Responsive Testing
```javascript
// Test across all breakpoints
await TestUtils.testResponsiveBreakpoints(page, async () => {
  await expect(page.locator('main')).toBeVisible();
});
```

### Accessibility Testing
```javascript
// Check accessibility attributes
const a11y = await TestUtils.verifyAccessibilityAttributes(page);
console.log('Accessibility score:', a11y);
```

## Contributing

### Adding New Tests
1. Create test in appropriate spec file
2. Use existing page object models or create new ones
3. Follow naming conventions: `test('descriptive name', async ({ page }) => {})`
4. Add documentation for complex test scenarios
5. Ensure tests are isolated and can run independently

### Best Practices
- Use descriptive test names
- Keep tests focused and atomic
- Use page object models for reusability
- Add meaningful assertions
- Handle async operations properly
- Clean up after tests (if needed)

## Reporting Issues

When reporting test failures:
1. Include full error message and stack trace
2. Provide screenshot if visual issue
3. Specify browser and environment
4. Include steps to reproduce
5. Note if test was previously passing

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Congressional Transparency Platform README](../../README.md)
- [Component Documentation](../../src/components/README.md)
- [API Documentation](../../../README.md)