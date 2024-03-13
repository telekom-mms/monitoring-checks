#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script for checking the health of a Redis Sentinel cluster.

Copyright 2024 Deutsche Telekom MMS GmbH
Maintainer: Daniel Uhlmann & Andreas Hering

This script is used to monitor and ensure the health of a Redis Sentinel cluster.
It checks the availability of the master, the replicas, and verifies that the
number of healthy replicas matches the expected count.

Usage:
    python3 check_redis_sentinel.py -u <sentinel_url> -p <sentinel_port>
              -t <sentinel_auth_token> -r <healthy_replica_count> -n <redis_primary_name>

Arguments:
    -u, --sentinel_url: The URL of the Redis Sentinel.
    -p, --sentinel_port: The port number of the Redis Sentinel.
    -t, --sentinel_auth_token: The authentication token for the Redis Sentinel.
    -r, --healthy_replica_count: The expected number of healthy replicas.
    -n, --redis_primary_name: The name of the Redis primary.
"""

import sys
import argparse
from redis.sentinel import Sentinel

def check_redis_sentinel(sentinel_url, sentinel_port,
                         sentinel_auth_token,
                         healthy_replica_count,
                         redis_primary_name) -> None:
    """
    Checks the health of a Redis Sentinel cluster.

    Parameters:
    - sentinel_url (str): The URL of the Redis Sentinel.
    - sentinel_port (int): The port number of the Redis Sentinel.
    - sentinel_auth_token (str): The authentication token for the Redis Sentinel.
    - healthy_replica_count (int): The expected number of healthy replicas.
    - redis_primary_name (str): The name of the Redis primary.

    Returns:
    - None
    """

    # Connect to the Redis Sentinel Cluster
    sentinel = Sentinel([(sentinel_url, sentinel_port)], password=sentinel_auth_token)

    # Get primary node
    try:
        sentinel.discover_master(redis_primary_name)
    except Exception as e:
        print(f"CRITICAL - {e}")
        sys.exit(2)

    # Get replica(s) node
    try:
        replicas = sentinel.discover_slaves(redis_primary_name)
    except Exception as e:
        print(f"CRITICAL - {e}")
        sys.exit(2)

    # Check number of replicas
    if len(replicas) < healthy_replica_count:
        print(
             f"WARNING - Found {len(replicas)} replica(s), "
             f"but expected at least {healthy_replica_count}"
        )
        sys.exit(1)

    print("OK - Redis sentinel cluster is healthy")
    sys.exit(0)

def main():
    """
    The main entry point of the script. Arguments getting initialized here.
    """
    parser = argparse.ArgumentParser(
        prog="Check Redis Sentinel",
        description="""This script checks the health of a Redis Sentinel cluster""",
    )
    parser.add_argument(
        "-u",
        "--sentinel_url",
        dest="sentinel_url",
        type=str,
        required=True
    )
    parser.add_argument(
        "-p",
        "--sentinel_port",
        dest="sentinel_port",
        type=int,
        required=True
    )
    parser.add_argument(
        "-t",
        "--sentinel_auth_token",
        dest="sentinel_auth_token",
        type=str,
        required=False
    )
    parser.add_argument(
        "-r",
        "--healthy_replica_count",
        dest="healthy_replica_count",
        type=int,
        required=True
    )
    parser.add_argument(
        "-n",
        "--redis_primary_name",
        dest="redis_primary_name",
        type=str,
        required=True
    )

    args = parser.parse_args()

    check_redis_sentinel(
        args.sentinel_url,
        args.sentinel_port,
        args.sentinel_auth_token,
        args.healthy_replica_count,
        args.redis_primary_name,
    )

if __name__ == "__main__":
    main()
