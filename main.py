from tradelocker import TLAPI
import threading
from fastapi import FastAPI, Request
import uvicorn
import argparse
from libs import AsciiAlerts
from libs.URLgenerator import *

app = FastAPI()
lock = threading.Lock()

def parse_args():
    parser = argparse.ArgumentParser(description="Add variables when starting")
    parser.add_argument('--username', type=str, required=True, help='username/email')
    parser.add_argument('--password', type=str, required=True, help='password')
    parser.add_argument('--server', type=str, required=True, help='server')
    parser.add_argument('--env', type=str, required=True, choices=['live', 'demo'], help='live/demo')
    parser.add_argument('--url', type=str, default='/strategy', help='Optional URL, default is /strategy')
    parser.add_argument('--acc_num', type=str, default='0', help='Optional account number')
    parser.add_argument('--acc_id', type=str, default='0', help='Optional account ID')
    parser.add_argument('--port', type=int, default=443, help='Port to run the application')
    return parser.parse_args()


def handle_position_normal(tl, payload_list, lock):
    with lock:
        symbol_name = payload_list[0]
        direction = payload_list[1]
        mainLot = payload_list[2]
        takeprofit = int(payload_list[3])
        stoploss = int(payload_list[4])
        isInvert = payload_list[6]
        balance = tl.get_account_state().get("projectedBalance")

        minilot, per = map(float, mainLot.split('/'))
        lot = round((balance / per) * minilot, 2)

        print("Normal: Locked")
        if payload_list[5] == "close":


        if payload_list[5] == "open":
            if isInvert == "NonInvert":
                order_direction = direction
            elif isInvert == "Invert":
                order_direction = 'sell' if direction == 'buy' else 'buy'
            else:
                raise ValueError("Invalid value for isInvert. Expected 'NonInvert' or 'Invert'.")


        print("Normal: Unlocked")

def main():
    args = parse_args()
    if args.env == "demo":


    if args.url == "generate":
        print(AsciiAlerts.RED + AsciiAlerts.ascii_art_url + AsciiAlerts.RESET)
        args.url = generate_random_url()
        print(args.url)

    print(AsciiAlerts.GREEN + AsciiAlerts.ascii_art_hello + AsciiAlerts.RESET)



    @app.post(args.url)
    async def process_webhook(request: Request):
        payload_bytes = await request.body()
        payload_list = payload_bytes.decode().splitlines()
        normal_thread = threading.Thread(target=handle_position_normal, args=(tl, payload_list, lock))
        normal_thread.start()

    uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()