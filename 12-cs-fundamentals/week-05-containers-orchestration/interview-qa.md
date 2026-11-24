# Week 5 - Containers and Orchestration: Interview Q&A

Practice: answer out loud in 30-60 seconds first, then compare.

Facts marked "(check current docs)" are version-dependent.

---

**1. What is a container, and how is it different from a VM?**
A container is a normal Linux process isolated by namespaces (pid, net, mnt, uts, ipc, user), limited by cgroups (cpu, memory, pids), and given a layered overlay root filesystem. It shares the host kernel. A VM runs a full guest OS and kernel on a hypervisor. Containers start in ms-seconds and are MBs; VMs are heavier but have stronger isolation. For untrusted code, add gVisor/Kata/Firecracker.

**2. What do namespaces and cgroups each do?**
Namespaces limit what a process can SEE (its own PIDs, network stack, mounts, hostname, users). Cgroups limit what it can USE (CPU shares/quota, memory, process count, IO). Memory over the cgroup limit triggers the OOM killer (exit 137); CPU over limit is throttled.

**3. Explain image layers and why instruction order matters.**
Each filesystem-changing Dockerfile instruction creates a read-only layer; layers are cached and shared. If a layer changes, all later layers rebuild. So put rarely changing steps first (base, system packages, dependency manifests and install) and frequently changing source last. Example: copy pyproject/uv.lock and install deps before `COPY src`.

**4. Tag vs digest? Why not use `latest`?**
A tag is a mutable pointer; a digest (`@sha256:...`) is the immutable content hash. `latest` is just a default name, not "newest", and can change underneath you, so deploys are not reproducible and rollbacks are ambiguous. Pin a version tag at least, a digest for strict reproducibility and supply-chain control, and automate bumps with Renovate/Dependabot.

**5. How do multi-stage builds help? Show the idea.**
Build in a fat stage (compilers, uv/pip, build deps) and copy only the resulting venv/artifacts into a slim runtime stage. Result: smaller image, fewer CVEs, no build tools or caches for an attacker. `FROM python:3.12-slim AS builder` ... `FROM python:3.12-slim AS runtime` + `COPY --from=builder /app /app` (check current docs for tags).

**6. Why exec-form CMD, and what is the PID 1 problem?**
Exec form `CMD ["uvicorn", ...]` makes the app PID 1 so it receives SIGTERM directly. Shell form wraps it in `sh -c`, which does not forward signals, so `docker stop`/K8s waits out the grace period then SIGKILLs (slow, ungraceful shutdown). PID 1 also gets no default signal handlers and must reap zombies; use `--init`/tini if the app spawns children or ignores signals.

**7. List the main Dockerfile best practices.**
Slim pinned base; `.dockerignore`; dependency-first layer ordering with cache mounts; multi-stage; non-root numeric USER; exec-form CMD; HEALTHCHECK; no secrets in layers (use BuildKit secret mounts); one process per container; log to stdout; combine apt update/install/cleanup in one RUN; scan the image.

**8. A secret was added in one layer and deleted in the next. Is it safe?**
No. Layers are additive; the earlier layer still contains it and anyone with the image can extract it (`docker history`, `docker save`). ENV/ARG values are also stored in image metadata. Use `RUN --mount=type=secret` at build time and inject runtime secrets via the orchestrator; rotate anything that leaked.

**9. Volumes vs bind mounts vs tmpfs?**
Volumes are Docker-managed persistent storage (best for DB data, portable). Bind mounts map a host path in (good for dev hot reload; host-specific, permission pitfalls, hides image contents). tmpfs is RAM-only, non-persistent (scratch or sensitive temp data, handy with a read-only rootfs). The container writable layer is ephemeral and slower. In K8s the equivalents are PVC, hostPath (avoid), and emptyDir.

**10. How does Docker networking work? Why does `localhost:5432` fail in my app container?**
Containers on a user-defined bridge get private IPs and automatic DNS by service/container name; outbound is NAT'd and inbound requires port publishing (`-p host:container`). `localhost` inside a container is the container itself, so connect to the DB by service name (`db:5432`). Also bind the app to `0.0.0.0`, not `127.0.0.1`. `EXPOSE` is documentation only.

**11. In Compose, how do you make the API wait for Postgres properly?**
Give `db` a healthcheck (`pg_isready`) and use `depends_on: db: condition: service_healthy`. Plain `depends_on` only orders startup, not readiness. Still add retry/backoff in the app since DBs can restart later. Run Alembic as a one-shot service with `service_completed_successfully`, not in each replica.

**12. Walk through the Kubernetes architecture.**
Control plane: kube-apiserver (single front door; authn/authz/admission; only component that talks to etcd), etcd (consistent store of all state), scheduler (assigns pods to nodes by requests, taints, affinity), controller-manager (Deployment/ReplicaSet/Node/Job controllers). Node: kubelet (runs pods, probes), kube-proxy (Service routing rules), container runtime (containerd/CRI-O via CRI), plus a CNI plugin for pod networking.

**13. What is the reconciliation loop and why is K8s "declarative"?**
You submit desired state; controllers constantly observe actual state, diff it against desired, and act to converge, forever. That is why deleted pods come back, why `apply` is idempotent, and why systems self-heal. Contrast with imperative "run this command once".

**14. What happens when you run `kubectl apply` on a Deployment?**
kubectl calls the apiserver (authn, RBAC, admission, validation) which persists to etcd. Deployment controller creates a ReplicaSet; ReplicaSet controller creates Pods; scheduler binds each Pod to a node; kubelet pulls the image and starts containers, runs probes, reports status; once Ready, pods join Service endpoints and kube-proxy/the dataplane routes traffic.

**15. ClusterIP vs NodePort vs LoadBalancer vs Ingress?**
ClusterIP: stable internal virtual IP and DNS (default). NodePort: opens a high port on every node (builds on ClusterIP). LoadBalancer: provisions a cloud L4 LB (builds on NodePort; one per Service costs money). Ingress: L7 HTTP(S) routing by host/path with TLS to many Services behind one entry point, requires an Ingress controller (Gateway API is the newer successor (check current docs)).

**16. Liveness vs readiness vs startup probes? Common mistakes?**
Startup: gates the others while the app boots. Liveness: failing restarts the container (detect deadlock). Readiness: failing removes the pod from Service endpoints without restart. Mistakes: liveness that checks the DB (cascading restarts when DB blips), no startup probe for slow apps (restart loop), identical probes for liveness and readiness, timeouts too short.

**17. Explain requests, limits, and QoS. What happens when each is exceeded?**
Requests drive scheduling and are the guaranteed minimum; limits are enforced by cgroups. Exceed CPU limit: throttled. Exceed memory limit: OOMKilled (137). QoS: Guaranteed (requests == limits for all), Burstable, BestEffort; under node pressure BestEffort is evicted first. HPA's CPU utilization is relative to the request, so missing requests breaks autoscaling.

**18. Is a Kubernetes Secret secure? How do you handle secrets properly?**
Not by default: values are base64-encoded, which is encoding not encryption, and anyone with read RBAC (or etcd access) sees them. Harden: etcd encryption at rest/KMS, tight RBAC, prefer mounted files over env vars, external secret managers (Vault, cloud KMS/Secrets Manager via External Secrets or CSI), SealedSecrets/SOPS for GitOps, rotation, never bake secrets into images.

**19. A pod is in CrashLoopBackOff. How do you debug it? Also ImagePullBackOff, Pending, and a Service with no endpoints?**
CrashLoopBackOff: `kubectl get pod`, `describe` (exit code, Last State, events), `logs --previous`, reproduce locally with same env; causes: app error, bad config/secret, wrong command, failing liveness, OOM (137). ImagePullBackOff: wrong name/tag, missing imagePullSecret, registry auth/rate limit, wrong arch. Pending: `describe` events - insufficient resources, taints, affinity, unbound PVC. No endpoints: Service selector does not match pod labels, pods not Ready, wrong namespace or targetPort; check `get endpointslices` and `--show-labels`.

**20. How do you harden a container and a K8s deployment?**
Image: minimal/slim base, pinned digest, multi-stage, scan with trivy in CI, SBOM and cosign signing, no secrets. Runtime: non-root numeric UID, `readOnlyRootFilesystem`, drop ALL capabilities, `allowPrivilegeEscalation: false`, seccomp RuntimeDefault, no privileged/hostPath/docker.sock. Cluster: Pod Security Admission (restricted), least-privilege RBAC and no token automount, default-deny NetworkPolicy (needs an enforcing CNI), resource limits, admission policies verifying signed images. In a customer environment, expect to comply with their policies and diagnose their admission rejections.
