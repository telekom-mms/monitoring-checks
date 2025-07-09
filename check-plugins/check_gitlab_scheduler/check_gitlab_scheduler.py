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


class StateOk(Exception):
    name: str = "OK"
    weight: int = 0

class StateWarning(Exception):
    name: str = "WARNING"
    weight: int = 1

class StateCritical(Exception):
    name: str = "CRITICAL"
    weight: int = 2


def get_pipeline_url(
    gitlab_url: str, client: requests.session, project_id: str, pipeline_id: str
) -> str:
    "Gets the full URL for the pipeline to display in the output"
    url = gitlab_url + "/api/v4/projects/" + project_id + "/pipelines/" + pipeline_id
    try:
        r = client.get(url)
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
    client: requests.session,
    project_id: str,
    scheduler_id: str | None,
    pending_timeout: float,
    last_run: float,
) -> str:
    "Gets all schedules of an project"
    url = (
        gitlab_url
        + "/api/v4/projects/"
        + project_id
        + "/pipeline_schedules"
    )
    try:
        r = client.get(url)
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"CRITICAL - {err}")
        sys.exit(2)

    scheduler_ids: list[str] = []
    if scheduler_id:
        scheduler_ids = scheduler_id.split(",")

    states: list[StateOk | StateWarning | StateCritical] = []

    for scheduler_data in r.json():
        if not scheduler_id or (scheduler_id and str(scheduler_data['id']) in scheduler_ids):
            states.append(
                check_scheduler(
                    gitlab_url,
                    client,
                    project_id,
                    str(scheduler_data['id']),
                    pending_timeout,
                    last_run
                )
            )

    states.sort(key=lambda state: state.weight, reverse=True)

    for state in states:
        print(f"[{state.name}] {state}")

    if any(isinstance(s, StateCritical) for s in states):
        sys.exit(2)
    if any(isinstance(s, StateWarning) for s in states):
        sys.exit(1)

    sys.exit(0)


# pylint: disable=too-many-arguments
def check_scheduler(
    gitlab_url: str,
    client: requests.session,
    project_id: str,
    scheduler_id: str,
    pending_timeout: float,
    last_run: float,
) -> StateOk | StateWarning | StateCritical:
    "Checks the schedule"
    url = (
        gitlab_url
        + "/api/v4/projects/"
        + project_id
        + "/pipeline_schedules/"
        + scheduler_id
    )
    try:
        r = client.get(url)
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        return StateCritical(f"CRITICAL - {err}")

    variables = r.json()

    last_pipeline = variables["last_pipeline"]
    description = variables["description"]  # noqa: F841
    status = last_pipeline["status"]
    pipeline_id = last_pipeline["id"]
    last_pipeline_creation_time = get_datetime(last_pipeline["created_at"])
    scheduler_active = variables["active"]

    pipe_url = get_pipeline_url(  # noqa: F841
        gitlab_url, client, str(project_id), str(pipeline_id)
    )

    if scheduler_active is not True:
        return StateWarning(
            f"Scheduler is disabled - Pipeline:"
            f" {description}, Job-Status: {status}, Pipeline-URL: {pipe_url}"
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
            return StateCritical(
                f"Pipeline not run since {last_run_since} - Pipeline:"
                f" {description}, Job-Status: {status}, Pipeline-URL: {pipe_url}"
            )
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
        return StateCritical(
            f"Pipeline pending since {pipeline_pending_since} - Pipeline:"
            f" {description}, Status: {status}, URL: {pipe_url}"
        )
    else:
        return StateCritical(f"Pipeline: {description}, Status: {status}, URL: {pipe_url}")

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
            r2 = client.get(jobs_url)
            r2.raise_for_status()
            for job in r2.json():
                job_datetime = get_datetime(job["created_at"])
                if job_datetime < datetime.datetime.now(
                    datetime.timezone.utc
                ) - datetime.timedelta(seconds=pending_timeout):
                    job_pending_since = (  # noqa: F841
                        datetime.datetime.now(datetime.timezone.utc) - job_datetime
                    )
                    return StateCritical(
                        f"CRITICAL - Job pending since {job_pending_since} - Pipeline:"
                        f" {description}, Job: {job['id']}, Job-Status: {job['status']},"
                        f" Pipeline-URL: {pipe_url}"
                    )
        except requests.exceptions.HTTPError as err:
            return StateCritical(f"CRITICAL - {err}")

    return StateOk(f"Pipeline: {description}, Status: {status}, URL: {pipe_url}")


def get_datetime(date: str):
    "Returns a correctly formatted date"
    split = date.split("T")
    date_time_str = f"{split[0]} {split[1].split('.')[0]}"
    date_time = datetime.datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
    date_time = pytz.utc.localize(date_time)
    return date_time


def main() -> None:
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
    parser.add_argument(
        "-s",
        "--schedulerid",
        dest="scheduler_id",
        required=False,
        help="Optional, can also be multiple scheduler ids separated by comma"
    )
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

    client = requests.Session()
    client.headers.update({'PRIVATE-TOKEN': args.token})

    check_gitlab_scheduler(
        args.gitlab_url,
        client,
        args.project_id,
        args.scheduler_id,
        args.pending_timeout,
        args.last_run,
    )


if __name__ == "__main__":
    main()
