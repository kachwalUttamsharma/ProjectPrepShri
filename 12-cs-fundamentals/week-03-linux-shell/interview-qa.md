# Week 3 Interview Q&A - Linux & Shell for Engineers

Practice: answer out loud in 30-60 seconds first, then compare.

**1. What do /etc, /var, /proc, /sys, /dev, /tmp, and /usr hold?**
/etc is host-wide text config. /var is variable data: logs (/var/log), service data (/var/lib), spools. /proc and /sys are virtual kernel views (processes and tunables; devices and drivers), not on disk. /dev holds device files like /dev/null. /tmp is world-writable scratch with the sticky bit, possibly cleared on reboot. /usr holds userland programs and libraries, with /usr/local for admin-installed software. macOS has no /proc or /sys.

**2. df says the disk is 100% full but du shows far less. Why, and how do you fix it?**
Usually a deleted file still held open by a process: the name is gone but blocks are freed only when the last fd closes. Find it with `lsof +L1`, then restart the process or truncate through `/proc/<pid>/fd/N`. Other causes: a mount hiding data under its mount point, or inode exhaustion (`df -i`). Prevent with logrotate and truncating logs in place instead of `rm`.

**3. Explain permission 4755, 1777, and 640. What does umask 027 produce?**
4755 = setuid + rwxr-xr-x: runs as the file owner. 1777 = sticky + rwxrwxrwx: anyone may create, only the owner may delete (/tmp). 640 = rw-r-----. umask 027 gives new files 640 (666 & ~027) and new directories 750 (777 & ~027).

**4. What does the x bit mean on a directory, and what is needed to delete a file?**
x on a directory means you can traverse it (cd, access entries by name); r means list names. Deleting a file needs w and x on the containing directory, not write on the file itself. The sticky bit further restricts deletion to the file or directory owner.

**5. SIGTERM vs SIGKILL vs SIGHUP?**
SIGTERM (15) is a catchable polite request: the app should stop accepting work, drain in-flight requests, release resources, and exit. SIGKILL (9) cannot be caught or ignored; the kernel ends the process with no cleanup, so use it only after TERM times out. SIGHUP (1) originally meant the terminal hung up; daemons often reuse it as "reload config", and nohup makes a process ignore it.

**6. How should a service shut down gracefully, and how does the supervisor enforce it?**
Install a SIGTERM handler that flips a "draining" flag, stops the listener, finishes in-flight work, closes DB pools, and exits 0 within a grace period. The supervisor sends SIGTERM, waits (systemd TimeoutStopSec, Docker stop 10s, Kubernetes terminationGracePeriodSeconds 30s by default - check current docs), then sends SIGKILL. Uvicorn does this when it receives SIGTERM directly.

**7. Why does PID 1 in a container matter?**
The kernel does not apply default signal actions to PID 1, so SIGTERM is ignored unless the process installs a handler; `docker stop` then waits for SIGKILL. PID 1 must also reap orphaned zombies. Shell-form `CMD` wraps the app in `sh -c`, which may not forward signals. Use exec form, `exec` in entrypoint scripts, or an init like tini (`docker run --init`).

**8. What is a zombie process, and what is a process in D state?**
A zombie has exited but its parent has not called wait(), so only a process-table entry remains; you cannot kill it, so fix or kill the parent so init reaps it. D is uninterruptible sleep, usually blocked on IO (dead NFS, failing disk); it ignores signals until IO returns and inflates load average while CPU stays idle.

**9. How do you keep a job alive after your ssh session drops?**
Best: run inside tmux or screen and reattach. Quick: `nohup cmd > out.log 2>&1 &` or `disown` after backgrounding. For anything long-lived or production, make it a systemd service (or a scheduled job) so it restarts and logs properly.

**10. Give a one-liner for the top 10 client IPs in an access log, and say what each tool does.**
`awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10`. awk extracts field 1, sort groups identical lines (uniq only merges adjacent ones), `uniq -c` counts, `sort -rn` orders by count descending, head keeps ten. For JSON logs use `jq -r .ip` instead of regex.

**11. When would you choose rg, fd, sd, jq, bat over grep, find, sed, and cat? When not?**
rg: fast recursive search that respects .gitignore. fd: simple, fast filename search. sd: substitution without sed escaping. jq: any JSON (never regex JSON). bat: readable file viewing. Stay with the classics on customer servers where the modern tools are not installed, in portable scripts, and for features like find's `-mtime/-perm/-exec`. Also remember macOS sed is BSD: `sed -i ''`.

**12. What does `cmd > out 2>&1` do and does order matter? Why does `sudo echo x > /etc/f` fail?**
It points fd1 at `out`, then fd2 at wherever fd1 now points, so both streams go to the file. Reversed (`2>&1 > out`) sends stderr to the original stdout (terminal). The sudo case fails because the redirect is performed by your unprivileged shell; use `echo x | sudo tee /etc/f`.

**13. What is a file descriptor, and what are here-docs and process substitution?**
An fd is a small integer indexing a process's open-file table; 0, 1, 2 are stdin, stdout, stderr; sockets, pipes, and files all use them (see `/proc/<pid>/fd`). A here-doc (`<<'EOF'`) feeds inline text to stdin (quoted delimiter disables expansion). Process substitution `<(cmd)` exposes a command's output as a file path: `diff <(sort a) <(sort b)`, and avoids the pipe-subshell variable loss.

**14. How does ssh key auth work, and what is in ~/.ssh/config worth knowing?**
The server holds your public key in authorized_keys; at login it challenges you and you prove possession by signing with the private key, which never leaves your machine. known_hosts pins server host keys to detect MITM. Config gives per-host aliases, User, IdentityFile, ProxyJump for bastions, ServerAliveInterval, and ControlMaster multiplexing. Permissions must be strict (~/.ssh 700, private key 600).

**15. Explain ssh -L vs -R, and how you reach a private database via a jump host.**
-L opens a listener on your laptop and forwards through the ssh server to a target: `ssh -L 5432:db.internal:5432 bastion`, then connect to localhost:5432. -R opens a listener on the remote host that forwards back to something on your side (expose my local service to them). Jump host: `ssh -J bastion user@private`, preferred over agent forwarding (`-A`) for security.

**16. scp vs rsync?**
scp is a simple one-shot copy. rsync transfers only differences, resumes, preserves attributes, can `--delete`-mirror (dry-run with `-n` first), and works over ssh (`-e "ssh -J bastion"`). Trailing slash on the source copies its contents rather than the directory itself. Use rsync for anything large or repeated.

**17. Write a systemd unit for a uvicorn FastAPI service and explain Restart=.**
[Unit] After=network-online.target; [Service] User=app, WorkingDirectory, EnvironmentFile=/etc/app.env, `ExecStart=/opt/app/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000`, Restart=on-failure, RestartSec=3, TimeoutStopSec=30; [Install] WantedBy=multi-user.target. Then `daemon-reload`, `enable --now`. on-failure restarts on non-zero exit or signal kill; always restarts even after clean exit; start-limit settings stop crash loops (`reset-failed` clears). Debug with `systemctl status` and `journalctl -u app -e`.

**18. A script works in your shell but fails in cron or systemd. Why?**
Different environment: minimal PATH, no profile or rc files, different cwd and user, no ssh-agent or activated venv. Fix with absolute paths, explicit `PATH=`, `cd` inside the command, `EnvironmentFile=`/`Environment=` in systemd, and redirect output (`>> log 2>&1`) because cron otherwise mails or drops it. Escape `%` in crontab lines and use `flock` to prevent overlapping runs.

**19. A service is slow. Walk me through diagnosis, then the cases of hung, OOM-killed, and disk full.**
Orient with `uptime`, `top`, `free -h`, `df -h`, `ss -ltnp`, then the app log. Slow with high CPU: top/ps, then py-spy or `strace -c`. Slow with low CPU and high load: `vmstat`/`iostat -x` for IO wait or D-state. Hung: check it listens, `strace -p`/`py-spy dump`, `lsof` to see what it waits on (often exhausted DB pool). Killed with no traceback: `dmesg -T | rg -i oom`, exit 137. Disk full: `df -h`, `df -i`, `du -xh | sort -h`, `lsof +L1`. Capture evidence before restarting, change one thing at a time.

**20. What do `set -euo pipefail`, quoting, and trap do in a robust deploy script, and what are the limits?**
`-e` aborts on failure, `-u` errors on unset variables, pipefail fails a pipeline if any stage fails. Quote every expansion (`"$f"`, `"$@"`) to prevent word splitting and globbing. `trap cleanup EXIT` runs cleanup/rollback on success, failure, or interrupt (SIGKILL cannot be trapped). Add a lock (`flock`), bounded health-check retries with timeouts, meaningful exit codes, and run shellcheck. Limits: `-e` is ignored in `if`/`||` contexts and `local x=$(cmd)` hides failures; switch to Python when logic grows.
