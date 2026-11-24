# 04 - Resume and Portfolio

## 1. Resume principles
- One page (two only with 10+ years). Plain single-column format, standard fonts; applicant tracking systems parse plain structure best.
- Every line proves impact. Recruiters spend seconds on first pass; make the top third count.
- Tailor 2-3 bullets and the skills list per role (FDE: customer-facing, integrations, LLMs; SWE: systems, scale).
- No photo, no personal data beyond email, phone, city, LinkedIn, GitHub.

## 2. Structure for a career-changer or beginner
1. Header: name, email, phone, city, LinkedIn, GitHub, portfolio link.
2. Summary (2 lines, optional): "Backend engineer (Python, FastAPI, SQL, AWS) with 4 years in [prior field]; built RAG and agent projects with measured evals."
3. **Projects** (near top if little SWE experience): 3-4 items, each 2-3 bullets with links.
4. Experience: prior roles, reframed for transferable skills (ownership, customers, data, automation).
5. Skills: grouped (Languages, Backend, Data, Cloud, AI/LLM, Tools); only what you can discuss deeply.
6. Education / certifications (brief; AWS cert if earned).
7. Optional: open source, talks, writing.

## 3. Bullet formula
**Action verb + what you built/did + how (tech) + measurable result.**
"Accomplished [X], as measured by [Y], by doing [Z]."

Impact metrics to hunt for: time saved, error or ticket reduction, latency, cost, throughput, users, test coverage, accuracy on an eval set, revenue, adoption. If no hard number, use scale (records, endpoints, requests/day) or honest estimates ("~").

### Before / after examples
| Before | After |
|---|---|
| Worked on API for tickets | Built FastAPI ticket service (CRUD, JWT auth, pagination) with 40+ pytest cases and Postgres migrations; cut manual triage steps from 6 to 2 in demo workflow |
| Made a chatbot using LLM | Built RAG assistant over 500 support docs (chunking, embeddings, reranking); raised answer accuracy from 62% to 84% on a 100-question eval set |
| Responsible for reports | Automated weekly sales reporting with Python and SQL, saving ~5 hrs/week for a team of 8 |
| Helped customers with issues | Resolved 30+ customer escalations per month with root-cause fixes; reduced repeat tickets by 25% |
| Learned AWS | Deployed containerized API to AWS (ECS Fargate, RDS, ALB) with IaC and CloudWatch alarms; documented runbook |
| Managed team tasks | Led a 4-person project to migrate a spreadsheet process to a web app; delivered in 6 weeks, 90% adoption |

Avoid: "responsible for", "worked on", tool lists with no outcomes, unverifiable superlatives, anything you can't explain in an interview. Everything on the resume is fair game for deep questions.

## 4. GitHub portfolio plan (using the course projects)
Four flagship repos, each with a strong README, tests, and a run command that works from scratch.

| Repo | Contents | What it signals |
|---|---|---|
| ticket-api (FastAPI) | CRUD, auth, validation, pagination, SQL, tests, Docker | Backend fundamentals |
| rag-demo | Ingestion, chunking, embeddings, retrieval, citations, simple UI/API | LLM integration |
| support-agent | Tool-using agent with guardrails, logging, human-approval step | Agent design and safety |
| eval-harness | Test set, metrics, regression run, comparison report across prompts/models | Rigor, FDE-critical skill |

Optional fifth: a deployment (AWS or similar) with IaC and a short architecture write-up; an integrated mini-project connecting all four.

Portfolio hygiene:
- Pin README to GitHub profile top 4-6 repos; write a profile README.
- Commit regularly with clear messages; small PRs even on your own repos.
- No secrets in git (use .env.example); check history before publishing.
- Add CI (lint + tests) badge if possible.
- Short demo GIF or Loom-style recording linked in README.
- Keep scope focused; fewer polished projects beat many abandoned ones.
- Write one blog-style post per project: problem, decisions, trade-offs, results.

## 5. Project README template
```
# Project Name
One-sentence description and who it is for.

## Demo
GIF/screenshot or link. Live URL if hosted.

## Problem
What problem, why it matters (2-3 sentences).

## Features
- ...

## Architecture
Diagram (ASCII or image) + 1 paragraph. Key components and data flow.

## Tech stack
Python 3.x, FastAPI, Postgres, ...

## Getting started
1. Clone, create venv, install: pip install -r requirements.txt
2. Copy .env.example to .env and set values
3. Run: ...
4. Test: pytest

## API / Usage examples
curl or code snippets.

## Evaluation / Results
Metrics, test set description, before/after table.

## Design decisions and trade-offs
Why X over Y. Known limitations.

## Roadmap
- ...

## License / Contact
```

## 6. LinkedIn tips
- Headline: role and value, not just "Student": "Backend & AI engineer | Python, FastAPI, RAG | Building customer-facing LLM systems".
- About: 3-4 short paragraphs: what you do, proof (projects with numbers), what you want, how to reach you.
- Featured: pin GitHub repos, a demo video, a write-up.
- Experience: mirror resume bullets; add skills.
- Use a clear photo; custom URL; open to work setting limited to recruiters if you prefer discretion.
- Post occasionally: what you learned building a project. Comment thoughtfully on engineers' posts.
- Connect with recruiters and engineers with a short personalized note (2 sentences, specific ask).
- Keep resume, LinkedIn, and GitHub consistent.

## 7. Final resume checks
- Run spell-check; read aloud; ask a friend in industry to review.
- One page, PDF, filename "FirstLast_Resume.pdf".
- Every bullet starts with a verb, has a result, and fits two lines max.
- Links work.
