#!/usr/bin/env node

/**
 * Congressional Transparency Platform Test Runner
 *
 * This script helps run the Playwright test suite with various options
 * and provides helpful output for debugging and monitoring.
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const http = require('http');

// ANSI color codes for console output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m'
};

function colorize(text, color) {
  return `${colors[color]}${text}${colors.reset}`;
}

function log(message, color = 'white') {
  console.log(colorize(message, color));
}

function logSection(title) {
  console.log('\n' + colorize('='.repeat(60), 'cyan'));
  console.log(colorize(`  ${title}`, 'cyan'));
  console.log(colorize('='.repeat(60), 'cyan') + '\n');
}

async function checkPrerequisites() {
  logSection('Checking Prerequisites');

  // Check if node_modules exists
  if (!fs.existsSync('node_modules')) {
    log('❌ node_modules not found. Run: pnpm install', 'red');
    return false;
  }

  // Check if Playwright is installed
  if (!fs.existsSync('node_modules/@playwright')) {
    log('❌ Playwright not found. Run: pnpm add -D @playwright/test', 'red');
    return false;
  }

  // Check if test files exist
  const testDir = 'tests/e2e';
  if (!fs.existsSync(testDir)) {
    log(`❌ Test directory not found: ${testDir}`, 'red');
    return false;
  }

  // Check if playwright config exists
  if (!fs.existsSync('playwright.config.ts')) {
    log('❌ playwright.config.ts not found', 'red');
    return false;
  }

  log('✅ All prerequisites met', 'green');
  return true;
}

function checkServerStatus() {
  return new Promise((resolve) => {
    const req = http.get('http://localhost:5173', (res) => {
      log('✅ Development server is running on http://localhost:5173', 'green');
      resolve(true);
    });

    req.on('error', () => {
      log('❌ Development server not running. Start with: pnpm run dev', 'red');
      log('   The server must be running on http://localhost:5173', 'yellow');
      resolve(false);
    });

    req.setTimeout(3000, () => {
      req.destroy();
      log('❌ Server check timed out. Is the server running?', 'red');
      resolve(false);
    });
  });
}

function runCommand(command, args = [], options = {}) {
  return new Promise((resolve, reject) => {
    log(`Running: ${command} ${args.join(' ')}`, 'blue');

    const child = spawn(command, args, {
      stdio: 'inherit',
      shell: true,
      ...options
    });

    child.on('close', (code) => {
      if (code === 0) {
        resolve(code);
      } else {
        reject(new Error(`Command failed with exit code ${code}`));
      }
    });

    child.on('error', (error) => {
      reject(error);
    });
  });
}

async function installBrowsers() {
  logSection('Installing Playwright Browsers');

  try {
    await runCommand('npx', ['playwright', 'install']);
    log('✅ Browsers installed successfully', 'green');
    return true;
  } catch (error) {
    log('❌ Failed to install browsers', 'red');
    log(error.message, 'red');
    return false;
  }
}

async function runTests(options = {}) {
  logSection('Running Tests');

  const args = ['playwright', 'test'];

  // Add options based on parameters
  if (options.headed) args.push('--headed');
  if (options.debug) args.push('--debug');
  if (options.ui) args.push('--ui');
  if (options.browser) args.push('--project', options.browser);
  if (options.grep) args.push('--grep', options.grep);
  if (options.reporter) args.push('--reporter', options.reporter);
  if (options.workers) args.push('--workers', options.workers);

  // Add specific test file if provided
  if (options.testFile) {
    args.push(`tests/e2e/${options.testFile}`);
  }

  try {
    await runCommand('npx', args);
    log('✅ Tests completed successfully', 'green');
    return true;
  } catch (error) {
    log('❌ Tests failed', 'red');
    return false;
  }
}

function showHelp() {
  logSection('Congressional Transparency Platform Test Runner');

  console.log(colorize('Usage:', 'yellow'));
  console.log('  node test-runner.cjs [command] [options]\n');

  console.log(colorize('Commands:', 'yellow'));
  console.log('  check       Check prerequisites and server status');
  console.log('  install     Install Playwright browsers');
  console.log('  run         Run tests (default)');
  console.log('  ui          Run tests with UI mode');
  console.log('  debug       Run tests in debug mode');
  console.log('  headed      Run tests in headed mode (visible browser)');
  console.log('  report      Show test report\n');

  console.log(colorize('Test Suites:', 'yellow'));
  console.log('  platform    Run main platform tests');
  console.log('  export      Run export functionality tests');
  console.log('  performance Run performance tests');
  console.log('  all         Run all tests (default)\n');

  console.log(colorize('Options:', 'yellow'));
  console.log('  --browser [chrome|firefox|safari|edge]  Run on specific browser');
  console.log('  --grep [pattern]                         Run tests matching pattern');
  console.log('  --workers [number]                       Number of parallel workers');
  console.log('  --reporter [html|json|line]              Test reporter\n');

  console.log(colorize('Examples:', 'yellow'));
  console.log('  node test-runner.cjs check');
  console.log('  node test-runner.cjs run platform');
  console.log('  node test-runner.cjs ui');
  console.log('  node test-runner.cjs debug --grep "dashboard"');
  console.log('  node test-runner.cjs run --browser chrome --workers 1');
}

async function main() {
  const args = process.argv.slice(2);
  const command = args[0] || 'run';
  const suite = args[1];

  // Parse options
  const options = {};
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith('--')) {
      const key = arg.substring(2);
      const value = args[i + 1];
      options[key] = value || true;
      i++; // Skip next argument as it's the value
    }
  }

  switch (command) {
    case 'help':
    case '--help':
    case '-h':
      showHelp();
      break;

    case 'check':
      logSection('System Check');
      const prereqsOk = await checkPrerequisites();
      const serverOk = await checkServerStatus();

      if (prereqsOk && serverOk) {
        log('\n✅ System ready for testing!', 'green');
        process.exit(0);
      } else {
        log('\n❌ System not ready. Please fix issues above.', 'red');
        process.exit(1);
      }
      break;

    case 'install':
      const installOk = await installBrowsers();
      process.exit(installOk ? 0 : 1);
      break;

    case 'report':
      try {
        await runCommand('npx', ['playwright', 'show-report']);
      } catch (error) {
        log('❌ Failed to show report', 'red');
        process.exit(1);
      }
      break;

    case 'ui':
      const prereqsUi = await checkPrerequisites();
      const serverUi = await checkServerStatus();

      if (!prereqsUi || !serverUi) process.exit(1);

      await runTests({ ui: true, ...options });
      break;

    case 'debug':
      const prereqsDebug = await checkPrerequisites();
      const serverDebug = await checkServerStatus();

      if (!prereqsDebug || !serverDebug) process.exit(1);

      await runTests({ debug: true, ...options });
      break;

    case 'headed':
      const prereqsHeaded = await checkPrerequisites();
      const serverHeaded = await checkServerStatus();

      if (!prereqsHeaded || !serverHeaded) process.exit(1);

      await runTests({ headed: true, ...options });
      break;

    case 'run':
    default:
      // Check prerequisites
      const prereqsRun = await checkPrerequisites();
      const serverRun = await checkServerStatus();

      if (!prereqsRun || !serverRun) {
        log('\nTo start the development server:', 'yellow');
        log('  pnpm run dev', 'cyan');
        process.exit(1);
      }

      // Determine test file based on suite
      let testFile = '';
      switch (suite) {
        case 'platform':
          testFile = 'congress-platform.spec.ts';
          break;
        case 'export':
          testFile = 'export-functionality.spec.ts';
          break;
        case 'performance':
          testFile = 'performance.spec.ts';
          break;
        case 'all':
        default:
          // Run all tests
          break;
      }

      const testOptions = {
        testFile,
        reporter: 'html',
        ...options
      };

      const success = await runTests(testOptions);

      if (success) {
        logSection('Test Summary');
        log('✅ All tests passed!', 'green');
        log('📊 View detailed report: pnpm run test:e2e:report', 'blue');
        log('🔍 Screenshots saved in: tests/screenshots/', 'blue');
      } else {
        logSection('Test Summary');
        log('❌ Some tests failed', 'red');
        log('📊 View detailed report: pnpm run test:e2e:report', 'blue');
        log('🐛 Run with debug: node test-runner.cjs debug', 'yellow');
      }

      process.exit(success ? 0 : 1);
  }
}

// Run the main function
main().catch((error) => {
  log(`\n❌ Unexpected error: ${error.message}`, 'red');
  process.exit(1);
});

module.exports = {
  checkPrerequisites,
  checkServerStatus,
  runTests,
  installBrowsers
};