#!/usr/bin/env python3
"""
run_all.py — Python wrapper that:
  1. Establishes an SSH tunnel to forward remote MLflow UI port to localhost and verifies success.
  2. Starts MLflow UI on the remote head node (via start_mlflow.sh) and verifies it's running.
  3. Submits the Slurm training job (train.sh) on the remote head node and verifies it's queued.
  4. Opens your local browser at http://localhost:<port> to view the live MLflow dashboard.
  5. Performs final checks: confirms the Slurm job is running, MLflow UI responds, and the tunnel remains open.

Configuration:
  Adjust HOST, USER, PORT, and REMOTE_BASE_DIR below before running.

Usage:
  python run_all.py

Requires that `start_mlflow.sh` and `train.sh` reside in REMOTE_BASE_DIR on the remote host.
"""
import subprocess
import socket
import time
import webbrowser
import sys
import urllib.request

# --- Configuration: set these before running ---
HOST = "10.26.36.96"      # Remote head node hostname or IP
USER = "yakirh"                  # SSH username on the remote
PORT = 5000                              # MLflow UI port
REMOTE_BASE_DIR = "~/Projects/yakirs_thesis/thesis/"                  # Remote directory where scripts reside
TUNNEL_RETRY = 5                         # Seconds to wait for tunnel
MFLOW_RETRY = 10                         # Seconds to wait for MLflow startup
JOB_CHECK_DELAY = 5                      # Seconds after submission to check job status


def is_local_port_open(port):
    """Check if TCP port on localhost is accepting connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(('127.0.0.1', port)) == 0


def start_ssh_tunnel():
    """Start an SSH tunnel in background to forward local port to remote port."""
    cmd = ['ssh', '-N', '-L', f'{PORT}:localhost:{PORT}', f'{USER}@{HOST}']
    print(f"Starting SSH tunnel: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd)
    for i in range(TUNNEL_RETRY):
        time.sleep(1)
        if is_local_port_open(PORT):
            print(f"SSH tunnel established (localhost:{PORT} → {HOST}:{PORT}).")
            return proc
    print(f"Error: SSH tunnel failed to open local port {PORT} after {TUNNEL_RETRY}s.", file=sys.stderr)
    proc.terminate()
    sys.exit(1)


def run_remote_command(command):
    """Run a shell command on the remote host via SSH (blocking)."""
    full_cmd = ['ssh', f'{USER}@{HOST}', command]
    print(f"Running on remote: {command}")
    result = subprocess.run(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Remote command failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def http_check(url, timeout=5):
    """Check that HTTP GET to url returns 200."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"HTTP check failed: {e}", file=sys.stderr)
        return False


def main():
    # 1) SSH tunnel and verify
    tunnel_proc = start_ssh_tunnel()

    # 2) Run git.sh on the remote to perform any necessary git actions
    print("Running git.sh on remote...")
    run_remote_command(f"bash {REMOTE_BASE_DIR}git.sh")

    # 3) Start MLflow UI on remote and verify
    start_cmd = f"bash {REMOTE_BASE_DIR}start_mlflow.sh &"
    run_remote_command(start_cmd)
    print("MLflow start command sent to remote.")

    print(f"Waiting up to {MFLOW_RETRY}s for MLflow UI to become available...")
    for i in range(MFLOW_RETRY):
        time.sleep(1)
        if is_local_port_open(PORT) and http_check(f'http://localhost:{PORT}'):
            print(f"MLflow UI reachable at http://localhost:{PORT}.")
            break
    else:
        print(f"Warning: MLflow UI did not respond on localhost:{PORT} after {MFLOW_RETRY}s.", file=sys.stderr)

    # 4) Submit Slurm job on remote, capture job ID
    submission = run_remote_command(f"sbatch {REMOTE_BASE_DIR}train.sh")
    print(f"Slurm submission response: {submission}")
    try:
        job_id = submission.strip().split()[-1]
    except Exception:
        print("Could not parse job ID from submission.", file=sys.stderr)
        job_id = None

    # Delay then verify job is queued/running
    if job_id:
        time.sleep(JOB_CHECK_DELAY)
        check_cmd = f"squeue -j {job_id} -h | wc -l"
        count = run_remote_command(check_cmd)
        if count.strip() != '0':
            print(f"Job {job_id} is currently queued/running.")
        else:
            print(f"Warning: Job {job_id} not found in squeue.", file=sys.stderr)

    # 5) Open local browser
    url = f'http://localhost:{PORT}'
    print(f"Opening browser at {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Could not open browser: {e}")

    # 5) Final verification summary
    print("\n=== Verification Summary ===")
    print(f"Tunnel open: {'yes' if is_local_port_open(PORT) else 'no'}")
    print(f"MLflow running: {'yes' if http_check(f'http://localhost:{PORT}') else 'no'}")
    if job_id:
        running = 'yes' if count.strip() != '0' else 'no'
        print(f"Slurm job {job_id} running: {running}")

    print("Setup complete. Script will keep running to maintain SSH tunnel.")

    # Keep script alive to maintain tunnel
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nReceived Ctrl-C, exiting and closing SSH tunnel.")
        tunnel_proc.terminate()
        sys.exit(0)


if __name__ == '__main__':
    main()
