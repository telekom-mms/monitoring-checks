# Check Gitlab Scheduler

This script can check Gitlab Scheduled Pipelines and its jobs for errors.
Additionally it can check if the pipeline and jobs are stuck in pending state (with --pending-timeout).
It can also check if a Pipeline's last execution happened longer than a specified amount of time (--last-run).

```
usage: Check Gitlab Scheduler [-h] -u GITLAB_URL -p PROJECT_ID [-s SCHEDULER_ID] -t TOKEN [-o PENDING_TIMEOUT] [-l LAST_RUN]

options:
  -h, --help            show this help message and exit
  -u GITLAB_URL, --gitlab_url GITLAB_URL
  -p PROJECT_ID, --projectid PROJECT_ID
  -s SCHEDULER_ID, --schedulerid SCHEDULER_ID
                        Optional, can also be multiple scheduler ids separated by comma
  -t TOKEN, --token TOKEN
  -o PENDING_TIMEOUT, --pending-timeout PENDING_TIMEOUT
                        check the pipeline itself and the jobs in the pipeline if they are in pending for pending_timeout seconds
  -l LAST_RUN, --last-run LAST_RUN
                        check if the last pipeline was ran for more then last_run seconds
```

# Authors

- Christopher Grau
- Sebastian Gumprich
- Julian Mühmelt
- Martin Neubert
