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


class State:
    name: str
    weight: int

    def __init__(self, output: str):
        self.output = output

    def __str__(self):
        return f"[{self.name}] {self.output}"


class StateOk(State):
    name: str = "OK"
    weight: int = 0


class StateWarning(State):
    name: str = "WARNING"
    weight: int = 1


class StateCritical(State):
    name: str = "CRITICAL"
    weight: int = 2


def check_token(token) -> State:
    expires_at = datetime.strptime(token.expires_at, "%Y-%m-%d").date()

    # check days until expiration
    if (expires_at - datetime.today().date()).days <= args.crit:
        return StateCritical(
            f"private token {token.name} will expires in less then {args.crit} days"
        )
    elif (expires_at - datetime.today().date()).days <= args.warn:
        return StateWarning(
            f"private token {token.name} will expires in less then {args.warn} days"
        )
    else:
        return StateOk(
            f"private token {token.name} will expires in {(expires_at - datetime.today().date()).days} days"
        )


parser = argparse.ArgumentParser(
    prog="check_gitlab_token_expiration.py",
    description="check when a personal, project or group access token will expire",
)

parser.add_argument("--url", required=True)
parser.add_argument("--private_token", required=True)
parser.add_argument(
    "--scope",
    choices=["user", "project", "group"],
    required=True,
    help="Scope for access token",
)
parser.add_argument("--id", required=True, help="User ID, Project ID or Group ID")
parser.add_argument("--token_name")
parser.add_argument("--warn", default=10, type=int)
parser.add_argument("--crit", default=5, type=int)
parser.add_argument("--recursive", default=False, action="store_true")

args = parser.parse_args()

# login to gitlab with private token
try:
    gl = gitlab.Gitlab(f"https://{args.url}", args.private_token)
except gitlab.GitlabAuthenticationError:
    print("login with private token failed")
    sys.exit(255)

if args.scope == "user":
    access_tokens = gl.personal_access_tokens.list(
        user_id=args.id, lazy=True, active=True
    )
elif args.scope == "project":
    access_tokens = gl.projects.get(
        args.id, lazy=True, active=True
    ).access_tokens.list()
elif args.scope == "group":
    if args.recursive:
        access_tokens = []
        access_tokens = (
            access_tokens
            + gl.groups.get(args.id, lazy=True, active=True).access_tokens.list()
        )

        group = gl.groups.get(args.id, lazy=True, active=True)
        for subgroup in group.descendant_groups.list(
            get_all=True, lazy=True, include_subgroups=True, active=True
        ):
            subgroup = gl.groups.get(subgroup.id, lazy=True)
            access_tokens = access_tokens + subgroup.access_tokens.list()

        for project in group.projects.list(
            get_all=True, lazy=True, include_subgroups=True, active=True
        ):
            project = gl.projects.get(project.id)
            if project.permissions.get("group_access"):
                access_tokens = access_tokens + project.access_tokens.list()
    else:
        access_tokens = gl.groups.get(
            args.id, lazy=True, active=True
        ).access_tokens.list()

states: list[State] = []

# get expires_at of access_token with the name args.token_name
if args.token_name:
    token_names = [t.name for t in access_tokens if t.active]
    if args.token_name not in token_names:
        states.append(StateCritical(f"private token {args.token_name} not found"))
    else:
        for token in access_tokens:
            if token.name == args.token_name:
                states.append(check_token(token))
else:
    for token in access_tokens:
        if token.active:
            states.append(check_token(token))

states.sort(key=lambda state: state.weight, reverse=True)

for state in states:
    print(state)

if any(isinstance(s, StateCritical) for s in states):
    sys.exit(2)
if any(isinstance(s, StateWarning) for s in states):
    sys.exit(1)

sys.exit(0)
