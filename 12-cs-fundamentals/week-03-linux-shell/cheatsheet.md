# Week 3 Cheatsheet - Linux & Shell

Items marked "(check current docs)" are version/distro dependent. Linux unless noted; macOS = BSD userland, no /proc, systemd, strace.

## Filesystem

| Path | One-liner |
|---|---|
| /etc | host config (text) |
| /var/log, /var/lib | logs, service data |
| /proc, /sys | virtual kernel views (Linux only) |
| /dev | device files (null, zero, urandom, tty) |
| /tmp | world-writable scratch, sticky bit |
| /usr, /opt | packaged userland, third-party software |
| /run | runtime state (pid files, sockets), tmpfs |

## Permissions

| Item | One-liner |
|---|---|
| r/w/x = 4/2/1 | 755 dirs/exec, 644 files, 600 secrets/keys |
| dir x / dir w | traverse / create+delete entries |
| setuid 4xxx | run as file owner |
| setgid 2xxx | run as group; dir: new files inherit group |
| sticky 1xxx | only owner may delete in dir (/tmp = 1777) |
| umask | files 666 & ~mask, dirs 777 & ~mask (022 -> 644/755) |
| chmod -R u=rwX,go=rX | sane recursive perms without making files executable |

## Signals and processes

| Item | One-liner |
|---|---|
| SIGTERM 15 | graceful stop (default kill) |
| SIGKILL 9 | uncatchable, no cleanup, last resort |
| SIGHUP 1 | terminal hangup / reload config |
| SIGINT 2 / SIGQUIT 3 | Ctrl-C / Ctrl-\ |
| SIGSTOP / SIGCONT | pause / resume |
| Zombie (Z) | exited, parent has not wait()ed |
| D state | uninterruptible IO wait, unkillable |
| PID 1 in container | ignores default signals, must reap; use exec form / --init |
| Exit codes | 126 not exec, 127 not found, 130 INT, 137 KILL/OOM, 143 TERM, 139 segv |

## Text tools

| Tool | One-liner |
|---|---|
| grep -rniE 'a\|b' | search; -v invert, -c count, -o match only, -A/-B context |
| awk -F: '$3>=1000{print $1}' | field logic, sums, filters |
| sed 's/a/b/g' ; sed -n '5,9p' | substitute; print range (macOS: `sed -i ''`) |
| cut -d, -f1,3 | fixed delimiter columns |
| sort -k2,2nr \| uniq -c | count duplicates (sort before uniq) |
| find . -type f -size +100M -mtime -1 | predicate search |
| find ... -print0 \| xargs -0 -P4 cmd | safe parallel batch |
| tee -a file | write and pass through |
| rg / fd / sd / jq / bat / ast-grep | fast grep / find / sed-s / JSON / cat / code AST (may be missing on customer boxes) |

## Redirects and fds

| Syntax | Meaning |
|---|---|
| `> f` / `>> f` / `< f` | stdout truncate / append / stdin |
| `2> f` | stderr to file |
| `> f 2>&1` or `&> f` | both to file (order matters) |
| `cmd 2>&1 \| x` or `\|&` | pipe both |
| `> /dev/null 2>&1` | discard all |
| `<<'EOF'` / `<<<"s"` | here-doc (no expansion) / here-string |
| `<(cmd)` | process substitution (cmd output as file) |
| `echo x \| sudo tee f` | privileged write (sudo echo > f fails) |
| `$?`, `${PIPESTATUS[@]}`, pipefail | exit status of last / each stage / any stage |

## ssh

| Item | One-liner |
|---|---|
| ssh-keygen -t ed25519 | create key; private 600, ~/.ssh 700 |
| ssh-copy-id u@h | install public key |
| ssh-add / ssh-add -l | load / list agent keys (macOS: --apple-use-keychain) |
| ssh -J bastion u@h | jump host (prefer over -A) |
| -L 8080:host:80 | local listener -> remote target |
| -R 9000:localhost:3000 | remote listener -> my local service |
| -D 1080 | SOCKS proxy |
| -fNL ... | background tunnel only |
| rsync -avz src/ u@h:dst/ | delta copy; -n dry run; --delete mirrors |
| ssh-keygen -R host | drop stale known_hosts entry |
| ssh -vvv | debug auth/connect |
| config keys | Host, HostName, User, IdentityFile, ProxyJump, ServerAliveInterval, ControlMaster/Path/Persist |

## systemd and cron

| Item | One-liner |
|---|---|
| systemctl daemon-reload | after editing units |
| systemctl enable --now svc | start now + boot |
| systemctl status / restart / reload / stop svc | state and control |
| systemctl list-units --failed | what is broken |
| systemctl cat / edit svc | effective unit / drop-in override |
| systemctl reset-failed svc | clear start-limit-hit |
| journalctl -u svc -f / -n 200 / --since "1h ago" -p err | service logs |
| journalctl -b -1 / -k | previous boot / kernel |
| Restart= | no / on-failure / on-abnormal / always |
| EnvironmentFile=/etc/app.env | KEY=value lines, chmod 600 |
| Exec status 203 / 217 / 200 | EXEC path / USER missing / CHDIR missing |
| cron fields | min hour dom mon dow; `*/5 * * * *`; `@reboot` |
| cron gotchas | minimal PATH, `%` needs `\%`, no catch-up, redirect output, flock for overlap |
| crontab -l / -e (never -r) | list / edit / DELETES ALL |

## Env and secrets

| Item | One-liner |
|---|---|
| `export X=1` vs `X=1` | inherited by children vs shell-local |
| `X=1 cmd` | one command only |
| PATH | first match wins; `type -a cmd`, `command -v cmd` |
| `set -a; source .env; set +a` | load .env into shell |
| Secrets | not in argv, history, git, logs; use vault / 0400 files / IAM roles |
| systemd, cron, sudo | do not inherit your env |

## Debug: symptom -> tool

| Symptom | Tool |
|---|---|
| CPU high | top/htop, ps --sort=-pcpu, py-spy top, strace -c |
| load high, CPU low | vmstat 1 (b, wa), iostat -x 1, ps for D state |
| memory pressure | free -h (available), vmstat si/so, ps --sort=-rss |
| hung | ss -ltnp, curl -m5 -v, strace -p, py-spy dump, lsof -p |
| crashing | systemctl status, journalctl -u, dmesg -T, coredumpctl |
| OOM | dmesg -T \| rg -i oom, exit 137, cgroup limits |
| disk full | df -h, df -i, du -xh \| sort -h, lsof +L1 |
| port/file owner | lsof -i :PORT, ss -ltnp, fuser -v |
| network | dig, curl -w timings, nc -vz, ip a/r, mtr |
| fd exhaustion | lsof -p PID \| wc -l, /proc/PID/limits |

## Bash essentials

| Item | One-liner |
|---|---|
| `set -euo pipefail` | exit on error, unset var, pipe failure |
| `"$var"`, `"$@"`, `"${arr[@]}"` | always quote |
| `[[ -f f && -n "$v" ]]` | tests; `(( n > 3 ))` arithmetic |
| `${1:?usage}` / `${v:-default}` | require arg / default |
| `trap cleanup EXIT` | cleanup on any exit (not SIGKILL) |
| `local x; x=$(cmd)` | keeps exit status visible |
| `shellcheck f.sh`, `bash -n`, `set -x` | lint, syntax, trace |
| `flock -n 9` | single-instance lock (Linux) |
| macOS | bash 3.2, zsh default, BSD sed/ps/date; `brew install coreutils gnu-sed bash` |

## Memorize

- Everything is a file; config /etc, logs /var/log, data /var/lib.
- 4/2/1; 755 / 644 / 600; umask subtracts; setuid 4, setgid 2, sticky 1.
- TERM first, KILL last; KILL cannot be trapped; PID 1 ignores default signals.
- `> f 2>&1` (order matters); `sudo tee` for privileged writes.
- sort before uniq; `-print0 | xargs -0`; quote everything in bash.
- ssh: -L brings remote to me, -R pushes mine to them; use ProxyJump.
- systemd: edit unit -> daemon-reload -> restart; logs via journalctl -u.
- cron/systemd/sudo have a clean env: absolute paths, explicit env.
- df vs du mismatch = deleted-open file (lsof +L1); df -i for inodes.
- Exit 137 = SIGKILL (likely OOM); check dmesg.
- Capture evidence before restart; read-only first; one change at a time.

## Command quick reference

```
# orient
uname -a; cat /etc/os-release; uptime; nproc; free -h; df -h; date
# processes
ps -eo pid,ppid,stat,pcpu,pmem,rss,etime,cmd --sort=-pcpu | head
pstree -p; pgrep -fa name; kill -TERM PID; kill -l
# network
ss -ltnp; ss -tan state established | wc -l; lsof -i :8000; curl -v -m5 URL
dig host; nc -vz host 443
# logs
journalctl -u svc -f; journalctl -p err -b; dmesg -T | tail; tail -F file
# disk
du -xh /var --max-depth=2 | sort -h | tail; df -i; lsof +L1
# trace
strace -f -tt -T -p PID; strace -c -p PID; py-spy dump -p PID
# files
find . -type f -mtime -1 -size +10M; rg -n 'ERROR' .; fd '\.py$'
jq -r '.items[].name' < data.json
# ssh
ssh -J bastion user@host; ssh -fNL 5432:db:5432 bastion; rsync -avzn src/ user@host:/dst/
# tmux
tmux new -s name; Ctrl-b d; tmux attach -t name; tmux ls
```
