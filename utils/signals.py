import signal
import sys

def setup_signal_handlers(cleanup_fn):
    def handler(sig, frame):
        print("\n🛑 Shutdown signal received. Safe exit.")
        cleanup_fn()
        sys.exit(0)

    signal.signal(signal.SIGINT, handler)
