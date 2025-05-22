import dotenv
import os
import signal
import sys
import time
from nestiqdns.remotedict import RemoteDict
from nestiqdns.dnsserver import DNSServer

# This script starts only the DNS server and RemoteDict in background threads.
# The Flask web API should be run separately using Gunicorn.

def main():
    dotenv.load_dotenv()
    REDIS_HOST = os.environ.get("REDIS_HOST", "127.0.0.1")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
    DNS_ADDRESS = os.environ.get("DNS_ADDRESS", "0.0.0.0")
    DNS_PORT = int(os.environ.get("DNS_PORT", 53))

    rd = None
    dns = None

    def handle_sigint(sig, frame):
        print("\nReceived interrupt. Shutting down...")
        if dns is not None:
            dns.stop_thread()
        if rd is not None:
            rd.stop_thread()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    try:
        rd = RemoteDict(address=REDIS_HOST, port=REDIS_PORT)
        rd.start_thread()
        dns = DNSServer(address=DNS_ADDRESS, port=DNS_PORT, db_host=REDIS_HOST, db_port=REDIS_PORT)
        dns.start_thread()
        print("DNS server and RemoteDict started. Run the web API with Gunicorn.")
        while True:
            time.sleep(1)
    except Exception as e:
        print(f"Exception occurred: {e}")
        sys.exit(1)
    finally:
        if dns is not None:
            dns.stop_thread()
        if rd is not None:
            rd.stop_thread()

if __name__ == "__main__":
    main()
