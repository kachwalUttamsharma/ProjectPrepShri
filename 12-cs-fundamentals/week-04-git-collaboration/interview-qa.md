# Week 4 Interview Q&A - Git, Collaboration, Code Review, CI/CD

Practice: answer out loud in 30-60 seconds first, then compare.

**1. What is a Git branch, really, and what does a commit contain?**
A branch is a small file holding one commit hash: a movable pointer, so creating one is O(1). A commit is a snapshot: it references a root tree (directory listing of trees and blobs), parent commit hash(es), author/committer and message. Objects are content-addressed (hash of content), immutable, and deduplicated; history is a DAG with edges pointing to parents.

**2. Explain the working tree, index, and repository. What does `git add` do?**
Working tree = files on disk. Index (staging area) = the proposed next commit. Repository = committed history. `git add` copies the file's current content into the index as a blob; later edits are not staged until you add again. `git commit` writes a tree from the index and a commit object, and moves the current branch.

**3. Merge vs rebase: when do you use each?**
Merge preserves true history with a merge commit (or fast-forwards if possible) and is safe on shared branches. Rebase replays your commits on a new base, creating new commits for a linear history; use it on private branches to stay current with main. Squash merge turns a PR into one commit on main. Team convention matters most; the invariant is not rewriting shared history.

**4. What is the golden rule of rebasing and what is `--force-with-lease`?**
Never rebase commits others have based work on (pushed shared history), because new hashes force everyone to reconcile. After rebasing your own pushed branch you must force push; `--force-with-lease` refuses if the remote branch has moved since you last fetched, so you cannot overwrite a teammate's commits unseen. Plain `--force` has no such check.

**5. Reset --soft vs --mixed vs --hard, and how do they differ from revert and restore?**
All three reset moves the branch pointer; soft keeps changes staged, mixed (default) unstages them, hard also overwrites the working tree (destroys uncommitted work). `revert` adds a new commit that inverts an earlier one, safe on shared history. `restore` changes files (working tree or `--staged` index) without moving branches.

**6. A bad commit is on main and already deployed. What do you do?**
Mitigate first: `git revert <sha>` (for a merge, `-m 1`), push through CI (or roll back the deployment artifact / turn off the feature flag if faster). Do not reset or force-push main. Then root-cause, add a regression test, and write a postmortem if user-impacting.

**7. You ran `git reset --hard` and lost commits. How do you recover?**
`git reflog` shows where HEAD has been; find the hash from before the reset and `git reset --hard <hash>` or `git branch rescue <hash>`. Works for committed work (until expiry, roughly 30-90 days by default; check current docs). Uncommitted, never-staged changes are not recoverable. Reflog is local only.

**8. What is cherry-pick and when would you use it?**
It applies the change introduced by a commit onto the current branch as a new commit with a new hash. Typical uses: backporting a hotfix to a release branch (`-x` records the source), or salvaging one commit. Downside: duplicated commits and possible later conflicts; if you want all changes, merge instead.

**9. How do you resolve a merge conflict, and what is different during a rebase?**
Run `git status`, open files, reconcile markers (or choose `--ours`/`--theirs`), run tests, `git add`, then `git merge --continue` (or `rebase --continue`); `--abort` backs out. In a rebase, ours and theirs are swapped: ours is the branch you are rebasing onto, theirs is your commit being replayed, and conflicts may recur per commit. Reduce them with small PRs, frequent syncing, and `rerere`.

**10. How does `git bisect` work, and how do you automate it?**
It binary-searches history between a known good and a known bad commit, checking out midpoints so you find the first bad commit in about log2(N) steps. Automate with `git bisect run <cmd>`: exit 0 = good, 1-127 except 125 = bad, 125 = skip. Needs a deterministic repro and buildable commits; small atomic commits make the result more actionable.

**11. How do you clean up a messy branch before review?**
`git rebase -i main`: reword, squash/fixup, drop, and reorder commits into logical units. For review feedback, use `git commit --fixup <sha>` and later `git rebase -i --autosquash`. Only do this on unshared commits, then push with `--force-with-lease` and tell reviewers you rewrote history.

**12. What goes in `.gitignore`, and what if a secret was committed?**
Build output, caches, virtualenvs, local config, `.env`; it only affects untracked files (use `git rm --cached` for tracked ones). If a secret is committed, assume it leaked: rotate/revoke it immediately, then optionally purge history with `git filter-repo`/BFG and force push; deletion in a new commit does not remove it from history.

**13. Lightweight vs annotated tags, and how does semantic versioning work?**
Lightweight tag = just a ref; annotated tag = an object with tagger, date, message, optional signature; use annotated for releases. Tags are not pushed by default. SemVer MAJOR.MINOR.PATCH: breaking change bumps MAJOR, backward-compatible feature bumps MINOR, backward-compatible fix bumps PATCH; pre-releases like `1.2.0-rc.1`. Never move a published tag.

**14. What makes a good pull request, and how do you respond to review feedback?**
Small, single-purpose, with a description of what, why, how tested, risk, and rollback; self-reviewed and CI-green. On feedback: assume good intent, respond to every comment (fix, or explain with data), push follow-up commits, avoid silent force-pushes during review, and re-request review. Distinguish blocking from nit comments and automate repeated style feedback into linters.

**15. What do you look for when reviewing code, and how do you give feedback?**
Correctness and edge cases, design fit, test quality, security (input, authz, secrets), performance and data/migration impact, operability (logs, metrics, rollback), then readability; leave pure style to tools. Be specific, explain why, ask questions rather than command, label nit/optional/blocking, praise good work, review the code not the person, and review promptly.

**16. Compare trunk-based development, GitHub flow, and Gitflow. Where do feature flags fit?**
Trunk-based: tiny branches merged to main at least daily, always releasable, relies on CI and flags. GitHub flow: short-lived feature branch -> PR -> merge -> deploy; simple for SaaS. Gitflow: develop/release/hotfix branches for versioned products with several supported releases; heavy and merge-prone for continuous delivery. Feature flags decouple deploy from release, enabling dark launches, gradual rollout and kill switches; they need owners, expiry, and cleanup to avoid flag debt.

**17. Monorepo vs polyrepo?**
Monorepo: atomic cross-project changes, shared tooling and single dependency versions, easier refactors; costs are scalable build/CI (affected-target builds, remote caching, Bazel/Nx), VCS performance, and ownership via CODEOWNERS. Polyrepo: clear boundaries and independent release cadence, but version skew and painful cross-repo changes. Choose based on coupling and team/tooling maturity.

**18. Distinguish continuous integration, continuous delivery, and continuous deployment.**
CI: merge small changes often with automated build/test on every push. Continuous delivery: every main build is releasable and deployable at the push of a button (manual approval gate). Continuous deployment: every green build goes to production automatically. Principles: fail fast, build once and promote the same immutable artifact, keep environments similar, automate rollback.

**19. Compare rolling, blue-green, and canary deployments. How do you make rollbacks and DB migrations safe?**
Rolling replaces instances gradually (no extra capacity, mixed versions). Blue-green keeps two full environments and flips traffic (instant rollback, double capacity). Canary sends a small percentage of traffic to the new version while watching error rate/latency, then expands (smallest blast radius, needs good metrics). For safe rollback, deploy immutable artifacts by digest, keep previous versions, and make schema changes backward compatible using expand/contract: add nullable column, dual write/backfill, switch reads, drop the old column in a later release. GitOps adds Git as the source of truth with a controller such as Argo CD or Flux reconciling the cluster; rollback is a revert.

**20. Walk me through a secure CI/CD pipeline for a Python/FastAPI service on GitHub Actions.**
Triggers on PR and main. Parallel gates: ruff (lint and format check), mypy, pytest with coverage and a Postgres service container with a health check. Then, on main only, build with buildx and push to GHCR using `GITHUB_TOKEN` (`packages: write`), tagged by SHA/semver with layer caching, and output the image digest. Deploy job needs build, runs in a protected `production` environment (required reviewers), deploys that digest (kubectl/ssh/GitOps update), smoke-tests, and can roll back. Security: top-level `permissions: contents: read` with per-job escalation, third-party actions pinned to full SHAs (check current docs for versions), OIDC (`id-token: write`) instead of long-lived cloud keys, secrets scoped to environments, no untrusted input in `run:`, concurrency control so deploys are serialized.
