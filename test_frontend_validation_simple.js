#!/usr/bin/env node
/**
 * Simple frontend validation using basic Node.js HTTP client
 *
 * Tests that the React viewer application:
 * 1. Server responds correctly
 * 2. Returns HTML content
 * 3. Contains expected React elements
 */

const http = require('http');
const https = require('https');

// Configuration
const CONFIG = {
    baseUrl: 'http://localhost:5173',
    timeout: 10000
};

class SimpleFrontendValidator {
    constructor() {
        this.errors = [];
        this.warnings = [];
        this.successes = [];
    }

    async testServerConnection() {
        console.log('\n📡 Testing server connection...');

        return new Promise((resolve) => {
            const req = http.get(CONFIG.baseUrl, (res) => {
                if (res.statusCode === 200) {
                    this.success(`Server responding with status ${res.statusCode}`);

                    let body = '';
                    res.on('data', (chunk) => {
                        body += chunk;
                    });

                    res.on('end', () => {
                        this.analyzeResponse(body);
                        resolve(true);
                    });
                } else {
                    this.error(`Server returned status: ${res.statusCode}`);
                    resolve(false);
                }
            });

            req.on('error', (error) => {
                this.error(`Failed to connect to server: ${error.message}`);
                this.warning('Make sure the dev server is running: cd congress-viewer && pnpm run dev');
                resolve(false);
            });

            req.setTimeout(CONFIG.timeout, () => {
                this.error('Server connection timed out');
                req.destroy();
                resolve(false);
            });
        });
    }

    analyzeResponse(body) {
        console.log('\n📄 Analyzing response content...');

        // Check if response contains HTML
        if (body.includes('<html') || body.includes('<!DOCTYPE html')) {
            this.success('Response contains HTML document');
        } else {
            this.warning('Response does not appear to be HTML');
        }

        // Check for React indicators
        const reactIndicators = [
            { name: 'React root div', pattern: 'id="root"' },
            { name: 'React scripts', pattern: 'react' },
            { name: 'Vite dev server', pattern: '@vite' },
            { name: 'JavaScript modules', pattern: 'type="module"' },
            { name: 'Title tag', pattern: '<title>' }
        ];

        reactIndicators.forEach(indicator => {
            if (body.toLowerCase().includes(indicator.pattern.toLowerCase())) {
                this.success(`Found ${indicator.name}`);
            } else {
                this.warning(`${indicator.name} not detected`);
            }
        });

        // Check content length
        if (body.length > 1000) {
            this.success(`Response has substantial content (${body.length} characters)`);
        } else if (body.length > 100) {
            this.warning(`Response has minimal content (${body.length} characters)`);
        } else {
            this.error(`Response has very little content (${body.length} characters)`);
        }

        // Check for error indicators
        const errorIndicators = ['error', 'exception', 'failed', 'not found'];
        const lowerBody = body.toLowerCase();

        let hasErrors = false;
        errorIndicators.forEach(errorText => {
            if (lowerBody.includes(errorText)) {
                this.warning(`Response contains error indicator: "${errorText}"`);
                hasErrors = true;
            }
        });

        if (!hasErrors) {
            this.success('No obvious error indicators in response');
        }

        // Look for React/Vite specific content
        if (body.includes('localhost:5173') || body.includes('vite')) {
            this.success('Vite development server detected');
        }

        if (body.includes('React') || body.includes('_react')) {
            this.success('React framework detected');
        }
    }

    async testAPIEndpoints() {
        console.log('\n🔗 Testing potential API endpoints...');

        const endpoints = [
            '/api/health',
            '/api/status',
            '/health',
            '/status'
        ];

        for (const endpoint of endpoints) {
            try {
                const url = CONFIG.baseUrl + endpoint;
                const result = await this.makeRequest(url);

                if (result.success) {
                    this.success(`API endpoint ${endpoint} is accessible`);
                } else {
                    // This is expected - not all endpoints may exist
                    console.log(`ℹ️  API endpoint ${endpoint} not found (this is normal)`);
                }
            } catch (error) {
                // Expected for non-existent endpoints
            }
        }
    }

    makeRequest(url) {
        return new Promise((resolve) => {
            const req = http.get(url, (res) => {
                resolve({
                    success: res.statusCode < 400,
                    status: res.statusCode
                });
            });

            req.on('error', () => {
                resolve({ success: false, status: 0 });
            });

            req.setTimeout(2000, () => {
                req.destroy();
                resolve({ success: false, status: 0 });
            });
        });
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
        console.log('SIMPLE FRONTEND VALIDATION SUMMARY');
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

        const isSuccess = this.errors.length === 0 && this.successes.length > 3;

        console.log('\n' + '='.repeat(60));
        if (isSuccess) {
            console.log('🎉 SIMPLE FRONTEND VALIDATION PASSED!');
            console.log('✅ Frontend appears to be working correctly');
        } else {
            console.log('⚠️  SIMPLE FRONTEND VALIDATION COMPLETED WITH ISSUES');
            if (this.errors.length > 0) {
                console.log('❌ Frontend has critical issues');
            } else {
                console.log('⚠️  Frontend may have minor issues but appears functional');
            }
        }
        console.log('='.repeat(60));

        return isSuccess;
    }
}

async function runSimpleFrontendValidation() {
    console.log('='.repeat(60));
    console.log('SIMPLE FRONTEND VALIDATION');
    console.log('='.repeat(60));
    console.log(`Testing: ${CONFIG.baseUrl}`);
    console.log('Make sure the dev server is running: cd congress-viewer && pnpm run dev');
    console.log('='.repeat(60));

    const validator = new SimpleFrontendValidator();

    try {
        const connectionSuccess = await validator.testServerConnection();

        if (connectionSuccess) {
            await validator.testAPIEndpoints();
        }

        return validator.printSummary();

    } catch (error) {
        validator.error(`Test execution failed: ${error.message}`);
        console.error('Full error:', error);
        return false;
    }
}

// Main execution
if (require.main === module) {
    runSimpleFrontendValidation()
        .then(success => {
            process.exit(success ? 0 : 1);
        })
        .catch(error => {
            console.error('Fatal error:', error);
            process.exit(1);
        });
}

module.exports = { runSimpleFrontendValidation, SimpleFrontendValidator };