# Delete After - Automatic File Cleanup Script

A Python script that scans directories for `.delete_after` files and automatically deletes files based on specified durations.

I personally use it to automatically delete my wife's reality TV shows after a week, but I'm sure others would fine other use cases.

Can be ran manually or automated using various scheduling methods like cron, systemd timers, or other task schedulers. Cron jobs are recommended for their simplicity and reliability.

> [!Important]
> Considering the script involves *permanently deleting* your files, use at your own discretion.

## Features

- Recursive directory scanning with hierarchical configuration
- Safe operation (only processes directories with `.delete_after` files)
- Flexible time units (minutes, hours, days, weeks, months, years)
- Dry-run mode and comprehensive logging
- Can be used with other schedulers (cron, etc.)

## Installation

This installation guide covers setting up cron jobs for automatic scheduling, supporting both system-wide and user-specific configurations.

### 1. Download the Project

```bash
git clone https://github.com/JoshPaulie/delete-after.git
cd delete-after
```

### 2. Install the Script

#### For System-Wide Installation (Recommended for system-level directories)

```bash
sudo cp delete_after.py /usr/local/bin/
sudo chmod +x /usr/local/bin/delete_after.py
```

#### For User Installation (User-specific directories)

```bash
mkdir -p ~/.local/bin
cp delete_after.py ~/.local/bin/
chmod +x ~/.local/bin/delete_after.py

# Note: Ensure your directory is on your $PATH
```

### 3. Configure Cron Jobs

#### System-Wide Cron Job

For system-level directories like `/tmp`, `/var/tmp`, or shared directories (requires root access):

```bash
sudo crontab -e
```

Add a line to run the cleanup daily at 3 AM (adjust paths as needed):

```cron
# Run delete-after cleanup daily at 3:00 AM
0 3 * * * /usr/local/bin/delete_after.py /tmp /var/tmp /opt/shared/downloads
```

#### User Cron Job

For user-specific directories like downloads, cache, or temporary work files:

```bash
crontab -e
```

Add a line to run the cleanup daily at 3 AM:

```cron
# Run delete-after cleanup daily at 3:00 AM
0 3 * * * ~/.local/bin/delete_after.py /home/username/Downloads /home/username/.cache/temp /home/username/workspace/temp
```

### 4. Common Cron Schedule Examples

```cron
# Daily at 3:00 AM
0 3 * * * /path/to/delete_after.py /your/temp/path

# Every 6 hours
0 */6 * * * /path/to/delete_after.py /your/temp/path

# Weekly on Sunday at 2:00 AM
0 2 * * 0 /path/to/delete_after.py /your/temp/path

# Twice daily (6 AM and 6 PM)
0 6,18 * * * /path/to/delete_after.py /your/temp/path
```

### 5. Verify Installation

Check that your cron job is scheduled:

```bash
# For user cron jobs
crontab -l

# For system cron jobs
sudo crontab -l
```

Check script execution logs:

```bash
# System-wide installation logs
sudo tail -f /var/log/delete_after.log

# User installation logs
tail -f ~/delete_after.log

# Also check cron execution logs
sudo tail -f /var/log/cron
# or
grep CRON /var/log/syslog
```

## Usage

### Command Line

```bash
delete_after.py /tmp                                 # Run once on temporary directory
delete_after.py --dry-run ~/Downloads                # Test mode on downloads folder
delete_after.py --verbose /var/tmp                   # Verbose logging on system temp
```

### Alternative Scheduling Methods

While this guide focuses on cron jobs, the script can be scheduled using other methods:

- **Systemd timers:** For systems that prefer systemd-based scheduling
- **Task schedulers:** Use your system's preferred task scheduler  
- **Manual execution:** Run as needed from command line or scripts

## Configuration

### .delete_after File Format

Create a `.delete_after` file in any directory you want monitored:

```
<number> <unit>
```

**Supported units:**

| Unit    | Abbreviations                   | Example      |
| ------- | ------------------------------- | ------------ |
| Minutes | `minute`, `minutes`, `min`, `m` | `30 minutes` |
| Hours   | `hour`, `hours`, `hr`, `h`      | `2.5 hours`  |
| Days    | `day`, `days`, `d`              | `7 days`     |
| Weeks   | `week`, `weeks`, `w`            | `2 weeks`    |
| Months  | `month`, `months`, `mo`         | `1 month`    |
| Years   | `year`, `years`, `yr`, `y`      | `1 year`     |

**Examples:**
```bash
echo "30 days" > ~/Downloads/.delete_after
echo "2 weeks" > /tmp/project_cache/.delete_after  
echo "1 week" > /media/series
echo "3 days" > /var/tmp/logs/.delete_after
```

### How It Works

- Files are deleted recursively from directories containing `.delete_after` files
- Child directories can override parent rules with their own `.delete_after` files
- Only files older than the specified duration are deleted
- `.delete_after` files themselves are never deleted

### Example Directory Structure

```
/tmp/
├── .delete_after              # "1 week" - default for temp files
├── project_builds/
│   ├── build_artifacts/       # Files deleted after 1 week (inherits)
│   └── cache/
│       ├── .delete_after      # "3 days" (overrides parent)
│       └── temp_data.json     # Kept for 3 days
├── downloads/
│   ├── .delete_after          # "30 days" - default for downloads
│   ├── software_packages/     # Files deleted after 30 days
│   └── browser_downloads/
│       ├── .delete_after      # "1 week" (overrides parent)
│       └── temp_file.zip      # Deleted after 1 week
└── logs/
    ├── .delete_after          # "7 days"  
    └── app_logs/              # Log files deleted after 7 days
```

## Troubleshooting

**Cron job not running:**
```bash
# Check if cron service is running
sudo systemctl status cron  # or crond on some systems

# View user cron jobs
crontab -l

# View system cron jobs
sudo crontab -l

# Check script execution logs
sudo tail -f /var/log/delete_after.log  # system-wide
tail -f ~/delete_after.log              # user installation

# Check cron daemon logs
sudo tail -f /var/log/cron
# or on some systems:
grep CRON /var/log/syslog
```

**Files not being deleted:**
```bash
# Test with dry-run on your directory
delete_after.py --dry-run --verbose /tmp

# Check .delete_after file exists and is readable
cat ~/Downloads/.delete_after

# Run manually to check for errors
/usr/local/bin/delete_after.py /your/temp/path
```

**Cron job permissions:**
```bash
# Make sure the script is executable
ls -la /usr/local/bin/delete_after.py  # or ~/.local/bin/delete_after.py

# Ensure cron can access the directories
# For system cron jobs, paths should be accessible by root
# For user cron jobs, paths should be accessible by the user
```

**Report issues:** Include OS version, Python version, cron logs, and error messages.
