#!/usr/bin/env python

from src.sources.loader import get_source

def main():
    print("Testing Stooq market data source:")
    try:
        stooq_data = get_source("markets", "stooq").fetch()
        print(stooq_data[:2])
    except Exception as e:
        print(f"Error with stooq source: {e}")

    print("\nTesting PapersWithCode AI source:")
    try:
        pwc_data = get_source("ai", "paperswithcode_trending").fetch()
        print(pwc_data[:1])
    except Exception as e:
        print(f"Error with PapersWithCode source: {e}")

if __name__ == "__main__":
    main() 