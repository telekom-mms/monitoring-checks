#! /usr/bin/env python3

"""
Copyright 2023 Deutsche Telekom MMS GmbH
Maintainer: Christopher Grau
check a pull mirror in the given gitlab project
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
import gitlab
import requests

parser = argparse.ArgumentParser(
  prog = "check_gitlab_pull_miror.py"
  )

parser.add_argument('--url', required=True)
parser.add_argument('--private_token', required=True)
parser.add_argument('--project_id', required=True)
parser.add_argument('--crit', default=60, help='minutes to last successful run')

args = parser.parse_args()

# login to gitlab with private token
try:
    gl = gitlab.Gitlab(f'https://{args.url}', args.private_token)
except gitlab.GitlabAuthenticationError:
    print('login with private token failed')
    sys.exit(255)

# get pull mirror details from project
# pylint: disable=line-too-long
URL = f'https://{args.url}/api/v4/projects/{args.project_id}/mirror/pull'
headers = {
    'PRIVATE-TOKEN': args.private_token
    }
try:
    r = requests.get(URL,headers=headers,timeout=60)
    r_json = r.json()
    last_successful_update = r_json['last_successful_update_at']
    last_successful_update_at = datetime.strptime(r_json['last_successful_update_at'],"%Y-%m-%dT%H:%M:%S.%fZ")
except requests.exceptions.HTTPError as err:
    print(err)
    sys.exit(255)
except requests.exceptions.JSONDecodeError as err:
    print('unable to decode JSON from the HTTP Response', err)
    sys.exit(255)
except KeyError:
    print('unable to load timestamp from api response', r_json)
    sys.exit(255)

age = datetime.now(timezone.utc) - last_successful_update_at.replace(tzinfo=timezone.utc)

if r_json['update_status'] != 'finished':
    print(f'CRIT - pull mirror of project https://{args.url}/projects/{args.project_id} not in status finished')
    sys.exit(2)
elif age > timedelta(minutes=args.crit):
    project_url = f"http://{args.url}/projects/{args.project_id}"
    ts_last_update = last_successful_update_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    print(f'CRIT - last successful of pull mirror in project {project_url} at {ts_last_update}')
    sys.exit(2)
else:
    print(f'OK - pull mirror of project https://{args.url}/projects/{args.project_id} in status finished')
    sys.exit(0)
