![Python](https://img.shields.io/badge/Python-3.x-blue)
![Status](https://img.shields.io/badge/status-active-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

# Proxy Strainer

Proxy Strainer is a high-performance Python utility designed to validate, and filter public proxies. It uses concurrent threading to rapidly test proxy lists for syntax accuracy and connectivity, performing multiple rounds of verification to ensure only the most reliable proxies make it to your final list.

## Features
- Multi-Stage Validation: Performs an initial check, retries specific network errors (timeouts/connection issues), and executes a final "double-check" pass for maximum reliability.

- Syntax Filtering: Uses Regex and URL parsing to validate proxy formats (IP:Port or Protocol-based http:// socks5:// https:// etc..) before testing connectivity.

- High Concurrency: Utilizes ThreadPoolExecutor with configurable worker counts (defaulting to 120) for rapid processing.

- Smart Error Handling: Categorizes failures (Timeout, IP Mismatch, Proxy Error) and logs them for debugging or retries.

- SOCKS5 Extraction: Automatically identifies and isolates SOCKS5 proxies into a dedicated file, this feature can be configured to extract any specific type you need.

## Performance showcase
#### These are some examples of the output

Run-example (full logic with retries):

Checking 2193 proxies
starting at: 2026-04-16 00:40:11
completed at: 2026-04-16 00:44:10

Re-checking 1356 read-timeout and connection-error proxies
starting at: 2026-04-16 00:44:10
completed at: 2026-04-16 00:46:59

Checking 398 proxies
starting second try at: 2026-04-16 00:46:59
completed at: 2026-04-16 00:47:40

initially: 2193
after first check: 398
after second check: 171

Changed logic for quick checks:

Checking 2203 proxies

starting at: 2026-04-15 00:59:13
completed at: 2026-04-15 01:01:46

## How It Works

`Input files → Syntax + Request Validation → Retry Engine → Verification → Export files`

1. **Load proxies** from `data/proxies.txt`
2. **Syntax validation** (format check)
3. **Primary test** (HTTP request test)
4. **Retry failed proxies** (timeouts + connection errors)
5. **Double verification** (ensures reliability)
6. **Export results**
   - `1check.txt` → first-pass valid proxies
   - `2check.txt` → fully verified proxies
   - `socks5.txt` → SOCKS5-only proxies

# Prerequisites
Python 3.x

Requests Library:


```Bash
pip install requests
```

## File Structure (Important for usage)
```plaintext
proxy-validator/
├── strainer.py
├── data/
│   ├── proxies.txt
│   ├── 1check.txt
│   ├── 2check.txt
│   ├── failed_proxies.txt
│   └── socks5.txt
```
#### Additional output files can be configured in the script.

The script expects a data/ directory to manage its I/O:

data/proxies.txt: Your initial raw proxy list.

data/1check.txt: Proxies that passed the first round.

data/2check.txt: Proxies that passed both validation rounds.

data/failed_proxies.txt: A log of failed attempts with error types.

data/socks5.txt: The final subset of verified SOCKS5 proxies.

## Configuration
You can adjust the performance settings directly in the script:

Timeout(line: 117): Located in validate_request, default is 10 seconds.

Max Workers(line: 174): Located in validate_proxies, default is 120 threads.

Retry Logic(line:30): Modify fetch_failed_proxies to include different error types for re-testing.

Main logic(line: 209): Can be configured to whatever your needs are, feel free to adjust it, the code is commented so it should be easy to understand.

# Disclaimer
This tool is intended for testing public proxy lists. Always ensure your web scraping and proxy usage comply with the Terms of Service of the target resources and local regulations.
