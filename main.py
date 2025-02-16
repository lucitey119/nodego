import requests
import time
import itertools
import threading
from concurrent.futures import ThreadPoolExecutor

# Endpoints
ping_url = "https://nodego.ai/api/user/nodes/ping"
client_ip_url = "https://api.bigdatacloud.net/data/client-ip"

# Default Authorization token
default_token = "your_default_token_here"

# Load tokens from forest.txt
def load_tokens(filename="forest.txt"):
    try:
        with open(filename, "r") as f:
            tokens = [line.strip() for line in f if line.strip()]
        return tokens if tokens else [default_token]  # Use default if file is empty
    except FileNotFoundError:
        return [default_token]  # Use default if file doesn't exist

# Load proxies from proxies.txt (each line should be like: http://ip:port)
def load_proxies(filename="proxies.txt"):
    try:
        with open(filename, "r") as f:
            proxies = [line.strip() for line in f if line.strip()]
        return proxies
    except FileNotFoundError:
        return []

tokens = load_tokens()
# Create a global token cycle and a lock for thread-safe token retrieval
token_cycle = itertools.cycle(tokens)
token_lock = threading.Lock()

def get_next_token():
    with token_lock:
        return next(token_cycle)

# Load proxies from file
proxies_list = load_proxies()

# Common headers for all requests
headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}

# Payload for the ping request
ping_payload = {"type": "extension"}

def process_requests(proxy=None):
    """
    Continuously send requests using the given proxy.
    If proxy is None, no proxy is used.
    """
    request_count = 0
    # If a proxy is provided, build the proxies dictionary for requests
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy
        }
        proxy_label = f"Proxy {proxy}"
    else:
        proxies = None
        proxy_label = "No Proxy"

    while True:
        request_count += 1
        current_token = get_next_token()

        # Prepare headers for the ping request
        ping_headers = headers.copy()
        ping_headers["Authorization"] = f"Bearer {current_token}"
        ping_headers["Content-Type"] = "application/json"

        # Send POST request to the ping endpoint
        try:
            ping_response = requests.post(
                ping_url,
                headers=ping_headers,
                json=ping_payload,
                proxies=proxies,
                timeout=10
            )
            if ping_response.status_code == 201:
                try:
                    print(f"[{proxy_label} | Request {request_count}] Ping Success: {ping_response.json()}")
                except ValueError:
                    print(f"[{proxy_label} | Request {request_count}] Ping Success (Non-JSON): {ping_response.text}")
            else:
                print(f"[{proxy_label} | Request {request_count}] Ping Failed: {ping_response.status_code}, Response: {ping_response.text}")
        except Exception as e:
            print(f"[{proxy_label} | Request {request_count}] Ping Error: {str(e)}")

        # Send GET request to the client IP endpoint
        try:
            ip_response = requests.get(
                client_ip_url,
                headers=headers,
                proxies=proxies,
                timeout=10
            )
            if ip_response.status_code == 200:
                try:
                    print(f"[{proxy_label} | Request {request_count}] Client IP Success: {ip_response.json()}")
                except ValueError:
                    print(f"[{proxy_label} | Request {request_count}] Client IP Success (Non-JSON): {ip_response.text}")
            else:
                print(f"[{proxy_label} | Request {request_count}] Client IP Failed: {ip_response.status_code}, Response: {ip_response.text}")
        except Exception as e:
            print(f"[{proxy_label} | Request {request_count}] Client IP Error: {str(e)}")

        time.sleep(5)  # Delay to prevent excessive load

def main():
    try:
        if proxies_list:
            # Start a thread for each proxy
            with ThreadPoolExecutor(max_workers=len(proxies_list)) as executor:
                for proxy in proxies_list:
                    executor.submit(process_requests, proxy)
                # Keep the main thread alive indefinitely
                while True:
                    time.sleep(1)
        else:
            # If no proxies are loaded, run without proxy in a single thread
            process_requests(None)
    except KeyboardInterrupt:
        print("\nScript stopped by user.")

if __name__ == "__main__":
    main()
