# Week 2 - Operating Systems: Interview Q&A

Practice: answer out loud in 30-60 seconds first, then compare.
Facts marked "(check current docs)" are version-dependent.

---

**1. What is the difference between a process and a thread?**
A process has its own virtual address space, file descriptor table and PID; a thread is a unit of execution inside a process that shares the heap, globals and fds with sibling threads but has its own stack, registers and program counter. Threads are cheaper to create and switch and communicate through shared memory (needing locks); processes give fault isolation and need IPC. On Linux both are tasks created by clone() with different sharing flags.

**2. What happens during a context switch, and why is it expensive?**
The kernel saves the running task's registers and program counter into its control block, picks the next task via the scheduler, restores that task's registers and, if it is a different process, switches page tables. The direct cost is a few microseconds; the larger hidden cost is cold CPU caches, branch predictors and TLB entries. Switching between threads of one process is cheaper since the address space does not change.

**3. Compare FCFS, Round Robin, priority scheduling and MLFQ.**
FCFS is simple but suffers the convoy effect. Round Robin gives each task a time quantum: fair and good response time, but a tiny quantum wastes time on switches and a huge one degenerates to FCFS. Priority scheduling favors important work but can starve low priority tasks (fix with aging) and cause priority inversion (fix with priority inheritance). MLFQ uses several priority queues, demotes tasks that burn their quantum and periodically boosts everyone, approximating shortest-job-first without knowing job lengths.

**4. How does Linux's CFS work, at the idea level?**
Each runnable task tracks a virtual runtime; the scheduler always picks the task with the smallest one (kept in a red-black tree), so every task gets a share of CPU proportional to its weight (nice value). It aims for fairness rather than fixed quanta. Newer kernels (6.6+) moved to EEVDF as the default (check current docs).

**5. Explain virtual memory and how an address gets translated.**
Each process sees a private, flat virtual address space. The MMU splits a virtual address into page number and offset, looks the page number up in the process's (multi-level) page table to get a physical frame, and appends the offset. Recent translations are cached in the TLB; a TLB miss triggers a page table walk. Virtual memory provides isolation, sharing, lazy allocation, overcommit and memory-mapped files.

**6. What is a page fault? Distinguish minor, major and invalid.**
A page fault is an exception raised when a page is not mapped or not permitted. Minor: page is already in RAM (or needs zero-fill/COW) and only the mapping must be set up. Major: the kernel must read the page from disk (swap or a file), taking milliseconds. Invalid: illegal access, which delivers SIGSEGV. Demand paging means the first touch of malloc'd memory causes minor faults.

**7. What is the TLB, and why do huge pages help?**
The TLB is a small hardware cache of virtual-to-physical translations; hits avoid a multi-access page table walk. Huge pages (2 MiB, 1 GiB) cover much more memory per TLB entry, reducing misses for large working sets like databases, at the cost of fragmentation and less flexible allocation (check current docs for transparent huge page behavior).

**8. What is swap, what is thrashing, and what does the OOM killer do?**
Swap is disk space for evicting anonymous pages when RAM is short. Thrashing is when the working set exceeds RAM so the system spends its time paging instead of computing. When memory cannot be reclaimed, the Linux OOM killer picks a process by oom_score and sends SIGKILL; in containers the cgroup memory limit triggers the same, which shows as exit code 137 or "OOMKilled" in Kubernetes. Because Linux overcommits, malloc rarely fails; the kill happens when pages are touched.

**9. What does mmap do and when would you use it?**
mmap maps a file or anonymous memory into the process's address space; accesses become page faults served from the page cache, avoiding explicit read/write copies. It is used for loading shared libraries, large read-mostly files, databases, and shared memory between processes (MAP_SHARED). Caveats: I/O errors surface as signals, and page fault latency is unpredictable.

**10. Stack versus heap: where do things live and how do they fail?**
The stack holds per-thread call frames (locals, return addresses), allocated automatically with LIFO lifetime, fast and small (commonly 8 MiB main thread on Linux). The heap holds dynamically allocated data with arbitrary lifetime, managed by malloc/GC, larger and slower, and shared across threads. Stack fails with overflow from deep recursion; heap fails with leaks, fragmentation or out-of-memory. In Python all objects are on the heap.

**11. How do you tell a memory leak from fragmentation, and how would you debug a growing service?**
A leak means live objects keep growing (references retained or memory never freed), so heap profiles show growth by allocation site. Fragmentation means live data is stable but RSS stays high because the allocator cannot return scattered free space to the OS. Approach: chart RSS over time, take heap snapshots at intervals and diff (tracemalloc, memray, valgrind, jemalloc profiling), check unbounded caches/queues, and consider worker recycling or a different allocator as mitigation.

**12. State the four Coffman conditions and how to prevent deadlock.**
Mutual exclusion, hold and wait, no preemption, circular wait; all four must hold for deadlock. Prevention breaks one: acquire all locks at once or none (hold and wait), use trylock with timeout and back off (no preemption), and most commonly impose a global lock ordering (circular wait). Avoidance (Banker's algorithm) needs advance knowledge; detection finds cycles in the wait-for graph and aborts a victim, as databases do.

**13. Transfer(a, b) and transfer(b, a) run concurrently with a lock per account. What goes wrong and how do you fix it?**
Each thread locks its source then its destination, so they can hold one lock each and wait for the other: deadlock. Fix by always locking in a consistent order, such as by account id, regardless of transfer direction; alternatively use a single coarser lock or try-lock with retry.

**14. Mutex vs semaphore vs condition variable vs spinlock.**
A mutex gives exclusive ownership; only the owner unlocks, waiters sleep. A semaphore is a counter allowing N concurrent holders and has no owner, so it also works for signaling. A condition variable lets a thread wait for a predicate to become true, atomically releasing its mutex while waiting; always wait in a loop due to spurious wakeups. A spinlock busy-waits and suits very short critical sections on multicore or contexts that cannot sleep; on long holds it burns CPU.

**15. What is a race condition and how does an atomic operation help?**
A race is when correctness depends on the interleaving of unsynchronized accesses, e.g. two threads doing n += 1 (load, add, store) can lose an update. Atomic operations such as compare-and-swap or fetch-and-add execute indivisibly in hardware, enabling lock-free counters and structures, but they only cover single variables and bring subtleties like the ABA problem and memory ordering. For multi-step invariants use locks.

**16. Compare IPC mechanisms and pick the fastest.**
Pipes: simple unidirectional byte streams between related processes. Unix domain sockets: bidirectional local streams that can pass fds. TCP sockets: work across machines. Message queues: discrete messages managed by the kernel or a broker. Signals: tiny asynchronous notifications. Shared memory is fastest because it avoids copies (both processes map the same frames) but you must synchronize yourself with semaphores or atomics.

**17. What is an inode, and how do hard links differ from soft links?**
An inode stores file metadata (type, size, owner, permissions, timestamps, link count, block locations) but not the name; directory entries map names to inode numbers. A hard link is another name for the same inode (same filesystem, increments link count); data is freed when the count hits zero and no process holds it open. A soft link is a separate small file holding a path, can cross filesystems and can dangle.

**18. How do you durably write a file, and what do page cache, fsync and journaling each guarantee?**
write() usually only dirties pages in the page cache and returns; a crash can lose it. fsync forces data and metadata to stable storage. Journaling (ext4, XFS) logs metadata changes first so the filesystem structure stays consistent after a crash, but does not by itself make your data durable. The safe replace pattern: write a temp file, fsync it, rename over the target (atomic), then fsync the directory. In Python, flush() is not enough; use os.fsync.

**19. Explain blocking, non-blocking, select/poll/epoll and async I/O, and how an event loop uses them.**
Blocking calls sleep the thread until ready. Non-blocking calls return EAGAIN immediately. select/poll scan all fds each call (O(n)); epoll (kqueue on macOS) keeps an interest list in the kernel and returns only ready fds, which scales to tens of thousands of connections. True async/completion models (io_uring, IOCP) let the kernel perform the I/O and notify on completion. An event loop is a single thread calling epoll_wait and resuming coroutines whose I/O is ready; asyncio, uvicorn and FastAPI's async def endpoints work this way, so any blocking call inside async code stalls all requests. Plain def endpoints in FastAPI run in a thread pool.

**20. What is the GIL, and how do you choose between threads, processes and asyncio in Python?**
The GIL lets only one thread run Python bytecode at a time in CPython, so threads cannot speed up CPU-bound pure Python, though the GIL is released during blocking I/O and in many C extensions. Use asyncio for large numbers of I/O waits, threads for moderate I/O with blocking libraries, and processes (multiprocessing, ProcessPoolExecutor, or several uvicorn/gunicorn workers) for CPU-bound work, accepting pickling and startup overhead. A free-threaded build exists (PEP 703) but is not the default (check current docs). The GIL does not make compound operations like n += 1 thread-safe.
