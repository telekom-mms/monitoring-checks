# Check Redis Sentinel Cluster

This script checks if a Redis Sentinel cluster is in a healthy condition.

```
usage: Check Redis Sentinel [-h] -u SENTINEL_URL -p SENTINEL_PORT
                            [-t SENTINEL_AUTH_TOKEN] -r HEALTHY_REPLICA_COUNT
                            -n REDIS_PRIMARY_NAME
```

Note: Unfortunately, we did not get around "master" and "slave" assignments everywhere in the code, as the official redis-py library still uses the old terms, for example: https://redis.readthedocs.io/en/stable/connections.html#redis.sentinel.Sentinel.discover_master

# Authors

- Andreas Hering
- Daniel Uhlmann
