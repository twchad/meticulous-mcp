#!/bin/bash

# Script to run all tests across all projects
# Each project needs to be run from its own directory with proper dependencies

# Don't exit on error - we want to run all tests even if one fails
set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "Running All Tests"
echo "========================================="
echo ""

# Track if any tests failed
FAILED=0

# Function to run tests for a project
run_tests() {
    local project_dir=$1
    local project_name=$2
    shift 2  # Remove first two arguments
    local pytest_args=("$@")  # Remaining arguments for pytest
    
    echo "----------------------------------------"
    echo "Testing: $project_name"
    echo "----------------------------------------"
    
    if [ ! -d "$project_dir" ]; then
        echo "⚠ Directory $project_dir not found, skipping..."
        echo ""
        return
    fi
    
    cd "$project_dir"
    
    # Run pytest with any additional arguments passed to the script
    if pytest "${pytest_args[@]}"; then
        echo "✓ $project_name tests passed"
        echo ""
    else
        echo "✗ $project_name tests failed"
        echo ""
        FAILED=1
    fi
    
    cd "$SCRIPT_DIR"
}

# Run meticulous-mcp tests
if [ -d "meticulous-mcp/tests" ]; then
    run_tests "meticulous-mcp" "meticulous-mcp" "$@"
fi

# Note: pyMeticulous and python-sdk are external dependencies
# Their tests are assumed to work and are not run here

# Summary
echo "========================================="
if [ $FAILED -eq 0 ]; then
    echo "All tests passed! ✓"
    exit 0
else
    echo "Some tests failed! ✗"
    exit 1
fi

