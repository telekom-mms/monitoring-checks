# Nagios/Icinga Checks for Kubernetes

You will need a kubeconfig file for both checks.

## Python Compatibility

Python >= 3.10

## Dependencies

Both Check Scripts are using inline uv, so just install uv and run the scripts direct.

Alternative, you can install the requirements via `requirements.txt` and run the scripts with `python check_kubernetes_nodes.py` and `python check_kubernetes_pods.py`.

## check_kubernetes_nodes.py

Checks the State of your nodes via the Kubernetes API. One node with Problems is a warning, two nodes are critical. Perfdata are supplied.

### Usage
```
usage: check_kubernetes_nodes.py [-h] [--kube-config KUBE_CONFIG]

optional arguments:
  -h, --help            show this help message and exit
  --kube-config KUBE_CONFIG
                        Kubernetes Config File
```

## check_kubernetes_pods.py

Checks the State of all pods in the Kubernetes Cluster.

### Usage
```
usage: check_kubernetes_pods.py [-h] [--kube-config KUBE_CONFIG]
                     [--warning-pending WARNING_PENDING]
                     [--critical-pending CRITICAL_PENDING]
                     [--warning-running WARNING_RUNNING]
                     [--critical-running CRITICAL_RUNNING]
                     [--warning-succeeded WARNING_SUCCEEDED]
                     [--critical-succeeded CRITICAL_SUCCEEDED]
                     [--warning-failed WARNING_FAILED]
                     [--critical-failed CRITICAL_FAILED]
                     [--warning-unknown WARNING_UNKNOWN]
                     [--critical-unknown CRITICAL_UNKNOWN]

optional arguments:
  -h, --help            show this help message and exit
  --kube-config KUBE_CONFIG
                        Kubernetes Config File
  --warning-pending WARNING_PENDING
  --critical-pending CRITICAL_PENDING
  --warning-running WARNING_RUNNING
  --critical-running CRITICAL_RUNNING
  --warning-succeeded WARNING_SUCCEEDED
  --critical-succeeded CRITICAL_SUCCEEDED
  --warning-failed WARNING_FAILED
  --critical-failed CRITICAL_FAILED
  --warning-unknown WARNING_UNKNOWN
  --critical-unknown CRITICAL_UNKNOWN
```
 