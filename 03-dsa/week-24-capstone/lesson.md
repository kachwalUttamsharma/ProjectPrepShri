# Week 24: Capstone (mock interviews, cheat sheet, communication, prep checklist)

This week has no new algorithm. You rehearse the real thing: recognise the
pattern fast, communicate clearly, finish in time.

## 1. How to use this week
`exercises.py` has 10 problems grouped into three timed mock sets. Rules:
1. Set a visible timer for the whole set (A: 45 min, B: 50 min, C: 75 min).
2. Plain editor, no autocomplete, no looking up solutions. Docstring hints are allowed ONLY after you've burned half the question's budget (note that you used one).
3. Talk out loud (or record yourself). Follow the protocol in section 3.
4. Run the tests only when you believe you are done, like a real interviewer saying "does it work?". Count how many attempts you needed.
5. After each set: write down what slowed you down, then redo the weakest problem from scratch the next day.
Suggested schedule (7-8 hrs): Set A + review (1.5h), Set B + review (1.5h), Set C + review (2h), cheat sheet / weak-topic drills (2h), final checklist (1h).

Mock sets:
- Set A, phone screen, 45 min: group_anagrams (10), length_of_longest_substring (15), merge_k_lists (20).
- Set B, onsite trees/graphs, 50 min: lowest_common_ancestor (15), num_islands (15), can_finish (20).
- Set C, stretch, 75 min: top_k_frequent (15), word_break (20), generate_parentheses (15), network_delay_time (25). Aim for 3 of 4 clean.
Scoring: full marks = tests green at first run, correct complexity stated, no hints. Passing bar for a Google/Uber-style loop: 2 of 3 per set clean, remaining one close with a correct approach.

## 2. Pattern-recognition cheat sheet
| Signal in the problem | Pattern | Tool / Complexity |
|---|---|---|
| Sorted array, find pair/target | Two pointers / binary search | O(n) / O(log n) |
| Contiguous subarray/substring with a constraint | Sliding window | O(n) |
| Subarray sum equals k, range sums | Prefix sums + hash map | O(n) |
| Lookups, duplicates, grouping, counting | Hash map / set / Counter | O(n) |
| Matching brackets, next greater element, nested structure | Stack / monotonic stack | O(n) |
| Level by level, shortest path unweighted | BFS (deque) | O(V+E) |
| Linked list cycle, middle, k-th from end | Fast/slow pointers, dummy node | O(n), O(1) |
| "Minimum X such that condition holds" with monotonic check | Binary search on the answer | O(n log range) |
| Top K, K-th largest, merge K sorted, running median | Heap (heapq) | O(n log k) |
| Tree traversal, path sums, LCA, depth | DFS recursion (post-order returns info up) | O(n), O(h) |
| BST property, kth smallest, validate | Inorder traversal / bounds | O(n) / O(h) |
| Prefix search, autocomplete, word dictionary | Trie | O(L) per op |
| Connected components, islands, flood fill | DFS/BFS or union-find | O(V+E) |
| Dependencies, ordering, cycle in directed graph | Topological sort (Kahn / DFS colors) | O(V+E) |
| Dynamic connectivity, "are they in the same group" | Union-find | ~O(alpha(n)) |
| Weighted shortest path, non-negative | Dijkstra (heap) | O((V+E) log V) |
| Weights only 0/1 | 0-1 BFS (deque, appendleft for 0) | O(V+E) |
| Generate all combos/permutations/subsets, constraint pruning | Backtracking | exponential, prune |
| Count ways / min cost / max value with overlapping subproblems | 1-D DP | O(n*k) |
| Two sequences or grid or knapsack | 2-D DP | O(m*n) |
| Local best choice provably works (intervals, jumps, scheduling) | Greedy + sort | O(n log n) |
| Find unique / missing, subsets of small n, flags | Bit manipulation / bitmask | O(n) / O(2^n) |
| Input is small (n <= 20) | Exponential brute force is intended | bitmask / backtracking |
| n up to 1e5 or 1e6 | Need O(n) or O(n log n) | rules out O(n^2) |
Constraint trick: n <= 20 -> 2^n; n <= 500 -> n^3; n <= 1e4 -> n^2; n <= 1e5+ -> n log n.

## 3. How to communicate in an interview
Use the same protocol every time (aim: first 5-8 minutes before any code).
1. **Restate** the problem in your own words.
2. **Clarify** inputs: size, duplicates, negatives, empty input, sorted?, in-place?, return type, can I mutate the input? Ask about expected scale.
3. **Examples**: walk one normal case and one edge case with the interviewer.
4. **Brute force first**: say it and its complexity ("that's O(n^2), let me look for better"). Shows you can always produce something.
5. **Optimise** by naming the bottleneck and the pattern ("repeated lookup -> hash map").
6. **Agree** on the approach and complexity before coding ("Does this sound reasonable?").
7. **Code** with meaningful names, small helpers, narrate non-obvious lines. Don't go silent for more than ~30 seconds.
8. **Test** by hand-tracing a small example, then edge cases (empty, one element, duplicates, all same, max size). Find your own bugs before they do.
9. **Analyse** time and space, and mention trade-offs and follow-ups.

Useful phrases:
- "Let me make sure I understand..." / "Can I assume...?"
- "The naive approach is X in O(...). The bottleneck is Y."
- "I'll start with a simple version and optimise after."
- "I'm stuck on Z; let me try a smaller example." (thinking aloud while stuck is fine and expected)
- "I made a mistake here, fixing..." (calm, no panic)

When stuck: shrink the input, draw it, reverse (what would the last step be?), try a different data structure, ask for a hint early (a hint at minute 15 beats silence until minute 35).
When the interviewer adds a follow-up ("what if the stream is infinite / memory is limited / sorted input"): treat it as expected, not as a sign you were wrong.
Google specifics: strong on correctness, clean code, edge cases, and clear trade-off discussion; expect a follow-up that changes constraints.
Uber specifics: practical problems (graphs, grids, intervals, heaps, geo/matching flavour), working code, sometimes a coding round that looks like a mini-service or data-processing task; discuss complexity and scale.

## 4. Common mistakes in mocks
- Jumping to code before agreeing on the approach.
- Not stating complexity unprompted.
- Skipping the dry run; shipping off-by-one bugs.
- Silent debugging. Narrate it.
- Over-optimising early or going for a fancy structure when a hash map works.
- Forgetting empty / single-element / duplicate inputs.
- Recursion depth on a deep tree or big grid in Python (use iterative, or say you know the limit).
- Comparing nodes in a heap tuple without a tiebreaker index.
- Mutating input unexpectedly.

## 5. Google/Uber-style prep checklist
Content
- [ ] Can solve a new medium in 25-30 min and a hard in 40-45 min about 70% of the time.
- [ ] For each pattern in the cheat sheet, I can write the template from memory: sliding window, binary search (both variants), BFS/DFS (tree and grid), Kahn, Dijkstra, union-find with path compression, trie, backtracking, 1-D and 2-D DP, heap top-K.
- [ ] I can state time/space for everything I write without calculating.
- [ ] I know Python tools cold: `heapq` (min-heap, negate for max), `collections.deque/Counter/defaultdict`, `bisect`, `functools.cache`, `itertools`, slicing cost (copies are O(k)), `sorted(key=...)`, `sys.setrecursionlimit` and its risks.
- [ ] I've done at least 3 timed mocks per week for the last 2 weeks (this folder counts as one cycle).
- [ ] I keep an error log: problem, mistake type, fix; I reread it weekly.
Practice
- [ ] Practise on a plain editor or a shared doc (Google interviews often use a doc/CoderPad-style environment without autocomplete or running tests).
- [ ] Do 1-2 mocks with a human (peer, or a mock platform) to practise talking.
- [ ] Rehearse follow-ups: "what if it doesn't fit in memory", "streaming input", "concurrent access", "can you do it in O(1) space".
- [ ] Review fundamentals: hash table internals, heap vs balanced BST, BFS vs DFS trade-offs, amortised analysis, recursion vs iteration, stability of sorts.
Logistics
- [ ] Interview day: sleep, water, a quiet place, charged laptop, test the video/IDE setup.
- [ ] Prepare 4-5 behavioural stories (conflict, failure, ambiguity, leadership, impact) with the STAR structure. Google's "Googleyness" and Uber's values both probe these.
- [ ] Prepare questions to ask the interviewer.
- [ ] If the role is senior: prepare for a system design round too (separate track, not covered by this repo).
- [ ] During the loop: reset between rounds; a bad round does not predict the next.

## 6. Final week plan after the mocks
- Pick the 3 weakest patterns from your error log; redo 3 problems each (no peeking, timed).
- Re-solve every problem you needed hints on, 2 days later, from scratch.
- Day before the interview: light review of the cheat sheet and templates only. No new hard problems.

## Your task
Do the three mock sets in `exercises.py` under timer. Run
`/Users/uttam.sharma/Desktop/python/.venv/bin/pytest -q` from this folder,
and use `pytest -q -k lca` style filters to run a single question.
