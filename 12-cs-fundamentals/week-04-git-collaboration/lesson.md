# Week 4 - Git, Collaboration, Code Review, and CI/CD

Time budget: ~7-8 hrs. Read lesson (3h), do sandbox exercises (2h), Q&A aloud (2h), cheatsheet (1h).
Facts marked "(check current docs)" are version-dependent (Git flags, GitHub Actions action versions, runner labels, limits); verify before quoting in an interview.

---
## 1. Mental model: Git is a content-addressed object store

```
 .git/objects  (immutable, named by hash of content)

   commit  --> tree (root dir snapshot) --> blob (file bytes)
      |                |-- tree (subdir) --> blob ...
      |-- parent commit(s)
      |-- author, committer, message

   tag (annotated) --> points at a commit (or any object), has its own message/signature

   Commits form a DAG (directed acyclic graph), edges point to PARENTS:

        A <-- B <-- C <-- F          main
              ^
              +---- D <-- E          feature
```

| Object | What it stores | Name |
|---|---|---|
| blob | file contents only (no filename) | SHA of content |
| tree | list of (mode, name, blob/tree hash) = a directory | SHA of listing |
| commit | tree hash, parent hash(es), author, message | SHA of all that |
| tag | pointer + tagger + message (annotated tags) | SHA |

Key points
- Same content -> same hash -> stored once (dedup). Change one byte -> new blob -> new tree(s) -> new commit hash up the chain. History cannot be edited, only replaced with new commits.
- A commit is a SNAPSHOT (full tree), not a diff. Diffs are computed on demand. Packfiles delta-compress for storage.
- SHA-1 is the default hash; SHA-256 repos are supported but not widely deployed (check current docs).
- Branch = a tiny file holding a commit hash (a movable pointer). Creating a branch is O(1).
- HEAD = pointer to the current branch (symbolic ref) or directly to a commit (detached HEAD).
- Three areas:

```
 working tree  --git add-->  index (staging)  --git commit-->  repository (.git)
   (files on disk)        (proposed next commit)               (history)
        ^                                                          |
        +------------- git restore / checkout / reset -------------+

 remotes: origin/main is a remote-tracking ref = your local cache of where origin's main was
   git fetch  -> updates origin/* refs only (safe)
   git pull   -> fetch + merge (or fetch + rebase with --rebase)
   git push   -> uploads commits, moves the remote branch
```

Inspect it yourself (sandbox, Section 15, Exercise A):
```
git cat-file -t <hash>      # type: blob/tree/commit/tag
git cat-file -p <hash>      # pretty-print contents
git ls-tree HEAD            # the root tree
git rev-parse HEAD main     # resolve names to hashes
```

Gotcha: "git add" stages the file content AS OF that moment. Edit again after add and the index holds the old version; `git status` shows the file in both staged and unstaged lists.
Gotcha: A commit not reachable from any branch/tag/reflog is eventually garbage collected (reflog entries default ~90 days reachable, ~30 days unreachable; check current docs).

How interviewers probe it: "What is a branch, really?" (a pointer file). "What happens on commit?" (write blobs/trees, new commit with parent = HEAD, move current branch). "Why is rebase rewriting history?" (new commits, new hashes).

---
## 2. Merge vs rebase

```
 Start:            A--B--C        main
                      \
                       D--E       feature

 Fast-forward (main has not moved; just move the pointer):
   git switch main; git merge feature
                   A--B--C--D--E  main, feature

 Merge commit (both moved; 2-parent commit, history preserved):
                   A--B--C-------M   main
                      \         /
                       D-------E     feature
   (use --no-ff to force M even when FF is possible)

 Rebase (replay D,E on top of C as NEW commits D',E'):
   git switch feature; git rebase main
                   A--B--C--D'--E'   feature      (then FF-merge main)
```

| Strategy | History shape | Pros | Cons |
|---|---|---|---|
| Merge commit | non-linear, true history | non-destructive, safe on shared branches, easy revert of whole merge (`revert -m 1`) | noisy graph |
| Rebase + FF | linear | clean log, easy bisect | rewrites commits, conflicts replayed per commit |
| Squash merge | one commit per PR on main | clean main, WIP commits vanish; trivial revert | loses granular history; branch must be deleted (its commits are not ancestors of main) |

Golden rule: never rebase (or amend, or reset) commits that others have based work on, i.e. shared/pushed history on public branches. Rebase your private feature branch freely.

Safe force push: `git push --force-with-lease` refuses if the remote branch moved since your last fetch. Plain `--force` can silently destroy a teammate's commits. Even better: `--force-with-lease --force-if-includes` (check current docs).

```
git pull --rebase            # replay your local commits atop upstream (avoids pointless merge bubbles)
git config --global pull.rebase true     # or pull.ff only to refuse accidental merges
git merge --abort / git rebase --abort   # bail out of a messy conflict
```

Gotcha: After rebasing a branch you already pushed, push needs force (hashes changed). With --force-with-lease only.
Gotcha: Squash-merge then keep working on the same feature branch -> Git sees the old commits as unmerged and re-conflicts. Delete the branch, start fresh.
Gotcha: `git pull` on diverged branches without config: modern Git errors and asks you to choose merge/rebase/ff-only.

How interviewers probe it: "Merge or rebase?" (answer by context: rebase private, merge/squash into shared; team convention wins). "Why not rebase main?" "What does --force-with-lease protect?" "How would you undo a merge that is already on main?"

---
## 3. Cherry-pick

```
 git cherry-pick <sha>            # apply that commit's CHANGE as a new commit on current branch
 git cherry-pick A..B             # range (excludes A, includes B)
 git cherry-pick -x <sha>         # append "(cherry picked from commit ...)" to message
 git cherry-pick -m 1 <merge>     # picking a merge commit needs a mainline parent
 git cherry-pick --continue | --abort
```

Use for: hotfix on a release branch, backporting a fix, rescuing one commit from an abandoned branch.
Gotcha: The copy has a different hash. If both branches later merge, Git usually handles identical changes fine, but duplicates and odd conflicts can appear. Prefer merging when you want everything.
How interviewers probe it: "How do you backport a fix to release-1.2?" (cherry-pick -x, open PR to the release branch).

---
## 4. Undoing things: reset vs revert vs restore

```
                       moves branch?   touches index?   touches working tree?
 reset --soft  <c>         yes             no               no     (changes stay STAGED)
 reset --mixed <c>         yes             yes              no     (default; changes UNSTAGED)
 reset --hard  <c>         yes             yes              yes    (DESTROYS uncommitted work)
 revert <c>                no (adds new commit that inverts <c>)   safe on shared history
 restore <path>            no              no               yes    (discard working-tree edits)
 restore --staged <path>   no              yes              no     (unstage)
```

| Situation | Command |
|---|---|
| Unstage a file | `git restore --staged f` (old: `git reset HEAD f`) |
| Throw away local edits to a file | `git restore f` (old: `git checkout -- f`) (irreversible) |
| Redo last commit message / add a forgotten file | `git commit --amend` (local only) |
| Undo last commit, keep changes staged | `git reset --soft HEAD~1` |
| Undo last commit, keep changes unstaged | `git reset HEAD~1` |
| Nuke last commit and changes | `git reset --hard HEAD~1` |
| Undo a pushed commit on shared branch | `git revert <sha>` then push |
| Undo a merge commit | `git revert -m 1 <merge-sha>` |
| Inspect an old version of a file | `git show <sha>:path` or `git restore --source=<sha> path` |

Gotcha: `git checkout` is overloaded (switch branches AND restore files). Modern Git split it: `git switch` and `git restore` (Git 2.23+).
Gotcha: Reverting a merge tells Git those changes are "done"; re-merging the branch later brings nothing in unless you revert the revert.
Gotcha: `reset --hard` loses uncommitted work forever; committed work is recoverable via reflog.

How interviewers probe it: "Soft vs mixed vs hard?" "Production is broken by a commit on main; what do you do?" (revert, ship fast, then root-cause). "Why revert rather than reset on shared branches?"

---
## 5. Reflog: your safety net

The reflog is a LOCAL log of where HEAD and each branch pointed over time (not pushed, not shared).

```
 git reflog                     # HEAD history: HEAD@{0}, HEAD@{1}, ...
 git reflog show feature        # per-branch
 git branch rescue <sha>        # resurrect a "lost" commit
 git reset --hard HEAD@{2}      # go back to where HEAD was two moves ago
 git checkout -b rescue HEAD@{yesterday}   # time-based syntax
```

Recoverable: after reset --hard, deleted branch, bad rebase, dropped stash (via `git fsck --lost-found`), amended-away commits.
Not recoverable: never-committed working-tree changes; never-added files wiped by `reset --hard` / `clean -fd`.

Gotcha: A fresh clone has an empty reflog. Reflog expiry and `git gc` eventually prune unreachable objects.
How interviewers probe it: "I ran reset --hard and lost commits. Now what?" (reflog, find sha, branch/reset to it). Do the exercise in Section 15.

---
## 6. Stash

```
 git stash push -m "wip: parser"      # save tracked changes (add -u for untracked, -a for ignored too)
 git stash list
 git stash show -p stash@{0}
 git stash pop                        # apply + drop (leaves entry if conflict)
 git stash apply stash@{1}            # apply, keep entry
 git stash branch fix-x stash@{0}     # new branch from the commit the stash was made on
 git stash drop / git stash clear
```
Use it to switch context quickly. Do not treat it as long-term storage; WIP commits on a branch are more durable and visible.
Gotcha: By default untracked files are NOT stashed (`-u`). Gotcha: `stash pop` with conflicts keeps the stash; resolve then drop manually.

---
## 7. Conflicts: what they are and how to resolve

A conflict = both sides changed the same lines (or one deleted what the other edited) relative to the common ancestor. Git does a 3-way merge: base, ours, theirs.

```
 <<<<<<< HEAD (ours: the branch you are on)
 timeout = 30
 =======
 timeout = 60
 >>>>>>> feature (theirs: the branch being merged)
```
Note: during a REBASE, "ours" and "theirs" are swapped (ours = the branch you rebase onto; theirs = your commit being replayed).

Workflow
1. `git status` - lists "both modified" files.
2. Edit: choose/merge, delete markers. Or `git checkout --ours f` / `--theirs f`.
3. Run tests (a clean textual merge can still be semantically broken).
4. `git add f`, then `git merge --continue` (or `git rebase --continue`; `git commit` also works for merge).
5. Stuck? `git merge --abort` / `git rebase --abort`.

Helpful: `git config --global merge.conflictstyle zdiff3` (shows base too; zdiff3 needs Git 2.35+, else diff3; check current docs), `git config --global rerere.enabled true` (reuse recorded resolutions), `git mergetool`, `git diff --name-only --diff-filter=U`.

Reduce conflicts: small PRs, merge/rebase from main often, avoid mass reformatting, use CODEOWNERS and modular code.
How interviewers probe it: "Walk me through resolving a conflict" and "how do you prevent them?" Expect follow-up on ours/theirs in rebase.

---
## 8. Interactive rebase, fixup, autosquash

```
 git rebase -i HEAD~4          # or: git rebase -i main
   pick   a1b2c3 Add parser
   reword d4e5f6 Fix typo         # edit message
   edit   ...                     # stop to amend the commit
   squash ...                     # meld into previous, combine messages
   fixup  ...                     # meld into previous, discard message
   drop   ...                     # delete the commit
   (reorder lines to reorder commits)

 Autosquash workflow:
   git commit --fixup <sha>            # creates "fixup! <subject>"
   git rebase -i --autosquash main     # auto-orders and marks fixups
   git config --global rebase.autoSquash true
```
Typical use: clean a feature branch into logical commits before review; address review feedback by fixup commits, then autosquash before merge.
Gotcha: Interactive rebase is rewriting history; only on commits not yet shared (or branches only you use; then force-with-lease).
Gotcha: Rebase `--onto`: `git rebase --onto main old-base feature` moves a branch segment to a new base.

How interviewers probe it: "How do you clean up a messy branch?" "Squash vs fixup?" "How do you split one commit into two?" (rebase -i, edit, `reset HEAD~`, add -p in two commits, `rebase --continue`).

---
## 9. Bisect: binary search for the bad commit

```
 good ---- good ---- ?? ---- ?? ---- BAD     N commits -> ~log2(N) steps
 git bisect start
 git bisect bad                 # current commit is broken
 git bisect good v1.4.0         # a known-good ref
   ... Git checks out the middle; you test, then say:
 git bisect good | bad | skip
 git bisect reset               # return to original HEAD when done

 Automate: script exits 0 = good, 1-127 (except 125) = bad, 125 = skip
 git bisect start HEAD v1.4.0
 git bisect run pytest -x tests/test_parser.py
 git bisect run sh -c 'make && ./check.sh'
```
Requirements: the bug must be reproducible deterministically; the history must be buildable; works best with small, atomic commits (another reason to avoid giant squashed PRs... or at least keep PRs small). `git bisect log` / `replay` help share a session.
Gotcha: Merge-heavy history is fine; `--first-parent` can restrict to mainline merges (check current docs).
How interviewers probe it: "Test suite started failing sometime last month; how do you find the cause?" Mention bisect run plus a written failing test.

---
## 10. Housekeeping: .gitignore, hooks, tags, semver

.gitignore
```
 __pycache__/        # directories
 *.pyc
 .venv/
 .env                # secrets never committed
 !.env.example       # negation re-includes
 /build              # leading slash anchors to repo root
```
- Only affects UNTRACKED files. Already tracked? `git rm --cached file` then commit.
- Global ignore: `git config --global core.excludesFile ~/.gitignore_global`. Per-repo private: `.git/info/exclude`. Debug: `git check-ignore -v path`.
- Committed a secret? Rotating the secret is step 1; rewriting history (git filter-repo, BFG) is step 2. Assume it leaked.

Hooks (`.git/hooks/*`, not versioned/cloned): pre-commit, commit-msg, pre-push (client side); pre-receive, update (server side). Share via the `pre-commit` framework (Section 14) or `core.hooksPath`. Client hooks can be bypassed (`--no-verify`), so enforce the same checks in CI.

Tags
```
 git tag v1.2.0                      # lightweight (just a pointer)
 git tag -a v1.2.0 -m "Release 1.2"  # annotated (object; use for releases)
 git push origin v1.2.0   |  git push origin --tags
 git tag -d v1.2.0; git push origin :refs/tags/v1.2.0     # delete
 git describe --tags                 # v1.2.0-5-gabc123 (5 commits after tag)
```
Semantic versioning MAJOR.MINOR.PATCH: MAJOR = breaking change, MINOR = backward-compatible feature, PATCH = backward-compatible fix. Pre-release: `1.2.0-rc.1`. Conventional Commits (`feat:`, `fix:`, `feat!:`) let tools derive the next version and changelog.
Gotcha: Tags are not pushed by default. Gotcha: Moving a published tag breaks reproducibility; cut a new version instead.

---
## 11. Pull requests and code review

PR etiquette (author)
- Small, single-purpose PRs (rule of thumb: reviewable in under ~30 min / a few hundred lines; split refactors from behavior changes).
- Title says what; description says why, how, how tested, risks, rollout/rollback, screenshots, linked issue.
- Self-review the diff first. Run CI locally. Mark WIP as Draft.
- Respond to every comment: fix, or explain/discuss; do not silently resolve. Push fixups, then re-request review. Thank, do not argue defensively; disagree with data. Do not force-push mid-review without saying so (it destroys review context).
- Do not merge with red CI; do not bypass required reviews.

Sample PR template (`.github/pull_request_template.md`)
```markdown
## What and why
<!-- One paragraph. Link the issue: Closes #123 -->

## How
<!-- Key design decisions, alternatives rejected -->

## Testing
- [ ] Unit tests added/updated
- [ ] Manually verified: <steps / screenshots>

## Risk and rollout
- Blast radius:
- Feature flag / migration / config changes:
- Rollback plan:

## Checklist
- [ ] Docs updated
- [ ] No secrets or debug code
- [ ] Backward compatible (or breaking change called out)
```

Reviewer: what to look for (rough priority)
1. Correctness and edge cases (nulls, empty, concurrency, off-by-one, error paths).
2. Design: right abstraction, fits the architecture, minimal API surface.
3. Tests: do they fail without the change, cover edge cases, avoid flakiness?
4. Security: input validation, authz, secrets, injection, PII in logs.
5. Performance and data: N+1 queries, unbounded loops, migrations, indexes.
6. Operability: logging, metrics, error handling, config, rollback.
7. Readability and naming. Leave pure style to linters/formatters.

Giving feedback: be specific, explain why, ask questions ("what happens if X is None?"), separate blocking from non-blocking (prefix `nit:`, `optional:`, `blocking:`), praise good work, review the code not the person, respond within a business day (team SLA).
Receiving feedback: assume good intent, ask for clarification, batch changes, close the loop, learn recurring themes and automate them into lint rules.
Gotcha: Approving without reading ("LGTM" rubber-stamp) is the main failure mode; so is a 3000-line PR nobody can review.
How interviewers probe it: "Tell me about a time you disagreed in code review." "What do you check first?" "A teammate's PR is too large; what do you do?"

---
## 12. Branching strategies, feature flags, repo layout

```
 Trunk-based:    main  o--o--o--o--o--o--o      short-lived branches (<1-2 days) or direct commits
                       \o/  \o/                 incomplete work hidden behind feature flags
                       deploys from main continuously

 GitHub flow:    main  o------o-----o           feature branch -> PR -> review -> merge -> deploy
                         \__/   \__/

 Gitflow:        main     o-----------o----o          releases only (tagged)
                 release      o---o  /
                 develop o--o--o--o--o--o--o         integration
                 feature   \o/  \o/ ; hotfix branches off main
```

| Model | Best for | Trade-offs |
|---|---|---|
| Trunk-based | high-velocity teams with strong CI, continuous deploy (Google-style) | needs feature flags, fast tests, discipline |
| GitHub flow | web services, SaaS, small to mid teams | simple; long-lived branches still hurt |
| Gitflow | versioned/boxed software (mobile apps, on-prem, multiple supported releases) | heavy, long-lived branches, merge pain; generally discouraged for CD |

Feature flags: decouple deploy from release. Types: release flags (short-lived), experiment/A-B flags, ops/kill-switch flags, permission flags. Practices: default off, owner + expiry date, remove after rollout (flag debt), test both paths, avoid flag-in-flag combinatorics, evaluate server-side for security.

Monorepo vs polyrepo
| | Monorepo | Polyrepo |
|---|---|---|
| Pros | atomic cross-project changes, shared tooling, easy refactors, single version of deps | clear ownership/boundaries, independent release cycles, smaller clones, simpler permissions |
| Cons | needs scalable build/CI (Bazel, Nx, Turborepo, path filters), VCS performance (sparse checkout), noisy ownership | version skew, dependency hell, cross-repo changes need coordinated PRs |
Mitigations: CODEOWNERS, path-based CI triggers (`on.push.paths`), affected-target builds, remote caching. Google famously uses a monorepo with trunk-based development.

How interviewers probe it: "How do you ship half-finished work safely on trunk?" (flags). "Why might Gitflow be bad for a SaaS team?" "Monorepo tradeoffs?"

---
## 13. CI/CD concepts

```
 Continuous Integration:  every push -> build + test + lint (merge often, keep main green)
 Continuous Delivery:     every green main build is RELEASABLE; deploy to prod is a manual approval
 Continuous Deployment:   every green main build deploys to prod automatically

 commit -> [lint/typecheck] -> [unit tests] -> [build artifact] -> [integration/e2e] -> [deploy staging]
        -> [smoke tests] -> (approval?) -> [deploy prod] -> [verify/monitor] -> (auto-rollback)
```

Pipeline design principles
- Fail fast: cheap checks first (lint, types), run independent jobs in parallel.
- Build once, deploy the same immutable artifact (image digest) to every environment; config differs per environment, not the binary.
- Artifacts: Docker images (registry), wheels, test reports, coverage. Tag with git SHA (traceability), plus semver for releases. Pin by digest in deploys.
- Caching: dependency caches (pip/uv cache keyed by lockfile hash), Docker layer cache (buildx `cache-from/to`). Cache keys must change when inputs change; never cache secrets.
- Environments: dev -> staging -> prod; staging mirrors prod; protection rules (required reviewers, wait timers, branch restrictions) on prod.
- Secrets: stored in the CI secret store / vault, scoped per environment, masked in logs, never in the repo, not available to PRs from forks. Prefer short-lived credentials via OIDC over long-lived keys.
- Flaky tests: quarantine, fix, track; flakiness destroys trust in CI.

Deployment strategies
| Strategy | How | Pros | Cons |
|---|---|---|---|
| Recreate | stop old, start new | simplest | downtime |
| Rolling | replace instances gradually | no downtime, no extra capacity | mixed versions concurrently; slow rollback |
| Blue-green | two full envs, flip traffic | instant switch and rollback | double capacity; DB must be compatible with both |
| Canary | route 1-5% -> 25% -> 100% while watching metrics | limits blast radius, real traffic validation | needs good metrics, routing (mesh/LB), automation |
| Feature-flag release | deploy dark, enable gradually | decoupled, per-user | flag management |

Rollback: redeploy the previous artifact (fast path, keep N previous versions), traffic flip (blue-green), flag off, or `git revert` + pipeline. Define rollback criteria ahead (error rate, p99 latency, SLO burn). Rollback fails if the DB migration is not backward compatible.

Migration safety: use expand/contract (parallel change).
```
 1. Expand:   add new nullable column/table (old code still works)
 2. Deploy code that writes both / reads new with fallback
 3. Backfill in batches
 4. Switch reads to new
 5. Contract:  drop old column in a LATER release
```
Rules: never rename/drop in the same release as code that stops using it; add indexes concurrently (Postgres `CREATE INDEX CONCURRENTLY`); avoid long locks; migrations must be forward and backward compatible with N and N-1 app versions; run migrations as a separate step with its own failure handling.

GitOps: Git is the source of truth for desired state (Kubernetes manifests/Helm/Kustomize). A controller (Argo CD, Flux) continuously reconciles the cluster to match the repo; deploy = merge a PR; rollback = revert; audit trail is git log; drift is detected and corrected. CI builds/pushes the image and updates the manifest repo; CD (the controller) pulls.

How interviewers probe it: "CI vs CD vs CD?" "Design a pipeline for service X." "Blue-green vs canary?" "How do you do a zero-downtime column rename?" "How do you keep secrets out of CI logs?"

---
## 14. Sample pipeline: Python/FastAPI on GitHub Actions

File: `.github/workflows/ci.yml`. Action versions below are examples (check current docs); in security-sensitive repos pin third-party actions to a full commit SHA with a version comment, e.g. `uses: actions/checkout@<40-char-sha> # v4.x.y`, and let Dependabot/Renovate bump them. Tags like `@v4` are mutable (a compromised tag changes what you run); SHAs are immutable. Runner label `ubuntu-latest` floats to a new Ubuntu LTS over time; use `ubuntu-24.04` to pin (check current docs).

```yaml
name: ci

on:
  push:
    branches: [main]
    tags: ["v*.*.*"]
  pull_request:
    branches: [main]

# Least privilege: default token can only read repo contents. Jobs opt in to more.
permissions:
  contents: read

# Cancel superseded runs on the same PR/branch (saves minutes).
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

env:
  PYTHON_VERSION: "3.12"
  IMAGE_NAME: ghcr.io/${{ github.repository }}

jobs:
  lint:
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4            # pin to SHA in production (check current docs)
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
          cache-dependency-path: requirements*.txt
      - run: pip install ruff
      - run: ruff check .
      - run: ruff format --check .

  typecheck:
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
          cache-dependency-path: requirements*.txt
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: mypy app

  test:
    runs-on: ubuntu-24.04
    timeout-minutes: 20
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: app
          POSTGRES_PASSWORD: app          # throwaway CI-only credential, not a real secret
          POSTGRES_DB: app_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U app -d app_test"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 10
    env:
      DATABASE_URL: postgresql+psycopg://app:app@localhost:5432/app_test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
          cache-dependency-path: requirements*.txt
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest --cov=app --cov-report=xml --cov-report=term-missing --cov-fail-under=80
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-xml
          path: coverage.xml

  build:
    needs: [lint, typecheck, test]             # only build if all gates pass
    if: github.event_name == 'push'            # PRs do not publish images
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    permissions:
      contents: read
      packages: write                          # needed to push to GHCR
    outputs:
      digest: ${{ steps.push.outputs.digest }}
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}   # short-lived, auto-provisioned
      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.IMAGE_NAME }}
          tags: |
            type=sha
            type=semver,pattern={{version}}
            type=raw,value=latest,enable={{is_default_branch}}
      - id: push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-24.04
    environment:
      name: production                         # protection rules: required reviewers, branch limits
      url: https://api.example.com
    permissions:
      contents: read
      id-token: write                          # only if using OIDC to a cloud provider
    concurrency:
      group: deploy-production
      cancel-in-progress: false                # never cancel a deploy mid-flight
    steps:
      - name: Deploy (placeholder)
        env:
          IMAGE: ${{ env.IMAGE_NAME }}@${{ needs.build.outputs.digest }}
        run: |
          echo "Deploying $IMAGE"
          # Option A, kubectl (after configuring cluster auth via OIDC or a kubeconfig secret):
          #   kubectl set image deployment/api api="$IMAGE" -n prod
          #   kubectl rollout status deployment/api -n prod --timeout=180s
          # Option B, ssh:
          #   ssh deploy@host "docker pull $IMAGE && docker compose up -d"
          # Then run a smoke test: curl --fail https://api.example.com/healthz
```

Block-by-block
| Block | Why it is there |
|---|---|
| `on:` | push to main and tags run the full flow; PRs run checks only |
| top-level `permissions: contents: read` | default GITHUB_TOKEN is least-privileged; each job escalates only what it needs (`packages: write`, `id-token: write`). Set repo/org default to read-only too |
| `concurrency` | cancel stale PR runs; serialize deploys and never cancel them |
| lint / typecheck / test | parallel, independent fast gates. `ruff check` for lint rules, `ruff format --check` for formatting, `mypy` for types, `pytest` for behavior |
| `services: postgres` | a real DB container on the runner; `--health-cmd` makes the job wait until Postgres is ready; job reaches it at `localhost:5432` (when steps run on the runner, not in a container job) |
| coverage | `--cov-fail-under` enforces a floor; XML artifact for later upload to Codecov/Sonar |
| `needs` + `if` | build only after gates pass and only on push |
| buildx + `cache-to: type=gha` | BuildKit with layer cache in the Actions cache (check current docs for cache backend/limits) |
| metadata-action | generates tags: git SHA (traceable), semver from git tags, `latest` on default branch |
| login with GITHUB_TOKEN | no stored registry password; needs `packages: write` |
| digest output | deploy by immutable digest, not a mutable tag (build once, deploy the same bytes) |
| `environment: production` | enables required reviewers (manual approval), wait timers, environment-scoped secrets, deployment history |
| placeholder deploy | replace with kubectl/ssh/Helm/Argo CD image-tag bump. In a GitOps setup this step instead opens a PR on the manifests repo |

OIDC note: instead of storing long-lived cloud keys as secrets, GitHub issues a short-lived signed JWT per job (requires `id-token: write`). The cloud provider (AWS IAM role with a web-identity trust policy, GCP Workload Identity Federation, Azure federated credentials) trusts GitHub's issuer and checks claims (`sub` such as `repo:org/repo:environment:production`) to mint temporary credentials. Example AWS step: `aws-actions/configure-aws-credentials@v4` with `role-to-assume` (check current docs). Scope the trust policy to the repo, branch, and environment.

Security checklist
- Pin third-party actions to SHAs; allow-list actions at the org level; Dependabot for `github-actions`.
- Never use `pull_request_target` with checkout of PR code and secrets (untrusted code with privileges). Fork PRs get no secrets on `pull_request`.
- Never interpolate untrusted input (`${{ github.event.pull_request.title }}`) directly in `run:`; pass via `env:` to avoid script injection.
- Mask and scope secrets; use environment secrets for prod.
- Branch protection / rulesets: require PR, required status checks, linear history optional, no force-push to main, CODEOWNERS review.

Sample `.pre-commit-config.yaml` (shift checks left; `rev` values are examples, run `pre-commit autoupdate`; check current docs)
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: detect-private-key
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, types-requests]
```
Setup: `pip install pre-commit && pre-commit install` (also `pre-commit run --all-files`). CI should run the same checks (`pre-commit run --all-files`) since local hooks can be skipped.

Gotcha: A green pipeline that deploys on `pull_request` from forks, or caches keyed only by branch name, can leak or serve stale/poisoned state.
Gotcha: `services:` hostname is `localhost` for runner steps but the service label (`postgres`) if the job itself runs in a `container:`.
How interviewers probe it: "Walk through this pipeline." "How would you speed it up?" (cache, parallelism, path filters, test sharding). "How do you secure it?" (pinning, permissions, OIDC, environments). "How do you roll back?"

---
## 15. Sandbox exercises (all in /tmp, safe to delete)

Setup used by all: `export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@x GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@x`

Exercise A: look inside the object store
```
rm -rf /tmp/g-a && mkdir /tmp/g-a && cd /tmp/g-a && git init -q -b main
echo "hello" > a.txt && git add a.txt && git commit -qm "first"
git cat-file -p HEAD                 # commit: tree + author + message
git cat-file -p HEAD^{tree}          # tree: blob entry for a.txt
git cat-file -p HEAD:a.txt           # blob: hello
cat .git/HEAD; cat .git/refs/heads/main     # symbolic ref and branch pointer
```
Predict before running: how many objects exist? (1 blob, 1 tree, 1 commit; `find .git/objects -type f`.)

Exercise B: create and resolve a conflict
```
rm -rf /tmp/g-b && mkdir /tmp/g-b && cd /tmp/g-b && git init -q -b main
printf 'timeout = 30\n' > cfg.txt && git add . && git commit -qm "base"
git switch -qc feature && printf 'timeout = 60\n' > cfg.txt && git commit -qam "feature: 60"
git switch -q main        && printf 'timeout = 45\n' > cfg.txt && git commit -qam "main: 45"
git merge feature         # CONFLICT (content)
git status                # both modified
cat cfg.txt               # see markers
printf 'timeout = 50\n' > cfg.txt
git add cfg.txt && git commit -qm "merge feature; timeout 50"
git log --oneline --graph --all
```
Repeat with `git rebase main` from feature (reset first) and notice that ours/theirs swap and you use `git rebase --continue`.

Exercise C: bisect run
```
rm -rf /tmp/g-c && mkdir /tmp/g-c && cd /tmp/g-c && git init -q -b main
for i in 1 2 3 4 5 6 7 8; do echo "ok $i" > f.txt; git add .; git commit -qm "c$i"; done
echo "BROKEN" > f.txt; git commit -qam "c9 introduces bug"
for i in 10 11 12; do echo "BROKEN $i" > f.txt; git commit -qam "c$i"; done
git bisect start HEAD HEAD~11
git bisect run sh -c '! grep -q BROKEN f.txt'
git bisect reset
```
Expected: Git names "c9 introduces bug" as the first bad commit in about 3-4 steps.

Exercise D: reflog recovery
```
rm -rf /tmp/g-d && mkdir /tmp/g-d && cd /tmp/g-d && git init -q -b main
for i in 1 2 3 4; do echo $i > f; git add f; git commit -qm "c$i"; done
git reset --hard HEAD~2      # "oops": c3 and c4 vanish from git log
git log --oneline            # only c1, c2
git reflog                   # find the sha of c4 (HEAD@{1})
git reset --hard HEAD@{1}    # back at c4
git log --oneline
# also: delete a branch and bring it back
git switch -qc topic && echo t > t && git add t && git commit -qm "topic work"
git switch -q main && git branch -D topic
git reflog | head            # find topic's last commit
git branch topic <sha>
```

Exercise E (stretch): interactive rebase with autosquash
```
rm -rf /tmp/g-e && mkdir /tmp/g-e && cd /tmp/g-e && git init -q -b main
echo a > a && git add a && git commit -qm "add a"
echo b > b && git add b && git commit -qm "add b"
echo A >> a && git add a && git commit -q --fixup HEAD~1
GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash --root
git log --oneline            # fixup folded into "add a"
```

Cleanup: `rm -rf /tmp/g-a /tmp/g-b /tmp/g-c /tmp/g-d /tmp/g-e`

---
## 16. Wrap-up: what a strong answer sounds like

- Start with the mental model (objects, DAG, pointers) and derive behavior from it: "rebase creates new commits, so the hashes change, so shared history breaks."
- Choose tools by risk: revert on shared history, reset/rebase on private; reflog as the net; force-with-lease not force.
- For process questions, tie to outcomes: small PRs reduce review latency and bisect cost; flags decouple deploy from release; expand/contract makes rollback possible.
- For CI/CD, always state: fail fast, build once, immutable artifacts, least privilege, gated prod environment, observable rollout, rehearsed rollback.
