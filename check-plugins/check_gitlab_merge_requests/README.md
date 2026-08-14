# Check Gitlab Merge Requests

This script checks how many merge requests are in state open in an project or group.
`-c` and `-w` can adjust the limit which is default on `1`

```
usage: check_gitlab_merge_requests.py [-h] -u GITLAB_URL -t TOKEN [--project-id PROJECT_ID] [--group-id GROUP_ID] [-w WARNING] [-c CRITICAL]

check if project or group has open merge requests

options:
  -h, --help            show this help message and exit
  -u, --gitlab_url GITLAB_URL
  -t, --token TOKEN
  --project-id PROJECT_ID
                        Project ID
  --group-id GROUP_ID   Group ID
  -w, --warning WARNING
                        warning limit of count of open merge requests
  -c, --critical CRITICAL
                        critical limit of count of open merge requests
```

# Authors

- Martin Neubert
