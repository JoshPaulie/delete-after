# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - June 22, 2025

### Added
- Initial release of automatic file cleanup script
- Recursive directory scanning with `.delete_after` configuration files
- Support for flexible time units (minutes, hours, days, weeks, months, years)
- Dry-run mode for safe testing before actual deletion
- Comprehensive logging with configurable verbosity
- Command-line interface with directory path argument
- Test suite with sample media library structure

### Features
- Hierarchical configuration inheritance
- Safe operation (only processes directories with `.delete_after` files)
- Automatic log file management (system or user home directory)
- Cross-platform compatibility

