# Week 5 - Containers and Orchestration: Cheatsheet

Facts marked "(check current docs)" are version-dependent (K8s API versions, base image tags, compose spec details).

---
## Core one-liners

| Concept | One-liner |
|---------|-----------|
| Container | Isolated Linux process: namespaces (see) + cgroups (use) + overlayfs (files), shared host kernel |
| Namespace types | pid, net, mnt, uts, ipc, user, cgroup |
| cgroups | Limit cpu/mem/pids/io; mem over limit -> OOM kill (137); cpu over limit -> throttle |
| Image | Ordered read-only layers + config; content-addressed by sha256 |
| Container | Image + thin writable layer; writes lost on `rm` |
| Tag vs digest | Tag mutable pointer; digest immutable identity |
| Cache rule | Change a layer -> all later layers rebuild; put volatile COPY last |
| Exec vs shell CMD | Exec form makes app PID 1, gets SIGTERM; shell form wraps in sh, signals lost |
| ENTRYPOINT vs CMD | ENTRYPOINT = executable, CMD = default args; K8s `command`=ENTRYPOINT, `args`=CMD |
| EXPOSE | Documentation only; `-p` actually publishes |
| Volume / bind / tmpfs | Managed persistent / host path / RAM |
| Compose depends_on | Order only, unless `condition: service_healthy` |
| localhost in container | The container itself; use service name |
| Pod | 1+ containers, shared IP and volumes; ephemeral |
| Deployment | Manages ReplicaSets for stateless apps; rolling update + rollback |
| StatefulSet | Stable identity + per-pod storage + ordered rollout |
| Service | Stable virtual IP/DNS selecting READY pods by labels |
| Ingress | L7 host/path routing; needs a controller |
| ConfigMap / Secret | Config / sensitive config (base64, NOT encrypted) |
| Liveness | Failing -> container restart |
| Readiness | Failing -> removed from endpoints, no restart |
| Startup | Failing -> restart; protects slow boot |
| Requests / limits | Scheduling guarantee / runtime ceiling |
| QoS | Guaranteed (req==lim) > Burstable > BestEffort (evicted first) |
| HPA | desired = ceil(current * currentMetric / target); needs requests + metrics-server |
| Job / CronJob | Run-to-completion / scheduled |
| PV / PVC / StorageClass | Storage / request for storage / dynamic provisioner |
| RBAC | Role(Binding) namespaced; ClusterRole(Binding) cluster-wide; additive only |

---
## Control plane and node

| Component | Role |
|-----------|------|
| kube-apiserver | REST front door, authn/authz/admission, only one talking to etcd |
| etcd | Consistent KV store of all cluster state; back it up |
| kube-scheduler | Picks node for unscheduled pods (filter, score) |
| controller-manager | Runs controllers (Deployment, ReplicaSet, Node, Job, EndpointSlice) |
| kubelet | Node agent: starts containers, runs probes, reports status |
| kube-proxy | Programs Service routing (iptables/IPVS) |
| container runtime | containerd / CRI-O via CRI (dockershim removed in 1.24) |
| CNI | Pod networking plugin (Calico, Cilium, Flannel); NetworkPolicy needs support |

---
## Failure decision table

| Symptom | First check | Common causes |
|---------|-------------|---------------|
| CrashLoopBackOff | `logs --previous`, `describe` exit code | app error, bad env/secret, wrong command, liveness too strict, OOM |
| ImagePullBackOff | `describe` events | bad tag/name, no imagePullSecret, rate limit, arch mismatch |
| Pending | `describe` events (`0/N nodes available`) | requests too big, taints, affinity, unbound PVC, quota |
| ContainerCreating | `describe` events | missing ConfigMap/Secret/PVC, CNI, slow pull |
| OOMKilled / 137 | `describe` Reason | limit too low, leak, too many workers |
| Exit 143 | - | SIGTERM (normal stop) |
| Exit 127 / 126 | logs | command not found / not executable |
| exec format error | image arch | built arm64, running amd64 |
| Running, not Ready | probe events, port-forward + curl | wrong probe path/port, dep down, timeout |
| Service no endpoints | `get endpointslices`, `--show-labels` | selector mismatch, pods not ready, wrong ns/targetPort |
| 502/503 from Ingress | controller logs, svc via port-forward | no endpoints, wrong port, ingressClass |
| Evicted | `describe node` | node memory/disk pressure, BestEffort pods |
| CreateContainerConfigError | `describe` event | missing key in ConfigMap/Secret |
| Forbidden in app logs | RBAC | missing Role/RoleBinding for ServiceAccount |

Exit code math: 128 + signal. 137 = SIGKILL(9), 143 = SIGTERM(15), 139 = SIGSEGV(11).

---
## Memorize

- Container = process + namespaces + cgroups + overlayfs; shared kernel.
- Order Dockerfile layers by change frequency; deps before source.
- Never put secrets in layers/ENV/ARG; deleting later does not help.
- Non-root numeric USER, exec-form CMD, HEALTHCHECK, `.dockerignore`, multi-stage, pinned versions.
- `depends_on` + `service_healthy`; DB by service name; bind `0.0.0.0`.
- `down -v` destroys named volumes.
- K8s = declarative desired state + reconciliation loops; apiserver is the only etcd client.
- Pending = scheduling problem; ContainerCreating = kubelet/volume/image problem.
- Liveness = restart; readiness = traffic gate; liveness must not check dependencies.
- Memory over limit = 137 OOMKilled; CPU over limit = throttled.
- Secrets are base64, not encrypted: etcd encryption + RBAC + external manager.
- Migrations as a one-shot Job, backward-compatible schema changes.
- `kubectl logs --previous` for crash loops; `describe` events first.
- Selector must match labels; no endpoints = label/readiness problem.
- Harden: non-root, read-only rootfs, drop ALL caps, no privilege escalation, seccomp, NetworkPolicy default-deny (allow DNS), scan with trivy, pin digests, SBOM, sign images.
- FDE habit: ask "what changed?", read-only evidence first, mitigate (rollback) before root cause, document.

---
## Docker command reference

| Task | Command |
|------|---------|
| Build | `docker build -t app:1.0 .` ; multi-arch `docker buildx build --platform linux/amd64,linux/arm64 -t repo/app:1.0 --push .` |
| Build with secret | `docker build --secret id=tok,src=tok.txt .` (Dockerfile: `RUN --mount=type=secret,id=tok ...`) |
| Run | `docker run -d --name api -p 8000:8000 --env-file .env app:1.0` |
| Run limits | `docker run -m 256m --cpus 1 --read-only --tmpfs /tmp --cap-drop ALL app` |
| List | `docker ps -a` ; `docker images` |
| Logs | `docker logs -f --tail 100 api` |
| Inspect state | `docker inspect api --format '{{.State.ExitCode}} {{.State.OOMKilled}}'` |
| Shell | `docker exec -it api sh` ; `docker run --rm -it --entrypoint sh app:1.0` |
| Stats | `docker stats` |
| Layers | `docker history app:1.0` |
| Volumes | `docker volume ls` ; `docker volume rm pgdata` |
| Networks | `docker network ls` ; `docker network inspect <net>` |
| Cleanup | `docker system prune` (careful) ; `docker system df` |
| Push | `docker tag app:1.0 reg/app:1.0 && docker push reg/app:1.0` |
| Digest | `docker buildx imagetools inspect reg/app:1.0` |
| Scan | `trivy image app:1.0` ; SBOM `syft app:1.0` / `trivy image --format cyclonedx app:1.0` |

---
## Compose command reference

| Task | Command |
|------|---------|
| Validate / show config | `docker compose config` |
| Up (build, detached) | `docker compose up --build -d` |
| Status | `docker compose ps` |
| Logs | `docker compose logs -f api` |
| Exec | `docker compose exec db psql -U app -d appdb` |
| One-off | `docker compose run --rm api alembic upgrade head` |
| Stop, keep data | `docker compose down` |
| Stop, delete volumes | `docker compose down -v` |
| Rebuild one | `docker compose build api` |

Compose notes: `version:` key obsolete in Compose Spec (check current docs); `.env` = interpolation, `env_file` = container env; healthcheck states: starting, healthy, unhealthy.

---
## kubectl command reference

| Task | Command |
|------|---------|
| Context / namespace | `kubectl config get-contexts` ; `kubectl config use-context X` ; `kubectl config set-context --current --namespace=myapp` |
| Apply / delete | `kubectl apply -f k8s/` ; `kubectl apply -k overlays/prod` ; `kubectl delete -f k8s/` |
| List | `kubectl get pods -n ns -o wide` ; `kubectl get all -n ns` ; `kubectl get pods --show-labels` |
| Describe (events) | `kubectl describe pod P -n ns` |
| Logs | `kubectl logs P -n ns -c C -f` ; `--previous` ; `--tail 100` ; `-l app=api --all-containers` |
| Exec | `kubectl exec -it P -n ns -- sh` |
| Ephemeral debug | `kubectl debug -it P --image=busybox --target=C` |
| Port-forward | `kubectl port-forward svc/api 8080:80 -n ns` |
| Events | `kubectl get events -n ns --sort-by=.lastTimestamp` |
| Metrics | `kubectl top pod -n ns` ; `kubectl top node` |
| Endpoints | `kubectl get endpointslices -n ns` |
| Rollout | `kubectl rollout status deploy/api` ; `history` ; `undo` ; `restart` |
| Update image | `kubectl set image deploy/api api=repo/app:1.4.3` |
| Scale | `kubectl scale deploy/api --replicas=5` |
| YAML out | `kubectl get deploy api -o yaml` ; `kubectl explain deployment.spec.strategy` |
| Dry run / diff | `kubectl apply -f x.yaml --dry-run=server` ; `kubectl diff -f x.yaml` |
| Create secret | `kubectl create secret generic s --from-literal=K=V -n ns` |
| Decode secret | `kubectl get secret s -o jsonpath='{.data.K}' \| base64 -d` |
| RBAC check | `kubectl auth can-i list pods --as system:serviceaccount:ns:sa -n ns` |
| Node issues | `kubectl describe node N` ; `kubectl cordon N` ; `kubectl drain N --ignore-daemonsets` |
| Wait | `kubectl wait --for=condition=available deploy/api --timeout=120s` |
| Local cluster | `kind create cluster` ; `minikube start` |

---
## Key manifest values and defaults

| Item | Value |
|------|-------|
| Deployment/ReplicaSet apiVersion | `apps/v1` |
| Service / ConfigMap / Secret / Pod | `v1` |
| Ingress | `networking.k8s.io/v1` |
| HPA | `autoscaling/v2` |
| PDB | `policy/v1` |
| Job / CronJob | `batch/v1` |
| NetworkPolicy | `networking.k8s.io/v1` |
| (all above: check current docs for deprecations) | |
| Default rolling update | maxSurge 25%, maxUnavailable 25% (check current docs) |
| Default grace period | 30s (K8s), 10s (docker stop) |
| NodePort range | 30000-32767 |
| imagePullPolicy default | `Always` for `latest`/no tag, else `IfNotPresent` |
| CPU units | 1 = 1000m; memory Mi/Gi (binary) vs M/G (decimal) |
| Pod DNS / Service DNS | `svc.ns.svc.cluster.local` |
| PSP | removed in 1.25; use Pod Security Admission |

---
## Hardened securityContext snippet

```yaml
securityContext:             # pod level
  runAsNonRoot: true
  runAsUser: 10001
  seccompProfile: { type: RuntimeDefault }
containers:
  - securityContext:         # container level
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities: { drop: ["ALL"] }
```

## Dockerfile skeleton

```dockerfile
FROM python:3.12-slim AS builder      # check current docs for tags
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev
COPY src ./src
FROM python:3.12-slim AS runtime
COPY --from=builder --chown=10001:10001 /app /app
USER 10001
HEALTHCHECK CMD ["python","-c","..."]
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
```
