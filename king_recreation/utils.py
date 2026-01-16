import time
import atexit
from functools import wraps, partial


class track_performance:
    def __init__(self, func):
        wraps(func)(self)
        self.func = func
        self.total_time = 0
        self.call_count = 0
        # Register the report method to run when the script ends
        atexit.register(self.print_report)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return partial(self, obj)

    def __call__(self, *args, **kwargs):
        start = time.perf_counter()
        result = self.func(*args, **kwargs)
        end = time.perf_counter()

        # Accumulate stats from "natural" execution
        self.total_time += end - start
        self.call_count += 1
        return result

    def print_report(self):
        if self.call_count > 0:
            avg = self.total_time / self.call_count
            print(f"\n--- Final Performance Report: {self.func.__name__} ---")
            print(f"Total Calls:   {self.call_count}")
            print(f"Total Time:    {self.total_time:.6f}s")
            print(f"Average Time:  {avg:.6f}s")
