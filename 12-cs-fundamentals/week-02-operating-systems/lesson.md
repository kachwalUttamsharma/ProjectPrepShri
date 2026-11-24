# Week 2 - Operating Systems: Processes, Memory, Concurrency, I/O

Time budget: ~7-8 hrs. Read lesson (3h), Q&A aloud (2h), cheatsheet + run the commands/snippets (2h).
Facts marked "(check current docs)" are version-dependent (kernel, Python, OS); verify before quoting in an interview.
Commands are for macOS and Linux; where they differ, both are shown. Python snippets assume Python 3.9+.

---
## 1. What an OS does, user mode vs kernel mode, system calls

```
 +-------------------------------------------+
 |  User space:  your Python / Java / Go app |   unprivileged CPU mode (ring 3)
 |      |  libc / runtime wrappers           |
 +------|------------------------------------+
        | syscall instruction (trap)              <-- mode switch
 +------v------------------------------------+
 |  Kernel: scheduler, VM, FS, net stack,    |   privileged CPU mode (ring 0)
 |          drivers, IPC                     |
 +------|------------------------------------+
        v
     Hardware: CPU, RAM, disk, NIC
```

Key points
- The OS does three jobs: abstract hardware (files, sockets), multiplex resources (CPU time, RAM), and isolate/protect (processes cannot read each other's memory).
- The CPU has at least two modes. Only kernel mode may touch page tables, I/O ports, interrupts. User code asks the kernel via a system call (open, read, write, mmap, fork, execve, futex, epoll_wait ...).
- A syscall = trap into kernel, validate args, do work, return. Cheaper than a context switch but not free (hundreds of ns to a few microseconds; mitigations for CPU vulnerabilities raised it) (check current docs).
- Interrupts (hardware: timer, NIC) and exceptions (page fault, divide by zero) also enter the kernel. The timer interrupt is what enables preemption.

Try it
```
# Linux
strace -c python3 -c "print('hi')"          # syscall counts summary
strace -e trace=openat,read,write cat /etc/hostname
# macOS (needs SIP caveats; dtruss needs sudo)
sudo dtruss -f cat /etc/hostname 2>&1 | head
```
Typical strace line: `openat(AT_FDCWD, "/etc/hostname", O_RDONLY) = 3` -> returns file descriptor 3 (0,1,2 are stdin/out/err).

Gotcha: `print()` is not a syscall; it buffers in user space, then `write(1, ...)` is the syscall. Buffering is why output can appear late when piped.

How interviewers probe it: "What happens when you call read() on a file?" Walk: libc wrapper -> trap -> kernel VFS -> page cache hit? copy to user buffer : issue disk I/O, block the process, schedule another -> interrupt on completion -> wake process.

---
## 2. Processes vs threads

```
 Process A                         Process B
 +---------------------------+     +---------------------------+
 | own virtual address space |     | own virtual address space |
 | code | data | heap        |     | ...                       |
 | fd table, PID, creds      |     |                           |
 | Thread1 Thread2 (shared   |     |                           |
 |  heap/globals/fds;        |     |                           |
 |  own stack + registers)   |     |                           |
 +---------------------------+     +---------------------------+
```

| Aspect | Process | Thread |
|---|---|---|
| Address space | Private | Shared with siblings |
| Own state | Everything (memory, fds, PID) | Stack, registers, PC, thread-local storage |
| Creation cost | Higher (copy page tables; COW) | Lower |
| Context switch | Costlier (address-space switch, TLB effects) | Cheaper (same address space) |
| Communication | IPC needed | Shared memory directly (needs locks) |
| Fault isolation | Crash is contained | One bad thread can kill the process |

- On Linux both are "tasks" created by clone(); flags decide what is shared. A thread is a task sharing the address space.
- Process states: new -> ready -> running -> blocked (waiting on I/O/lock) -> ready ... -> terminated.
- PCB (process control block) holds PID, state, saved registers, page table pointer, open fds, scheduling info.
- Green threads / goroutines / asyncio tasks are user-space scheduled and multiplexed on a few kernel threads.

fork/exec model (Unix)
```
 parent --fork()--> child (copy of parent, COW pages)
                      |--execve("/bin/ls")--> replaces program image, same PID
 parent --wait()--> reaps child's exit status
```
- fork returns twice: 0 in the child, child PID in the parent.
- COW (copy-on-write): pages are shared read-only after fork; copied only when someone writes. Makes fork cheap.
- Zombie: child exited, parent has not called wait(); entry (PID + exit status) lingers in the process table. Not using memory/CPU, but leaks PIDs. Fix: parent waits, or handles SIGCHLD, or dies (init/systemd adopts and reaps).
- Orphan: parent exits first; child is re-parented to PID 1 (or a subreaper). Harmless. In containers, PID 1 must reap children (use `tini`/`--init`).
- Daemon: detached background process.

Try it
```python
import os, time
pid = os.fork()                 # Unix only
if pid == 0:
    os._exit(0)                 # child exits immediately
else:
    time.sleep(30)              # child is a zombie for 30s; parent never waits
```
Then `ps -o pid,ppid,stat,comm | grep -i python` -> child shows state `Z` (zombie, "<defunct>").

Gotcha: fork in a multithreaded program only duplicates the calling thread; locks held by other threads stay locked in the child -> deadlocks. Python 3.12+ warns about fork with threads; macOS defaults multiprocessing to "spawn" (check current docs).

How interviewers probe it: "Process vs thread?", "What does fork do with memory?", "What is a zombie and how do you get rid of one?", "Why can you not kill a zombie with kill -9?" (it is already dead; reap via parent).

---
## 3. CPU scheduling

Goals: throughput, latency/response time, fairness, avoid starvation. Preemptive (timer interrupt can take CPU away) vs non-preemptive (process yields).

| Algorithm | Idea | Pros | Cons |
|---|---|---|---|
| FCFS | Run in arrival order | Simple | Convoy effect: short jobs wait behind long |
| SJF / SRTF | Shortest (remaining) job first | Optimal avg wait | Needs burst estimate; starves long jobs |
| Round Robin | Fixed time quantum, rotate | Fair, good response | Quantum too small -> switch overhead; too large -> FCFS |
| Priority | Highest priority first | Models importance | Starvation; priority inversion |
| MLFQ | Multiple queues; new jobs high, demote if they use full quantum, periodic boost | Approximates SJF without knowing lengths; good for interactive + batch | Tuning; gaming |
| CFS (Linux) | Give each task a fair share; pick task with smallest virtual runtime (red-black tree); nice values = weights | Fairness, O(log n) | Replaced by EEVDF as default in Linux 6.6+ (check current docs) |

Worked example (RR, quantum 2; P1=5, P2=3, P3=1, all arrive at 0)
```
 time: 0  2  4  5  7  8  9
       |P1|P2|P3|P1|P2|P1|
 P3 finishes at 5, P2 at 8, P1 at 9. avg turnaround = (9+8+5)/3 = 7.33
```
- Priority inversion: low-priority task holds a lock needed by high-priority task, while a medium task preempts the low one. Fix: priority inheritance (Mars Pathfinder 1997 is the classic story).
- Real-time scheduling (SCHED_FIFO/RR) exists on Linux; nice values -20..19 for normal tasks.
- CPU-bound vs I/O-bound: schedulers favor I/O-bound (they block often, need quick response).

Try it
```
nice -n 10 python3 -c "while True: pass" &       # low priority hog
top -o cpu      # macOS;  top -o %CPU on Linux (or htop)
renice -n 5 -p <pid>
```

Gotcha: "Load average" counts runnable + (on Linux) uninterruptible-sleep tasks; high load with idle CPU often means I/O wait.

How interviewers probe it: "Design a scheduler for interactive + batch" -> MLFQ answer. "Why does RR quantum matter?" "How to avoid starvation?" (aging).

---
## 4. Context switches and their cost

```
 Process A running --timer irq/syscall block--> kernel saves A's registers + PC into PCB
   -> scheduler picks B -> loads B's registers, switches page table (CR3) -> B runs
```
- Direct cost: save/restore registers, scheduler run, kernel entry/exit: ~1-5 microseconds order (check current docs).
- Indirect cost (often bigger): cold CPU caches, branch predictor pollution, TLB misses after address-space switch (modern CPUs tag TLB entries with PCID/ASID to reduce flushes).
- Thread switch within one process skips page-table switch -> cheaper.
- Voluntary switch: task blocks (I/O, lock). Involuntary: preempted by timer.
- Too many threads -> time lost in switching and cache thrash. This is why thread-per-connection fails at 10k+ connections and event loops exist.

Try it
```
# Linux: per-process context switches
grep ctxt /proc/$$/status            # voluntary_ctxt_switches / nonvoluntary_ctxt_switches
vmstat 1                             # 'cs' column = system-wide switches/sec
# macOS
vm_stat; top -l 1 | head -12
```

Gotcha: a context switch is not the same as a mode switch (user->kernel). A syscall that does not block does not necessarily switch processes.

How interviewers probe it: "What is saved on a context switch?" "Why are thread switches cheaper?" "What is the hidden cost?" (caches/TLB).

---
## 5. Virtual memory, paging, page tables, TLB

```
 Virtual address (e.g. 48-bit)           Physical RAM
 +--------+--------+                      +-----------+
 | page # | offset |  --page table-->     | frame #   | + same offset
 +--------+--------+                      +-----------+
   |
   v  TLB (cache of recent translations): hit ~1 cycle-ish, miss -> walk page table
```
Why virtual memory: isolation, each process sees a flat private address space; allows overcommit, sharing (libc mapped once), lazy allocation, memory-mapped files, and protection bits (R/W/X).

- Page: fixed-size unit (commonly 4 KiB; huge pages 2 MiB/1 GiB). Frame: same-size physical chunk.
- Page table: per-process map page -> frame + flags (present, dirty, accessed, R/W, user/supervisor). x86-64 uses 4-level (5 on some) multi-level tables so sparse address spaces do not need a giant flat table.
- MMU does translation in hardware; kernel populates tables.
- TLB: small fast cache of translations. Miss costs a multi-level walk (several memory accesses). Huge pages increase TLB reach (databases use them) (check current docs).

Page faults
| Type | Meaning | Cost |
|---|---|---|
| Minor (soft) | Page is in RAM but not mapped yet (first touch of malloc'd memory, COW copy, page in page cache) | microseconds |
| Major (hard) | Must read from disk (file-backed page or swapped-out page) | milliseconds |
| Invalid | Illegal address/permission -> SIGSEGV | process killed |

Demand paging: malloc(1GB) only reserves virtual range; frames are allocated on first touch.

Page replacement: when RAM is full, evict a page. FIFO (Belady's anomaly possible), LRU (ideal, expensive), Clock/second-chance (approximates LRU with a reference bit), Linux uses an active/inactive list scheme (approximate LRU).
Thrashing: working set > RAM, system spends time paging, not computing.

Swap: disk area for anonymous pages evicted from RAM. Swapping is slow; some servers (DBs, latency-sensitive) tune swappiness low or disable swap. Swap is not a fix for too little RAM.

OOM killer (Linux): when memory is exhausted and reclaim fails, kernel picks a process by `oom_score` (mostly memory use, adjustable via `oom_score_adj`) and sends SIGKILL. Check `dmesg | grep -i "killed process"`. Overcommit: Linux lets you allocate more virtual than physical by default (heuristic), which is why OOM kills happen later at touch time, not at malloc. In containers, cgroup memory limit triggers a cgroup-scoped OOM kill (exit code 137 = 128+9) - very common in Kubernetes ("OOMKilled").

mmap: map a file (or anonymous memory) into the address space. Reads become page faults served from the page cache; no explicit read() copy. Used by DBs (LMDB), loaders of shared libs, numpy.memmap, and shared memory between processes.

Try it
```
# macOS
vm_stat ; sysctl hw.pagesize ; memory_pressure | head
# Linux
free -h ; cat /proc/meminfo | head ; getconf PAGESIZE
/usr/bin/time -v python3 -c "x=bytearray(200_000_000)"   # Linux: see Minor/Major faults
/usr/bin/time -l python3 -c "x=bytearray(200_000_000)"   # macOS: page reclaims, faults
```
```python
import mmap
with open("big.bin", "wb") as f: f.truncate(1 << 20)
with open("big.bin", "r+b") as f:
    m = mmap.mmap(f.fileno(), 0)
    m[0:5] = b"hello"         # write goes to page cache; flush() = msync
    m.flush(); m.close()
```

Gotcha: RSS (resident set) vs VSZ (virtual size). A process can have huge VSZ and tiny RSS. Shared pages are counted in each process's RSS; use PSS (Linux smem) for fair accounting.

How interviewers probe it: "What happens on a page fault?" "Why multi-level page tables?" "malloc succeeded but process got killed - why?" "What is the TLB and why do huge pages help?"

---
## 6. Stack vs heap, memory leaks, fragmentation

```
 high addr  +-----------------+
            | stack (grows v) |  per thread, LIFO, frames: locals, return addr
            |       ...       |
            | mmap region     |  shared libs, mmap'd files, big mallocs
            |       ...       |
            | heap (grows ^)  |  malloc/new, brk/sbrk
            | .data / .bss    |  globals
 low addr   | .text (code)    |
            +-----------------+
```

| | Stack | Heap |
|---|---|---|
| Allocation | Automatic, move stack pointer | Explicit (malloc/new) or GC |
| Lifetime | Function scope | Until freed / unreachable |
| Speed | Very fast, cache friendly | Slower, allocator bookkeeping |
| Size | Small fixed (commonly 8 MiB main thread on Linux; threads may be less) (check current docs) | Large, limited by memory |
| Failure | Stack overflow (deep recursion) | Out of memory, fragmentation, leaks |
| Thread-safety | Private per thread | Shared; needs sync |

- Python: all objects live on the heap; the stack holds frames/references. `sys.setrecursionlimit` guards the interpreter stack, not the C stack.
- Memory leak: memory that is no longer needed but never released (unfreed in C, or still referenced in managed languages: unbounded caches, global lists, listeners). Symptom: RSS grows monotonically.
- Fragmentation: external = free memory exists but in small non-contiguous pieces so a big allocation fails; internal = wasted space inside an allocated block (rounding up). Paging eliminates external fragmentation of physical memory but heap allocators can still fragment virtual memory; long-running processes may show high RSS after frees because the allocator cannot return fragmented arenas to the OS. Mitigations: arena/slab/pool allocators, jemalloc/tcmalloc, restart workers periodically (gunicorn max_requests).

Try it
```python
import tracemalloc
tracemalloc.start()
leak = []
for _ in range(100000): leak.append("x" * 100)
print(tracemalloc.get_traced_memory())
snap = tracemalloc.take_snapshot()
for s in snap.statistics("lineno")[:3]: print(s)
```
Tools: valgrind/ASan (C), `pmap -x <pid>` (Linux), `vmmap <pid>` (macOS), memray/tracemalloc (Python).

Gotcha: "Memory leak" in a GC language is usually a reachable-but-unneeded reference, not unreachable garbage.

How interviewers probe it: "Where do locals vs malloc'd data live?" "How would you debug a service whose memory grows until OOMKilled?" (heap profile over time, compare snapshots, check caches, check native extensions, check fragmentation vs leak by whether live-object count grows).

---
## 7. Synchronization primitives and race conditions

Race condition: outcome depends on interleaving of threads. Critical section: code touching shared state that must not run concurrently.

```python
import threading
n = 0
def work():
    global n
    for _ in range(1_000_000):
        n += 1           # load, add, store: NOT atomic
ts = [threading.Thread(target=work) for _ in range(4)]
[t.start() for t in ts]; [t.join() for t in ts]
print(n)   # often < 4_000_000 on some versions/builds; fix with a Lock
```
(Whether it visibly loses updates depends on the CPython version and build, e.g. the GIL switch interval and free-threaded builds (check current docs). It is still a bug by the language's guarantees.)

| Primitive | What it is | Use when |
|---|---|---|
| Mutex (lock) | One owner at a time; owner unlocks; blocks waiters (sleeps) | Protect critical section |
| Spinlock | Busy-wait loop on an atomic flag | Very short critical sections, kernel/no-sleep contexts, multicore |
| Semaphore | Counter with wait(P)/signal(V); counting or binary; no ownership | Limit N concurrent users (connection pool), signaling |
| Condition variable | Wait until predicate true; paired with a mutex; wait releases mutex atomically | Producer/consumer, "wait for state change" |
| Read-write lock | Many readers OR one writer | Read-heavy data; beware writer starvation |
| Barrier | All threads wait until N arrive | Phased parallel algorithms |
| Atomic ops | Hardware instructions (CAS, fetch-add) | Counters, lock-free structures |
| Monitor | Mutex + condition variables bundled (Java synchronized, Python Condition) | Structured sync |

- Mutex vs binary semaphore: mutex has an owner (only locker unlocks, enables priority inheritance); semaphore is a signaling mechanism.
- Condition variables: always wait in a loop (`while not predicate: cv.wait()`) because of spurious wakeups and stolen wakeups.
- CAS (compare-and-swap): atomically "if value == expected, set new". Lock-free algorithms loop on CAS; beware the ABA problem.
- Memory ordering: CPUs/compilers reorder; locks and atomics include barriers. Visibility is a separate problem from atomicity.
- Futex (Linux): user-space fast path with atomics, kernel sleep only on contention. Python/pthread mutexes use it.

Producer/consumer sketch
```python
import threading, collections
q, cv, MAX = collections.deque(), threading.Condition(), 10
def produce(x):
    with cv:
        while len(q) >= MAX: cv.wait()
        q.append(x); cv.notify_all()
def consume():
    with cv:
        while not q: cv.wait()
        x = q.popleft(); cv.notify_all(); return x
# In practice: queue.Queue does this for you.
```

Gotcha: A lock protects data only if every access takes the same lock. Locking only the writer is a bug.

How interviewers probe it: "Implement a thread-safe counter / bounded buffer", "Mutex vs semaphore", "When spinlock over mutex?", "What is a lost update?", "Explain CAS".

---
## 8. Deadlock

Four Coffman conditions (all must hold):
1. Mutual exclusion: resource held exclusively.
2. Hold and wait: holds one resource while waiting for another.
3. No preemption: resources cannot be forcibly taken.
4. Circular wait: cycle of threads each waiting on the next.

```
 T1 holds A, wants B        T1 --wants--> B --held by--> T2
 T2 holds B, wants A        T2 --wants--> A --held by--> T1     (cycle)
```

| Strategy | How | Example |
|---|---|---|
| Prevention | Break one condition by design | Lock ordering (breaks circular wait); acquire all locks at once (breaks hold-and-wait); allow preemption/trylock+backoff |
| Avoidance | Grant only if system stays in a safe state | Banker's algorithm (needs max demands up front; rarely used in practice) |
| Detection + recovery | Build wait-for graph, find cycle, kill/rollback a victim | Databases detect deadlocks and abort one transaction |
| Ignore (ostrich) | Rare; reboot | General-purpose OSes for app-level locks |

Related: livelock (threads keep reacting but make no progress), starvation (never scheduled/never gets lock).

Deadlock demo (it hangs; Ctrl-C to stop)
```python
import threading, time
A, B = threading.Lock(), threading.Lock()
def t1():
    with A:
        time.sleep(0.1)
        with B: print("t1 done")
def t2():
    with B:
        time.sleep(0.1)
        with A: print("t2 done")
for f in (t1, t2): threading.Thread(target=f, daemon=True).start()
time.sleep(2); print("deadlocked: neither finished")
# Fix: always acquire in a global order, e.g. sorted(locks, key=id), or use A.acquire(timeout=1)
```
Debug: Python `faulthandler.dump_traceback_later(5)` or `py-spy dump --pid <pid>`; Java `jstack`; gdb `thread apply all bt`.

Gotcha: locks + callbacks/user code under a lock + re-entrance cause hidden cycles. Do not call unknown code while holding a lock. Non-reentrant lock acquired twice by the same thread = self-deadlock (use RLock if truly needed, but prefer redesign).

How interviewers probe it: "List the Coffman conditions", "How do you prevent it in code?", "Two bank accounts transfer(a,b) and transfer(b,a) - what goes wrong?" (lock ordering by account id).

---
## 9. Inter-process communication (IPC)

| Mechanism | Model | Notes |
|---|---|---|
| Pipe (anonymous) | Unidirectional byte stream, related processes | `a | b` in shell; bounded kernel buffer (commonly 64 KiB on Linux) -> writer blocks when full |
| Named pipe (FIFO) | Pipe with a filesystem name | `mkfifo` |
| Unix domain socket | Bidirectional, local, can pass fds and credentials | Faster than TCP loopback; Docker socket |
| TCP/UDP socket | Network, works across machines | Same API local or remote |
| Shared memory | Same physical pages mapped into several processes | Fastest (no copy); needs your own synchronization |
| Message queue | Kernel/broker-managed discrete messages | POSIX mq, SysV; at scale: Kafka/RabbitMQ/SQS (different layer) |
| Signals | Async notification, tiny payload | SIGINT, SIGTERM (graceful), SIGKILL (uncatchable), SIGSEGV, SIGCHLD, SIGHUP |
| Files / mmap | Persistent, coordinate via locks | flock, fcntl |

```
 Copying IPC (pipe/socket):  A user buf -> kernel buf -> B user buf   (2 copies)
 Shared memory:              A and B map the same frames              (0 copies, you sync)
```

Signals to know: SIGTERM (polite stop, catchable, what `kill` sends and what Kubernetes sends first), SIGKILL (cannot catch/ignore), SIGINT (Ctrl-C), SIGSTOP/SIGCONT, SIGPIPE (write to closed pipe), SIGCHLD (child exited). Signal handlers must be minimal (async-signal-safe functions only). In Python handlers run in the main thread between bytecodes.

Try it
```
mkfifo /tmp/f; (echo hello > /tmp/f &); cat /tmp/f
yes | head -n 3                      # SIGPIPE ends 'yes' when head closes
kill -l                              # list signals
trap 'echo got TERM' TERM; kill -TERM $$
```
```python
from multiprocessing import shared_memory, Process
shm = shared_memory.SharedMemory(create=True, size=16)
shm.buf[:5] = b"hello"
def child(name):
    s = shared_memory.SharedMemory(name=name); print(bytes(s.buf[:5])); s.close()
p = Process(target=child, args=(shm.name,)); p.start(); p.join()
shm.close(); shm.unlink()
```

Gotcha: pipes carry bytes, not messages; you need framing (length prefix/newline). multiprocessing.Queue pickles objects (cost!) - large arrays: use shared_memory or mmap.

How interviewers probe it: "Fastest IPC?" (shared memory; but sync needed) "Pipe vs socket?" "How does graceful shutdown work?" (SIGTERM handler, drain, exit; SIGKILL after grace period).

---
## 10. File systems, inodes, links, page cache, fsync, journaling

```
 path "/a/b.txt" --directory entry (name -> inode#)--> inode
 inode: type, size, owner, perms, timestamps, link count, pointers to data blocks (or extents)
        NOTE: file name is NOT in the inode; it lives in the directory
 fd table (per process) -> open file description (offset, flags) -> inode
```

- Inode: metadata + block locations. File = inode + data blocks. Directory = file mapping names -> inode numbers.
- Hard link: another directory entry for the same inode (link count +1). Same filesystem only; cannot (normally) link directories. File data is freed when link count = 0 AND no process has it open. Deleting a file that a process still has open does not free disk space until it closes (classic "disk full but du shows little" bug; check `lsof +L1`).
- Soft (symbolic) link: a small file containing a path; can cross filesystems; can dangle.
- Page cache: kernel caches file data in RAM. `read` often hits cache; `write` normally just dirties pages and returns (write-back), flushed later by kernel threads. This is why free RAM looks low on Linux (it is cache, reclaimable).
- fsync(fd): force file data and metadata to stable storage and wait. Without it a crash or power loss can lose "successful" writes. Durable-write pattern for atomic replace: write temp file -> fsync(temp) -> rename(temp, final) (rename is atomic on POSIX) -> fsync(directory).
- Python: `f.flush()` only moves from Python's buffer to the OS; `os.fsync(f.fileno())` moves to disk.
- Journaling (ext4, XFS, NTFS, APFS uses copy-on-write metadata instead): write intent to a journal first, then apply; after a crash replay/discard the journal so metadata stays consistent without a full fsck. Modes: metadata-only (default ext4 ordered) vs full data journaling. Journaling gives consistency, not necessarily durability of your data without fsync.
- Other ideas: extents, copy-on-write FS (ZFS, Btrfs, APFS), LSM trees/WAL in databases (the same "log first" principle), disk drive caches lying about flush (check current docs for hardware specifics).
- Everything is a file (Unix): devices, pipes, sockets are accessed through fds.

Try it
```
echo hi > a.txt; ln a.txt hard.txt; ln -s a.txt soft.txt
ls -li a.txt hard.txt soft.txt        # same inode for a and hard; link count 2
stat a.txt                            # macOS: stat -x a.txt
rm a.txt; cat hard.txt; cat soft.txt  # hard works, soft dangles
df -i                                 # inode exhaustion = "no space" with free bytes
lsof +L1                              # open-but-deleted files
```

Gotcha: running out of inodes (millions of tiny files) gives ENOSPC even with free space.

How interviewers probe it: "What is an inode?" "Hard vs soft links; what happens on rm?" "How to durably write a file?" "Why does a DB have a WAL?" "Why is `free` memory low but system fine?"

---
## 11. I/O models: blocking, non-blocking, multiplexing, async

```
 Blocking:        read() ---------sleeps until data----------> returns
 Non-blocking:    read() -> EAGAIN immediately (poll in a loop = busy waiting)
 Multiplexing:    select/poll/epoll_wait([many fds]) -> ready list -> read() those
 Async (true):    submit request; kernel completes it; you get notified (io_uring, Windows IOCP)
```

| Mechanism | Scalability | Notes |
|---|---|---|
| select | O(n) scan, fd limit (FD_SETSIZE 1024) | Portable, old |
| poll | O(n), no hard limit | Copies the array each call |
| epoll (Linux) | O(ready) events | Interest list in kernel; edge or level triggered; solves C10K |
| kqueue (macOS/BSD) | Like epoll | |
| io_uring (Linux 5.1+) | Shared submission/completion rings, true async incl. file I/O, fewer syscalls | Newer, security-sensitive; adoption growing (check current docs) |

- Readiness model (epoll): "tell me when I can read without blocking", then you do the read. Completion model (io_uring, IOCP): "do the read and tell me when done".
- Regular disk files are always "ready" to epoll, so event loops push file I/O to a thread pool (this is what libuv and `loop.run_in_executor` do).
- Level-triggered: notify while data remains. Edge-triggered: notify once on change; must drain until EAGAIN.
- C10K problem: thread-per-connection does not scale to 10k connections (stacks, switches); one thread with epoll does.

### asyncio, event loop, FastAPI/uvicorn
```
 event loop (1 thread):  while True:
     events = epoll_wait(timeout)         # sockets ready?
     run ready callbacks / resume coroutines whose awaited I/O finished
 await = "suspend me, let loop run others, resume when this I/O completes"
```
- async/await is cooperative multitasking: a coroutine only yields at `await`. One blocking call (time.sleep, requests.get, heavy CPU) freezes every request on that loop.
- uvicorn = ASGI server: runs the asyncio loop (uvloop optionally, built on libuv), accepts connections, parses HTTP, calls your app. FastAPI: `async def` endpoints run directly on the loop; plain `def` endpoints are run in a thread pool (so they will not block the loop, but are limited by pool size, default 40 threads via AnyIO) (check current docs).
- Scaling uvicorn/gunicorn: multiple worker processes (one loop each) to use all cores and bypass the GIL; `gunicorn -k uvicorn.workers.UvicornWorker -w N` or `uvicorn --workers N`.

```python
import asyncio, time
async def io_task(i):
    await asyncio.sleep(1)           # non-blocking wait
    return i
async def main():
    t = time.perf_counter()
    print(await asyncio.gather(*(io_task(i) for i in range(1000))))
    print(f"{time.perf_counter()-t:.2f}s")   # ~1s, not 1000s
asyncio.run(main())
# Bad: time.sleep(1) inside io_task -> ~1000s (blocks the loop).
# Offload blocking/CPU work: await asyncio.to_thread(fn)  or  loop.run_in_executor(ProcessPoolExecutor(), fn)
```
Try it: `strace -f -e trace=epoll_wait,epoll_ctl python3 server.py` (Linux) to see the loop. macOS: uses kqueue, `sudo dtruss -t kevent`.

Gotcha: async does not make code faster; it makes waiting cheap. CPU-bound async code gains nothing.

How interviewers probe it: "Blocking vs non-blocking vs async?" "How does epoll scale?" "Why did my FastAPI service stall under load?" (blocking call inside async def). "Explain the event loop."

---
## 12. Python concurrency: GIL, threads vs processes vs asyncio

- GIL (Global Interpreter Lock) in CPython: only one thread executes Python bytecode at a time. Protects interpreter internals (refcounts). Released during blocking I/O and many C extensions (numpy, hashlib, zlib). Switch interval default 5 ms (`sys.getswitchinterval()`).
- Consequence: threads give I/O concurrency but no CPU parallelism for pure-Python code.
- PEP 703: optional free-threaded (no-GIL) build, experimental in 3.13, supported-but-optional in 3.14; default build still has the GIL (check current docs). Also per-interpreter GIL / subinterpreters (3.12+).
- GIL does not make your code thread-safe: `n += 1` and check-then-act sequences still race.

| Workload | Best tool | Why |
|---|---|---|
| Many network/disk waits (thousands) | asyncio | Cheapest per task, one thread |
| Moderate I/O, blocking libraries | threading / ThreadPoolExecutor | Simple; GIL released on I/O |
| CPU-bound pure Python | multiprocessing / ProcessPoolExecutor | Separate interpreters, parallel cores; pickling + startup cost |
| CPU-bound numeric | numpy/native extensions (release GIL), or processes | Vectorize first |
| Mixed | asyncio + process pool via run_in_executor | Keep loop responsive |

```python
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

def cpu(n): 
    s = 0
    for i in range(n): s += i*i
    return s
def run(Ex, label):
    t = time.perf_counter()
    with Ex(4) as ex: list(ex.map(cpu, [5_000_000]*4))
    print(label, f"{time.perf_counter()-t:.2f}s")
if __name__ == "__main__":        # required for spawn start method (macOS/Windows)
    run(ThreadPoolExecutor, "threads  (GIL-bound)")
    run(ProcessPoolExecutor, "processes (parallel)")
```
Expect threads ~ sequential time; processes ~ 1/cores (on a multi-core machine). Swap `cpu` for `time.sleep(1)` and threads win easily (no pickling/spawn cost).

- multiprocessing start methods: fork (Linux default historically; unsafe with threads; changing in 3.14 to forkserver (check current docs)), spawn (macOS/Windows default; re-imports main module, hence the `__main__` guard), forkserver.
- Data crossing processes is pickled; passing big objects negates the speedup.
- Rule of thumb for thread count: I/O-bound can exceed core count; CPU-bound ~ number of cores.

Gotcha: `threading` for CPU work can be slower than single thread due to GIL contention and switching.

How interviewers probe it: "What is the GIL and why does it exist?" "Threads vs processes vs asyncio for X?" "Your FastAPI endpoint does image resizing - what do you do?" (process pool / worker queue) "How to get parallelism in Python?"

---
## 13. Putting it together: "What happens when..." walkthroughs

1. `python3 app.py` in a shell: shell fork()s -> child execve("python3") -> kernel maps binary and libs (mmap), sets up stack/heap -> page faults load code lazily -> interpreter reads file via syscalls -> shell wait()s.
2. A web request to uvicorn: NIC interrupt -> kernel TCP stack -> socket readable -> epoll_wait returns -> loop reads bytes -> parser -> your coroutine runs until `await db.query()` -> socket write -> coroutine suspended -> loop serves others -> DB response readable -> resume.
3. Process uses more memory than limit in a container: allocations succeed (virtual), page faults on touch grow RSS, cgroup limit hit, reclaim fails, cgroup OOM kill SIGKILL, exit 137.
4. Service hangs, CPU 0%: likely deadlock/lock wait/blocked I/O. Check `py-spy dump`, `strace -p`, `lsof -p`, thread states. CPU 100% single core in async service: blocking CPU work on the loop.
5. Latency spikes: page faults/swap (check `vmstat si/so`), GC pauses, noisy neighbor/CPU throttling (cgroup cpu quota), lock contention, disk fsync stalls.

Triage toolkit
```
top/htop | ps aux | vmstat 1 | iostat -x 1 (Linux) | lsof -p PID | ss -tanp (Linux) / netstat -an (macOS)
strace -p PID (Linux) | dtruss (macOS) | perf top (Linux) | py-spy top --pid PID | dmesg | tail
```

How interviewers probe it: open-ended debugging prompts at Google/Uber/FDE interviews: "Service is slow/hung/OOMing - walk me through your diagnosis." Structure: reproduce, check resources (CPU, memory, I/O, network, fds), inspect what it is waiting on, form hypothesis, verify.

---
## 14. Study plan and self-check

- Hour 1-2: sections 1-5, run strace/ps/vm_stat commands.
- Hour 3-4: sections 6-9, run the race, deadlock, shared_memory snippets.
- Hour 5: sections 10-12, run asyncio and Thread vs Process benchmark.
- Hour 6-7: interview-qa.md aloud (30-60 s each), then cheatsheet.
- Self-check: can you, without notes, (a) draw virtual->physical translation with TLB, (b) list Coffman conditions and a fix per condition, (c) explain why FastAPI `async def` with `time.sleep` is broken, (d) explain fsync + rename pattern, (e) pick threads/processes/asyncio for three workloads and justify?
