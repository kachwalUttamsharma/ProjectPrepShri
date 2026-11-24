# 03 - Interview Process and Strategy

**Important caveat**: company processes change frequently (round counts, formats, tools, leveling, team matching, whether remote or onsite). Everything below is a generic pattern. Verify current details from the official careers page, the recruiter's email, and the candidate prep materials the company sends. Ask the recruiter directly: "What are the rounds, how long, what is each testing, which language/tools are allowed?" Recruiters generally answer.

## 1. Generic loop structure
| Stage | Typical format | What it tests |
|---|---|---|
| Application / referral | Resume review | Match to role, impact evidence |
| Recruiter screen | 20-40 min call | Motivation, background, logistics, compensation expectations, timeline |
| Technical phone/video screen | 45-60 min, shared editor, 1-2 coding problems | Problem solving, DSA fundamentals, communication |
| Online assessment (some companies) | Timed coding test | Speed and correctness on standard problems |
| Onsite / virtual "loop" | 3-6 interviews in a day or split | See below |
| Hiring committee / team match | Internal review, sometimes team-fit calls | Calibration, leveling |
| Offer | Call plus written offer | Compensation and negotiation |

### Typical loop rounds (SWE)
- 2-3 coding/DSA rounds: arrays, strings, hashing, trees, graphs, DP, heaps; clean code, complexity, tests.
- System design (more at mid/senior levels): requirements, API, data model, scaling, trade-offs (see 08-system-design).
- Behavioral / "team fit" round (see 01).
- Sometimes low-level design / OOP (see 11-lld) and domain depth (see 10-python-depth, 12-cs-fundamentals).

### Typical loop rounds (FDE-type roles)
Expect a mix; ask the recruiter which apply:
- Coding (often practical: API integration, data wrangling, parsing, building a small service), possibly lighter DSA than pure SWE.
- Debugging or code-review style exercise.
- Technical design with customer context (integrate LLM into a workflow, data pipeline, RAG, auth).
- Customer-scenario / case round: discovery, scoping, handling pushback (see 02).
- Project deep dive or presentation of past work.
- Behavioral and values.
- Possibly a take-home or live build; check time limits and what is allowed (AI tools policy varies, ask).

## 2. What each round tests and how to prepare
| Round | Preparation |
|---|---|
| Recruiter screen | 60-second pitch, why this company/role, salary range research, timeline, competing processes |
| Coding | 03-dsa patterns daily, timed practice, verbal narration (05) |
| System design | 08-system-design frameworks, 3-4 classic designs, trade-off vocabulary |
| Practical/FDE coding | 04-fastapi, 06-sql, 05-fde-projects, HTTP/JSON/auth, error handling |
| Customer scenario | 02 frameworks out loud |
| Behavioral | 01 story bank |
| Project deep dive | README and architecture of your best project; metrics; trade-offs; what you'd change |

## 3. Timeline planning
- Preparation lead time: 3-6 months of focused prep before first real interviews is common for beginner-to-hire paths; this repo's 12-month plan (06) is more conservative.
- Applying: Start practice interviews with low-priority companies first. Cluster real interviews within 2-4 weeks so offers overlap (helps negotiation).
- Between stages: Companies often take days to weeks; follow up politely after one week.
- Scheduling: ask for 1-2 weeks of prep after the recruiter screen; most recruiters accommodate. Do not schedule your dream company first.
- Day before: light review only, sleep, test your audio/IDE/internet setup.

## 4. How to practice
1. **Coding**: pattern-based (two pointers, sliding window, BFS/DFS, binary search, heap, DP basics); solve, then re-solve from scratch after 3-7 days (spaced repetition). Time-box 25-35 min, then read solutions.
2. **Verbal**: always narrate; record yourself occasionally.
3. **System design**: practice drawing and talking; time 35-45 min.
4. **Behavioral**: out-loud answers, recorded.
5. **Mocks**: human mocks beat solo practice. Sources: friends, peers, mentors, community mock platforms, paid mock services (check quality and price yourself).
6. **Review loop**: after each mock, write 3 things done well, 3 to fix, add to a log.

## 5. Mock-interview schedule (suggested)
| Period | Cadence |
|---|---|
| Months 1-4 | None formal; solo timed practice, narrate aloud |
| Month 5-6 | 1 mock every 2 weeks (alternating coding / behavioral) |
| Month 7-9 | 1 per week (coding, design, behavioral rotating); first FDE scenario mocks |
| Month 10-12 | 2 per week in the 4 weeks before real loops; at least 2 full-loop simulations (4-5 consecutive rounds) |

## 6. Application strategy
- Referrals usually help get a resume read; reach out to people you genuinely know or engage with on professional channels, ask for advice before a referral.
- Target tiers: tier 3 (practice companies), tier 2 (good fits), tier 1 (dream). Interview in that order if possible.
- Track everything in a spreadsheet: company, role, date applied, contact, stage, next step, notes.
- Role titles vary (forward deployed engineer, solutions engineer, customer engineer, applied AI engineer, deployment strategist). Read the responsibilities, not just the title.

## 7. Negotiation basics
- Wait for a written offer before negotiating specifics; before that, deflect salary questions politely ("I'm focused on fit; I'm confident we can align on a range"). Rules on asking about pay history vary by location; do not assume.
- Know components: base, bonus, equity (vesting schedule, cliff, refresh), sign-on, relocation, level/title. Level matters as much as numbers.
- Research ranges from reputable sources and treat them as noisy.
- Be gracious and enthusiastic, ask for what you want with reasons (competing offers, market data), and ask for time to decide.
- Negotiate several items at once; use "Is there flexibility on ...?" phrasing.
- Never lie about competing offers.
- Get everything in writing. Consider taxes and benefits, and check legal/visa terms if relevant.
- Considering a lowball offer for experience: weigh learning, team, and growth, not only pay.

## 8. After each interview
- Within 30 minutes write what was asked and how you felt.
- Send a short thank-you note to the recruiter.
- If rejected, ask for feedback (often not given) and the re-application cooldown period; do not take it personally.
