import requests
import re
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from datetime import datetime

""" This is a list of resources to take public proxies from ->

    https://github.com/sunny9577/proxy-scraper/blob/master/proxies.txt
    https://proxyscrape.com/free-proxy-list
    https://github.com/proxifly/free-proxy-list/blob/main/proxies/all/data.txt  # personally recomend this one, all types, big list, good 👍
    https://proxydb.net/?country=
    https://github.com/ErcinDedeoglu/proxies/tree/main/proxies

"""

# Fetchers
def fetch_proxies(filename):
    proxies = []
    with open(filename) as file:
        for line in file:
            clean_line = line.strip()
            if clean_line and not clean_line in proxies:
                proxies.append(clean_line)
    return proxies

def fetch_failed_proxies():
    failed_proxies = []
    errors_to_retry = {"READ_TIMEOUT","CONNECTION_ERROR"}
    with open("data/failed_proxies.txt") as file:
        for line in file:
            parts = line.strip().split(" | ")
            if parts[1] in errors_to_retry:
                failed_proxies.append(parts[0])
    return failed_proxies


BASIC_PROXY_REGEX = re.compile(     #Syntax validation part
    r"""
    ^
    (?:(?P<user>[^:@]+):(?P<pass>[^:@]+)@)?   
    (?P<ip>(\d{1,3}\.){3}\d{1,3})            
    :
    (?P<port>\d{1,5})                        
    $
    """,
    re.VERBOSE
)
SUPPORTED_SCHEMES = {"http", "https", "socks4", "socks5"}

def is_valid_ip(ip: str) -> bool:
    parts = ip.split(".")
    return all(0 <= int(part) <= 255 for part in parts)

def is_valid_port(port: str) -> bool:
    return 1 <= int(port) <= 65535

def validate_basic_proxy(proxy: str) -> bool:
    match = BASIC_PROXY_REGEX.match(proxy)
    if not match:
        return False

    ip = match.group("ip")
    port = match.group("port")

    return is_valid_ip(ip) and is_valid_port(port)

def validate_url_proxy(proxy: str) -> bool:
    try:
        parsed = urlparse(proxy)

        if parsed.scheme not in SUPPORTED_SCHEMES:
            return False

        if not parsed.hostname or not parsed.port:
            return False

        if not is_valid_ip(parsed.hostname):
            return False

        if not is_valid_port(parsed.port):
            return False

        return True
    except Exception:
        return False

def is_syntax_valid_proxy(proxy: str) -> bool:
    return validate_basic_proxy(proxy) or validate_url_proxy(proxy)


def validate_request(proxy):    # Request validation part + timeout configuration
    if "://" in proxy:
        formatted_proxy = proxy
    else:
        formatted_proxy = f'http://{proxy}'

    proxy_dict = {
        'http': formatted_proxy,
        'https': formatted_proxy,
    }

    result = {
        "success": False,
        "proxy": proxy,
        "error_type": None,
        "message": None,
        "status_code": None,
        "response": None
    }

    try:
        response = requests.get(
            'http://httpbin.org/get',
            proxies=proxy_dict,
            timeout=10              # Timeout config
        )

        result["status_code"] = response.status_code
        result["response"] = response.text[:200]

        if response.status_code != 200:
            result["error_type"] = "HTTP_ERROR"
            result["message"] = f"Unexpected status code: {response.status_code}"
            return result

        origin_ip = response.json().get("origin", "")
        parsed_proxy = urlparse(formatted_proxy if "://" in formatted_proxy else f"http://{formatted_proxy}")
        proxy_ip = parsed_proxy.hostname

        if proxy_ip and proxy_ip in origin_ip:
            result["success"] = True
            result["message"] = "Proxy is working and matches origin IP"
        else:
            result["error_type"] = "IP_MISMATCH"
            result["message"] = f"Proxy IP ({proxy_ip}) does not match origin ({origin_ip})"

        return result

    except requests.exceptions.ProxyError as e:
        result["error_type"] = "PROXY_ERROR"
        result["message"] = str(e)[:200]

    except requests.exceptions.ConnectTimeout:
        result["error_type"] = "TIMEOUT"
        result["message"] = "Connection timed out"

    except requests.exceptions.ReadTimeout:
        result["error_type"] = "READ_TIMEOUT"
        result["message"] = "Server did not respond in time"

    except requests.exceptions.ConnectionError as e:
        result["error_type"] = "CONNECTION_ERROR"
        result["message"] = str(e)[:200]

    except requests.exceptions.InvalidURL:
        result["error_type"] = "INVALID_URL"
        result["message"] = "Proxy format is invalid"

    except requests.exceptions.RequestException as e:
        result["error_type"] = "REQUEST_EXCEPTION"
        result["message"] = str(e)[:200]

    except Exception as e:
        result["error_type"] = "UNKNOWN_ERROR"
        result["message"] = str(e)[:200]

    return result
    

file_lock = Lock()

def validate_proxies(exitfile, proxy_list, max_workers=120):   # Main function with worker configuration
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_proxy = {
            executor.submit(validate_request, proxy): proxy
            for proxy in proxy_list
        }

        for future in as_completed(future_to_proxy):
            proxy = future_to_proxy[future]

            try:
                result = future.result()
            except Exception as e:
                result = {
                    "success": False,
                    "proxy": proxy,
                    "error_type": "THREAD_ERROR",
                    "message": str(e),
                }

            if result.get("success"):
                with file_lock:
                    with open(exitfile, "a", encoding="utf-8") as f:
                        f.write(f"{proxy}\n")

            else:
                results.append(result)
                with open("data/failed_proxies.txt", "a", encoding="utf-8") as f:
                    f.write(f"{proxy} | {result.get('error_type')} | {result.get('message')}\n")

    return results


if __name__ == "__main__":      ## Feel free to change the main logic, it's simple

    proxies = fetch_proxies("data/proxies.txt")
    print(f"Checking {len(proxies)} proxies\nstarting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if all(is_syntax_valid_proxy(proxy) for proxy in proxies):    # Syntax validation of the origin list
        validate_proxies("data/1check.txt", proxies)
    else:
        print("proxies failed syntax validation, exiting process")
    print(f"completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    failed_proxies = fetch_failed_proxies()    # Re-checking the proxies in the failed_proxies.txt
    print(f"\nRe-checking {len(failed_proxies)} read-timeout and connection-error proxies\nstarting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    validate_proxies("data/1check.txt", failed_proxies)
    print(f"completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    once_checked = fetch_proxies("data/1check.txt")
    print(f"\nChecking {len(once_checked)} proxies\nstarting second filtering at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 
    validate_proxies("data/2check.txt", once_checked)    # Double-checking the proxies after first check & retries

    print(f"completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\ninitially: {len(proxies)}\nafter first check: {len(once_checked)}\nafter second check: {len(fetch_proxies('data/2check.txt'))}")

    with open("data/2check.txt") as file:
        for line in file:
            if "socks5://" in line:    # Taking just the socks5 proxies into a separate file
                with open("data/socks5.txt", "a", encoding="utf-8") as f:
                        f.write(f"{line}")

    """
    IF YOU WANT A DIFFERENT SPECIFIC PROXY TYPE:
    
    1.Create a file (for example: http.txt in the data/ folder)
    2.Copy the logic from lines 230-234

    example changed logic:

        with open("data/2check.txt") as file:
            for line in file:
                if "http://" in line:   # important to write with :// , otherwise https will also go through 
                    with open("data/http.txt", "a", encoding="utf-8") as f:
                            f.write(f"{line}")
    """