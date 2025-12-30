import time

class ConcurrencyController:
    def __init__(
        self,
        initial=5,
        min_c=1,
        max_c=20,
        window=20
    ):
        self.current = initial
        self.min_c = min_c
        self.max_c = max_c
        self.window = window

        self.success = 0
        self.errors = 0
        self.rtt_total = 0.0
        self.samples = 0
        self.last_adjust = time.time()

    def record(self, success: bool, rtt: float):
        if success:
            self.success += 1
        else:
            self.errors += 1

        self.rtt_total += rtt
        self.samples += 1

    def should_adjust(self):
        return self.samples >= self.window

    def adjust(self):
        if self.samples == 0:
            return self.current

        error_rate = self.errors / self.samples
        avg_rtt = self.rtt_total / self.samples

        new_c = self.current

        # Decrease aggressively
        if error_rate > 0.05 or avg_rtt > 3.0:
            new_c = max(self.current // 2, self.min_c)

        # Increase cautiously
        elif error_rate < 0.01 and avg_rtt < 1.5:
            new_c = min(self.current + 1, self.max_c)

        # Reset window
        self.success = 0
        self.errors = 0
        self.rtt_total = 0.0
        self.samples = 0
        self.current = new_c
        self.last_adjust = time.time()

        return new_c
