import threading
from fastapi import FastAPI, Request
from capitalcom import CapitalClient
import uvicorn
from libs import AsciiAlerts
from libs.URLgenerator import generate_random_url
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import argparse
import os

app = FastAPI()
clients = {}
strategy_urls = {}
LINKS_FILE = "webhook_links.txt"

class LoginRateLimitError(Exception):
    pass

# Retry login if the Capital.com API rate-limits us (HTTP 429)
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(LoginRateLimitError)
)
def create_client(api_key, login, password, demo):
    try:
        return CapitalClient(
            api_key=api_key,
            login=login,
            password=password,
            demo=demo
        )
    except Exception as e:
        if "429" in str(e):
            print("Hit rate limit during login. Retrying...")
            raise LoginRateLimitError()
        raise e

# Main logic that runs for each webhook strategy call
def handle_position_normal(client: CapitalClient, strategy_id: int, payload_list: list[str]):
    print(f"[Strategy {strategy_id}] Webhook received")
    try:
        symbol_name = payload_list[0]
        direction = payload_list[1]
        mainLot = payload_list[2]
        takeprofit = int(payload_list[3])
        stoploss = int(payload_list[4])
        action = payload_list[5]
        isInvert = payload_list[6]

        balance = client.get_balance(raw=False)
        minilot, per = map(float, mainLot.split('/'))
        lot = round((balance / per) * minilot, 2)

        if action == "close":
            print(f"[Strategy {strategy_id}] Closing position on {symbol_name}")
        elif action == "open":
            if isInvert == "Invert":
                direction = 'sell' if direction == 'buy' else 'buy'
            print(f"[Strategy {strategy_id}] Opening {direction.upper()} on {symbol_name} with lot {lot}")
        else:
            print(f"[Strategy {strategy_id}] Unknown action: {action}")

    except Exception as e:
        print(f"[Strategy {strategy_id}] ERROR: {e}")

# Register an endpoint in FastAPI dynamically for each strategy
def register_strategy_endpoint(strategy_id: int, route_path: str, client: CapitalClient):
    strategy_urls[strategy_id] = route_path

    @app.post(route_path)
    async def strategy_endpoint(request: Request, sid=strategy_id):
        payload_bytes = await request.body()
        payload_list = payload_bytes.decode().splitlines()
        thread = threading.Thread(target=handle_position_normal, args=(client, sid, payload_list))
        thread.start()
        return {"status": "received", "strategy": sid}

# Save generated or restored URLs to file
def save_links_to_file(urls: list[str]):
    with open(LINKS_FILE, "w") as f:
        for url in urls:
            f.write(url + "\n")

# Load URLs from file if present
def load_links_from_file() -> list[str]:
    if not os.path.exists(LINKS_FILE):
        return []
    with open(LINKS_FILE, "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def main():
    print(AsciiAlerts.GREEN + AsciiAlerts.ascii_art_hello + AsciiAlerts.RESET)

    parser = argparse.ArgumentParser()
    parser.add_argument("--Strategies", type=int, default=3, help="How many strategies to run")
    parser.add_argument("--ForceGenerate", type=bool, default=False, help="Force generation of new URLs, overwriting file")
    args = parser.parse_args()

    api_key = "s8GuzswLCONYMQwY"
    login = "wiktorjn@gmail.com"
    password = "Demo1234!"
    demo = True

    routes = []

    if args.ForceGenerate:
        print(f"Force-generating {args.Strategies} new strategy URLs...")
        routes = [generate_random_url() for _ in range(args.Strategies)]
        save_links_to_file(routes)
    else:
        routes = load_links_from_file()
        current_count = len(routes)

        if current_count == 0:
            print("No webhook links found in file.")
            choice = input("Do you want to generate new ones? (Y/N): ").strip().lower()
            if choice != "y":
                print("Aborting. No links to restore.")
                return
            routes = [generate_random_url() for _ in range(args.Strategies)]
            save_links_to_file(routes)

        elif current_count < args.Strategies:
            missing = args.Strategies - current_count
            print(f"Adding {missing} missing strategy URL(s)...")
            new_routes = [generate_random_url() for _ in range(missing)]
            routes.extend(new_routes)
            save_links_to_file(routes)

        elif current_count > args.Strategies:
            print(f"Found more links than requested ({current_count} > {args.Strategies}). Extra links will be ignored.")

    # Register only the first N routes, where N = --Strategies
    for i, route in enumerate(routes[:args.Strategies], start=1):
        client = create_client(api_key, login, password, demo)
        register_strategy_endpoint(i, route, client)
        print(f"Strategy {i} registered.")

    print(AsciiAlerts.RED + AsciiAlerts.ascii_art_url + AsciiAlerts.RESET)

    for sid, url in strategy_urls.items():
        print(f"Strategy {sid}: POST http://localhost:8080{url.lstrip()}")

    uvicorn.run(app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()
