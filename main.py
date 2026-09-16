"""
Binance Futures Demo (Testnet) Trading Bot - Starter
-----------------------------------------------------
Simple starter bot that connects to Binance Futures TESTNET
(demo trading, no real money) and runs a basic price-check loop.

This is a STARTER template — extend the trading logic in `trading_loop()`
with your own strategy before using it for anything real.

Deployment note (Render free Web Service):
Render's free tier requires the service to bind to an HTTP port to be
considered "healthy". This file runs a tiny Flask server on that port
AND runs the bot loop in a background thread at the same time.
"""

import os
import time
import threading
import logging

from flask import Flask, jsonify
from binance.client import Client
from binance.exceptions import BinanceAPIException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("bot")

# ---------------------------------------------------------------------------
# Configuration (set these as Environment Variables in Render, never in code)
# ---------------------------------------------------------------------------
API_KEY = os.environ.get("BINANCE_API_KEY", "")
API_SECRET = os.environ.get("BINANCE_API_SECRET", "")
SYMBOL = os.environ.get("TRADE_SYMBOL", "BTCUSDT")
LOOP_INTERVAL_SECONDS = int(os.environ.get("LOOP_INTERVAL_SECONDS", "30"))
PORT = int(os.environ.get("PORT", "10000"))  # Render sets PORT automatically

# Shared state for the health endpoint
bot_status = {
    "running": False,
    "last_price": None,
    "last_update": None,
    "last_error": None,
}


def build_client() -> Client:
    """Create a Binance client pointed at the FUTURES TESTNET (demo trading)."""
    if not API_KEY or not API_SECRET:
        raise RuntimeError(
            "BINANCE_API_KEY / BINANCE_API_SECRET environment variables are not set."
        )

    client = Client(API_KEY, API_SECRET)
    # IMPORTANT: this points the client at the Futures TESTNET (demo), not real funds.
    client.FUTURES_URL = "https://testnet.binancefuture.com/fapi"
    return client


def trading_loop():
    """
    Background loop: fetches the current price every LOOP_INTERVAL_SECONDS.
    Replace the body of this function with your real strategy
    (indicators, entry/exit rules, order placement, etc.).
    """
    bot_status["running"] = True

    try:
        client = build_client()
    except RuntimeError as e:
        logger.error(str(e))
        bot_status["last_error"] = str(e)
        bot_status["running"] = False
        return

    logger.info("Bot started. Watching %s on Binance Futures TESTNET.", SYMBOL)

    while True:
        try:
            ticker = client.futures_symbol_ticker(symbol=SYMBOL)
            price = float(ticker["price"])

            bot_status["last_price"] = price
            bot_status["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
            bot_status["last_error"] = None

            logger.info("%s price: %s", SYMBOL, price)

            # ------------------------------------------------------------
            # TODO: Add your real strategy here, e.g.:
            #
            # if price < some_threshold:
            #     client.futures_create_order(
            #         symbol=SYMBOL,
            #         side="BUY",
            #         type="MARKET",
            #         quantity=0.001,
            #     )
            # ------------------------------------------------------------

        except BinanceAPIException as e:
            logger.error("Binance API error: %s", e)
            bot_status["last_error"] = str(e)
        except Exception as e:
            logger.exception("Unexpected error in trading loop")
            bot_status["last_error"] = str(e)

        time.sleep(LOOP_INTERVAL_SECONDS)


# ---------------------------------------------------------------------------
# Minimal web server so Render sees the service as "healthy"
# ---------------------------------------------------------------------------
app = Flask(__name__)


@app.route("/")
def health():
    return jsonify(
        {
            "service": "binance-futures-demo-bot",
            "symbol": SYMBOL,
            **bot_status,
        }
    )


if __name__ == "__main__":
    # Start the trading loop in a background thread
    bot_thread = threading.Thread(target=trading_loop, daemon=True)
    bot_thread.start()

    # Start the web server in the main thread (keeps Render happy)
    app.run(host="0.0.0.0", port=PORT)
