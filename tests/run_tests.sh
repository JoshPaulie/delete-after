#!/bin/bash

# Test script for delete_after recursive functionality

echo "=== Delete After - Test Suite ==="
echo

# Function to make files old
age_files() {
    local dir="$1"
    local timestamp="$2"
    local description="$3"
    
    echo "Making files in $dir appear $description..."
    find "$dir" -name "*.mkv" -exec touch -t "$timestamp" {} \;
}

# Function to run test
run_test() {
    local test_dir="$1"
    local description="$2"
    
    echo
    echo "=== $description ==="
    echo "Testing directory: $test_dir"
    python ../delete_after.py --dry-run --verbose "$test_dir"
    echo
}

# Navigate to tests directory
cd "$(dirname "$0")" || exit 1

echo "Setting up test files with old timestamps..."

# Make The Office files 2 weeks old (should be deleted - 1 week limit)
age_files "media_library/TV_Shows/The_Office" "202506070900" "2 weeks old"

# Make Breaking Bad Season 1 files 3 weeks old (should be deleted - 2 week limit)
age_files "media_library/TV_Shows/Breaking_Bad/Season_01" "202505310900" "3 weeks old"

# Make Breaking Bad Season 2 files 1 week old (should be deleted - 3 day limit)
age_files "media_library/TV_Shows/Breaking_Bad/Season_02" "202506140900" "1 week old"

echo "Test file ages set up!"
echo

# Run tests
run_test "test_recursive" "Basic Recursive Test (1 minute limit)"

run_test "media_library/TV_Shows/The_Office" "TV Series Test - The Office (1 week limit, recursive)"

run_test "media_library/TV_Shows/Breaking_Bad" "TV Series Test - Breaking Bad (mixed limits)"

run_test "media_library/TV_Shows/Breaking_Bad/Season_02" "Season Override Test - Breaking Bad S02 (3 day limit)"

run_test "media_library" "Full Media Library Test"

echo "=== Test Suite Complete ==="
echo "All tests run in dry-run mode. No files were actually deleted."
