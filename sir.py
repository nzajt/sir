#!/usr/bin/env python3

import json
import random
import sys

def load_jokes():
    try:
        with open('dad_jokes.json', 'r') as f:
            data = json.load(f)
            return data['jokes']
    except FileNotFoundError:
        print("Error: dad_jokes.json file not found!")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in dad_jokes.json!")
        sys.exit(1)

def get_random_joke(jokes):
    return random.choice(jokes)

def tell_joke(joke):
    print(f"\n{joke['setup']}")
    input("Press Enter for the punchline...")
    print(f"{joke['punchline']}\n")

def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['joke', 'tell', 'j']:
        jokes = load_jokes()
        joke = get_random_joke(jokes)
        tell_joke(joke)
    else:
        print("Usage: python sir.py joke")
        print("Alternative: python sir.py j")

if __name__ == "__main__":
    main()