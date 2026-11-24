# CS Fundamentals Study Track (interview-focused, ~5 weeks at 7-8 hrs/week)

Goal: the systems fundamentals that Google/Uber-level SWE and forward-deployed-engineer (FDE) interviews probe, and that you need when debugging in a customer's environment. All material is reading + Q&A with commands to try in a terminal. Facts that change by version are marked "(check current docs)"; verify before quoting.

## Study order
| Week | Folder | Topics |
|---|---|---|
| 1 | week-01-networking | OSI/TCP-IP, IP/CIDR, TCP vs UDP, DNS, HTTP/1.1/2/3, TLS, REST/caching/CORS, cookies vs tokens, WebSockets/SSE, "type a URL", curl/dig/tcpdump |
| 2 | week-02-operating-systems | Processes/threads, scheduling, virtual memory, deadlock, sync primitives, IPC, file systems, I/O models (epoll), syscalls, GIL |
| 3 | week-03-linux-shell | FS layout, permissions, signals, text tools (rg/fd/jq), pipes, ssh, systemd, cron, debugging slow/hung/crashing services, bash |
| 4 | week-04-git-collaboration | Git internals, merge vs rebase, reset vs revert, bisect, PR/review etiquette, branching models, CI/CD, GitHub Actions for FastAPI |
| 5 | week-05-containers-orchestration | Docker, Dockerfile best practices, compose, Kubernetes core objects, probes/HPA, debugging pods, container security |

Why this order: networking and OS are the foundation; Linux/shell is how you observe both; Git/CI is how code ships; containers/K8s is where everything runs.

## Weekly routine (7-8 hrs)
1. Read lesson.md (~3 hrs); run every command at least once; redraw each ASCII diagram by hand.
2. Do interview-qa.md out loud, covering the answer first (~2 hrs).
3. Memorize cheatsheet.md (~1 hr).
4. Last 30 min: explain the week's top 3 "X vs Y" differences without notes.

## Files
- week-NN-*/lesson.md, interview-qa.md, cheatsheet.md
- rapid-fire.md: 50 quick questions across all five weeks; use daily in the final two weeks.

## Tips
- Answer in layers: one-sentence definition, how it works, trade-off, a debugging command.
- For FDE roles, always add "how would I verify this in a customer environment" (logs, curl, dig, kubectl describe) and "what would I check first".
- If unsure of a number or flag, say so and state how you would confirm it (man page, --help, docs).
