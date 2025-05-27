# AWS Account Validation Script

This script validates that each AWS account listed in the `accounts.yaml` file is still referenced on its source webpages.

## Requirements

- Python 3.7+
- Dependencies listed in `requirements.txt`

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the script with:

```bash
python validate_accounts.py
```

By default, this will:
1. Read accounts from `accounts.yaml`
2. Check each account ID against its source URLs
3. Write accounts that are still referenced to `referenced.yaml`

### Command-line Options

The script supports several command-line options:

```
-i, --input-file FILE    Input YAML file (default: accounts.yaml)
-o, --output-file FILE   Output YAML file (default: referenced.yaml)
-l, --limit N            Limit the number of accounts to check (default: 0 = all)
-q, --quiet              Suppress detailed output
-r, --retries N          Number of retries for failed requests (default: 2)
-c, --checkpoint N       Save progress every N accounts (default: 10, 0 to disable)
--resume                 Resume from last checkpoint
--no-headless            Run browser in visible mode (default: headless)
```

### Examples

Check only the first 5 accounts:
```bash
python validate_accounts.py --limit 5
```

Use a different input/output file:
```bash
python validate_accounts.py -i my_accounts.yaml -o valid_accounts.yaml
```

Run in quiet mode:
```bash
python validate_accounts.py -q
```

Increase the number of retries for unreliable connections:
```bash
python validate_accounts.py --retries 5
```

Save a checkpoint every 5 accounts:
```bash
python validate_accounts.py --checkpoint 5
```

Resume from where you left off:
```bash
python validate_accounts.py --resume
```

## How It Works

For each account in the input file, the script:

1. Opens each source URL in a headless browser
2. Searches for the account ID in the page content using multiple methods:
   - Checking the raw HTML
   - Checking the text content
   - Looking in specific elements like code blocks
3. If the account ID is found, adds the account to the output file
4. Periodically saves progress to allow resuming if interrupted

The script includes several features to make it robust:
- Retry mechanism for failed requests
- Graceful handling of interruptions (Ctrl+C)
- Progress tracking with a progress bar
- Checkpointing to save progress and resume later

## Troubleshooting

- If you encounter network issues, try running with `--no-headless` to see what's happening in the browser
- Some websites may block automated access; in this case, try increasing the number of retries with `--retries`
- If the script is too slow, use the `--limit` option to test with a smaller number of accounts first
- If the script gets interrupted, use `--resume` to continue from where it left off
- For websites that load content dynamically, you might need to modify the script to wait longer for content to load
