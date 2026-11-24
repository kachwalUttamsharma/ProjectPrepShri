# Week 2 - Operating Systems Cheatsheet

Facts marked "(check current docs)" are version-dependent.

---
## Core concepts

| Topic | One-liner |
|---|---|
| Kernel vs user mode | Privileged vs unprivileged CPU mode; apps enter kernel via syscalls, interrupts, exceptions |
| Syscall | Trap into kernel to do privileged work (open, read, write, mmap, fork, execve) |
| Process | Program in execution with private address space, fds, PID |
| Thread | Execution unit sharing process memory; own stack and registers |
| fork / exec | fork copies process (COW); exec replaces the program image |
| Zombie | Exited child not yet wait()ed by parent; fix by reaping |
| Orphan | Parent died first; adopted by PID 1 |
| Context switch | Save/restore registers (+ page table); hidden cost is cache/TLB cold start |
| Preemption | Timer interrupt takes CPU back from a running task |

## Scheduling

| Algorithm | One-liner |
|---|---|
| FCFS | Arrival order; convoy effect |
| SJF / SRTF | Shortest first; optimal avg wait, starves long jobs |
| Round Robin | Time quantum rotation; fair, quantum tuning matters |
| Priority | Highest first; starvation (aging), inversion (inheritance) |
| MLFQ | Multi-queue, demote CPU hogs, periodic boost |
| CFS | Smallest virtual runtime first (red-black tree); EEVDF in newer kernels (check current docs) |

## Memory

| Topic | One-liner |
|---|---|
| Virtual memory | Private address space per process; MMU translates via page tables |
| Page / frame | Fixed-size virtual / physical chunk (4 KiB typical) |
| Page table | Multi-level map page -> frame + flags |
| TLB | Cache of translations; huge pages extend reach |
| Minor fault | Mapping missing, data in RAM |
| Major fault | Must read from disk |
| Invalid fault | SIGSEGV |
| Demand paging | Frames allocated on first touch |
| COW | Share pages read-only; copy on write |
| Swap | Disk area for evicted anonymous pages |
| Thrashing | Working set > RAM; constant paging |
| OOM killer | Kernel SIGKILLs a victim by oom_score; container exit code 137 |
| mmap | Map file/anonymous memory into address space |
| Stack | Per-thread, automatic, LIFO, small |
| Heap | Dynamic, shared, larger, leaks/fragmentation |
| Leak vs fragmentation | Leak: live memory grows; fragmentation: free memory unusable/not returned |
| RSS vs VSZ | Resident physical vs total virtual size |

## Concurrency

| Primitive | One-liner |
|---|---|
| Mutex | Exclusive, owned, sleeping lock |
| Spinlock | Busy-wait; only for very short sections |
| Semaphore | Counter; N holders; no owner; signaling |
| Condition variable | Wait for predicate; always in a `while` loop |
| RW lock | Many readers or one writer |
| Atomic / CAS | Indivisible hardware op; beware ABA |
| Race condition | Result depends on interleaving |
| Deadlock | Circular wait among holders |
| Livelock / starvation | Busy without progress / never gets resource |

Coffman conditions: mutual exclusion, hold and wait, no preemption, circular wait.

| Deadlock strategy | Example |
|---|---|
| Prevention | Global lock order, all-or-nothing acquire, trylock + backoff |
| Avoidance | Banker's algorithm |
| Detection | Wait-for graph cycle, abort victim (databases) |

## IPC

| Mechanism | One-liner |
|---|---|
| Pipe / FIFO | Unidirectional byte stream, bounded buffer |
| Unix socket | Local bidirectional, can pass fds |
| TCP/UDP socket | Across machines |
| Shared memory | Fastest, no copy, needs your own sync |
| Message queue | Discrete messages (POSIX mq, brokers) |
| Signals | SIGTERM graceful, SIGKILL/SIGSTOP uncatchable, SIGINT, SIGCHLD, SIGPIPE |

## File systems

| Topic | One-liner |
|---|---|
| Inode | File metadata + block pointers; no name |
| Directory | Maps names to inode numbers |
| Hard link | Extra name for same inode; same FS; freed at link count 0 and no open fds |
| Soft link | File containing a path; can dangle |
| Page cache | Kernel RAM cache of file data; write-back |
| fsync | Force data/metadata to stable storage |
| Journaling | Log intent first; crash-consistent metadata, not automatic data durability |
| Atomic replace | temp file, fsync, rename, fsync dir |
| Inode exhaustion | ENOSPC with free bytes; `df -i` |

## I/O and Python

| Topic | One-liner |
|---|---|
| Blocking | Thread sleeps until done |
| Non-blocking | Returns EAGAIN |
| select / poll | O(n) scan; select capped at 1024 fds |
| epoll / kqueue | Kernel interest list; O(ready); scales |
| io_uring | Linux async rings, completion model (check current docs) |
| Event loop | One thread: wait for ready fds, resume coroutines |
| async/await | Cooperative; one blocking call stalls everyone |
| uvicorn / FastAPI | ASGI loop; `async def` on loop, `def` in thread pool; scale with worker processes |
| GIL | One thread runs Python bytecode at a time (CPython); released on I/O |
| Threads | I/O-bound, blocking libs |
| Processes | CPU-bound; pickling cost; use `__main__` guard |
| asyncio | Many concurrent I/O waits |
| Free-threaded Python | PEP 703, optional build (check current docs) |

---
## Memorize

1. Process = own address space; thread = shared memory, own stack.
2. fork returns 0 in child; zombie = unreaped child; orphan adopted by PID 1.
3. Context switch cost is mostly cache/TLB pollution, not register saves.
4. Virtual -> physical: page number via page table (TLB-cached) + offset.
5. Major fault = disk; minor fault = mapping only; invalid = SIGSEGV.
6. Exit code 137 = SIGKILL (128+9), usually OOM killer.
7. Coffman: mutual exclusion, hold and wait, no preemption, circular wait. Break circular wait with lock ordering.
8. Mutex has an owner; semaphore does not. Condition waits go in a while loop.
9. Shared memory is the fastest IPC; sync is on you.
10. Inode holds metadata, not the name; rm removes a name, not necessarily data.
11. write != durable; need fsync (and fsync dir after rename).
12. epoll scales because the kernel keeps the interest list and returns only ready fds.
13. Never block the event loop; offload with `asyncio.to_thread` or a process pool.
14. GIL: threads for I/O, processes for CPU, asyncio for massive I/O concurrency.
15. Debug flow: CPU, memory, I/O, network, fds; then what is it waiting on.

---
## Key commands

| Goal | Linux | macOS |
|---|---|---|
| Processes | `ps aux`, `htop`, `top` | `ps aux`, `top -o cpu` |
| Zombies | `ps -eo pid,ppid,stat,comm \| grep ' Z'` | same |
| Syscall trace | `strace -f -p PID`, `strace -c cmd` | `sudo dtruss -f cmd` |
| Memory | `free -h`, `vmstat 1`, `cat /proc/meminfo` | `vm_stat`, `memory_pressure` |
| Process memory map | `pmap -x PID`, `/proc/PID/smaps` | `vmmap PID` |
| Page faults / peak RSS | `/usr/bin/time -v cmd` | `/usr/bin/time -l cmd` |
| Context switches | `grep ctxt /proc/PID/status`, `pidstat -w` | `top -l 1` |
| OOM evidence | `dmesg \| grep -i killed` | Console / `log show` |
| Open files / sockets | `lsof -p PID`, `ss -tanp` | `lsof -p PID`, `netstat -an` |
| Open-but-deleted files | `lsof +L1` | `lsof +L1` |
| Disk / inodes | `df -h`, `df -i` | `df -h`, `df -i` |
| Disk I/O | `iostat -x 1` | `iostat 1` |
| Inode / links | `ls -li`, `stat file`, `ln`, `ln -s` | `ls -li`, `stat -x file` |
| Signals | `kill -TERM PID`, `kill -l`, `trap` | same |
| Priority | `nice -n 10 cmd`, `renice` | same |
| Python stack of live process | `py-spy dump --pid PID` | same |
| Python memory | `tracemalloc`, `memray` | same |
| Limits | `ulimit -a` | `ulimit -a` |

Python quick imports: `threading`, `multiprocessing`, `concurrent.futures`, `asyncio`, `mmap`, `multiprocessing.shared_memory`, `signal`, `os.fork/os.fsync`, `faulthandler`, `tracemalloc`.
