#!/usr/bin/env python3
"""
Master test runner for the Senate Gov project.

Runs all validation tests for both Python consolidation and frontend fixes.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command, description, critical=True):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"RUNNING: {description}")
    print(f"COMMAND: {command}")
    print("=" * 60)

    try:
        # Change to the directory containing the script
        project_dir = Path(__file__).parent

        result = subprocess.run(
            command,
            check=False,
            shell=True,
            cwd=project_dir,
            capture_output=False,  # Show output in real time
            text=True,
        )

        success = result.returncode == 0

        if success:
            print(f"\n✅ {description} PASSED")
        else:
            print(f"\n❌ {description} FAILED (Exit code: {result.returncode})")
            if critical:
                print("This is a critical failure!")

        return success

    except Exception as e:
        print(f"\n💥 {description} CRASHED: {e}")
        return False


def check_prerequisites():
    """Check that required components are available"""
    print("🔍 Checking prerequisites...")

    # Check Python
    try:
        python_version = subprocess.check_output(
            [sys.executable, "--version"], text=True
        ).strip()
        print(f"✅ Python: {python_version}")
    except Exception as e:
        print(f"❌ Python check failed: {e}")
        return False

    # Check if core package exists
    core_path = Path(__file__).parent / "core"
    if core_path.exists():
        print("✅ Core package directory exists")
    else:
        print("❌ Core package directory missing")
        return False

    # Check if test files exist
    test_files = [
        "test_core_package.py",
        "test_consolidation_validation.py",
        "test_frontend_validation_simple.js",
    ]

    missing_files = []
    for test_file in test_files:
        test_path = Path(__file__).parent / test_file
        if test_path.exists():
            print(f"✅ {test_file} exists")
        else:
            print(f"❌ {test_file} missing")
            missing_files.append(test_file)

    if missing_files:
        print(f"❌ Missing test files: {missing_files}")
        return False

    # Check if frontend server is running
    try:
        import urllib.request

        urllib.request.urlopen("http://localhost:5173", timeout=5)
        print("✅ Frontend server is running on localhost:5173")
    except:
        print("⚠️  Frontend server not detected (localhost:5173)")
        print("   Start it with: cd congress-viewer && pnpm run dev")
        # Not critical for Python tests

    print("\n✅ Prerequisites check completed")
    return True


def main():
    """Main test runner"""
    print("🚀 SENATE GOV PROJECT - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print("Testing Python consolidation and frontend fixes")
    print("=" * 60)

    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed!")
        return False

    all_results = []

    # 1. Core Package Unit Tests
    success = run_command(
        f"{sys.executable} test_core_package.py",
        "Core Package Unit Tests",
        critical=True,
    )
    all_results.append(("Core Package Unit Tests", success))

    # 2. Consolidation Validation Tests
    success = run_command(
        f"{sys.executable} test_consolidation_validation.py",
        "Python Consolidation Validation",
        critical=True,
    )
    all_results.append(("Python Consolidation Validation", success))

    # 3. Simple Frontend Validation
    success = run_command(
        "node test_frontend_validation_simple.js",
        "Frontend Validation (Simple)",
        critical=False,  # Less critical if Node.js issues
    )
    all_results.append(("Frontend Validation", success))

    # Print final summary
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST SUITE SUMMARY")
    print("=" * 60)

    total_tests = len(all_results)
    passed_tests = sum(1 for _, success in all_results if success)
    failed_tests = total_tests - passed_tests

    print(f"Total Test Suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")

    print("\nDETAILED RESULTS:")
    for test_name, success in all_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")

    overall_success = failed_tests == 0

    print("\n" + "=" * 60)
    if overall_success:
        print("🎉 ALL TEST SUITES PASSED!")
        print("✅ Python consolidation is working correctly")
        print("✅ Frontend fixes are working correctly")
        print("✅ The project is ready for use")
    else:
        print("⚠️  SOME TEST SUITES FAILED")
        if any(
            name in ["Core Package Unit Tests", "Python Consolidation Validation"]
            for name, success in all_results
            if not success
        ):
            print("❌ Critical Python issues detected")
        else:
            print("⚠️  Non-critical issues detected (likely frontend/Node.js)")
    print("=" * 60)

    # Additional guidance
    if not overall_success:
        print("\n📋 TROUBLESHOOTING GUIDE:")
        for test_name, success in all_results:
            if not success:
                if "Core Package" in test_name:
                    print(f"  ❌ {test_name}:")
                    print("     - Check that the core package is properly installed")
                    print("     - Verify all dependencies are available")
                    print("     - Check for import errors")
                elif "Consolidation" in test_name:
                    print(f"  ❌ {test_name}:")
                    print("     - Check that original scripts still work")
                    print("     - Verify backward compatibility")
                    print("     - Check for breaking changes")
                elif "Frontend" in test_name:
                    print(f"  ❌ {test_name}:")
                    print(
                        "     - Make sure frontend server is running: cd congress-viewer && pnpm run dev"
                    )
                    print("     - Check that Node.js is installed")
                    print("     - Verify the React app builds correctly")

    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
