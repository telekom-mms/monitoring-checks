#! /usr/bin/env python3

"""
Copyright 2023 Deutsche Telekom MMS GmbH
Maintainer: Christopher Grau
check a pull mirror in the given gitlab project
"""

import argparse
import sys
from datetime import datetime, timedelta
import gitlab
import requests

parser = argparse.ArgumentParser(
  prog = "check_gitlab_pull_miror.py"
  )

parser.add_argument('--url', required=True)
parser.add_argument('--private_token', required=True)
parser.add_argument('--project_id', required=True)
parser.add_argument('--crit', default=60, help='minutes to last successfull run')

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
except requests.exceptions.HTTPError as err:
    print(err)
    sys.exit(255)

last_successful_update_at = datetime.strptime(r.json()['last_successful_update_at'],"%Y-%m-%dT%H:%M:%S.%fZ")

if r.json()['update_status'] != 'finished':
    print(f'CRIT - pull mirror of project https://{args.url}/projects/{args.project_id} not in status finished')
    sys.exit(2)
elif datetime.now() - (last_successful_update_at + timedelta(hours=2)) > timedelta(minutes=args.crit):
    print(f'CRIT - last successfull of pull mirror in project https://{args.url}/projects/{args.project_id} {(last_successful_update_at + timedelta(hours=2)).strftime("%H:%M:%S")}')
    sys.exit(2)
else:
    print(f'OK - pull mirror of project https://{args.url}/projects/{args.project_id} in status finished')
    sys.exit(0)
