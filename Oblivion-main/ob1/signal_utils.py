import signal
import sys

def install_signal_handlers(oblivion_instance):
    def handler(signum, frame):
        signame = signal.Signals(signum).name
        print(f"[!] Caught signal {signame}, shutting down...")
        oblivion_instance.stop_all_attacks(reason="signal")
        sys.exit(0)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)