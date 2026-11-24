# Week 3 - Linux & Shell for Engineers: Filesystem, Permissions, Processes, Text Tools, ssh, systemd, Debugging, Bash

Time budget: ~7-8 hrs. Read lesson (3h), try commands in a Linux box/container (2h), Q&A aloud (1.5h), cheatsheet (1h).
Facts marked "(check current docs)" are version-dependent (distro, kernel, tool version); verify before quoting in an interview.

Platform note: most of this runs on Linux. macOS is BSD-flavored: no /proc, no systemd, no strace (use dtruss/fs_usage, needs SIP tweaks), no `free`/`ss`/`iostat -x`. BSD vs GNU flag differences are called out as "macOS:" lines. To practice Linux on a Mac: `docker run -it --rm ubuntu:24.04 bash` (check current docs for tag) or a Multipass/Lima VM. systemd generally does NOT run inside a plain container.

---
## 1. Filesystem layout (FHS)

```
 /                     root of the single tree (no drive letters)
 |-- bin, sbin, lib    essential binaries/libs (often symlinks into /usr on modern distros)
 |-- usr/              userland: /usr/bin, /usr/lib, /usr/local (admin-installed software)
 |-- etc/              host-wide CONFIG (text files): /etc/ssh, /etc/hosts, /etc/passwd, /etc/systemd
 |-- var/              VARIABLE data: /var/log, /var/lib (DB data), /var/spool (cron, mail), /var/cache
 |-- tmp/              scratch, world-writable + sticky; may be wiped at reboot
 |-- home/             user home dirs (/root is root's home)
 |-- opt/              self-contained third-party software
 |-- proc/             VIRTUAL: process + kernel info (/proc/<pid>/..., /proc/meminfo, /proc/cpuinfo)
 |-- sys/              VIRTUAL: kernel objects/devices/tunables (sysfs)
 |-- dev/              device files: /dev/null, /dev/zero, /dev/urandom, /dev/sda, /dev/tty
 |-- run/              runtime state since boot (tmpfs): pid files, sockets
 |-- mnt, media        mount points
```

Key points
- Everything is a file: regular files, directories, devices, sockets, pipes. That is why `cat /proc/meminfo` and `echo > /dev/null` work.
- Config in /etc, logs in /var/log, data in /var/lib, code in /usr or /opt. Knowing this = you can find things on an unfamiliar customer box in seconds.
- /proc and /sys are not on disk; they are kernel views. `ls -l /proc/<pid>/fd` lists open files of a process; `cat /proc/<pid>/cmdline | tr '\0' ' '` shows its args; `/proc/<pid>/environ` its env; `/proc/<pid>/limits` its ulimits.
- Inodes: a file name is a directory entry pointing to an inode. Hard link = another name for the same inode; symlink = a file holding a path. A disk can be "full" by blocks (`df -h`) or by inodes (`df -i`).
- Deleted-but-open files: `rm` removes the name; space is freed only when the last open fd closes. `lsof +L1` finds them. Classic "df says full, du says not".
- Mounts: `mount`, `findmnt`, `/etc/fstab` (persistent mounts). tmpfs is RAM-backed.

Try it
```
ls -l /proc/self/fd          # Linux only
df -h; df -i                 # space; inodes
du -sh /var/log/* | sort -h | tail
stat /etc/hosts              # inode, perms, times (macOS: stat -x /etc/hosts)
```

Gotcha: macOS has /Users instead of /home, /private/tmp, no /proc; paths in scripts are not portable.
Gotcha: `du -sh *` skips dotfiles; `du -sh .[!.]* *` or `du -sh . ` variants differ. `du` on macOS lacks `--max-depth` (use `-d 1`).

How interviewers probe it: "Where do logs/config/data live?", "Why is df full but du small?" (deleted open file / hidden mount shadowing), "What is /proc?", "Hard vs soft link?", "Out of inodes but free space - why?" (millions of tiny files).

---
## 2. Permissions

```
 -rwxr-xr-x  1 alice dev  4096 Jan  1 app.sh
 |\_/\_/\_/
 | |  |  +-- other   r-x = 5
 | |  +----- group   r-x = 5
 | +-------- owner   rwx = 7
 +---------- type: - file, d dir, l symlink, c/b device, s socket, p pipe

 r=4 w=2 x=1      755 = rwxr-xr-x     644 = rw-r--r--     600 = rw-------
```

| Bit | On a file | On a directory |
|---|---|---|
| r | read contents | list names (ls) |
| w | modify contents | create/delete/rename entries (needs x too) |
| x | execute | enter (cd) / access entries by name |

Special bits
```
 setuid (4xxx, s in owner x): exec runs as the FILE OWNER (e.g. /usr/bin/passwd)
 setgid (2xxx, s in group x): exec runs as file group; on a DIR new files inherit the dir's group
 sticky (1xxx, t in other x): on a dir, only file owner/dir owner can delete entries (/tmp is 1777)
```

Commands
```
chmod 640 f; chmod u+x,g-w f; chmod -R g+rX dir   # X = x only on dirs/already-exec files
chown alice:dev f; chown -R app: /srv/app           # macOS: same syntax; no --reference
umask            # default mask; new files = 666 & ~umask, dirs = 777 & ~umask
umask 027        # files 640, dirs 750
id; groups       # who am I
sudo -l          # what may I sudo
```

Key points
- Permission check order: owner class -> group class -> other. Root bypasses (except capability/immutable/SELinux limits).
- Default umask 022 (files 644, dirs 755); 002 on some distros with per-user groups (check current docs).
- Executing a script needs x on the file AND the interpreter; reading needs r. Directories along the path need x (`namei -l /path` shows each hop; Linux).
- setuid is ignored on shell scripts by Linux for security; avoid setuid generally. Prefer capabilities (`setcap`) or sudo rules.
- ACLs (`getfacl`/`setfacl`), `chattr +i` (immutable), SELinux/AppArmor can deny even when rwx says yes. `ls -Z`, `getenforce`. Suspect them when perms look right but access fails (FDE classic on RHEL customers).
- Never `chmod 777` to "fix" it; find the actual user (`ps -o user`, `id`) and grant narrowly. SSH private keys must be 600 or ssh refuses.

Gotcha: `chmod -R 755` makes all data files executable; use `find . -type d -exec chmod 755 {} +` and `-type f ... 644`, or `chmod -R u=rwX,go=rX`.
Gotcha: deleting a file needs w on the DIRECTORY, not on the file.
Gotcha: A service running as user `app` cannot read `/home/alice/...` if /home/alice is 700, even if the file itself is 644.

How interviewers probe it: "What does 4755 mean?", "Why can't I delete this file though I own it?" (sticky/dir perms), "What does x mean on a directory?", "umask 027 -> resulting modes?", "Container process reads fine as root but fails as non-root - why?"

---
## 3. Processes and signals

```
 init/systemd (PID 1)
   |-- sshd --- sshd (session) --- bash --- python app.py      parent/child tree (pstree -p)
   |-- cron
   `-- uvicorn (service)
 States (ps STAT): R running, S sleeping, D uninterruptible IO (cannot be killed!),
                   T stopped, Z zombie (exited, parent has not wait()ed)
```

Key points
- fork() copies a process, exec() replaces its image. Every process has PID, PPID, UID, cwd, env, open fds, signal handlers.
- Zombie: already dead, only a table entry; kill does nothing; fix the parent (or kill the parent so init reaps it). Orphan: parent died, reparented to PID 1.
- D state: blocked in kernel IO (dead NFS, failing disk). SIGKILL cannot take effect until IO returns. Many D processes + high load average with low CPU = IO problem.
- Load average counts runnable + D-state tasks; compare to core count (`nproc`).

Signals

| Signal | # | Meaning | Catchable | Typical use |
|---|---|---|---|---|
| SIGHUP | 1 | terminal hung up | yes | daemons treat as "reload config" (nginx, sshd) |
| SIGINT | 2 | Ctrl-C | yes | interactive interrupt |
| SIGQUIT | 3 | Ctrl-\ | yes | quit + core dump |
| SIGKILL | 9 | forced kill | NO | last resort; no cleanup |
| SIGTERM | 15 | polite terminate (default of `kill`) | yes | graceful shutdown |
| SIGSTOP / SIGCONT | 19/18 (Linux) | pause / resume | STOP no | job control (numbers differ on macOS) |
| SIGUSR1/2 | 10/12 (Linux) | app-defined | yes | log rotate/debug dump |
| SIGCHLD | 17 | child changed state | yes | parent reaping |

Graceful shutdown pattern: send SIGTERM -> app stops accepting new work, finishes in-flight requests, closes DB connections, flushes, exits within a grace period -> supervisor sends SIGKILL after timeout (systemd TimeoutStopSec default 90s; Kubernetes terminationGracePeriodSeconds default 30s; Docker stop 10s - check current docs).
```
kill PID            # SIGTERM
kill -HUP PID       # reload
kill -9 PID         # SIGKILL: last resort (leaves temp files, locks, half-written data)
pkill -f 'uvicorn app:app'; pgrep -fa python
kill -l             # list signals
```

PID 1 in containers
- The first process in a container is PID 1. The kernel gives PID 1 special treatment: signals with default action (like SIGTERM) are IGNORED unless PID 1 installs a handler. So a naive `python app.py` as PID 1 may not stop on `docker stop` until SIGKILL after 10s.
- PID 1 must also reap zombie children. Shell-form `CMD python app.py` runs `sh -c`, and sh may not forward signals. Use exec form `CMD ["uvicorn", ...]` or `exec python ...` in entrypoint scripts, and `--init` (tini) or `docker run --init` to get a proper init (check current docs).
- Python/uvicorn handle SIGTERM gracefully when run directly (uvicorn drains then exits).

Job control (interactive shell)
```
cmd &            # background        jobs        # list
Ctrl-Z           # stop (SIGTSTP)   bg %1 / fg %1
nohup cmd > out.log 2>&1 &    # ignore SIGHUP so it survives logout; output to file
disown -h %1     # detach already-running job from shell
tmux new -s fix  # persistent session: detach Ctrl-b d, reattach `tmux attach -t fix`
```
For FDEs: run long jobs inside tmux (or screen) on customer boxes so a dropped ssh does not kill them. For production services use systemd, not nohup.

Gotcha: `kill -9` first is a bad habit: skips cleanup, leaves lock/pid files, may corrupt state. TERM, wait, then KILL.
Gotcha: `kill` on a pipeline/child tree: negative PID kills a process group (`kill -TERM -PGID`).
Gotcha: `$!` is the PID of last background job; `wait $!` waits and returns its exit code.

How interviewers probe it: "SIGTERM vs SIGKILL?", "Why can't you trap SIGKILL?", "Why does my container take 10s to stop?" (PID 1 / shell form), "What is a zombie?", "Process stuck in D state?", "How do you keep a job alive after ssh drops?"

---
## 4. Text tools

```
 producer --> filter --> filter --> consumer          Unix philosophy: small tools, text streams
 tail -f app.log | grep ERROR | awk '{print $5}' | sort | uniq -c | sort -rn | head
```

| Tool | Does | Example |
|---|---|---|
| grep | match lines (regex) | `grep -rniE 'timeout\|refused' /var/log/app` ; `-v` invert, `-c` count, `-A3 -B3` context, `-o` only match |
| cut | slice columns | `cut -d, -f1,3 data.csv` ; `cut -c1-10` |
| awk | field-aware mini-language | `awk -F: '$3>=1000 {print $1}' /etc/passwd` ; `awk '{s+=$NF} END{print s}'` |
| sed | stream edit, mostly substitution | `sed -n '10,20p' f` ; `sed 's/foo/bar/g' f` |
| sort | order lines | `sort -k2,2nr` ; `-u`, `-h` human sizes, `-t, -k3` |
| uniq | collapse ADJACENT dupes (sort first!) | `sort \| uniq -c \| sort -rn` |
| tr | char map/delete | `tr -d '\r'` ; `tr 'a-z' 'A-Z'` |
| wc, head, tail | count, first/last N | `tail -n 100 -f`, `wc -l` |
| xargs | turn stdin into args | `find . -name '*.log' -print0 \| xargs -0 -P4 gzip` |
| find | walk tree by predicates | `find /var -type f -size +100M -mtime -1` ; `-exec cmd {} +` |
| tee | split stream to file and stdout | `cmd \| tee out.txt` |

Modern equivalents (install via brew/apt/cargo; not on every customer box)

| Modern | Replaces | Better when | Stick with the classic when |
|---|---|---|---|
| rg (ripgrep) | grep -r | big trees; respects .gitignore, skips binaries, parallel, fast; sane `-r` is recursive default | box lacks it (customer servers!), need POSIX portability, scripts |
| fd | find | simple name search `fd '\.py$'`; fast; ignores .git | complex predicates (-mtime, -perm, -size, -exec semantics) |
| sd | sed s/// | no escaping hell, PCRE-ish regex, `sd 'a(\d+)' 'b$1' f` edits in place | line addressing, `sed -n 'Np'`, portability |
| jq | (none: parse JSON) | any JSON: `curl -s api \| jq '.items[] \| {id,name}'`; `-r` raw; `-e` exit status | not JSON |
| bat | cat | syntax highlighting, paging, line numbers | piping (bat detects pipes and acts like cat) |
| ast-grep | grep for code | structural search/rewrite (`ast-grep -p 'print($A)'`) | plain text |

Key points
- Rule of thumb: grep to filter lines, cut for fixed delimiters, awk when you need conditions/arithmetic/columns, sed for substitution, jq for JSON (never regex JSON).
- On a customer box you will have grep/awk/sed/find, probably not rg/fd. Know the classics cold; use modern ones locally.
- Always `find ... -print0 | xargs -0` for names with spaces. `xargs -P N` parallelizes; `-n1` one arg per command; `-I{}` placeholder.
- Log analysis staple: top client IPs
```
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10
```
- Count errors per minute: `grep ERROR app.log | cut -c1-16 | uniq -c`.

macOS vs GNU
- macOS sed is BSD: in-place needs a suffix arg: `sed -i '' 's/a/b/' f` (GNU: `sed -i 's/a/b/' f`). `\+`, `\|`, `\b` and `\n` replacements often fail on BSD; use `sed -E`. Portable trick: `sed -i.bak ... f` works on both.
- BSD grep lacks `-P` (PCRE); use `grep -E` or install ggrep/rg. BSD `sort` lacks some GNU `-h`/`-V` in older versions; `date -d` is GNU only (macOS: `date -v-1d`); `readlink -f` missing on older macOS; `xargs -r` GNU only. `brew install coreutils gnu-sed` gives `gsed`, `gdate`.
- `ls --color` GNU vs `ls -G` BSD.

Gotcha: `grep pattern file | wc -l` counts lines; `grep -c` is the same but `-o ... | wc -l` counts matches.
Gotcha: unquoted `*.log` is expanded by the shell, not the tool; quote regexes (`'a|b'`) so the shell does not interpret `|`.
Gotcha: `uniq` without `sort` only merges adjacent lines.
Gotcha: `sort` uses locale; `LC_ALL=C sort` is faster and byte-ordered.

How interviewers probe it: "Top 10 IPs from an access log", "Find files > 1 GB modified today", "Replace a string across a repo", "Why sort before uniq?", "grep vs awk?", "Parse JSON in shell" (jq).

---
## 5. Pipes, redirects, file descriptors

```
 fd 0 stdin    fd 1 stdout    fd 2 stderr     (a process gets these three; more fds via open())

 cmd > out        stdout -> file (truncate)      cmd >> out       append
 cmd 2> err       stderr -> file                 cmd < in         stdin from file
 cmd > out 2>&1   BOTH to out   (order matters!) cmd &> out       bash shorthand for both
 cmd 2>&1 | grep  pipe both     cmd |& grep      bash shorthand
 cmd > /dev/null 2>&1     discard everything     cmd 2>/dev/null  discard errors only
```

Order matters: `cmd > f 2>&1` = point fd1 at f, THEN point fd2 at where fd1 now goes (f). `cmd 2>&1 > f` points fd2 at the old stdout (terminal) first, so stderr still hits the terminal.

More
```
cat <<'EOF' > conf.yml        # here-doc; quoted 'EOF' = no $var expansion; unquoted expands
name: $HOME
EOF
cat <<< "one-line here-string"
cmd | tee out.log | grep X          # save AND continue; tee -a appends
sudo sh -c 'echo x > /etc/f'        # redirect happens in YOUR shell, not sudo's:
echo x | sudo tee /etc/f >/dev/null # fix for "permission denied" on sudo echo > file
diff <(sort a) <(sort b)            # process substitution: command output as a file path
exec 3>audit.log; echo hi >&3; exec 3>&-   # custom fd
```
- Pipe `|` connects stdout of left to stdin of right; both run concurrently; a full pipe buffer blocks the writer (backpressure). stderr is not piped unless `2>&1`.
- `$?` is the exit code of the LAST command; with `set -o pipefail` the pipeline fails if any stage fails. `${PIPESTATUS[@]}` (bash) gives all.
- Pipes run stages in subshells: `cmd | while read x; do n=$((n+1)); done` loses `n` afterwards. Use process substitution: `while read x; do ...; done < <(cmd)`.
- `/dev/null` black hole, `/dev/zero` zeros, `/dev/urandom` random; `/dev/stdout`, `/dev/fd/N`.
- Redirecting a running process's output is not possible without tricks; look at `ls -l /proc/<pid>/fd` to see where it writes.
- Logging in services: write to stdout/stderr and let systemd/Docker capture; avoid app-managed files when possible.

Gotcha: `> file` truncates BEFORE the command runs: `sort f > f` empties f. Use `sort -o f f` or a temp file.
Gotcha: `cmd > /dev/null 2>&1 &` is the standard "run quietly in background" idiom.
Gotcha: `2>&1` must come after `>file`.

How interviewers probe it: "What does `2>&1` do and does order matter?", "Why does `sudo echo > /etc/x` fail?", "Explain `cmd > /dev/null 2>&1`", "Process substitution vs pipe?", "What is a file descriptor?" (small int index into a process's open-file table).

---
## 6. ssh

```
 laptop                          bastion/jump               private host
 ~/.ssh/id_ed25519 (private)     sshd                        sshd
 ~/.ssh/id_ed25519.pub  ---copied to--> ~/.ssh/authorized_keys (on server, perms 600; ~/.ssh 700)
 ~/.ssh/known_hosts: server host-key fingerprints (detects MITM / rebuilt hosts)
```

Keys and agent
```
ssh-keygen -t ed25519 -C "me@corp"       # prefer ed25519 (rsa >= 3072 if needed); set a passphrase
ssh-copy-id user@host                    # install the public key (macOS: may need brew install ssh-copy-id)
eval "$(ssh-agent -s)"; ssh-add ~/.ssh/id_ed25519   # agent holds decrypted key in memory
ssh-add -l                               # list loaded keys
ssh -A host                              # agent forwarding: convenient but risky (root on host can use your agent)
ssh -J bastion user@private              # ProxyJump: prefer over -A
```
macOS: `ssh-add --apple-use-keychain` (older: `-K`) stores the passphrase in Keychain.

~/.ssh/config (the FDE productivity tool)
```
Host bastion
    HostName bastion.customer.com
    User uttam
    IdentityFile ~/.ssh/id_ed25519
Host cust-*
    User deploy
    ProxyJump bastion
    ServerAliveInterval 30
    ServerAliveCountMax 3
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 10m
Host cust-api
    HostName 10.0.4.12
    LocalForward 5432 10.0.4.30:5432
```
Then `ssh cust-api`. ControlMaster multiplexes sessions over one connection (fast, no repeated MFA).

Port forwarding
```
 -L local:   ssh -L 8080:localhost:80 host    laptop:8080 --tunnel--> host --> localhost:80 (on host side)
             ssh -L 5432:db.internal:5432 bastion   reach a private DB via a jump: psql -h localhost -p 5432
 -R remote:  ssh -R 9000:localhost:3000 host  host:9000 --tunnel--> laptop:3000  (expose my local service to them)
 -D dynamic: ssh -D 1080 host                 SOCKS proxy through host
 flags: -N no command, -f background, -T no tty:  ssh -fNL 8080:localhost:80 host
```
Mnemonic: -L = bring a remote service to ME (listen Locally); -R = push my service to THEM (listen Remotely). Remote listen on non-loopback needs `GatewayPorts` in sshd_config.

File transfer
```
scp file user@host:/tmp/           # simple; legacy protocol in newer OpenSSH (check current docs)
scp -J bastion f user@private:~/
rsync -avz --progress src/ user@host:/dst/    # resumable, delta transfer; trailing / on src matters
rsync -avz --delete -e "ssh -J bastion" ...   # --delete mirrors; dry-run first with -n
```
rsync `src/` copies contents; `src` copies the directory itself.

Debug
```
ssh -vvv host                      # why auth fails
ssh -o StrictHostKeyChecking=accept-new host    # first-time only; do not disable checking blindly
ssh-keygen -R host                 # remove stale known_hosts entry after rebuild
ssh host 'journalctl -u app -n 50 --no-pager'   # run one command (quote for remote shell)
```
Common failures: "Permission denied (publickey)" -> wrong user/key, bad perms (~/.ssh 700, authorized_keys 600, home not group-writable), server `PasswordAuthentication no`; "REMOTE HOST IDENTIFICATION HAS CHANGED" -> rebuilt host or MITM, verify before `ssh-keygen -R`; hangs -> firewall/security group, DNS (`UseDNS`), use `-v`; "Connection closed" -> sshd limits, MaxStartups, or tcp wrappers. Server side: `journalctl -u ssh` (Debian/Ubuntu) or `-u sshd` (RHEL), `/var/log/auth.log` or `/var/log/secure`.

Gotcha: agent forwarding to untrusted hosts lets root there use your keys while connected; prefer ProxyJump.
Gotcha: `ssh host cmd` runs a non-interactive, non-login shell; your ~/.bashrc PATH may not apply.
Gotcha: Never commit private keys; keep `~/.ssh/config` host entries rather than long commands.

How interviewers probe it: "How does key-based auth work?" (server challenges, client signs with private key, never sent), "-L vs -R with an example", "Reach a DB in a private subnet from your laptop", "What is known_hosts?", "scp vs rsync?", "Jump host config?"

---
## 7. systemd

```
 systemd (PID 1) manages UNITS: .service .socket .timer .target .mount ...
 /usr/lib/systemd/system/   packaged units (do not edit)
 /etc/systemd/system/       your units and overrides (wins)  -> `systemctl edit app` writes drop-in override.conf
 After editing: sudo systemctl daemon-reload
```
Linux only (macOS uses launchd/launchctl).

Sample unit for a uvicorn FastAPI service: /etc/systemd/system/fastapi-app.service
```
[Unit]
Description=FastAPI app (uvicorn)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=app
Group=app
WorkingDirectory=/opt/fastapi-app
EnvironmentFile=/etc/fastapi-app.env
ExecStart=/opt/fastapi-app/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 2
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=3
StartLimitIntervalSec=60
StartLimitBurst=5
TimeoutStopSec=30
KillSignal=SIGTERM
LimitNOFILE=65536
NoNewPrivileges=true
ProtectSystem=full
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```
Notes: `/etc/fastapi-app.env` holds `KEY=value` lines, chmod 600, owned by root (no `export`, no quotes shell-expansion; systemd parses it itself). `Type=simple` fits uvicorn in foreground. Put a reverse proxy (nginx) in front for TLS. `--workers` and `--reload` are not the same: never use `--reload` in prod.

Lifecycle
```
sudo systemctl daemon-reload
sudo systemctl enable --now fastapi-app     # start now + at boot
systemctl status fastapi-app                # state, PID, last log lines, exit code
sudo systemctl restart|reload|stop fastapi-app
systemctl is-active|is-enabled fastapi-app
systemctl list-units --failed
systemctl cat fastapi-app                   # effective unit incl. overrides
systemd-analyze blame                       # slow boot units
```

Restart policies

| Restart= | Restarts when |
|---|---|
| no (default) | never |
| on-failure | non-zero exit, killed by signal (not clean exit), timeout |
| on-abnormal | signal/timeout/watchdog only |
| always | any exit, even clean (except explicit `systemctl stop`) |

Crash loop protection: StartLimitBurst starts within StartLimitIntervalSec then the unit enters "failed (start-limit-hit)"; clear with `systemctl reset-failed app`. In newer systemd these keys live in [Unit]; older accept them in [Service] (check current docs).

journalctl (systemd's log store)
```
journalctl -u fastapi-app -f                 # follow
journalctl -u fastapi-app --since "1 hour ago" -p err
journalctl -u fastapi-app -n 200 --no-pager
journalctl -b -1 -p err                      # previous boot errors
journalctl -k                                # kernel messages (like dmesg)
journalctl --disk-usage; sudo journalctl --vacuum-time=7d
```
Persistence: journal may be volatile unless /var/log/journal exists (Storage=persistent) (check current docs). stdout/stderr of the service land in the journal automatically.

Key points
- Exit code semantic: `status` shows `code=exited, status=1/FAILURE` or `signal=KILL` (OOM killer shows `signal=KILL` / "Out of memory" in journal).
- Timers (`.timer`) are the systemd alternative to cron: better logging, dependencies, `Persistent=true` catches up missed runs.
- Environment: services do NOT get your shell env. Use `Environment=` or `EnvironmentFile=`; `systemctl show -p Environment app`.

Gotcha: forgetting `daemon-reload` after editing a unit -> old config runs (systemd warns).
Gotcha: relative paths in ExecStart are not allowed; use absolute paths to venv binaries.
Gotcha: "Failed at step USER/EXEC" = user missing or exec bit/path wrong; `status=203/EXEC`; `217/USER`; `200/CHDIR` (WorkingDirectory missing).

How interviewers probe it: "Write a unit file for a Python service", "Restart=always vs on-failure", "How do you see why a service died?" (status + journalctl -u), "enable vs start", "How does systemd stop a service?" (KillSignal, TimeoutStopSec then SIGKILL).

---
## 8. cron

```
 +------------- minute (0-59)
 | +----------- hour (0-23)
 | | +--------- day of month (1-31)
 | | | +------- month (1-12)
 | | | | +----- day of week (0-7, 0 and 7 = Sunday)
 | | | | |
 * * * * *  command

 */5 * * * *      every 5 min        0 2 * * *       02:00 daily
 30 3 * * 1-5     03:30 Mon-Fri      @reboot         at boot (also @daily, @hourly)
```
```
crontab -e; crontab -l          # per-user table (no user field)
/etc/crontab, /etc/cron.d/*     # system tables HAVE a user field after the schedule
```

Env gotchas (the top cause of "works in shell, fails in cron")
- Minimal environment: PATH is often just `/usr/bin:/bin`; no profile/bashrc, no ssh-agent, no your venv. Use absolute paths, or set `PATH=` and `SHELL=/bin/bash` at top of the crontab.
- `%` is special in crontab lines (newline); escape as `\%` (common in `date +\%F`).
- cwd is the home dir; `cd /app && ./run.sh`.
- Day-of-month and day-of-week are OR'd when both restricted.
- Timezone is the system's (often UTC on servers); DST can skip/duplicate runs. cron does not catch up missed runs (anacron / systemd timer Persistent=true does).
- Overlap: slow job + short interval = pile-up. Guard with `flock -n /tmp/job.lock cmd` (Linux; macOS has no flock by default).
- macOS: cron exists but launchd is preferred; cron needs Full Disk Access in newer macOS (check current docs).

Logging
```
*/10 * * * * cd /opt/app && /opt/app/.venv/bin/python job.py >> /var/log/app/job.log 2>&1
```
- Without redirects, output is mailed to the user (if MTA exists) or lost. Cron's own execution log: `journalctl -u cron` (Debian: `cron`, RHEL: `crond`) or `/var/log/syslog`, `/var/log/cron`.
- Add a heartbeat/dead-man check (e.g. ping a monitor on success) because silent failure is the default.

Gotcha: `crontab -r` deletes your whole crontab with no confirm (right next to `-e`).
Gotcha: Script lacks exec bit or shebang -> failure only visible in mail/logs.

How interviewers probe it: "Why does my script work manually but not under cron?", "Schedule for 02:30 on the first of month", "How to prevent overlapping runs?", "cron vs systemd timer?"

---
## 9. Environment variables and secrets hygiene

```
 child process inherits a COPY of parent's exported env; children cannot change the parent's env.
 FOO=1            shell variable only (not inherited)
 export FOO=1     exported: visible to children
 FOO=1 cmd        set for that one command only
```
```
env; printenv PATH; echo "$PATH" | tr : '\n'
export PATH="$HOME/.local/bin:$PATH"     # prepend: your tools win
unset FOO; env -i bash --noprofile --norc   # clean environment for repro
```
PATH: colon-separated search list, first match wins. `which -a python`, `type -a python`, `command -v python`. "Wrong python" bugs = PATH order or venv not activated (`.venv/bin/python` explicit is robust).

Startup files: login shells read /etc/profile and ~/.profile or ~/.bash_profile; interactive non-login bash reads ~/.bashrc; zsh reads ~/.zshenv, ~/.zprofile, ~/.zshrc. macOS Terminal opens login shells; Linux terminals typically non-login. Non-interactive ssh commands and cron read almost nothing. Put env for services in unit files, not rc files.

.env files
- `.env` (KEY=value) is a convention loaded by libraries (python-dotenv, pydantic-settings, docker compose `env_file`) - not by the shell. Load into a shell with `set -a; source .env; set +a`. Parsing differs between tools (quotes, `export`, expansions).
- Never commit .env; commit `.env.example`. Add to .gitignore AND .dockerignore.

Secrets hygiene
- Do not put secrets in command-line args: visible in `ps aux` and /proc/<pid>/cmdline, and shell history. Env vars are visible to same-user processes via /proc/<pid>/environ and inherited by every child; also leak into crash dumps and `docker inspect`.
- Prefer: secret manager (Vault, AWS Secrets Manager/SSM, GCP Secret Manager), mounted files with 0400 perms (`/run/secrets/...`), short-lived credentials/IAM roles over static keys.
- Avoid `set -x` around secrets (it echoes them). Prefix a command with a space to skip history (needs HISTCONTROL=ignorespace). Read secrets with `read -rs`.
- Rotate anything that was pasted in a ticket/chat/log. Redact before sharing logs with customers or in interviews.
- Check what leaked: `git log -p | rg -i 'aws_secret|api[_-]?key'`; tools like gitleaks/trufflehog (check current docs).
- Customer environments: use their approved vault; never copy their secrets to your laptop; use least-privilege, time-boxed access.

Gotcha: `sudo` resets env (use `sudo -E` carefully or `sudo VAR=x cmd`); systemd and cron start with near-empty env.
Gotcha: `export` in a script does not affect the calling shell unless you `source` it.

How interviewers probe it: "Why does my env var disappear in cron/systemd/sudo?", "Where should secrets live?", "Why not pass the password on the CLI?", "Difference between shell variable and env variable?"

---
## 10. Debugging playbook

Method: 1) define the symptom and when it started, 2) check the four resources (CPU, memory, disk, network) plus the app log, 3) form ONE hypothesis, test with a read-only command, 4) change one thing, 5) record findings. (USE method: Utilization, Saturation, Errors per resource.) Prefer read-only tools on customer production.

Symptom -> tool decision table

| Symptom | First look | Then | Confirms |
|---|---|---|---|
| Slow, CPU high | `top`/`htop` (sort by CPU, press 1 for per-core) | `ps -eo pid,pcpu,cmd --sort=-pcpu \| head`; `py-spy top -p PID` (Python); `strace -c -p PID` | one hot process, or system-time heavy (kernel), or steal (`%st`) in VM |
| Slow, CPU low, load high | `vmstat 1`, `iostat -x 1` (r, b, wa columns) | `ps aux \| awk '$8 ~ /D/'` | IO wait or D-state processes |
| Slow, memory | `free -h`, `vmstat 1` (si/so swap) | `ps -eo pid,rss,cmd --sort=-rss \| head` | swapping = thrash |
| Hung (no response) | `ss -ltnp` (is it listening?), `curl -v --max-time 5` | `strace -p PID` (blocked in what syscall?), `lsof -p PID`, `py-spy dump -p PID` | blocked on futex/read/connect/DB lock |
| Crashing / restarting | `systemctl status`, `journalctl -u app -e` | `dmesg -T \| rg -i 'killed process\|oom'`; core dumps (`coredumpctl`) | exit code, signal, OOM |
| Disk full | `df -h`, `df -i` | `du -xh / --max-depth=1 \| sort -h` ; `lsof +L1` | big dir, deleted-open file, inode exhaustion |
| Out of memory | `dmesg -T`, `journalctl -k` | `free -h`; `ps --sort=-rss`; container cgroup limits | OOM-killer victim line |
| Cannot connect | `ss -ltnp`, `curl -v`, `nc -vz host port`, `dig host` | `ip a`, `ip r`, `traceroute`/`mtr`, firewall (`iptables -S`, `nft list ruleset`) | DNS vs routing vs firewall vs not listening |
| Which process owns file/port | `lsof -i :8000`, `lsof file`, `ss -ltnp` | `fuser -v` | PID and user |
| Too many open files | `lsof -p PID \| wc -l`; `cat /proc/PID/limits` | `ulimit -n`; unit `LimitNOFILE` | fd leak or low limit |

Tool notes
- top/htop: load average (1/5/15 min) vs `nproc`; %us user, %sy system, %wa IO wait, %st steal; RES vs VIRT (VIRT is mostly meaningless). htop: F6 sort, F5 tree, `t`. macOS: `top -o cpu`, Activity Monitor; no `free` (use `vm_stat`, `memory_pressure`).
- ps: `ps aux`, `ps -ef`, `ps -eo pid,ppid,stat,pcpu,pmem,rss,etime,cmd`; `pstree -p`. BSD/GNU option styles differ; `--sort` is GNU only (macOS: `ps aux -r` for CPU, `-m` memory).
- free -h: look at "available", not "free"; Linux uses spare RAM as page cache, which is good.
- vmstat 1: r (runnable), b (blocked), si/so (swap in/out), bi/bo (block IO), us/sy/id/wa/st. Ignore the first line (averages since boot). macOS vmstat differs.
- iostat -x 1 (sysstat package): %util near 100 and high await = disk saturated. macOS: `iostat -w 1`.
- lsof: `lsof -i :PORT`, `lsof -p PID`, `lsof +L1` (deleted but open), `lsof -u user`. Needs root for others' processes.
- ss (replaces netstat): `ss -ltnp` listening TCP + process; `ss -tan state established | wc -l`; `ss -s`. Many TIME_WAIT/CLOSE_WAIT: CLOSE_WAIT piling up = app not closing sockets. macOS: `netstat -an`, `lsof -iTCP -sTCP:LISTEN`.
- strace (Linux only; ptrace overhead can slow a prod process heavily, use briefly): `strace -f -tt -T -p PID`, `-e trace=network,file`, `-c` summary, `strace -f -o out.txt cmd`. See what a process is blocked on, which file it fails to open (ENOENT), and which config it reads. macOS: dtruss/dtrace needs SIP changes; `sample PID`, `fs_usage`.
- dmesg -T: kernel ring buffer (OOM kills, disk errors, segfaults); may need sudo; same data as `journalctl -k`.
- df/du: `df -hT`, `du -xsh /var/* \| sort -h`; `ncdu` is interactive. `-x` stays on one filesystem.

Worked examples

A) SLOW service (high CPU)
```
$ uptime            -> load average: 7.8 on 4 cores
$ top               -> python PID 2211 at 380% CPU; %sy low (user-space work)
$ py-spy top -p 2211 (or dump)   -> time in json parsing in /report endpoint
$ rg 'GET /report' access.log | wc -l   -> traffic spike on that endpoint
Fix: cache/paginate/rate-limit that endpoint; add worker or autoscale. Verify load falls.
```
If CPU low but load high: `vmstat 1` shows b>0, wa high -> `iostat -x 1` shows 100% util on /dev/nvme1n1 -> a batch job doing full scans; move it or throttle (`ionice`).

B) HUNG service (port open, requests never return)
```
$ ss -ltnp | rg 8000             -> listening, Recv-Q growing (accept queue backed up)
$ curl -m 5 -v localhost:8000/health   -> connects, no response
$ strace -f -p 2211 -tt -T       -> blocked in futex / poll on fd 14
$ ls -l /proc/2211/fd/14         -> socket; lsof -p 2211 | rg 14 -> to db:5432
$ ss -tnp | rg 5432 | wc -l      -> 100 established = connection pool exhausted
Root cause: DB connection pool exhausted by slow query/lock; requests wait forever for a conn.
Fix: timeouts on pool acquire + queries, kill long query, size pool. (py-spy dump shows all threads waiting in pool.get)
```

C) CRASHING service (restart loop)
```
$ systemctl status fastapi-app   -> activating (auto-restart), status=1/FAILURE, or start-limit-hit
$ journalctl -u fastapi-app -n 80 --no-pager
    ModuleNotFoundError: No module named 'pydantic_settings'  (after a deploy)
$ systemctl cat fastapi-app      -> ExecStart uses /opt/app/.venv; check that venv has deps
Fix: pip install -r requirements.txt into the venv, systemctl reset-failed, restart.
If signal=KILL with no Python traceback: suspect OOM (case E).
```

D) DISK FULL
```
$ df -h              -> /var 100%
$ df -i              -> inodes fine (else: many tiny files, e.g. session dirs)
$ du -xh /var --max-depth=2 | sort -h | tail   -> /var/log/app 38G
$ ls -lhS /var/log/app | head   -> app.log 37G (no rotation)
$ du says less than df? -> lsof +L1 shows deleted 37G app.log still open by PID 2211
Fix: truncate in place `: > app.log` (or `truncate -s 0`), NOT rm while open; for deleted-open file restart the process or `: > /proc/2211/fd/N`.
Prevent: logrotate (/etc/logrotate.d/), journald SystemMaxUse, container log limits.
```

E) OUT OF MEMORY
```
$ systemctl status app           -> Main process exited, code=killed, status=9/KILL
$ dmesg -T | rg -i 'out of memory|killed process'
    Out of memory: Killed process 2211 (python) total-vm:9.1GB, anon-rss:6.8GB
$ free -h                        -> available ~100M; swap full
$ ps -eo pid,rss,cmd --sort=-rss | head
Cause: memory leak or too many workers x per-worker memory; in containers, the cgroup limit (check `docker stats`, dmesg "Memory cgroup out of memory", exit code 137 = 128+9).
Fix: reduce workers, fix leak (tracemalloc/memray), raise limit, add swap/oom_score_adj as stopgap, set MemoryMax= in unit.
```

F) SLOW because of network/DNS (bonus)
```
$ curl -w '%{time_namelookup} %{time_connect} %{time_starttransfer} %{time_total}\n' -o /dev/null -s URL
   -> time_namelookup 5.0s  => DNS (check /etc/resolv.conf, `dig`, search/ndots in containers)
```

Gotcha: restart "fixes" it temporarily and destroys evidence. Capture first: `ps`, `ss`, `lsof`, `py-spy dump`, `dmesg`, `journalctl` snapshots, `strace` sample; then restart.
Gotcha: strace/gdb on production can freeze or slow the process; prefer py-spy/`perf`/eBPF tools (check current docs) and keep traces short.
Gotcha: Exit code 137 = SIGKILL (often OOM), 143 = SIGTERM, 139 = segfault, 126 = not executable, 127 = command not found.

How interviewers probe it: "Server is slow - walk me through it", "Disk full but du disagrees", "Process killed with no logs - why?" (OOM killer, check dmesg), "What does load average mean?", "How to find what a hung process is doing?", "Port already in use?" (lsof -i / ss -ltnp). They want a systematic order and read-only first, not tool trivia.

---
## 11. Bash scripting basics

Strict mode and why
```
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
```
- `-e` exit on any command failing (with exceptions: inside `if`, `&&`/`||` lists, `while` conditions; so it is not a full safety net).
- `-u` unset variable is an error (catches typos like `rm -rf "$DIR/"` with DIR empty).
- `-o pipefail` pipeline status = first failing stage.
- Debug with `set -x` (trace), `bash -n script` (syntax check), `shellcheck script.sh` (static analysis; catches unquoted vars, bad tests; install via brew/apt).

Quoting (most bugs live here)
```
f="my file.txt"
rm $f            # WRONG: word-splits into 'my' and 'file.txt', and globs
rm "$f"          # right
"$@"             # all args, each preserved; "$*" joins into one string
'single'         # literal; "double" expands $var and $(cmd); ${var:-default}; ${var%.txt}
files=(a b "c d"); for x in "${files[@]}"; do ...; done   # arrays (bash; not POSIX sh)
```

Conditionals
```
if [[ -f "$f" && -r "$f" ]]; then ...; elif [[ "$x" == *.py ]]; then ...; else ...; fi
[[ -z "$v" ]]  empty   [[ -n "$v" ]] non-empty   [[ -d d ]]  [[ -e p ]]  [[ $n -gt 3 ]] (numeric)
[[ $s == foo* ]] glob match   [[ $s =~ ^[0-9]+$ ]] regex   (( n > 3 ))  arithmetic
cmd && echo ok || echo fail      # careful: `||` also runs if echo fails
case "$1" in start) ... ;; stop|halt) ... ;; *) usage ;; esac
```
`[[ ]]` is bash/zsh (safer, no word splitting); `[ ]` is POSIX `test` (needs quoting). If the shebang is `#!/bin/sh`, bashisms break (on Debian sh is dash).

Loops and functions
```
for i in {1..5}; do echo "$i"; done
for f in *.log; do [[ -e $f ]] || continue; gzip "$f"; done
while IFS= read -r line; do echo "$line"; done < file       # -r and IFS= preserve content
while read -r a b; do ...; done < <(cmd)                    # no subshell variable loss
retry() { local n=0; until "$@"; do ((++n >= 5)) && return 1; sleep $((2**n)); done; }
```
- Functions: `local` for variables; return a status (0-255) with `return`, output data via stdout (`x=$(fn)`).
- Command substitution `$(...)` over backticks; it strips trailing newlines.
- Arithmetic: `$((a+b))`; bash has no floats (use `awk`/`bc`).
- Args: `$1..$9`, `$#`, `$0`, `${1:?usage: script ENV}` (die if missing), `getopts` for flags.

Exit codes
- 0 success, non-zero failure; 1 general, 2 misuse, 126 not executable, 127 not found, 128+N killed by signal N (130 = Ctrl-C, 137 = KILL, 143 = TERM). Your scripts: `exit 0/1`, and use distinct codes for distinct failures so callers (CI, cron, systemd) can react. `$?` is overwritten by every command; save it: `rc=$?`.

trap (cleanup and signals)
```
tmp=$(mktemp -d)
cleanup() { rm -rf "$tmp"; }
trap cleanup EXIT                      # runs on normal exit, error exit (set -e), and Ctrl-C/TERM exit
trap 'echo "failed at line $LINENO" >&2' ERR
trap 'echo shutting down; kill "$child" 2>/dev/null; exit 143' TERM INT
```
EXIT trap is the right place for temp files, locks, and "undo". SIGKILL cannot be trapped.

Sample robust deploy + health-check script
```
#!/usr/bin/env bash
# deploy.sh - deploy a release dir and verify health; roll back on failure.
# usage: ./deploy.sh <release-dir> [health-url]
set -euo pipefail

readonly APP_DIR=/opt/fastapi-app
readonly SERVICE=fastapi-app
readonly RELEASE="${1:?usage: $0 <release-dir> [health-url]}"
readonly HEALTH_URL="${2:-http://127.0.0.1:8000/health}"
readonly LOCK=/tmp/${SERVICE}-deploy.lock

log()  { printf '%s [deploy] %s\n' "$(date -u +%FT%TZ)" "$*" >&2; }
die()  { log "ERROR: $*"; exit 1; }

prev="$(readlink -f "$APP_DIR/current" || true)"   # macOS: use `readlink` without -f or greadlink

rollback() {
  if [[ -n "${prev:-}" && -d "$prev" ]]; then
    log "rolling back to $prev"
    ln -sfn "$prev" "$APP_DIR/current"
    sudo systemctl restart "$SERVICE" || true
  fi
}

on_exit() {
  local rc=$?
  if (( rc != 0 )); then log "failed with exit code $rc"; rollback; fi
  flock -u 9 2>/dev/null || true
}
trap on_exit EXIT

command -v curl >/dev/null || die "curl not installed"
[[ -d "$RELEASE" ]] || die "release dir not found: $RELEASE"

exec 9>"$LOCK"
flock -n 9 || die "another deploy is running"     # Linux flock

log "installing deps"
python3 -m venv "$RELEASE/.venv"
"$RELEASE/.venv/bin/pip" install -q -r "$RELEASE/requirements.txt"

log "switching symlink -> $RELEASE"
ln -sfn "$RELEASE" "$APP_DIR/current"
sudo systemctl restart "$SERVICE"

log "waiting for health at $HEALTH_URL"
for attempt in {1..30}; do
  if curl -fsS --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
    log "healthy after $attempt attempt(s)"
    exit 0
  fi
  sleep 2
done
die "service not healthy after 60s"     # EXIT trap triggers rollback
```
Why it is robust: strict mode; required-arg check; quoted expansions; lock to avoid concurrent deploys; EXIT trap rolls back on ANY failure; health check with timeout and bounded retries (never loop forever); logs to stderr with timestamps; idempotent symlink swap (atomic with `ln -sfn`); non-zero exit for CI. Run `shellcheck deploy.sh` before shipping.

When not to use bash: >100 lines, data structures, JSON, error handling needs -> use Python (`subprocess.run(..., check=True)`).

Gotcha: `set -e` is ignored in `if cmd`, `cmd || true`, and inside functions called in a conditional context; check critical commands explicitly.
Gotcha: `local x=$(cmd)` masks cmd's exit status; declare then assign.
Gotcha: `for f in $(ls)` breaks on spaces; use globs or `find -print0`.
Gotcha: `cd dir; rm -rf *` if cd fails deletes the wrong dir; `cd dir || exit` or use set -e and absolute paths.
Gotcha: macOS ships bash 3.2 (GPL-v2); associative arrays, `${var,,}`, `mapfile` need bash 4+ (`brew install bash`); default shell is zsh. Use `#!/usr/bin/env bash`.

How interviewers probe it: "What does set -euo pipefail do and where does -e not work?", "Why quote variables?", "Write a retry loop", "How do you clean up temp files on failure?" (trap EXIT), "How do you make a deploy script safe/idempotent?", "Exit code of a pipeline?", "bash vs python for this task?"

---
## 12. Putting it together: FDE habits on a customer box

```
 1. Orient:    whoami; id; hostname; uname -a; cat /etc/os-release; uptime; date (timezone!)
 2. Persist:   tmux new -s <ticket>   (survive dropped ssh)
 3. Survey:    df -h; free -h; top; ss -ltnp; systemctl --failed; journalctl -p err -b | tail
 4. Narrow:    app logs (journalctl -u svc -f), config in /etc, env in unit file, recent deploys (ls -lt)
 5. Capture evidence before restarting; change one thing at a time; note commands run.
 6. Leave clean: no stray files in /tmp, no secrets in history, document the fix for the customer.
```
- Constrained boxes: no root, no internet, no package install, old tools. Master classics (grep awk sed find ss/netstat ps) and read from /proc directly.
- Always know your blast radius: read-only first, `-n` dry-runs (rsync, find without -delete), backups before edits (`cp -a f f.bak.$(date +%F)`).
- Communicate: state hypothesis, evidence, action, and rollback plan; interviewers grade this as much as the commands.

Try it end to end (Linux or container)
```
1. yes > /tmp/big.log &   # fill disk; watch df -h; kill it; compare df vs du with lsof +L1 after rm while running
2. stress memory: python3 -c "x=[0]*10**9" under `ulimit -v 2000000` and read the error
3. write the sample unit, add Restart=on-failure, kill -9 the PID and watch systemctl status / journalctl
4. ssh -L to a local python3 -m http.server 8000; curl through the tunnel
5. awk/sort/uniq on a generated access log; rewrite with rg + jq if logs are JSON
6. run shellcheck on the deploy script and fix every warning
```

How interviewers probe it: "You ssh into a customer VM and the app is down. First five minutes?" Expect orient -> persist -> survey -> narrow -> evidence -> fix -> verify -> communicate.
