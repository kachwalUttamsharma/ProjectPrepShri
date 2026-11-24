# 02 - FDE Customer Scenarios

## 1. What a forward-deployed engineer does
An FDE is an engineer embedded with customers (or working closely with them) to turn a product or platform, often LLM-based, into a working solution in the customer's real environment. Typical work (varies by company; check the job description):
- Discovery: understand the customer's workflow, data, constraints, and success metrics.
- Prototype fast: integrate APIs, build RAG/agent/automation prototypes, connect to customer systems (CRMs, ticketing, data warehouses).
- Production-harden: auth, observability, evals, error handling, security review.
- Feed back to product: turn repeated field problems into product requirements.
- Communicate with technical and non-technical stakeholders, set expectations, handle escalations.

Interviewers look for: technical breadth plus practical judgment, structured thinking under ambiguity, honesty about limits, customer empathy without being a pushover, and bias toward shipping small and measuring.

## 2. Answer framework for scenarios (use every time)
1. **Clarify** (2-4 questions: goal, users, data, constraints, deadline).
2. **Restate** the problem and the success metric.
3. **Plan** in phases: what you do first, what you'd defer.
4. **Risks and mitigations** (technical, people, security).
5. **Communication**: who you tell what, when.
6. **Close the loop**: how you will know it worked.

## 3. Scenarios with model answers

### 1. Vague customer request: "We want AI for our support team."
Model: Ask what a good week looks like. Which tickets, volume, categories, current handling time, cost, who reviews. Pick one narrow, measurable use case (e.g., draft replies for the top 3 ticket categories, human approves). Define success (first-response time -X%, agent acceptance rate > Y%). Ask for 100-200 real historical tickets as a test set. Propose a 1-week prototype, then review. Write the agreed scope back in an email.

### 2. Angry customer: "Your product has wasted two weeks."
Model: Listen without defending; acknowledge impact in specific words ("a two-week delay on your launch is serious"). Get facts: what broke, what they've tried, deadline. Give an immediate action and a next-update time. Reproduce, find root cause, separate what is on you, the product, and their environment honestly. Follow up with a written summary, workaround, and prevention. Escalate internally early. Never blame them or promise unverified fixes.

### 3. Scope a prototype in one week
Model: Day 0 define one user, one workflow, one metric. Day 1 data access and a thin end-to-end slice (ugly but working). Days 2-3 improve quality using a small eval set. Day 4 harden obvious failure modes, logging. Day 5 demo plus honest "what's not done." Explicitly list out-of-scope (auth, scale, edge cases). Ask for an owner on their side and sample data on day 1; without data the plan slips.

### 4. Saying no
Model: Never a bare "no". Explain the reason (risk, feasibility, timeline), offer alternatives (smaller version, phased, different approach), and the cost of the original ask. Example: "A fully autonomous refund agent in two weeks is not safe. We can ship suggestion mode with human approval, measure accuracy, and graduate to autonomy for low-value cases." Confirm in writing; involve your manager if it is contractual.

### 5. Explaining LLM limits and hallucination to non-engineers
Model: Use an analogy: "It's an extremely well-read assistant that predicts plausible text; it can sound confident when wrong." Explain what we do about it: ground answers in your documents (retrieval), require citations, say "I don't know" when unsupported, add human review where cost of error is high, measure accuracy on your real examples. Set expectation: reduces, never reaches zero. Show a failing example proactively and what the safeguard did.

### 6. Data-quality surprise
Model: Stop and quantify: how many records, which fields, what pattern (duplicates, missing, stale, inconsistent formats, PDFs that are scans). Tell the customer early with examples, not blame. Offer options: clean a subset, add validation, restrict to good data for v1, schedule cleanup with owner. Adjust timeline/scope. Add data checks to the pipeline to detect regressions.

### 7. Security/compliance pushback
Model: Treat security as a requirement, not an obstacle. Ask for their policy (data residency, PII, retention, vendor review, SSO). Map where data flows; propose minimization (redact PII, no training on their data per contract terms, regional endpoints, private networking, least-privilege keys). Involve your security team; do not promise certifications you cannot verify. Offer a lower-risk path in the meantime (synthetic or anonymized data).

### 8. Demo fails live
Model: Stay calm, say what happened plainly, do not improvise unsafe fixes. Switch to the backup (recorded run, pre-cached example, screenshots). Prevention: rehearse on the same network, pin versions, test with live credentials an hour before, have fallback recordings. Afterwards send a follow-up with a working demo and the cause. Calm recovery builds more trust than a perfect demo.

### 9. Handing off to the customer team
Model: Plan the handoff from week one. Deliverables: README and architecture diagram, runbook (deploy, rollback, common errors), config/secrets inventory, eval set and how to rerun it, monitoring dashboards, known limitations. Run a walkthrough and a shadow period where they operate and you watch. Name owners, support path and SLAs. Confirm acceptance criteria.

### 10. Prioritizing multiple customers
Model: Make criteria explicit: revenue/strategic importance, severity (outage vs wish), deadline, effort, reuse across customers, risk of churn. Triage in a table, communicate transparently with each customer (realistic dates), seek help or delegate, and bundle reusable work into the product. Push back on "everything is urgent" by asking "what happens if this slips a week?"

### 11. Customer asks for a feature the product lacks
Model: Understand the underlying need; check for workaround in existing capabilities; if a custom build is needed, build it in a way that can be generalized; file a clear product request with customer impact and frequency; give honest timeline expectations.

### 12. Model quality is poor on the customer's domain
Model: Build a small labeled eval set from their data first. Diagnose: retrieval failure vs prompt vs model vs data. Try cheapest fixes first (better chunking, prompt with examples, metadata filters, reranking), then bigger ones (fine-tuning, a different model). Report metrics before/after, not feelings.

### 13. Prototype works; customer wants production next week
Model: Separate "demo-ready" from "production-ready". List gaps (auth, rate limits, retries, logging, PII, evals, cost caps, on-call). Propose a staged rollout: internal pilot, limited users, monitoring, then expand. Risk-communicate clearly and get sign-off on the scope.

### 14. Stakeholders disagree internally (champion vs blocker)
Model: Identify each person's goals and fears. Meet the blocker one-on-one, listen, address their concern (often risk or job impact). Give them a role (reviewer, approver). Use data from a small pilot. Keep your champion informed but don't weaponize them.

### 15. Cost or latency exceeds expectations
Model: Measure first (tokens per request, calls per task, cache hit rate). Levers: smaller model for easy steps, caching, shorter prompts, batching, streaming for perceived latency, fewer agent loops, limits and budgets. Present trade-offs with numbers.

### 16. You made a mistake in front of the customer
Model: Disclose quickly, state impact, fix, explain prevention. Do not hide. Customers value honesty and speed.

### 17. Customer wants an agent to take actions autonomously
Model: Classify actions by risk (read, reversible write, irreversible/financial). Start read-only or human-in-the-loop, add guardrails (allowlists, limits, audit logs, dry-run mode), evaluate on real cases, expand autonomy gradually.

### 18. Success metric is unclear or unmeasurable
Model: Propose a baseline: sample current work, measure time/accuracy manually, define target. Agree on an evaluation method before building; otherwise success becomes opinion.

## 4. Discovery-call question checklist
- Business: What problem, who suffers, what does it cost today, what does success look like in 3 months, who decides, what's the deadline and why?
- Users: Who will use it, how often, what do they do now, what tools do they live in?
- Process: Walk me through the last time this happened, step by step. Where are errors/delays?
- Data: Where does it live, format, volume, quality, sensitivity (PII/regulated), freshness, access method, who owns it?
- Systems: APIs available, auth method, rate limits, test environments, change freeze periods?
- Constraints: Security reviews, compliance, data residency, approved vendors, network restrictions, budget.
- Risk: What is the cost of a wrong answer? Who reviews outputs?
- Team: Who is the technical owner on your side? Who maintains it later?
- Past attempts: What have you tried, what failed, why?
- Next steps: Can we get sample data and a 30-minute follow-up this week?

## 5. Scoping template
```
Customer / Project: ______   Date: ____   Owner (them / us): ____
Problem statement (one sentence):
Primary user and workflow:
Success metric(s) and baseline -> target:
In scope (v1):
Out of scope (explicit):
Data sources and access status:
Integrations (system, auth, environment):
Assumptions (to validate):
Risks and mitigations (technical, security, people):
Evaluation plan (test set size, who labels, pass bar):
Timeline: Day/Week milestones, demo date, decision date
Dependencies from customer (with due dates):
Handoff plan and support model:
Sign-off: ____
```

## 6. Demo script template (15 minutes)
1. (1 min) Recap: the problem in their words, the metric.
2. (1 min) What you'll see and what you won't.
3. (6 min) Happy path using THEIR data/examples, narrate the "why".
4. (3 min) One failure case and how the system handles it (shows honesty and guardrails).
5. (2 min) Results: eval numbers, time saved.
6. (2 min) Next steps, asks (data, owner, decision date), questions.
Prep: rehearse on the real network, backup recording, pinned versions, reset state, test credentials, clean browser tabs, know the 3 questions they'll ask.

## 7. Post-mortem template (blameless)
```
Title / Date / Severity / Author
Summary (2-3 sentences, plain language)
Customer impact (who, how long, how much)
Timeline (UTC): detection, escalation, mitigation, resolution
Root cause (technical + process: "why" x5)
What went well / what went poorly / where we got lucky
Action items (owner, due date, priority): prevent, detect, mitigate
Customer communication: what we told them, when; follow-up needed
Lessons for product/field team
```

## 8. Practice
Pick 3 scenarios a week; answer out loud in 2-3 minutes with the framework; then draft the email you'd send the customer. Pair with 13-llm-ai-concepts (RAG, evals, agents) and 07-aws for technical backing.
