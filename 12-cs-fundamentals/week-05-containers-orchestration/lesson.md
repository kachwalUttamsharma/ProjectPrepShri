# Week 5 - Containers and Orchestration: Linux Primitives, Docker, Compose, Kubernetes, Debugging, Security

Time budget: ~7-8 hrs. Read lesson (3h), Q&A aloud (2h), cheatsheet + hands-on labs (2-3h).
Facts marked "(check current docs)" are version-dependent (K8s API versions, base image tags, compose spec details); verify before quoting in an interview.

---
## 1. What a container really is (Linux primitives)

A container is NOT a mini-VM. It is an ordinary Linux process (or process tree) that the kernel
lies to: it sees a private view of PIDs, network, mounts, hostname, and is limited in resources.

```
 Host kernel (ONE shared kernel)
 |
 |-- process A  (container 1)     namespaces: pid, net, mnt, uts, ipc, user, cgroup
 |-- process B  (container 2)     cgroups:    cpu, memory, pids, io limits
 |                                rootfs:     overlay mount of image layers + writable layer
 `-- process C  (host systemd)
```

| Primitive | What it gives | Example |
|-----------|---------------|---------|
| Namespaces | ISOLATION (what you can see) | pid: app is PID 1 inside; net: own eth0/IP; mnt: own filesystem tree; uts: own hostname; ipc; user: root inside maps to unprivileged outside; cgroup |
| cgroups (v1/v2) | LIMITS and accounting (what you can use) | memory.max, cpu.max, pids.max. Exceeding memory -> kernel OOM killer -> exit 137 |
| Union / overlay FS (overlayfs) | Layered, copy-on-write root filesystem | read-only lower layers + one thin writable upper layer |
| Capabilities, seccomp, AppArmor/SELinux | Reduce what root can do | drop NET_RAW, default seccomp profile blocks ~40+ syscalls |

Overlay filesystem

```
 merged (what the container sees)  /
   upperdir  (writable, per container, discarded on rm)
   lowerdir  layer N  (read-only)
   lowerdir  layer ...
   lowerdir  layer 1  (base image)
 Write to a file from a lower layer -> copy-up into upperdir (copy-on-write).
```

Container vs VM

| | Container | VM |
|--|-----------|----|
| Isolation unit | process + namespaces | full guest OS on a hypervisor |
| Kernel | shared with host | own kernel per VM |
| Start time | milliseconds-seconds | seconds-minutes |
| Size | MBs | GBs |
| Isolation strength | weaker (kernel shared; escape = host compromise) | stronger (hardware virtualization boundary) |
| Density | very high | lower |
| Hardened variants | gVisor, Kata Containers, Firecracker microVMs | - |

Quick demo you can say in an interview: `unshare --pid --fork --mount-proc bash` then `ps` shows PID 1 - that is a PID namespace.

Gotcha: Containers share the host kernel, so a Linux container cannot run a different kernel. On macOS/Windows Docker Desktop runs a hidden Linux VM.
Gotcha: Docker image = filesystem + metadata. Container = running (or stopped) instance of it. Image is immutable; container writes vanish on `docker rm`.
Gotcha: Memory limit in a container but runtime unaware of it (old JVMs, some Python/Node tuning) can cause OOMKill; set worker counts/heap explicitly.

How interviewers probe it:
- "What is a container, without saying Docker?" -> namespaces + cgroups + overlay FS on a shared kernel.
- "Why is exit code 137 common?" -> 128+9, SIGKILL, usually cgroup OOM killer.
- "Is a container a security boundary?" -> weaker than VM; mitigate with non-root, seccomp, dropped caps, gVisor/Kata for untrusted code.

---
## 2. Docker images, layers, registries

```
 Dockerfile instruction      -> layer (FROM/COPY/RUN/ADD create filesystem layers; ENV/CMD/etc. are metadata)
 Image = ordered list of layers + config JSON (env, entrypoint, user, ports)
 Image manifest -> content-addressed by sha256 digest
 Tag (python:3.12-slim)  = mutable pointer to a digest
 Digest (@sha256:ab12..) = immutable identity
```

Naming: `registry.example.com/team/app:1.4.2` -> registry / repository / tag. Default registry docker.io, default tag `latest` (which is just a name, not "newest").

Build cache and layer ordering

```
 Rule: each instruction is cached by (parent layer + instruction + inputs, e.g. file checksums for COPY).
 If a layer changes, EVERY layer after it is rebuilt.

 BAD                          GOOD
 COPY . /app                  COPY pyproject.toml uv.lock /app/     <- changes rarely
 RUN pip install -r req.txt   RUN uv sync --frozen --no-dev         <- cached until deps change
                              COPY src/ /app/src/                   <- changes often, last
```

- Order: least-changing first (OS packages, dependency manifests, dependency install), most-changing last (source).
- Combine `apt-get update && apt-get install -y --no-install-recommends ... && rm -rf /var/lib/apt/lists/*` in ONE RUN, else the cleanup does not shrink the image (deleted files stay in earlier layers).
- BuildKit cache mounts keep package caches out of layers: `RUN --mount=type=cache,target=/root/.cache/uv uv sync ...`.
- `.dockerignore` shrinks build context and avoids cache busting from irrelevant files (.git, .venv, __pycache__, .env, node_modules).

Tags vs digests

| | Tag | Digest |
|--|-----|--------|
| Mutable? | yes (re-pushed) | no |
| Reproducible build | no | yes |
| Use for | humans, dev | production pinning, supply-chain integrity |
| Example | `python:3.12-slim` | `python@sha256:<64 hex>` |

Gotcha: `:latest` in production = non-reproducible deploys and surprise rollbacks. Pin a version tag at minimum, a digest for strict reproducibility (pair with Renovate/Dependabot to bump).
Gotcha: Deleting a secret in a later layer does NOT remove it; it is still in the earlier layer (`docker history`, `docker save`).
Gotcha: Multi-arch: an image built on Apple Silicon (arm64) will fail on amd64 nodes with `exec format error`. Use `docker buildx build --platform linux/amd64,linux/arm64`.
Gotcha: `imagePullPolicy` defaults: `Always` if tag is `latest` or omitted, else `IfNotPresent`.

How interviewers probe it:
- "Your rebuilds take 5 minutes after a one-line code change. Why?" -> COPY . before dependency install.
- "Tag vs digest?" and "Why did prod change though we did not deploy?" -> mutable tag re-pushed / base image drift.
- "Why is my image 1.2 GB?" -> full base, build tools in final image, apt cache, no multi-stage.

---
## 3. Dockerfile best practices

| Practice | Why |
|----------|-----|
| Slim/minimal base (python:3.12-slim, distroless, alpine with care) | smaller attack surface, faster pulls (check current docs for supported tags) |
| Pin versions (base tag, system pkgs, lock file) | reproducible builds |
| `.dockerignore` | small context, no leaked secrets |
| Non-root `USER` | limits blast radius of an exploit |
| Exec-form `CMD ["uvicorn", ...]` | app is PID 1 and receives SIGTERM directly |
| No secrets in layers/ENV/ARG | layers and `docker history` leak them; use BuildKit `--mount=type=secret` |
| `HEALTHCHECK` | Docker/Compose know if app is actually serving (K8s ignores it; uses probes) |
| Multi-stage build | compile/install in builder, ship only runtime artifacts |
| One process per container | simpler scaling, logging, restarts |
| Log to stdout/stderr | runtime collects logs; no log files in the container |
| `PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1` | logs appear immediately; no .pyc clutter |

PID 1 and signals

```
 Shell form:  CMD uvicorn app:app        -> runs /bin/sh -c "uvicorn ..."
                                             sh is PID 1, does NOT forward SIGTERM -> 10s wait -> SIGKILL
 Exec form:   CMD ["uvicorn","app:app"]  -> uvicorn is PID 1, gets SIGTERM, can shut down gracefully
```

- PID 1 in a container has special kernel signal semantics: no default signal handlers, so SIGTERM is ignored unless the process installs a handler (uvicorn/gunicorn do). It also must reap zombie children.
- If your app spawns children or does not handle signals, use `docker run --init` / Compose `init: true` / `tini`.
- `docker stop` sends SIGTERM, waits (default 10s), then SIGKILL. K8s: SIGTERM, `terminationGracePeriodSeconds` (default 30s), then SIGKILL.

ENTRYPOINT vs CMD
- ENTRYPOINT = the executable; CMD = default arguments (or default command if no ENTRYPOINT). `docker run image args` replaces CMD, not ENTRYPOINT.
- In K8s: `command` overrides ENTRYPOINT, `args` overrides CMD.

COPY vs ADD: prefer COPY; ADD also untars and fetches URLs (surprising).

uv / pip install caching

```
 # uv (fast, lockfile-driven)
 COPY --from=ghcr.io/astral-sh/uv:<pin-version> /uv /bin/uv      # pin version (check current docs)
 COPY pyproject.toml uv.lock ./
 RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project
 COPY src ./src
 RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

 # pip equivalent
 COPY requirements.txt .
 RUN --mount=type=cache,target=/root/.cache/pip pip install --no-cache-dir -r requirements.txt
 (--no-cache-dir only if you do NOT use a cache mount; the cache mount is not in the final image anyway)
```

Gotcha: `ARG`/`ENV` values appear in `docker history` and image config. Never pass tokens that way.
Gotcha: alpine uses musl libc; many Python wheels (numpy, psycopg binary) are manylinux (glibc) and need compiling on alpine -> slow builds and odd bugs. `-slim` (Debian) is the safer default for Python.
Gotcha: running as non-root means can't bind ports <1024 (without capability) and volume mounts may have the wrong ownership; use port 8000 and `chown`/`--chown` on COPY.
Gotcha: `HEALTHCHECK` using `curl` requires curl in the image; in slim images use Python stdlib (`python -c "import urllib.request..."`).

How interviewers probe it:
- "Review this Dockerfile" (FROM ubuntu:latest, COPY ., pip install, root, shell CMD, secret ARG) - list all problems.
- "Why does my container take 10 seconds to stop?" -> shell-form CMD, SIGTERM never reaches the app.
- "How do you pass a private-index token at build time?" -> `--mount=type=secret`, not ARG.

---
## 4. Storage: volumes, bind mounts, tmpfs

```
 Container writable layer  -> ephemeral, slower (copy-on-write), gone on rm
 Volume   (docker-managed, /var/lib/docker/volumes/...)  -> persistent, portable, best for DB data
 Bind mount (host path -> container path)                -> dev workflow, live code reload, host-specific
 tmpfs    (RAM only)                                     -> secrets/scratch, never hits disk, gone on stop
```

| | Volume | Bind mount | tmpfs |
|--|--------|-----------|-------|
| Managed by Docker | yes | no (host path) | yes (memory) |
| Survives container rm | yes | yes (host files) | no |
| Portable across hosts | better | no | n/a |
| Typical use | Postgres data dir | mount source for hot reload | temp files with read-only rootfs |
| Flag | `-v pgdata:/var/lib/postgresql/data` | `-v $(pwd):/app` or `--mount type=bind` | `--tmpfs /tmp` |

Gotcha: `docker compose down -v` deletes named volumes (your database). Plain `down` keeps them.
Gotcha: bind-mounting over a directory hides what the image had there (e.g. mounting `.` over `/app` hides installed `.venv`).
Gotcha: bind mounts on macOS are slower (VM file sharing), and permission/UID mismatches are common on Linux.
Gotcha: in K8s, container filesystem is ephemeral; use PVC for state, `emptyDir` for scratch shared between containers in a pod.

How interviewers probe it:
- "Where does Postgres data live and what happens on redeploy?" -> named volume / PVC; without it data is lost.
- "Why can't my read-only container write temp files?" -> mount tmpfs/emptyDir at /tmp.

---
## 5. Docker networking

```
 Host
 +--------------------------------------------------+
 | docker0 / user-defined bridge  172.18.0.0/16     |
 |   [web 172.18.0.2]   [db 172.18.0.3]             |
 |       |  embedded DNS: "db" -> 172.18.0.3        |
 +-------+------------------------------------------+
         | NAT (iptables)   host:8000 -> web:8000   (port publishing -p 8000:8000)
       eth0 (host)
```

| Mode | Behavior | Use |
|------|----------|-----|
| bridge (default) | private network, NAT out, publish ports in | most apps |
| user-defined bridge | bridge + automatic DNS by container/service name | Compose default; always prefer over default bridge |
| host | shares host network stack, no isolation, no port mapping (Linux only) | max network performance, special tools |
| none | no network | isolated jobs |
| overlay | multi-host (Swarm) | legacy Swarm; K8s uses CNI instead |

- Port publishing: `-p HOST:CONTAINER` (`-p 127.0.0.1:5432:5432` binds to loopback only). `EXPOSE` is documentation only; it does not publish.
- Containers on the same user-defined network reach each other by service name and CONTAINER port (not the published host port).
- Compose creates one project network by default; services resolve each other by service name.

Gotcha: `localhost` inside a container is the container itself. App connecting to `localhost:5432` for Postgres fails; use `db:5432` (service name).
Gotcha: Binding the app to `127.0.0.1` inside the container makes it unreachable even with `-p`; bind `0.0.0.0` (`uvicorn --host 0.0.0.0`).
Gotcha: Published ports bypass host firewalls like ufw because Docker edits iptables directly; bind to 127.0.0.1 for internal-only services.
Gotcha: From a container to the host: `host.docker.internal` (Docker Desktop; on Linux add `--add-host=host.docker.internal:host-gateway`).

How interviewers probe it:
- "App can't reach DB in Compose, works locally." -> localhost vs service name; startup ordering; wrong network.
- "Difference between EXPOSE and -p?" -> metadata vs actual publishing.

---
## 6. Docker Compose

Compose describes a multi-container app in `compose.yaml` / `docker-compose.yml` (Compose Specification; the top-level `version:` key is obsolete and ignored by Compose v2 (check current docs)). Command is `docker compose` (v2 plugin), not `docker-compose` (v1, end of life).

Key concepts
- services, networks, volumes, configs, secrets at top level.
- `depends_on` alone = start order only. With `condition: service_healthy` it waits for the dependency's healthcheck to pass (other conditions: `service_started`, `service_completed_successfully`).
- `env_file:` loads variables into the container; `${VAR}` interpolation in the compose file reads the shell env and a `.env` file next to the compose file. They are different mechanisms.
- `profiles:` enable optional services; `docker compose up --build`; `restart: unless-stopped`.

Gotcha: `.env` is for compose-file interpolation (and default env for `env_file` if you point at it); it is NOT automatically injected into containers unless referenced via `environment:`/`env_file:`.
Gotcha: Without a healthcheck, `service_healthy` is invalid for that dependency; Postgres is "started" long before it accepts connections.
Gotcha: `docker compose up` does not rebuild on Dockerfile change unless `--build`.
Gotcha: Commit `.env.example`, never `.env`.

How interviewers probe it:
- "App crashes on first boot with connection refused to the DB" -> depends_on without health condition; also add app-level retry.
- "Compose vs Kubernetes?" -> single-host dev/test vs multi-node production orchestration (self-healing, scaling, rolling updates, service discovery at scale).

---
## 7. Complete example: FastAPI + Postgres

Layout

```
 myapp/
   Dockerfile
   docker-compose.yml
   .dockerignore
   .env                 (git-ignored; real values)
   .env.example
   pyproject.toml
   uv.lock
   alembic.ini
   alembic/             (migrations)
   src/app/main.py      (exposes FastAPI `app`, with GET /healthz and GET /readyz)
```

.dockerignore

```
.git
.venv
__pycache__/
*.pyc
.env
.pytest_cache
.mypy_cache
tests/
docs/
```

Dockerfile (multi-stage, non-root, exec-form CMD)

```dockerfile
# syntax=docker/dockerfile:1
# Pin base by tag; for strict reproducibility add @sha256:<digest> (check current docs for current tags)
FROM python:3.12-slim-bookworm AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1

# Pin uv version (check current docs for latest)
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv

WORKDIR /app

# 1) dependencies only (cached until pyproject/uv.lock change)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# 2) project source (changes often, so last)
COPY src ./src
COPY alembic.ini ./
COPY alembic ./alembic
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---------- runtime stage ----------
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# create unprivileged user with fixed UID (helps K8s runAsNonRoot checks)
RUN groupadd --system --gid 10001 app \
 && useradd  --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app
# copy only what runtime needs; no compilers, no uv, no build cache
COPY --from=builder --chown=app:app /app /app

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status==200 else 1)"]

# exec form -> uvicorn is PID 1 and receives SIGTERM
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

Notes: if you use psycopg with libpq you may need `libpq5` in the runtime stage (apt, one RUN, clean lists), or use `psycopg[binary]`. Paths like `/app/.venv` rely on uv creating the venv in the project dir (default). `--workers` in containers: often 1 worker per container and scale replicas instead (K8s HPA), tune to your CPU limit.

docker-compose.yml

```yaml
services:
  db:
    image: postgres:16-alpine           # pin major (check current docs for supported versions)
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data  # named volume: survives `down`, deleted by `down -v`
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s
    ports:
      - "127.0.0.1:5432:5432"            # optional: host access for psql, loopback only

  migrate:                               # one-shot job: run alembic then exit
    build: .
    command: ["alembic", "upgrade", "head"]
    env_file: .env
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
    depends_on:
      db:
        condition: service_healthy

  api:
    build:
      context: .
      target: runtime
    image: myapp-api:dev
    restart: unless-stopped
    env_file: .env
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully
    init: true                           # tini as PID 1: reaps zombies, forwards signals
    read_only: true
    tmpfs:
      - /tmp
    cap_drop: [ALL]
    security_opt:
      - no-new-privileges:true

volumes:
  pgdata:
```

.env.example

```
POSTGRES_USER=app
POSTGRES_PASSWORD=change-me-locally
POSTGRES_DB=appdb
```

Run and verify

```
 cp .env.example .env                       # edit values
 docker compose config                      # validate + show interpolated config
 docker compose up --build -d
 docker compose ps                          # db should be "healthy"; migrate "exited (0)"
 docker compose logs -f api                 # watch uvicorn start
 curl -i http://localhost:8000/healthz      # expect 200
 docker compose exec db psql -U app -d appdb -c '\dt'     # alembic_version + your tables exist
 docker compose exec api id                 # uid=10001 (non-root confirmed)
 docker compose down                        # keep data
 docker compose down -v                     # DESTROY data (named volume)
```

Alembic migration note
- Do not run migrations inside every app replica's startup in production: N replicas race. Run them as a one-shot job (Compose `migrate` service, K8s Job or Helm pre-upgrade hook / init step) before rolling out the new version.
- Make migrations backward compatible (expand/contract: add nullable column -> deploy code -> backfill -> enforce) so old and new pods coexist during a rolling update.

Gotcha: `read_only: true` breaks apps that write to unexpected paths; find them with logs, add tmpfs/volumes.
Gotcha: Special characters in DB password inside a URL must be percent-encoded.

How interviewers probe it:
- "Walk me through what happens on `docker compose up`" -> network created, volume created, db starts, healthcheck loops, migrate runs, api starts.
- "How do you do migrations safely with multiple replicas?" -> single job, backward-compatible schema changes.

---
## 8. Kubernetes architecture and the reconciliation loop

```
 CONTROL PLANE                                    WORKER NODE (many)
 +-------------------------------------+          +---------------------------------+
 | kube-apiserver  (REST front door,   |<-------->| kubelet   (runs pods, probes,   |
 |   authn/authz/admission, only one   |  watch   |            reports status)      |
 |   that talks to etcd)               |          | kube-proxy (Service virtual IPs |
 | etcd  (consistent KV store: ALL     |          |            via iptables/IPVS)   |
 |   cluster state)                    |          | container runtime (containerd / |
 | kube-scheduler (assigns Pods to     |          |            CRI-O) via CRI       |
 |   nodes: requests, taints, affinity)|          | CNI plugin (pod networking)     |
 | controller-manager (Deployment,     |          +---------------------------------+
 |   ReplicaSet, Node, Job controllers)|
 | cloud-controller-manager (LB, etc.) |
 +-------------------------------------+
```

Declarative model: you declare DESIRED state (YAML) -> apiserver stores in etcd -> controllers continuously compare desired vs actual and act. This is a level-triggered reconciliation loop: `observe -> diff -> act -> repeat`. This is why a deleted pod comes back and why `kubectl apply` is idempotent.

Life of `kubectl apply -f deployment.yaml`
1. kubectl -> apiserver (authn, authz/RBAC, admission, validation) -> persisted in etcd.
2. Deployment controller creates a ReplicaSet; ReplicaSet controller creates Pod objects (unscheduled).
3. Scheduler picks a node (filter then score) and binds the Pod.
4. kubelet on that node sees it, pulls the image, starts containers via the runtime, runs probes, reports status.
5. Endpoint/EndpointSlice controller adds ready pods behind Services; kube-proxy programs rules.

Gotcha: Kubernetes removed Docker (dockershim) in v1.24; runtime is containerd/CRI-O. Docker-built images still run (OCI images). (check current docs)
Gotcha: Losing etcd = losing the cluster state; back up etcd (managed services do this for you). Running pods keep running if the control plane is down briefly, but nothing reconciles.
Gotcha: The scheduler only places; the kubelet runs. "Pending" means scheduling failed; "ContainerCreating" means kubelet/runtime/image/volume stage.

How interviewers probe it:
- "What happens when you create a Deployment?" (above chain).
- "What if the scheduler is down?" -> existing pods continue; new pods stay Pending.
- "Why is K8s called declarative?" -> desired state + controllers vs imperative commands.

---
## 9. Core workload objects

```
 Deployment  --owns-->  ReplicaSet (one per template version)  --owns-->  Pods
 Service  --selects by labels-->  Pods (via EndpointSlices)
 Ingress  --routes HTTP host/path-->  Services   (needs an Ingress controller: nginx, traefik, cloud LB)
```

| Object | Purpose | Key notes |
|--------|---------|-----------|
| Pod | smallest deployable unit: 1+ containers sharing network namespace (one IP) and volumes | ephemeral, never "repaired", replaced; sidecars/init containers |
| ReplicaSet | keep N identical pods alive | rarely created directly |
| Deployment | declarative updates for stateless apps; rolling update + rollback | `kubectl rollout` |
| Service ClusterIP | stable virtual IP + DNS inside cluster (`svc.ns.svc.cluster.local`) | default |
| Service NodePort | opens a port (30000-32767 default) on every node | dev/on-prem; builds on ClusterIP |
| Service LoadBalancer | provisions cloud LB with external IP | builds on NodePort; one LB per Service = cost |
| Ingress | L7 HTTP(S) routing, TLS termination, host/path rules | requires a controller; Gateway API is the successor (check current docs) |
| ConfigMap | non-secret config (env vars, files) | |
| Secret | sensitive config | base64-encoded, NOT encrypted |
| Namespace | logical partition, scope for names, quotas, RBAC | not a security boundary by itself |
| StatefulSet | stable identity (pod-0, pod-1), stable storage per pod, ordered start | databases, Kafka; headless Service |
| DaemonSet | one pod per node | log agents, node exporters |
| Job / CronJob | run-to-completion / scheduled | migrations, batch; `restartPolicy: OnFailure/Never` |
| PV / PVC / StorageClass | PV = storage resource; PVC = request for it; StorageClass = dynamic provisioning | pod references PVC |

Secrets, honestly
- Secret data is base64: `echo cGFzcw== | base64 -d`. Encoding, not encryption. Anyone with `get secret` RBAC reads it.
- Hardening: enable etcd encryption at rest (EncryptionConfiguration / KMS provider), restrict RBAC, avoid secrets in env vars when possible (env leaks via `describe`, crash dumps, child processes; mounted files are safer), use external secret managers (External Secrets Operator, Vault, cloud secret managers, CSI secrets store driver).
- Never commit Secret YAML with real values; use SealedSecrets/SOPS or external operators.

Service mechanics
- Selector matches pod labels; mismatch -> "service has no endpoints".
- `port` (service) vs `targetPort` (container port) vs `nodePort`.
- Headless Service (`clusterIP: None`) returns pod IPs directly (StatefulSets).
- Only READY pods are in endpoints; failing readiness removes the pod from traffic without restarting it.

Gotcha: Deployment selector is immutable after creation; labels in `selector.matchLabels` must match template labels.
Gotcha: Pods are not durable - never rely on a pod IP; use a Service.
Gotcha: Changing a ConfigMap does not restart pods using it as env vars; mounted-file updates propagate eventually (not with subPath). Common trick: checksum annotation in pod template (Helm) or `kubectl rollout restart`.
Gotcha: StatefulSet PVCs are not deleted when the StatefulSet is deleted (by default).

How interviewers probe it:
- "ClusterIP vs NodePort vs LoadBalancer vs Ingress?" with when to use each.
- "Is a Secret secure?" -> no by default; list mitigations.
- "Deployment vs StatefulSet?" -> identity + storage + ordering.

---
## 10. Probes, resources, QoS, HPA, rollouts

Probes

| Probe | Question | On failure | Typical endpoint |
|-------|----------|-----------|------------------|
| startup | has the app finished booting? | kill/restart after failureThreshold; disables liveness/readiness until it passes | slow-starting apps (migrations, model loading) |
| liveness | is the process wedged/deadlocked? | kubelet RESTARTS container | `/healthz` (cheap, NO dependency checks) |
| readiness | can it serve traffic right now? | removed from Service endpoints (no restart) | `/readyz` (may check DB connectivity) |

Gotcha: A liveness probe that checks the database causes cascading restarts when the DB blips. Liveness = "am I alive", readiness = "can I serve".
Gotcha: Too-aggressive liveness (short timeout, no startupProbe) = restart loop on slow start, looks like CrashLoopBackOff.

Requests and limits

```
 resources:
   requests: cpu 250m, memory 256Mi   # used by SCHEDULER for placement; guaranteed minimum
   limits:   cpu 500m, memory 512Mi   # enforced by cgroups at runtime
 CPU over limit    -> THROTTLED (slow, not killed)
 Memory over limit -> OOMKilled (exit 137), pod restarts
```

QoS classes (set automatically)

| Class | Condition | Eviction order under node pressure |
|-------|-----------|-----------------------------------|
| Guaranteed | every container: requests == limits for cpu AND memory | last evicted |
| Burstable | at least one request/limit set, not Guaranteed | middle |
| BestEffort | no requests/limits at all | first evicted |

Gotcha: No requests -> scheduler packs pods blindly and HPA cannot compute CPU utilization (it is % of the REQUEST).
Gotcha: CPU limits can cause throttling even when the node is idle; many teams set memory limits but omit or loosen CPU limits (debated; know both sides).
Gotcha: 1 CPU = 1000m; Mi (mebibytes) vs M (megabytes).

HPA (HorizontalPodAutoscaler): scales replicas based on metrics (CPU/memory via metrics-server, custom/external metrics). Formula: `desired = ceil(current * currentMetric / targetMetric)`. Needs requests set, metrics-server installed, and has stabilization windows to avoid flapping. VPA adjusts requests; Cluster Autoscaler/Karpenter adds nodes for Pending pods.

Rolling updates and rollbacks
- Default strategy RollingUpdate with `maxSurge: 25%`, `maxUnavailable: 25%` (check current docs). New ReplicaSet scales up while old scales down; readiness gates progress.
- Zero-downtime needs: readiness probe, graceful shutdown (handle SIGTERM, `preStop` sleep for endpoint propagation), enough replicas, `PodDisruptionBudget` for voluntary disruptions.
- `kubectl rollout status deploy/api`, `kubectl rollout history deploy/api`, `kubectl rollout undo deploy/api [--to-revision=N]`, `kubectl set image deploy/api api=repo/app:1.4.3`.
- `Recreate` strategy = kill all then start (downtime; for singleton/incompatible versions).

How interviewers probe it:
- "Liveness vs readiness?" and "What happens if the DB is down and liveness checks it?"
- "Why is my pod OOMKilled but node has free memory?" -> container limit, cgroup.
- "Why isn't HPA scaling?" -> no requests, no metrics-server, target not exceeded, maxReplicas.
- "How do you roll back?" and "How is the deploy zero-downtime?"

---
## 11. RBAC basics and namespaces

```
 Subject (User / Group / ServiceAccount) --RoleBinding--> Role (verbs on resources, in a namespace)
 Subject --ClusterRoleBinding--> ClusterRole (cluster-wide or non-namespaced resources)
```

- Default deny: RBAC only adds permissions (additive, no deny rules).
- Every pod runs as a ServiceAccount (default one if unspecified); its token is mounted at `/var/run/secrets/kubernetes.io/serviceaccount`. Set `automountServiceAccountToken: false` if the pod does not call the API.
- Check: `kubectl auth can-i list pods --as system:serviceaccount:prod:api -n prod`.
- Principle of least privilege: namespace-scoped Roles, specific verbs, avoid `cluster-admin` and wildcards.

Gotcha: `Forbidden: ... cannot list resource "pods"` in app logs = missing Role/RoleBinding for its ServiceAccount.
Gotcha: Namespaces isolate names and RBAC/quota scope, but do NOT isolate network by default (add NetworkPolicy) and nodes are shared.

How interviewers probe it: "Difference between Role and ClusterRole?"; "How would you give a CI job permission to deploy only to staging?"

---
## 12. Full K8s manifests for the FastAPI app

API versions below are stable as of recent releases (check current docs).

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: myapp
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
  namespace: myapp
data:
  LOG_LEVEL: "info"
  POSTGRES_HOST: "postgres"        # Service name of DB (managed DB host in real prod)
  POSTGRES_DB: "appdb"
---
# Secret: created out-of-band; shown here only for shape. base64 is NOT encryption.
# Preferred: kubectl create secret generic api-secret -n myapp --from-literal=POSTGRES_PASSWORD='...'
# or External Secrets / SealedSecrets / SOPS. Never commit real values.
apiVersion: v1
kind: Secret
metadata:
  name: api-secret
  namespace: myapp
type: Opaque
stringData:
  POSTGRES_USER: app
  POSTGRES_PASSWORD: REPLACE_ME
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: myapp
  labels: { app: api }
spec:
  replicas: 3
  revisionHistoryLimit: 5
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }
  selector:
    matchLabels: { app: api }
  template:
    metadata:
      labels: { app: api }
    spec:
      automountServiceAccountToken: false
      terminationGracePeriodSeconds: 30
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        fsGroup: 10001
        seccompProfile: { type: RuntimeDefault }
      containers:
        - name: api
          image: registry.example.com/myapp/api:1.4.2   # pin tag; digest preferred: @sha256:...
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 8000
          envFrom:
            - configMapRef: { name: api-config }
          env:
            - name: POSTGRES_USER
              valueFrom: { secretKeyRef: { name: api-secret, key: POSTGRES_USER } }
            - name: POSTGRES_PASSWORD
              valueFrom: { secretKeyRef: { name: api-secret, key: POSTGRES_PASSWORD } }
          resources:
            requests: { cpu: 250m, memory: 256Mi }
            limits:   { memory: 512Mi }          # CPU limit omitted deliberately; add if your org requires it
          startupProbe:
            httpGet: { path: /healthz, port: http }
            periodSeconds: 3
            failureThreshold: 30                 # up to ~90s to boot
          livenessProbe:
            httpGet: { path: /healthz, port: http }
            periodSeconds: 10
            timeoutSeconds: 2
            failureThreshold: 3
          readinessProbe:
            httpGet: { path: /readyz, port: http }
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 3
          lifecycle:
            preStop:
              exec: { command: ["sleep", "5"] }  # let endpoints propagate before SIGTERM handling (needs sleep binary; slim images have it)
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: ["ALL"] }
          volumeMounts:
            - { name: tmp, mountPath: /tmp }
      volumes:
        - name: tmp
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: myapp
spec:
  type: ClusterIP
  selector: { app: api }          # must match pod template labels
  ports:
    - name: http
      port: 80
      targetPort: http            # container port name
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api
  namespace: myapp
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"   # controller-specific (check current docs)
spec:
  ingressClassName: nginx
  tls:
    - hosts: [api.example.com]
      secretName: api-tls          # e.g., issued by cert-manager
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api
                port: { number: 80 }
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api
  namespace: myapp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 70 }   # % of REQUEST
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api
  namespace: myapp
spec:
  minAvailable: 2
  selector:
    matchLabels: { app: api }
---
# Migration as a one-shot Job (run BEFORE rolling the Deployment; or Helm pre-upgrade hook)
apiVersion: batch/v1
kind: Job
metadata:
  name: api-migrate-142
  namespace: myapp
spec:
  backoffLimit: 2
  ttlSecondsAfterFinished: 600
  template:
    spec:
      restartPolicy: Never
      securityContext: { runAsNonRoot: true, runAsUser: 10001 }
      containers:
        - name: migrate
          image: registry.example.com/myapp/api:1.4.2
          command: ["alembic", "upgrade", "head"]
          envFrom:
            - configMapRef: { name: api-config }
          env:
            - name: POSTGRES_PASSWORD
              valueFrom: { secretKeyRef: { name: api-secret, key: POSTGRES_PASSWORD } }
```

Apply and verify

```
 kubectl apply -f k8s/                       # or kustomize: kubectl apply -k overlays/prod
 kubectl -n myapp rollout status deploy/api
 kubectl -n myapp get pods,svc,ingress,hpa
 kubectl -n myapp get endpointslices         # Service has ready backends?
 kubectl -n myapp port-forward svc/api 8080:80 & curl localhost:8080/healthz
 kubectl -n myapp top pods                   # needs metrics-server
 kubectl -n myapp rollout undo deploy/api    # rollback
```

Database in K8s: for production, a managed Postgres (RDS/Cloud SQL) is common; running Postgres yourself needs StatefulSet + PVC + backups + operator (CloudNativePG, Zalando) - mention trade-offs.

Gotcha: `readOnlyRootFilesystem: true` without an emptyDir for /tmp breaks many apps.
Gotcha: `runAsNonRoot: true` fails if the image's USER is a name (non-numeric) or root; use numeric `USER 10001`.
Gotcha: HPA with `replicas:` hard-coded in the Deployment and re-applied via CI will fight HPA; omit `replicas` when HPA manages it.
Gotcha: `maxUnavailable: 0, maxSurge: 1` needs spare capacity or new pods sit Pending.

How interviewers probe it: "Write a Deployment on a whiteboard" (labels/selector match, probes, resources, securityContext); "Where do secrets come from?"; "Why maxUnavailable 0?".

---
## 13. Debugging containers and pods

Docker

```
 docker ps -a                       # status, exit codes
 docker logs -f --tail 100 <c>      # stdout/stderr
 docker inspect <c> | jq '.[0].State'   # ExitCode, OOMKilled, Error, Health
 docker exec -it <c> sh             # shell in running container (slim images may lack bash)
 docker run --rm -it --entrypoint sh <image>   # container exits instantly? override entrypoint
 docker stats                       # live cpu/mem
 docker history <image>             # layers, sizes, leaked commands
 docker system df                   # disk usage;   docker system prune  # cleanup (careful)
```

Kubernetes workflow (always the same loop)

```
 1. kubectl get pods -n ns -o wide                    # STATUS, RESTARTS, node
 2. kubectl describe pod <p> -n ns                    # Events at bottom, Last State, Reason, Exit Code
 3. kubectl logs <p> -n ns [-c container] [--previous]   # --previous = the crashed instance
 4. kubectl get events -n ns --sort-by=.lastTimestamp
 5. kubectl exec -it <p> -n ns -- sh                  # poke around, curl, env, DNS (nslookup svc)
 6. kubectl port-forward svc/api 8080:80 -n ns        # test from laptop
 7. kubectl top pod / node                            # needs metrics-server
 8. kubectl debug -it <p> --image=busybox --target=<container>   # ephemeral debug container for distroless
 9. kubectl get deploy,rs,svc,endpointslices -n ns ; kubectl rollout history deploy/<d>
```

Decision table

| Symptom | Meaning | Likely causes | How to confirm / fix |
|---------|---------|---------------|----------------------|
| CrashLoopBackOff | container starts, exits, kubelet restarts with exponential backoff (up to 5 min) | app exception, bad config/env, missing secret, wrong command, failing liveness probe, OOM | `logs --previous`; `describe` Last State exit code; run image locally with same env |
| ImagePullBackOff / ErrImagePull | cannot pull image | typo in name/tag, tag missing, private registry without `imagePullSecrets`, rate limit, wrong arch, no network egress | `describe` events show pull error; verify with `docker pull`; create docker-registry secret |
| Pending | not scheduled (or PVC unbound) | insufficient cpu/mem (requests too large), taints without tolerations, nodeSelector/affinity mismatch, unbound PVC, quota | `describe` Events: `0/5 nodes available: ...`; fix requests, add nodes, check `kubectl get pvc` |
| ContainerCreating (stuck) | kubelet working on it | image pulling, volume mount failure (missing ConfigMap/Secret/PVC), CNI problem | `describe` events (MountVolume.SetUp failed) |
| OOMKilled, exit 137 | cgroup memory limit exceeded (137 = 128 + SIGKILL 9) | limit too low, memory leak, big payloads, too many workers | `describe` Reason OOMKilled; `top`; raise limit/fix leak/reduce workers |
| Exit 143 | SIGTERM (128+15) | normal shutdown signal | usually fine; check graceful handling |
| Exit 1 / 2 / 126 / 127 | app error / usage / not executable / command not found | bad command, missing binary, permission, wrong entrypoint | logs; check `command`/`args`, file perms, `exec format error` = wrong arch |
| Running but not Ready (0/1) | readiness probe failing | wrong path/port, app slow, dependency down, probe timeout too short | `describe` -> "Readiness probe failed: ..."; `port-forward` and curl the path |
| Service has no endpoints | no READY pods match selector | selector/labels mismatch, pods not ready, wrong namespace, targetPort mismatch | `kubectl get endpointslices`; compare `svc.spec.selector` with `pod --show-labels` |
| Ingress 502/503/404 | controller cannot reach backend / no rule | no endpoints, wrong service port, host/path mismatch, wrong ingressClass | controller logs; test Service via port-forward first |
| Evicted | node pressure (memory/disk) | BestEffort/Burstable pods exceeded, ephemeral storage | `describe node` conditions; set requests/limits |
| Terminating forever | finalizers or stuck node | finalizer not cleared, volume detach, node NotReady | `describe`, check finalizers (last resort `--force --grace-period=0`) |
| CreateContainerConfigError | config reference broken | missing ConfigMap/Secret key | `describe` event names the missing key |
| Cannot connect to DB from pod | network/DNS/credentials | wrong host, NetworkPolicy blocking, DNS (CoreDNS), wrong secret | `exec` + `nslookup`, `nc -zv host 5432`, check NetworkPolicy |

Forward-deployed engineer playbook (customer env, limited access)
1. Reproduce the symptom precisely (which pod, what error, since when, what changed?). Ask "what changed" first: image tag, config, secret rotation, node upgrade, quota.
2. Gather evidence read-only: `get`, `describe`, `logs --previous`, events. Save outputs; ask customers to paste them if you lack access.
3. Form hypothesis from the decision table; test the cheapest check first (events and exit code give 80% of answers).
4. Mitigate before root-causing if prod is down: `rollout undo`, scale up, raise limit temporarily - communicate each action.
5. Document: timeline, root cause, fix, prevention (probe, limit, alert).
Customer env quirks: air-gapped registries (mirror images, imagePullSecrets), corporate proxies (`HTTP_PROXY`/`NO_PROXY` on pods), custom CA certs (mount CA bundle), strict PodSecurity/admission policies rejecting your pod (read the admission error), restrictive NetworkPolicies/egress firewalls, older K8s versions (deprecated APIs), no `kubectl exec` allowed (use ephemeral debug or logs only), different ingress controllers.

Gotcha: `kubectl logs` shows the CURRENT container; for a crash loop you need `--previous`.
Gotcha: `kubectl describe` Events expire (~1 hour by default); check early or rely on log aggregation.
Gotcha: distroless/scratch images have no shell; use `kubectl debug` with an ephemeral container.
Gotcha: `CrashLoopBackOff` is a state not a cause; the exit code and previous logs are the cause.

How interviewers probe it:
- "A pod is in CrashLoopBackOff; walk me through it." (get -> describe -> logs --previous -> exit code -> reproduce).
- "Deploy succeeded but users get 503." -> readiness, endpoints, selector, ingress.
- "Pod OOMKilled, what do you do?" -> confirm limit vs usage, fix leak, tune workers, raise limit, add alert.

---
## 14. Container and K8s security basics

| Control | What / how |
|---------|-----------|
| Non-root | `USER 10001`; K8s `runAsNonRoot: true` |
| Read-only root filesystem | `readOnlyRootFilesystem: true` + emptyDir/tmpfs for writable paths |
| Drop capabilities | `capabilities.drop: [ALL]`, add back only what is needed (e.g., NET_BIND_SERVICE) |
| No privilege escalation | `allowPrivilegeEscalation: false`; never `privileged: true`, no hostPath/hostNetwork unless essential |
| Seccomp | `seccompProfile: RuntimeDefault` |
| Pod Security Admission | namespace labels enforce `restricted` / `baseline` / `privileged` profiles (PSP was removed in 1.25) (check current docs) |
| Secrets handling | not in image/ENV/ARG/git; K8s Secret + etcd encryption + RBAC, or external manager; rotate |
| Minimal base image | distroless / slim; fewer packages = fewer CVEs |
| Image scanning | `trivy image myapp:1.4.2` in CI; fail on HIGH/CRITICAL (also `grype`, Docker Scout) |
| Pin digests | `image@sha256:...`; admission policy to allow only pinned/signed images |
| Supply chain | generate SBOM (`syft`, `trivy sbom`; formats SPDX/CycloneDX), sign images (cosign/Sigstore), provenance attestations (SLSA), verify at admission (Kyverno/Gatekeeper/policy-controller), private trusted registry |
| NetworkPolicy | default-deny then allow specific ingress/egress (needs CNI that enforces: Calico, Cilium) |
| RBAC least privilege | scoped Roles, dedicated ServiceAccounts, disable token automount |
| Resource limits | prevents noisy neighbor / DoS |
| Runtime sandbox | gVisor / Kata for untrusted workloads |

Default-deny NetworkPolicy plus an allow rule

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny, namespace: myapp }
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-ingress-to-api, namespace: myapp }
spec:
  podSelector: { matchLabels: { app: api } }
  policyTypes: [Ingress]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels: { kubernetes.io/metadata.name: ingress-nginx }
      ports: [{ port: 8000 }]
# remember to also allow egress for DNS (UDP/TCP 53 to kube-dns) and to the database once egress is denied
```

Gotcha: NetworkPolicy objects do nothing if the CNI does not support them.
Gotcha: Default-deny egress breaks DNS - allow port 53 to kube-dns.
Gotcha: Scanning once at build is not enough; new CVEs appear for old images - rescan registry images regularly.
Gotcha: Mounting the Docker socket (`/var/run/docker.sock`) into a container = root on the host.
Gotcha: A distroless/pinned image still needs a patch process; pinned digests do not auto-update.

How interviewers probe it:
- "Harden this container" -> list from the table in priority order (non-root, drop caps, read-only fs, no secrets in image, scan, pin).
- "What is in an SBOM and why?" -> inventory of components for vulnerability/license tracking and incident response (e.g., log4shell style).
- "How would you stop pods from talking to each other?" -> NetworkPolicy default deny.

---
## 15. Putting it together: interview narratives

1. "Containerize and deploy a FastAPI service."
   Multi-stage Dockerfile, non-root, exec CMD, healthcheck, cached deps -> Compose locally with Postgres healthcheck -> push to registry with immutable tag/digest -> K8s Deployment + Service + Ingress + HPA, probes, resources, securityContext -> migrations as Job -> scan in CI.
2. "Production is returning 502s after a deploy."
   Check rollout status and events -> pods Ready? -> endpoints and selector -> readiness probe logs -> compare image/config diff -> rollback if impact ongoing -> root cause afterwards.
3. "Design for zero-downtime." Readiness + maxUnavailable 0 + preStop + SIGTERM handling + PDB + backward-compatible DB migrations + multiple replicas across zones (topology spread).
4. "Container vs VM; when not to use containers?" Need strong isolation, custom kernel, GPU/driver complexity, stateful systems with heavy ops (use managed services).

Labs (hands-on, 2-3h)
1. `unshare` a PID namespace; inspect `/sys/fs/cgroup` memory limit of a running container (`docker run -m 64m`) and trigger an OOM (exit 137).
2. Break the Dockerfile cache on purpose (COPY . first), measure, then fix ordering.
3. Run the section 7 stack; kill `db`, watch healthcheck; run `down` vs `down -v`.
4. kind or minikube: apply section 12; break each thing (bad image tag, wrong selector, failing readiness, tiny memory limit) and diagnose with the decision table.
5. `trivy image` your image; compare slim vs full base vulnerability counts.
