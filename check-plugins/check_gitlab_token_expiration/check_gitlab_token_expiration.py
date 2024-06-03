#!/usr/bin/env python3

"""
Copyright 2023-2024 Deutsche Telekom MMS GmbH
Maintainer: Christopher Grau
check when a personal, project or group access token will expire
"""

import argparse
import sys
from datetime import datetime
import gitlab

parser = argparse.ArgumentParser(
  prog = "check_gitlab_token_expiration.py",
  description = "check when a personal, project or group access token will expire"
)

parser.add_argument('--url', required=True)
parser.add_argument('--private_token',required=True)
parser.add_argument('--scope',
        choices=['user','project','group'],
        required=True,
        help='Scope for access token'
)
parser.add_argument('--id',
        required=True,
        help='User ID, Project ID or Group ID'
)
parser.add_argument('--token_name', required=True)
parser.add_argument('--warn', default=10)
parser.add_argument('--crit', default=5)

args = parser.parse_args()

# login to gitlab with private token
try:
    gl = gitlab.Gitlab(f'https://{args.url}', args.private_token)
except gitlab.GitlabAuthenticationError:
    print('login with private token failed')
    sys.exit(255)

if args.scope == 'user':
    access_tokens = gl.personal_access_tokens.list(user_id=args.id, lazy=True, active=True)
elif args.scope == 'project':
    access_tokens = gl.projects.get(args.id, lazy=True, active=True).access_tokens.list()
elif args.scope == 'group':
    access_tokens = gl.groups.get(args.id, lazy=True, active=True).access_tokens.list()

# get expires_at of access_token with the name args.token_name
for token in access_tokens:
    if token.name == args.token_name:
        expires_at = datetime.strptime(token.expires_at, '%Y-%m-%d').date()

# check days until expiration
if (expires_at - datetime.today().date()).days <= args.crit:
    print(f'CRIT - private token {args.token_name} will expires in less then {args.crit} days')
    sys.exit(2)
elif (expires_at - datetime.today().date()).days <= args.warn:
    print(f'WARN - private token {args.token_name} will expires in less then {args.warn} days')
    sys.exit(1)
else:
    print(f'OK - private token {args.token_name} will expires in {(expires_at - datetime.today().date()).days} days')
    sys.exit(0)
