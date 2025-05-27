import yaml
import asyncio
from pyppeteer import launch
import sys
import re
import argparse
import os
import time
from tqdm import tqdm
import signal
import json

# Global variable to track if the script is being interrupted
is_interrupted = False

def signal_handler(sig, frame):
    """Handle interrupt signals to gracefully exit."""
    global is_interrupted
    print("\n⚠️ Interrupt received, finishing current task and exiting...")
    is_interrupted = True

# Register the signal handler for SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)

async def check_account_reference(browser, url, account_id, retry_count=2, verbose=False):
    """Check if the account ID is referenced on the given URL."""
    page = None
    for attempt in range(retry_count + 1):
        try:
            if page:
                await page.close()

            page = await browser.newPage()

            # Set a user agent to avoid being blocked
            await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

            # Set extra HTTP headers
            await page.setExtraHTTPHeaders({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            })

            # Navigate to the URL with a timeout
            response = await page.goto(url, {
                'waitUntil': 'networkidle0', 
                'timeout': 60000
            })

            # Check if the page loaded successfully
            if not response:
                if verbose or attempt == retry_count:
                    print(f"⚠️ Failed to load {url}: No response")
                if attempt < retry_count:
                    time.sleep(2)  # Wait before retrying
                    continue
                await page.close()
                return False

            if response.status >= 400:
                if verbose or attempt == retry_count:
                    print(f"⚠️ Failed to load {url}: HTTP {response.status}")
                if attempt < retry_count:
                    time.sleep(2)  # Wait before retrying
                    continue
                await page.close()
                return False

            # Get the page content
            content = await page.content()

            # Check if the account ID is in the page content
            if account_id in content:
                print(f"✅ Account ID {account_id} found in {url}")
                await page.close()
                return True

            # Try multiple search methods

            # Method 1: Check in body text
            found = await page.evaluate(f'document.body.innerText.includes("{account_id}")')
            if found:
                print(f"✅ Account ID {account_id} found in {url} (in text content)")
                await page.close()
                return True

            # Method 2: Check in specific elements that might contain the account ID
            selectors = ['pre', 'code', '.blob-code', '.highlight']
            for selector in selectors:
                try:
                    # Use JavaScript to find elements and check their content
                    found = await page.evaluate(f'''
                        (() => {{
                            const elements = document.querySelectorAll('{selector}');
                            for (const el of elements) {{
                                if (el.textContent.includes('{account_id}')) {{
                                    return true;
                                }}
                            }}
                            return false;
                        }})()
                    ''')

                    if found:
                        print(f"✅ Account ID {account_id} found in {url} (in {selector} element)")
                        await page.close()
                        return True
                except Exception:
                    pass  # Ignore errors for individual selectors

            # Not found after all checks
            print(f"❌ Account ID {account_id} NOT found in {url}")
            await page.close()
            return False

        except Exception as e:
            if verbose or attempt == retry_count:
                print(f"⚠️ Error checking {url} for account {account_id} (attempt {attempt+1}/{retry_count+1}): {str(e)}")
            if attempt < retry_count:
                time.sleep(2)  # Wait before retrying
                continue
            if page:
                await page.close()
            return False

    # This should not be reached, but just in case
    if page:
        await page.close()
    return False

async def validate_accounts(args):
    """Validate that each AWS account is still referenced on its source webpages."""
    global is_interrupted

    # Load the accounts.yaml file
    try:
        with open(args.input_file, 'r') as file:
            accounts = yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading {args.input_file}: {str(e)}")
        return

    if not accounts:
        print(f"No accounts found in {args.input_file}")
        return

    print(f"Loaded {len(accounts)} accounts from {args.input_file}")

    # Initialize the browser with options
    browser_args = [
        '--no-sandbox', 
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--disable-gpu'
    ]
    if args.headless:
        browser_args.append('--headless')

    try:
        browser = await launch(
            headless=args.headless,
            args=browser_args,
            ignoreHTTPSErrors=True
        )
    except Exception as e:
        print(f"Failed to launch browser: {str(e)}")
        print("Make sure you have Chrome or Chromium installed.")
        return

    # List to store referenced accounts
    referenced_accounts = []

    # For resuming from a checkpoint
    start_index = 0
    if args.resume and os.path.exists(args.output_file):
        try:
            with open(args.output_file, 'r') as file:
                referenced_accounts = yaml.safe_load(file) or []

            # Find the index to resume from
            if referenced_accounts:
                last_account = referenced_accounts[-1]
                for i, account in enumerate(accounts):
                    if account.get('name') == last_account.get('name') and account.get('accounts') == last_account.get('accounts'):
                        start_index = i + 1
                        break

                print(f"Resuming from account #{start_index} (after '{last_account.get('name')}')")
        except Exception as e:
            print(f"Error loading checkpoint from {args.output_file}: {str(e)}")
            referenced_accounts = []

    # Slice the accounts list based on limit and start_index
    if args.limit > 0:
        end_index = min(start_index + args.limit, len(accounts))
        accounts_to_process = accounts[start_index:end_index]
    else:
        accounts_to_process = accounts[start_index:]

    # Process each account with a progress bar
    with tqdm(total=len(accounts_to_process), desc="Validating accounts") as pbar:
        for account in accounts_to_process:
            if is_interrupted:
                print("Interrupted by user. Saving progress...")
                break

            name = account.get('name', 'Unknown')
            sources = account.get('source', [])
            account_ids = account.get('accounts', [])

            if not sources:
                if not args.quiet:
                    print(f"Skipping {name} - No sources provided")
                pbar.update(1)
                continue

            account_referenced = False

            for account_id in account_ids:
                if is_interrupted:
                    break

                # Check each source for the account ID
                for source in sources:
                    if is_interrupted:
                        break

                    is_referenced = await check_account_reference(
                        browser, 
                        source, 
                        account_id,
                        retry_count=args.retries,
                        verbose=not args.quiet
                    )

                    if is_referenced:
                        account_referenced = True
                        break

                if account_referenced:
                    break

            if account_referenced:
                # Add the account to the referenced accounts list
                referenced_accounts.append(account)
                if not args.quiet:
                    print(f"Added {name} to referenced accounts")
            else:
                if not args.quiet:
                    print(f"Account {name} is not referenced in any of its sources")

            # Save progress periodically
            if args.checkpoint > 0 and len(referenced_accounts) % args.checkpoint == 0:
                try:
                    with open(args.output_file, 'w') as file:
                        yaml.dump(referenced_accounts, file, default_flow_style=False)
                    if not args.quiet:
                        print(f"Checkpoint saved to {args.output_file}")
                except Exception as e:
                    print(f"Error saving checkpoint: {str(e)}")

            pbar.update(1)

    # Close the browser
    await browser.close()

    # Write the referenced accounts to output file
    try:
        with open(args.output_file, 'w') as file:
            yaml.dump(referenced_accounts, file, default_flow_style=False)

        print(f"Validation complete. {len(referenced_accounts)} accounts are still referenced.")
        print(f"Results written to {args.output_file}")
    except Exception as e:
        print(f"Error writing to {args.output_file}: {str(e)}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Validate AWS account references in source URLs.')
    parser.add_argument('-i', '--input-file', default='accounts.yaml', help='Input YAML file (default: accounts.yaml)')
    parser.add_argument('-o', '--output-file', default='referenced.yaml', help='Output YAML file (default: referenced.yaml)')
    parser.add_argument('-l', '--limit', type=int, default=0, help='Limit the number of accounts to check (default: 0 = all)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress detailed output')
    parser.add_argument('-r', '--retries', type=int, default=2, help='Number of retries for failed requests (default: 2)')
    parser.add_argument('-c', '--checkpoint', type=int, default=10, help='Save progress every N accounts (default: 10, 0 to disable)')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    parser.add_argument('--no-headless', dest='headless', action='store_false', help='Run browser in visible mode')
    parser.set_defaults(headless=True)
    return parser.parse_args()

if __name__ == "__main__":
    try:
        args = parse_arguments()
        asyncio.get_event_loop().run_until_complete(validate_accounts(args))
    except KeyboardInterrupt:
        print("\nScript terminated by user.")
    except Exception as e:
        print(f"Unhandled error: {str(e)}")
        import traceback
        traceback.print_exc()
