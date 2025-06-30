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
        client = CapitalClient(
            api_key=api_key,
            login=login,
            password=password,
            demo=demo
        )
        client.open_positions = {}  # {symbol_name: [deal_id, ...]}
        return client
    except Exception as e:
        if "429" in str(e):
            print("Hit rate limit during login. Retrying...")
            raise LoginRateLimitError()
        raise e

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

        if not hasattr(client, "open_positions"):
            client.open_positions = {}

        if action == "close":
            if symbol_name in client.open_positions and client.open_positions[symbol_name]:
                deal_ids = client.open_positions[symbol_name]
                print(f"[Strategy {strategy_id}] Closing {len(deal_ids)} position(s) on {symbol_name}")
                for deal_id in deal_ids:
                    try:
                        client.close_position_by_id(deal_id)
                        print(f"[Strategy {strategy_id}] Closed deal {deal_id}")
                    except Exception as e:
                        print(f"[Strategy {strategy_id}] Failed to close deal {deal_id}: {e}")
                client.open_positions[symbol_name] = []
            else:
                print(f"[Strategy {strategy_id}] No open positions recorded for {symbol_name} to close.")

        elif action == "open":
            if isInvert == "Invert":
                if direction == 'BUY':
                    direction = 'SELL'
                elif direction == 'SELL':
                    direction = 'BUY'
                else:
                    raise ValueError(f"Unknown direction: {direction}")

            balance = client.get_balance(raw=False)
            minilot, per = map(float, mainLot.split('/'))
            raw_lot = (balance / per) * minilot
            lot = round(raw_lot, 3)

            if lot < 0.001:
                print(f"[Strategy {strategy_id}] Computed lot {lot} is too small, setting to 0.001")
                lot = 0.001

            try:
                deal_id = client.open_forex_position(symbol_name, lot, direction, stoploss, takeprofit)
                print(f"[Strategy {strategy_id}] Deal opened. Deal ID: {deal_id} | SL: {stoploss} | TP: {takeprofit}")
                if symbol_name not in client.open_positions:
                    client.open_positions[symbol_name] = []
                client.open_positions[symbol_name].append(deal_id)
            except Exception as e:
                print(f"[Strategy {strategy_id}] Failed to open position: {e}")
        else:
            print(f"[Strategy {strategy_id}] Unknown action: {action}")
    except Exception as e:
        print(f"[Strategy {strategy_id}] ERROR: {e}")

def register_strategy_endpoint(strategy_id: int, route_path: str, client: CapitalClient):
    strategy_urls[strategy_id] = route_path

    @app.post(route_path)
    async def strategy_endpoint(request: Request, sid=strategy_id):
        payload_bytes = await request.body()
        payload_list = payload_bytes.decode().splitlines()
        thread = threading.Thread(target=handle_position_normal, args=(client, sid, payload_list))
        thread.start()
        return {"status": "received", "strategy": sid}

def save_links_to_file(urls: list[str]):
    with open(LINKS_FILE, "w") as f:
        for url in urls:
            f.write(url + "\n")

def load_links_from_file() -> list[str]:
    if not os.path.exists(LINKS_FILE):
        return []
    with open(LINKS_FILE, "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def main():
    print(AsciiAlerts.GREEN + AsciiAlerts.ascii_art_hello + AsciiAlerts.RESET)

    parser = argparse.ArgumentParser()
    parser.add_argument("--Strategies", type=int, default=1, help="How many strategies to run")
    parser.add_argument("--api_key", required=True, help="Capital.com API key")
    parser.add_argument("--login", required=True, help="Capital.com account login (email)")
    parser.add_argument("--password", required=True, help="Capital.com account password")
    parser.add_argument("--demo", type=bool, default=True, required=True, help="Use demo account: True or False")
    parser.add_argument("--port", type=int, required=True, help="Port to run FastAPI server on")

    args = parser.parse_args()
    routes = load_links_from_file()
    current_count = len(routes)

    if current_count == 0:
        print(f"No links found — generating {args.Strategies} new strategy URL(s)...")
        routes = [generate_random_url() for _ in range(args.Strategies)]
        save_links_to_file(routes)
    elif current_count < args.Strategies:
        missing = args.Strategies - current_count
        print(f"Found {current_count} link(s), generating {missing} more...")
        new_routes = [generate_random_url() for _ in range(missing)]
        routes.extend(new_routes)
        save_links_to_file(routes)
    elif current_count > args.Strategies:
        print(f"Found more links than requested ({current_count} > {args.Strategies}). Extra links will be ignored.")

    for i, route in enumerate(routes[:args.Strategies], start=1):
        client = create_client(args.api_key, args.login, args.password, args.demo)
        register_strategy_endpoint(i, route, client)
        print(f"Strategy {i} registered.")

    print(AsciiAlerts.RED + AsciiAlerts.ascii_art_url + AsciiAlerts.RESET)

    for sid, url in strategy_urls.items():
        print(f"Strategy {sid}: POST http://localhost:{args.port}{url.lstrip()}")

    uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()
