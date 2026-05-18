import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Add redis/ to path so prelim_redis is importable regardless of working directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "redis")))


def main():
    import prelim_redis
    prelim_redis.main()


if __name__ == "__main__":
    main()
