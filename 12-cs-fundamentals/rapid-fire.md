# Rapid-Fire: 50 Quick Questions (all weeks)

Answer each in 1-2 sentences, out loud. Cover the answer first.

## Networking
**1. TCP vs UDP?** TCP: connection-oriented, reliable, ordered, flow/congestion controlled. UDP: connectionless, no delivery guarantees, low overhead; good for DNS, video, QUIC base.

**2. TCP three-way handshake?** SYN, SYN-ACK, ACK; syncs initial sequence numbers and costs 1 RTT before data.

**3. What is TIME_WAIT and why?** State held (about 2xMSL, commonly 60s on Linux) by the side that closes first, so late packets expire and the final ACK can be retransmitted. Many of them signals short-lived connections; fix with keep-alive/pooling, not by disabling it.

**4. Flow control vs congestion control?** Flow: receiver window protects the receiver. Congestion: cwnd (slow start, AIMD) protects the network.

**5. /24 holds how many hosts?** 256 addresses, 254 usable (minus network and broadcast). Cloud providers reserve more (check current docs).

**6. Describe DNS resolution.** Stub resolver -> recursive resolver (cache) -> root -> TLD -> authoritative; answers cached per TTL.

**7. A vs CNAME vs NS record?** A: name to IPv4. CNAME: alias to another name (not at zone apex). NS: delegates a zone.

**8. HTTP/1.1 vs 2 vs 3?** 1.1: one request at a time per connection (HOL blocking at HTTP layer). 2: multiplexed streams over one TCP, header compression, but TCP-level HOL blocking. 3: over QUIC/UDP, per-stream loss recovery, faster handshakes.

**9. TLS in one breath?** Negotiate version/cipher, server proves identity via certificate chain, key exchange (ephemeral ECDHE) yields symmetric session keys; TLS 1.3 does it in 1 RTT.

**10. 401 vs 403?** 401: not authenticated (missing/invalid credentials). 403: authenticated but not allowed.

**11. 502 vs 503 vs 504?** 502: bad response from upstream. 503: unavailable/overloaded. 504: upstream timed out.

**12. What is CORS?** Browser-enforced policy restricting cross-origin reads; server opts in with Access-Control-* headers; non-simple requests trigger an OPTIONS preflight. It is not server-side security.

**13. Cookies vs JWT?** Cookie: browser-stored, auto-sent, pair with HttpOnly/Secure/SameSite, server session lookup. JWT: signed self-contained token, stateless but hard to revoke; store carefully.

**14. WebSocket vs SSE?** WebSocket: full-duplex over upgraded connection. SSE: one-way server-to-client over plain HTTP with auto-reconnect.

**15. "Connection refused" vs timeout?** Refused: host reachable, nothing listening (RST). Timeout: packets dropped (firewall/route/host down).

## Operating systems
**16. Process vs thread?** Process: own address space and resources. Threads: share a process's memory, separate stacks/registers; cheaper to create/switch, but need synchronization.

**17. What is a context switch and its cost?** Saving/restoring CPU state to run another task; direct cost small, indirect cost is cache/TLB pollution (more for process switch).

**18. Virtual memory benefits?** Isolation, per-process contiguous address space, demand paging, sharing (mmap, copy-on-write), overcommit.

**19. Page fault?** Access to a page not mapped/resident; minor (just map, e.g. zero page or cached) or major (read from disk).

**20. Stack vs heap?** Stack: per-thread, automatic, LIFO frames, fast, limited. Heap: dynamic, manually/GC managed, shared.

**21. Four deadlock conditions?** Mutual exclusion, hold and wait, no preemption, circular wait. Break one; consistent lock ordering breaks circular wait.

**22. Mutex vs semaphore?** Mutex: ownership, binary lock for mutual exclusion. Semaphore: counter for resource counting/signaling, no owner.

**23. Why while-loop around cond.wait()?** Spurious wakeups and state may change before you run; always recheck the predicate.

**24. Python GIL?** CPython lock allowing one thread to run bytecode at a time; threads help I/O-bound, use processes (or native/C extensions) for CPU-bound. Free-threaded builds exist (check current docs).

**25. select/poll vs epoll?** select/poll scan all fds each call (O(n)); epoll keeps a kernel interest list and returns only ready fds (scales).

**26. Blocking vs non-blocking vs async I/O?** Blocking waits; non-blocking returns EAGAIN and you poll/readiness-notify; true async (io_uring, IOCP) completes in background.

**27. What is an inode?** Metadata (owner, perms, size, block pointers) for a file; names are directory entries pointing to inodes.

**28. Hard vs soft link?** Hard: another name for the same inode (same filesystem, not dirs). Soft: a file holding a path; can dangle.

**29. What is a system call?** Controlled entry from user mode to kernel (trap) to request services; seen with strace/dtruss.

**30. Zombie process?** Exited child whose parent has not wait()ed; occupies a process-table slot only.

## Linux and shell
**31. SIGTERM vs SIGKILL?** TERM can be caught for graceful shutdown; KILL cannot be caught or ignored.

**32. chmod 640?** Owner rw, group r, others none.

**33. What does 2>&1 do?** Redirects stderr to wherever stdout currently points; order matters (`> f 2>&1`).

**34. rg/fd/jq vs grep/find?** rg: faster recursive grep honoring .gitignore. fd: friendlier find. jq: query/transform JSON.

**35. Service is slow; first commands?** top/htop (CPU, load), free -m (memory/swap), iostat/vmstat (IO wait), ss (connections), then app logs/journalctl.

**36. Disk full but df shows space free?** Check inodes (df -i) or deleted-but-open files (lsof +L1).

**37. Process hung; how to see what it does?** strace -p PID, lsof -p PID, py-spy dump for Python.

**38. cron gotcha?** Minimal environment/PATH; use absolute paths, redirect output, set env explicitly.

**39. set -euo pipefail?** Exit on error, on unset variables, and fail a pipeline if any stage fails.

**40. systemd: restart a crashing service?** `Restart=on-failure` in the unit; inspect with `systemctl status` and `journalctl -u name -f`.

## Git, CI/CD
**41. Merge vs rebase?** Merge preserves history with a merge commit; rebase rewrites commits onto a new base for linear history. Never rebase shared branches.

**42. reset vs revert?** reset moves the branch pointer (rewrites history); revert adds a new commit undoing a change (safe for shared history).

**43. Recover a "lost" commit?** `git reflog`, then checkout/branch the old hash.

**44. git bisect?** Binary search over commits between a good and bad one to find the culprit; automate with `bisect run`.

**45. Trunk-based vs gitflow?** Trunk: short-lived branches into main, feature flags, frequent deploys. Gitflow: long-lived develop/release branches; heavier, suits versioned releases.

**46. CI vs CD?** CI: automatically build/test every change. Delivery: always deployable, manual release. Deployment: automatic release to prod.

## Containers and Kubernetes
**47. Container vs VM?** Container: isolated process using host kernel (namespaces + cgroups), light and fast. VM: full guest OS on a hypervisor, stronger isolation.

**48. Why multi-stage builds / order Dockerfile layers?** Smaller final image without build tools; put rarely-changing steps (dependency install) before frequently-changing code to use cache.

**49. Pod CrashLoopBackOff: how to debug?** `kubectl describe pod` (events, exit code, OOMKilled), `kubectl logs --previous`, check probes, config/secret, image command.

**50. Liveness vs readiness probe?** Liveness failing restarts the container; readiness failing removes the pod from Service endpoints without restarting. Startup probe protects slow starts.
