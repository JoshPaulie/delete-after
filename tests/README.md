# Delete After - Test Scenarios

This directory contains test scenarios for the recursive delete functionality.

## Test Structures

### test_recursive/
Simple test case with:
- Root directory with `.delete_after` set to "1 minute"
- Files in subdirectories (season1/, season2/) that should be processed recursively
- Demonstrates basic recursive functionality

### media_library/
Realistic media library structure demonstrating:
- **The_Office/**: Has `.delete_after` set to "1 week"
  - All seasons (Season_01/, Season_02/) inherit this rule
  - Files older than 1 week in any season will be deleted
  
- **Breaking_Bad/**: Has `.delete_after` set to "2 weeks"
  - Season_01/ inherits the 2-week rule
  - Season_02/ has its own `.delete_after` set to "3 days" (overrides parent)
  - Demonstrates how child directories can override parent rules

## Testing the Implementation

To test these scenarios:

```bash
# Dry run on the entire media library
python delete_after.py --dry-run --verbose tests/media_library

# Test specific show (recursive processing)
python delete_after.py --dry-run --verbose tests/media_library/TV_Shows/The_Office

# Test specific season with override
python delete_after.py --dry-run --verbose tests/media_library/TV_Shows/Breaking_Bad/Season_02
```

## Expected Behavior

1. **Recursive Processing**: When a directory has a `.delete_after` file, it applies to all files in subdirectories
2. **Override Behavior**: Child directories with their own `.delete_after` files are processed independently
3. **Media Use Case**: Perfect for managing TV series where you want:
   - Series-level deletion rules (e.g., "delete after 1 week")
   - Season-specific overrides (e.g., "keep current season for 3 days only")

## Making Files Old for Testing

To make files appear old for testing:

```bash
# Make files appear to be from 2 weeks ago
touch -t 202506070900 tests/media_library/TV_Shows/The_Office/Season_01/*.mkv

# Make files appear to be from 1 month ago  
touch -t 202505210900 tests/media_library/TV_Shows/Breaking_Bad/Season_01/*.mkv
```
