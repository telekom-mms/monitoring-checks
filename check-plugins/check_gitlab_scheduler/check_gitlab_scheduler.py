#!/usr/bin/env python3
# -*- coding: utf-8 *-*

"""
Copyright 2023 Deutsche Telekom MMS GmbH
Maintainer: Christopher Grau
"""

import sys
import datetime
import argparse
from argparse import RawDescriptionHelpFormatter
import json
import requests
import pytz


def get_pipeline_url(
    gitlab_url: str, token: str, project_id: str, pipeline_id: str
) -> str:
    "Gets the full URL for the pipeline to display in the output"
    url = gitlab_url + "/api/v4/projects/" + project_id + "/pipelines/" + pipeline_id
    headers = {"PRIVATE-TOKEN": token}
    try:
        r = requests.request("GET", url, headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"CRITICAL - {err}")
        sys.exit(2)

    variables = json.loads(r.text)
    web_url = variables["web_url"]

    return web_url


# pylint: disable=too-many-arguments
def check_gitlab_scheduler(
    gitlab_url: str,
    token: str,
    project_id: str,
    scheduler_id: str,
    pending_timeout: float,
    last_run: float,
) -> str:
    "Checks the schedule"
    url = (
        gitlab_url
        + "/api/v4/projects/"
        + project_id
        + "/pipeline_schedules/"
        + scheduler_id
    )
    headers = {"PRIVATE-TOKEN": token}
    try:
        r = requests.request("GET", url, headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"CRITICAL - {err}")
        sys.exit(2)

    variables = json.loads(r.text)

    last_pipeline = variables["last_pipeline"]
    description = variables["description"]  # noqa: F841
    status = last_pipeline["status"]
    pipeline_id = last_pipeline["id"]
    last_pipeline_creation_time = get_datetime(last_pipeline["created_at"])

    pipe_url = get_pipeline_url(  # noqa: F841
        gitlab_url, token, str(project_id), str(pipeline_id)
    )

    if status in ["success", "running"]:
        # check if the last run of the pipeline is not older than last_run seconds
        if last_run is not None and last_pipeline_creation_time < datetime.datetime.now(
            datetime.timezone.utc
        ) - datetime.timedelta(seconds=last_run):
            last_run_since = (  # noqa: F841
                datetime.datetime.now(datetime.timezone.utc)
                - last_pipeline_creation_time
            )
            print(
                f"CRITICAL - Pipeline not run since {last_run_since} - Pipeline:"
                f" {description}, Job-Status: {status}, Pipeline-URL: {pipe_url}"
            )
            sys.exit(2)
        else:
            pass
    elif (
        pending_timeout is not None
        and status == "pending"
        and last_pipeline_creation_time
        < datetime.datetime.now(datetime.timezone.utc)
        - datetime.timedelta(seconds=pending_timeout)
    ):
        pipeline_pending_since = (  # noqa: F841
            datetime.datetime.now(datetime.timezone.utc) - last_pipeline_creation_time
        )
        print(
            f"CRITICAL - Pipeline pending since {pipeline_pending_since} - Pipeline:"
            f" {description}, Status: {status}, URL: {pipe_url}"
        )
        sys.exit(2)
    else:
        print(f"CRITICAL - Pipeline: {description}, Status: {status}, URL: {pipe_url}")
        sys.exit(2)

    # check for pending jobs inside the pipeline. they can be pending, too
    if pending_timeout is not None:
        jobs_url = (
            gitlab_url
            + "/api/v4/projects/"
            + project_id
            + "/pipelines/"
            + str(pipeline_id)
            + "/jobs?scope[]=pending"
        )
        try:
            r2 = requests.request("GET", jobs_url, headers=headers)
            r2.raise_for_status()
            for job in r2.json():
                job_datetime = get_datetime(job["created_at"])
                if job_datetime < datetime.datetime.now(
                    datetime.timezone.utc
                ) - datetime.timedelta(seconds=pending_timeout):
                    job_pending_since = (  # noqa: F841
                        datetime.datetime.now(datetime.timezone.utc) - job_datetime
                    )
                    print(
                        f"CRITICAL - Job pending since {job_pending_since} - Pipeline:"
                        f" {description}, Job: {job['id']}, Job-Status: {job['status']},"
                        f" Pipeline-URL: {pipe_url}"
                    )
                    sys.exit(2)
        except requests.exceptions.HTTPError as err:
            print(f"CRITICAL - {err}")
            sys.exit(2)

    print(f"OK - Pipeline: {description}, Status: {status}, URL: {pipe_url}")
    sys.exit(0)


def get_datetime(date: str):
    "Returns a correctly formatted date"
    split = date.split("T")
    date_time_str = f"{split[0]} {split[1].split('.')[0]}"
    date_time = datetime.datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
    date_time = pytz.utc.localize(date_time)
    return date_time


def main():
    "Entrypoint"
    parser = argparse.ArgumentParser(
        prog="Check Gitlab Scheduler",
        description="""This script can check Gitlab Scheduled Pipelines and its
jobs for errors. Additionally it can check if the pipeline and jobs are stuck
in pending state (with --pending-timeout). It can also check if a Pipeline's
last execution happened longer than a specified amount of time (--last-run)""",
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument("-u", "--gitlab_url", dest="gitlab_url", required=True)
    parser.add_argument("-p", "--projectid", dest="project_id", required=True)
    parser.add_argument("-s", "--schedulerid", dest="scheduler_id", required=True)
    parser.add_argument("-t", "--token", dest="token", required=True)
    parser.add_argument(
        "-o",
        "--pending-timeout",
        dest="pending_timeout",
        type=int,
        help=(
            "check the pipeline itself and the jobs in the pipeline if they are in"
            " pending for pending_timeout seconds"
        ),
    )
    parser.add_argument(
        "-l",
        "--last-run",
        dest="last_run",
        type=int,
        help="check if the last pipeline was ran for more then last_run seconds",
    )
    args = parser.parse_args()

    check_gitlab_scheduler(
        args.gitlab_url,
        args.token,
        args.project_id,
        args.scheduler_id,
        args.pending_timeout,
        args.last_run,
    )


if __name__ == "__main__":
    main()
