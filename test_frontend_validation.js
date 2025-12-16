#!/usr/bin/env node
/**
 * Frontend validation tests using Playwright
 *
 * Tests that the React viewer application:
 * 1. Starts up correctly
 * 2. Navigation works
 * 3. No console errors
 * 4. Responsive design works
 * 5. Key pages load
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Configuration
const CONFIG = {
    baseUrl: 'http://localhost:5173',
    timeout: 30000,
    screenshotDir: './test_screenshots',
    viewports: [
        { name: 'Desktop', width: 1920, height: 1080 },
        { name: 'Tablet', width: 768, height: 1024 },
        { name: 'Mobile', width: 375, height: 812 }
    ]
};

class FrontendValidator {
    constructor() {
        this.browser = null;
        this.context = null;
        this.page = null;
        this.errors = [];
        this.warnings = [];
        this.successes = [];
    }

    async setup() {
        try {
            // Create screenshot directory
            if (!fs.existsSync(CONFIG.screenshotDir)) {
                fs.mkdirSync(CONFIG.screenshotDir, { recursive: true });
            }

            // Launch browser
            console.log('🚀 Launching browser...');
            this.browser = await chromium.launch({
                headless: true,
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            });

            this.context = await this.browser.newContext({
                viewport: CONFIG.viewports[0]
            });

            this.page = await this.context.newPage();

            // Listen for console messages
            this.page.on('console', (msg) => {
                const type = msg.type();
                const text = msg.text();

                if (type === 'error') {
                    this.errors.push(`Console Error: ${text}`);
                } else if (type === 'warning') {
                    this.warnings.push(`Console Warning: ${text}`);
                }
            });

            // Listen for page errors
            this.page.on('pageerror', (error) => {
                this.errors.push(`Page Error: ${error.message}`);
            });

            this.success('Browser setup completed');
            return true;

        } catch (error) {
            this.error(`Browser setup failed: ${error.message}`);
            return false;
        }
    }

    async testServerConnection() {
        console.log('\n📡 Testing server connection...');

        try {
            const response = await this.page.goto(CONFIG.baseUrl, {
                waitUntil: 'networkidle',
                timeout: CONFIG.timeout
            });

            if (response && response.ok()) {
                this.success(`Server responding at ${CONFIG.baseUrl}`);

                // Wait for React to load
                await this.page.waitForTimeout(2000);

                // Check if it's a React app by looking for React root
                const hasReactRoot = await this.page.evaluate(() => {
                    return document.querySelector('#root') !== null ||
                           document.querySelector('[data-reactroot]') !== null ||
                           window.React !== undefined;
                });

                if (hasReactRoot) {
                    this.success('React application detected');
                } else {
                    this.warning('React application not clearly detected');
                }

                return true;
            } else {
                this.error(`Server returned status: ${response?.status()}`);
                return false;
            }

        } catch (error) {
            this.error(`Failed to connect to server: ${error.message}`);
            this.warning('Make sure the dev server is running: cd congress-viewer && pnpm run dev');
            return false;
        }
    }

    async testPageContent() {
        console.log('\n📄 Testing page content...');

        try {
            // Check for basic HTML structure
            const title = await this.page.title();
            if (title) {
                this.success(`Page title: "${title}"`);
            } else {
                this.warning('No page title found');
            }

            // Check for body content
            const bodyText = await this.page.evaluate(() => {
                return document.body.innerText.substring(0, 200);
            });

            if (bodyText && bodyText.trim().length > 0) {
                this.success('Page has content');
                if (bodyText.length > 50) {
                    this.success('Page has substantial content');
                }
            } else {
                this.error('Page appears to be empty');
            }

            // Check for navigation elements
            const hasNavigation = await this.page.evaluate(() => {
                return document.querySelector('nav') !== null ||
                       document.querySelector('[role="navigation"]') !== null ||
                       document.querySelector('header') !== null;
            });

            if (hasNavigation) {
                this.success('Navigation elements found');
            } else {
                this.warning('No clear navigation elements found');
            }

            // Take screenshot
            await this.page.screenshot({
                path: path.join(CONFIG.screenshotDir, 'homepage-desktop.png'),
                fullPage: true
            });
            this.success('Homepage screenshot captured');

            return true;

        } catch (error) {
            this.error(`Page content test failed: ${error.message}`);
            return false;
        }
    }

    async testResponsiveDesign() {
        console.log('\n📱 Testing responsive design...');

        try {
            for (const viewport of CONFIG.viewports) {
                console.log(`  Testing ${viewport.name} (${viewport.width}x${viewport.height})`);

                await this.page.setViewportSize({
                    width: viewport.width,
                    height: viewport.height
                });

                // Wait for any layout changes
                await this.page.waitForTimeout(1000);

                // Take screenshot
                const screenshotPath = path.join(
                    CONFIG.screenshotDir,
                    `homepage-${viewport.name.toLowerCase()}.png`
                );

                await this.page.screenshot({
                    path: screenshotPath,
                    fullPage: true
                });

                this.success(`${viewport.name} screenshot captured`);

                // Check if content is visible
                const isContentVisible = await this.page.evaluate(() => {
                    const body = document.body;
                    return body.scrollHeight > 100 && body.offsetWidth > 100;
                });

                if (isContentVisible) {
                    this.success(`${viewport.name} layout appears correct`);
                } else {
                    this.warning(`${viewport.name} layout may have issues`);
                }
            }

            return true;

        } catch (error) {
            this.error(`Responsive design test failed: ${error.message}`);
            return false;
        }
    }

    async testNavigation() {
        console.log('\n🧭 Testing navigation...');

        try {
            // Reset to desktop viewport
            await this.page.setViewportSize(CONFIG.viewports[0]);

            // Look for clickable elements
            const clickableElements = await this.page.evaluate(() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const links = Array.from(document.querySelectorAll('a[href]'));
                const navItems = Array.from(document.querySelectorAll('[role="button"], .nav-item, .menu-item'));

                return {
                    buttons: buttons.length,
                    links: links.length,
                    navItems: navItems.length,
                    totalClickable: buttons.length + links.length + navItems.length
                };
            });

            if (clickableElements.totalClickable > 0) {
                this.success(`Found ${clickableElements.totalClickable} clickable elements`);
                this.success(`- ${clickableElements.buttons} buttons`);
                this.success(`- ${clickableElements.links} links`);
                this.success(`- ${clickableElements.navItems} nav items`);
            } else {
                this.warning('No clickable elements found');
            }

            // Try to click a navigation element if available
            const firstButton = await this.page.querySelector('button');
            if (firstButton) {
                try {
                    await firstButton.click();
                    await this.page.waitForTimeout(1000);
                    this.success('Successfully clicked a button element');
                } catch (error) {
                    this.warning(`Button click failed: ${error.message}`);
                }
            }

            return true;

        } catch (error) {
            this.error(`Navigation test failed: ${error.message}`);
            return false;
        }
    }

    async testPerformance() {
        console.log('\n⚡ Testing performance...');

        try {
            // Reload page and measure load time
            const startTime = Date.now();
            await this.page.reload({ waitUntil: 'networkidle' });
            const loadTime = Date.now() - startTime;

            if (loadTime < 5000) {
                this.success(`Page loaded in ${loadTime}ms (Good)`);
            } else if (loadTime < 10000) {
                this.warning(`Page loaded in ${loadTime}ms (Slow)`);
            } else {
                this.error(`Page loaded in ${loadTime}ms (Very Slow)`);
            }

            // Check for JavaScript errors that might affect performance
            const jsErrors = this.errors.filter(error =>
                error.includes('Console Error') || error.includes('Page Error')
            );

            if (jsErrors.length === 0) {
                this.success('No JavaScript errors detected');
            } else {
                this.warning(`${jsErrors.length} JavaScript errors detected`);
            }

            return true;

        } catch (error) {
            this.error(`Performance test failed: ${error.message}`);
            return false;
        }
    }

    async testBuildValidation() {
        console.log('\n🔨 Testing if app looks like a proper build...');

        try {
            // Check for development vs production indicators
            const pageSource = await this.page.content();

            // Look for Vite dev server indicators
            const hasViteDevServer = pageSource.includes('vite') ||
                                   pageSource.includes('@vite') ||
                                   await this.page.evaluate(() => window.__vite_is_modern_browser);

            if (hasViteDevServer) {
                this.success('Vite development server detected (expected for dev testing)');
            }

            // Check for React development vs production
            const reactMode = await this.page.evaluate(() => {
                if (typeof window.React !== 'undefined') {
                    return window.React.version ? 'detected' : 'unknown';
                }
                return 'not_detected';
            });

            if (reactMode === 'detected') {
                this.success('React detected in browser');
            } else {
                this.warning('React not clearly detected in browser');
            }

            // Check for basic CSS loading
            const hasStyles = await this.page.evaluate(() => {
                const computedStyle = window.getComputedStyle(document.body);
                return computedStyle.fontFamily !== 'Times' ||
                       computedStyle.backgroundColor !== 'rgba(0, 0, 0, 0)' ||
                       document.querySelectorAll('style, link[rel="stylesheet"]').length > 0;
            });

            if (hasStyles) {
                this.success('CSS styling appears to be loaded');
            } else {
                this.warning('CSS styling may not be loading properly');
            }

            return true;

        } catch (error) {
            this.error(`Build validation failed: ${error.message}`);
            return false;
        }
    }

    async cleanup() {
        try {
            if (this.browser) {
                await this.browser.close();
                this.success('Browser closed successfully');
            }
        } catch (error) {
            this.error(`Cleanup failed: ${error.message}`);
        }
    }

    success(message) {
        this.successes.push(message);
        console.log(`✅ ${message}`);
    }

    warning(message) {
        this.warnings.push(message);
        console.log(`⚠️  ${message}`);
    }

    error(message) {
        this.errors.push(message);
        console.log(`❌ ${message}`);
    }

    printSummary() {
        console.log('\n' + '='.repeat(60));
        console.log('FRONTEND VALIDATION SUMMARY');
        console.log('='.repeat(60));

        console.log(`✅ Successes: ${this.successes.length}`);
        console.log(`⚠️  Warnings: ${this.warnings.length}`);
        console.log(`❌ Errors: ${this.errors.length}`);

        if (this.successes.length > 0) {
            console.log('\nSUCCESSES:');
            this.successes.forEach(success => console.log(`  ✅ ${success}`));
        }

        if (this.warnings.length > 0) {
            console.log('\nWARNINGS:');
            this.warnings.forEach(warning => console.log(`  ⚠️  ${warning}`));
        }

        if (this.errors.length > 0) {
            console.log('\nERRORS:');
            this.errors.forEach(error => console.log(`  ❌ ${error}`));
        }

        const isSuccess = this.errors.length === 0;

        console.log('\n' + '='.repeat(60));
        if (isSuccess) {
            console.log('🎉 FRONTEND VALIDATION PASSED!');
            console.log('✅ React viewer application is working correctly');
        } else {
            console.log('💥 FRONTEND VALIDATION FAILED!');
            console.log('❌ React viewer application has issues');
        }
        console.log('='.repeat(60));

        if (fs.existsSync(CONFIG.screenshotDir)) {
            console.log(`\n📸 Screenshots saved to: ${CONFIG.screenshotDir}`);
        }

        return isSuccess;
    }
}

async function runFrontendValidation() {
    console.log('='.repeat(60));
    console.log('FRONTEND VALIDATION TESTS');
    console.log('='.repeat(60));
    console.log(`Testing: ${CONFIG.baseUrl}`);
    console.log('Make sure the dev server is running: cd congress-viewer && pnpm run dev');
    console.log('='.repeat(60));

    const validator = new FrontendValidator();
    let success = false;

    try {
        // Setup
        const setupSuccess = await validator.setup();
        if (!setupSuccess) {
            return false;
        }

        // Run tests
        await validator.testServerConnection();
        await validator.testPageContent();
        await validator.testResponsiveDesign();
        await validator.testNavigation();
        await validator.testPerformance();
        await validator.testBuildValidation();

        success = validator.printSummary();

    } catch (error) {
        validator.error(`Test execution failed: ${error.message}`);
        console.error('Full error:', error);
    } finally {
        await validator.cleanup();
    }

    return success;
}

// Self-executing check for required dependencies
function checkDependencies() {
    try {
        require('playwright');
        return true;
    } catch (error) {
        console.error('❌ Playwright is not installed!');
        console.error('Install with: npm install playwright');
        console.error('Then install browsers: npx playwright install');
        return false;
    }
}

// Main execution
if (require.main === module) {
    if (!checkDependencies()) {
        process.exit(1);
    }

    runFrontendValidation()
        .then(success => {
            process.exit(success ? 0 : 1);
        })
        .catch(error => {
            console.error('Fatal error:', error);
            process.exit(1);
        });
}

module.exports = { runFrontendValidation, FrontendValidator };