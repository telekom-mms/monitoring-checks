import argparse
import sys

import gitlab


def main():
    parser = argparse.ArgumentParser(
        prog="check_gitlab_merge_requests.py",
        description="check if project or group has open merge requests",
    )

    parser.add_argument("-u", "--gitlab_url", dest="gitlab_url", required=True)
    parser.add_argument("-t", "--token", dest="token", required=True)
    parser.add_argument("--project-id", help="Project ID", type=int)
    parser.add_argument("--group-id", help="Group ID", type=int)
    parser.add_argument(
        "-w",
        "--warning",
        dest="warning",
        type=int,
        help="warning limit of count of open merge requests",
        default=1,
    )
    parser.add_argument(
        "-c",
        "--critical",
        dest="critical",
        type=int,
        help="critical limit of count of open merge requests",
        default=1,
    )

    args = parser.parse_args()
    if not (any([args.group_id, args.project_id])):
        print("Please provide either a project ID or a group ID")
        sys.exit(255)

    try:
        gl = gitlab.Gitlab(args.gitlab_url, args.token)
    except gitlab.GitlabAuthenticationError:
        print("login with private token failed")
        sys.exit(255)

    if args.group_id:
        gitlab_object = gl.groups.get(args.group_id, lazy=False)
    elif args.project_id:
        gitlab_object = gl.projects.get(args.project_id, lazy=False)
    count_mrs = len(gitlab_object.mergerequests.list(state="opened", get_all=True))

    if count_mrs >= args.critical:
        print(
            f"[CRITICAL]: {count_mrs} open merge requests in {gitlab_object.__class__.__name__} {gitlab_object.name}"
        )
        sys.exit(2)
    if count_mrs >= args.warning:
        print(
            f"[WARNING]: {count_mrs} open merge requests in {gitlab_object.__class__.__name__} {gitlab_object.name}"
        )
        sys.exit(1)
    print(
        f"[OK]: {count_mrs} open merge requests in {gitlab_object.__class__.__name__} {gitlab_object.name}"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
