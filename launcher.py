#!/usr/bin/env python3
"""
launcher script for the data agent with different database options.
this script demonstrates how to run the system with different configurations.
"""

import subprocess
import sys
import argparse

def run_amazon_mode():
    """run with the amazon database"""
    print("Command: python3 main.py --etl 0 --agent 1 --amazon 1 --spotify 0")
    subprocess.run([
        sys.executable, "main.py", 
        "--etl", "0", 
        "--agent", "1", 
        "--amazon", "1", 
        "--spotify", "0"
    ])

def run_spotify_mode():
    """run with the spotify database"""
    print("Command: python3 main.py --etl 0 --agent 1 --amazon 0 --spotify 1")
    subprocess.run([
        sys.executable, "main.py", 
        "--etl", "0", 
        "--agent", "1", 
        "--amazon", "0", 
        "--spotify", "1"
    ])

def run_etl_amazon():
    """run etl only for amazon"""
    print("🛒 running etl for amazon data...")
    print("Command: python3 main.py --etl 1 --agent 0 --amazon 1 --spotify 0")
    subprocess.run([
        sys.executable, "main.py", 
        "--etl", "1", 
        "--agent", "0", 
        "--amazon", "1", 
        "--spotify", "0"
    ])

def run_etl_spotify():
    """run etl only for spotify"""
    print("Command: python3 main.py --etl 1 --agent 0 --amazon 0 --spotify 1")
    subprocess.run([
        sys.executable, "main.py", 
        "--etl", "1", 
        "--agent", "0", 
        "--amazon", "0", 
        "--spotify", "1"
    ])

def main():
    parser = argparse.ArgumentParser(description='Data Agent Launcher')
    parser.add_argument('--mode', choices=['amazon', 'spotify', 'both', 'etl-amazon', 'etl-spotify'], 
                       default='amazon', help='Mode to run')
    
    args = parser.parse_args()
    
    if args.mode == 'amazon':
        run_amazon_mode()
    elif args.mode == 'spotify':
        run_spotify_mode()
    elif args.mode == 'both':
        run_both_mode()
    elif args.mode == 'etl-amazon':
        run_etl_amazon()
    elif args.mode == 'etl-spotify':
        run_etl_spotify()

if __name__ == "__main__":
    main()
