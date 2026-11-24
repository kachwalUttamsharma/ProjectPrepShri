# Week 4 Cheatsheet - Git, Collaboration, CI/CD

Version-dependent items are marked "(check current docs)".

## Concepts

| Concept | One-liner |
|---|---|
| blob / tree / commit / tag | file bytes / directory listing / snapshot + parents + message / named pointer object |
| Content-addressed | object name = hash of content; same content stored once; immutable |
| DAG | commits point to parents; no cycles |
| Branch | file holding one commit hash (movable pointer) |
| HEAD | current branch (symbolic ref) or commit (detached) |
| Working tree / index / repo | files on disk / staged next commit / committed history |
| Remote-tracking ref | `origin/main` = local cache of remote branch; updated by fetch |
| fetch vs pull | fetch updates origin/*; pull = fetch + merge (or rebase) |
| Fast-forward | branch pointer just moves; no merge commit |
| Merge commit | commit with two parents; preserves history |
| Rebase | replay commits on a new base as new commits (new hashes) |
| Squash merge | whole PR becomes one commit on target |
| Golden rule | do not rewrite shared/pushed history |
| force-with-lease | force push only if remote is where you last saw it |
| Reflog | local history of where HEAD/branches pointed; recovery net |
| Detached HEAD | HEAD at a commit, not a branch; make a branch before leaving |

## Undo matrix

| Goal | Command |
|---|---|
| Unstage file | `git restore --staged f` |
| Discard working edits | `git restore f` (irreversible) |
| Amend last commit (local) | `git commit --amend` |
| Undo commit, keep staged | `git reset --soft HEAD~1` |
| Undo commit, keep unstaged | `git reset --mixed HEAD~1` |
| Undo commit and changes | `git reset --hard HEAD~1` |
| Undo pushed commit | `git revert <sha>` |
| Undo merge commit | `git revert -m 1 <merge-sha>` |
| Recover lost commit | `git reflog` then `git reset --hard <sha>` or `git branch rescue <sha>` |
| Backport one commit | `git cherry-pick -x <sha>` |

## Strategies and delivery

| Topic | One-liner |
|---|---|
| Trunk-based | short-lived branches, merge to main daily, feature flags, always releasable |
| GitHub flow | feature branch -> PR -> merge -> deploy |
| Gitflow | develop/release/hotfix branches; for versioned products; heavy |
| Feature flag | deploy != release; owner + expiry; remove after rollout |
| Monorepo | atomic changes, shared tooling; needs scalable build/CI |
| Polyrepo | clear ownership; version skew and cross-repo pain |
| CI | merge often, automated build/test on every push |
| Continuous delivery | always releasable; manual prod approval |
| Continuous deployment | every green build auto-deploys |
| Rolling | gradual replace; mixed versions; no extra capacity |
| Blue-green | two envs, flip traffic; instant rollback; 2x capacity |
| Canary | small % first, watch metrics, expand |
| Expand/contract | add new -> dual write -> backfill -> switch reads -> drop old later |
| GitOps | Git = desired state; Argo CD/Flux reconcile; deploy = merge, rollback = revert |
| SemVer | MAJOR breaking / MINOR feature / PATCH fix |
| Artifact | build once, deploy same immutable image by digest |
| OIDC | short-lived cloud creds via signed job token; needs `id-token: write` |

## GitHub Actions essentials (check current docs for versions and labels)

| Item | Note |
|---|---|
| `permissions: contents: read` | least-privilege default at workflow top; escalate per job |
| Pin actions | full commit SHA + version comment; tags are mutable |
| `ubuntu-latest` vs `ubuntu-24.04` | latest floats; pin label for reproducibility (check current docs) |
| `actions/checkout@v4`, `setup-python@v5` | example versions (check current docs) |
| `docker/setup-buildx-action@v3`, `login-action@v3`, `metadata-action@v5`, `build-push-action@v6` | example versions (check current docs) |
| `services:` + `--health-cmd` | DB container with readiness wait |
| `needs:` / `if:` | job ordering and conditions |
| `environment:` | protection rules, approvals, scoped secrets |
| `concurrency:` | cancel stale PR runs; never cancel deploys |
| `GITHUB_TOKEN` | auto, short-lived; `packages: write` to push to GHCR |
| `pull_request_target` | runs with secrets; never check out untrusted PR code with it |
| Script injection | pass `${{ ... }}` untrusted values through `env:`, not inline `run:` |
| Cache | key on lockfile hash; `cache-from/to type=gha` for Docker layers |

## Memorize

- A commit is a snapshot; a branch is a pointer; rebase = new hashes.
- Shared branch: revert, never reset/force. Private branch: rebase, amend, force-with-lease.
- Reset: soft keeps staged, mixed keeps unstaged, hard destroys working tree.
- Reflog saves committed work (local, ~30-90 days; check current docs). Uncommitted work is gone.
- During rebase, ours/theirs are swapped.
- Bisect run exit codes: 0 good, 1-127 bad, 125 skip.
- Secret committed = rotate first, scrub history second.
- Small PRs; describe what/why/test/risk/rollback; label nit vs blocking.
- Build once, deploy the same digest everywhere; fail fast; gate prod with an environment.
- Backward-compatible migrations (expand/contract) are what make rollback possible.
- Pin actions to SHAs, least-privilege permissions, OIDC over stored cloud keys.
- Local hooks are bypassable; re-run the same checks in CI.

## Command reference

```
# inspect
git status -sb ; git log --oneline --graph --all ; git diff [--staged]
git show <sha>[:path] ; git blame -L 10,20 f ; git log -S"text" ; git log -p -- path
git cat-file -t|-p <hash> ; git ls-tree HEAD ; git rev-parse HEAD
git reflog ; git describe --tags

# branch / sync
git switch -c feat ; git switch - ; git branch -d|-D feat
git fetch --prune ; git pull --rebase ; git push -u origin feat
git push --force-with-lease

# integrate
git merge [--no-ff|--squash] feat ; git merge --abort
git rebase main ; git rebase -i HEAD~4 ; git rebase -i --autosquash main
git rebase --onto newbase oldbase feat ; git rebase --continue|--abort
git cherry-pick [-x] <sha> ; git cherry-pick --continue|--abort
git commit --fixup <sha>

# undo
git restore f ; git restore --staged f ; git restore --source=<sha> f
git reset --soft|--mixed|--hard <ref> ; git revert [-m 1] <sha> ; git clean -fdn
git commit --amend

# stash
git stash push -m msg [-u] ; git stash list ; git stash pop|apply|drop

# bisect
git bisect start ; git bisect bad ; git bisect good <ref> ; git bisect run <cmd> ; git bisect reset

# conflicts
git diff --name-only --diff-filter=U ; git checkout --ours|--theirs f ; git mergetool
git config --global rerere.enabled true
git config --global merge.conflictstyle zdiff3      # Git 2.35+ (check current docs)

# tags
git tag -a v1.2.0 -m "msg" ; git push origin v1.2.0 ; git tag -d v1.2.0

# ignore / hooks
git rm --cached f ; git check-ignore -v path ; git config core.hooksPath .githooks
pre-commit install ; pre-commit run --all-files ; pre-commit autoupdate
```
