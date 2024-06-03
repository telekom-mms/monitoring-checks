# Check Gitlab Token Expiration

This script is an icinga2 monitoring check to check when a personal, project or group access token will expire.

```
usage: check_gitlab_token_expiration.py [-h] --url URL --private_token PRIVATE_TOKEN --scope {user,project,group} --id ID --token_name TOKEN_NAME [--warn WARN] [--crit CRIT]

check when a personal access token, a project access token or a group access token will expire

options:
  -h, --help            show this help message and exit
  --url URL
  --private_token PRIVATE_TOKEN
  --scope {user,project,group}
                        Scope for access token
  --id ID               User ID, Project ID or Group ID
  --token_name TOKEN_NAME
  --warn WARN
  --crit CRIT
```

# Authors

- Christopher Grau
