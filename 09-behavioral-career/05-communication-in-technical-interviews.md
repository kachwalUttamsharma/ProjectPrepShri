# 05 - Communication in Technical Interviews

Interviewers cannot read your mind; they score what they hear. A correct silent solution often scores lower than a slightly flawed, well-communicated one.

## 1. Standard flow for a coding problem (about 35-45 min)
1. **Listen and restate** (1-2 min): "So given X, we need to return Y. Is that right?"
2. **Clarify** (2-3 min): input size and ranges, duplicates, empty input, negative values, sorted or not, memory limits, return format, what to do on invalid input.
3. **Examples**: write one normal and one edge case; walk through expected output.
4. **Brute force first** (2 min): state it and its complexity: "O(n^2), works but too slow for n = 10^5."
5. **Optimize**: name the bottleneck and the idea ("lookups are the bottleneck; a hash map makes it O(1)"). Agree on the approach before coding.
6. **Code** (15-20 min) while narrating intent, not every keystroke.
7. **Test verbally** (5 min).
8. **Complexity and trade-offs** (2 min).
9. **Follow-ups**: scale, streaming input, concurrency.

## 2. Thinking aloud
- Say the options you are weighing: "I could use a heap or sort; sorting is simpler, heap is better if k is small."
- Name the pattern: "This looks like sliding window."
- State invariants: "left always points at the start of a valid window."
- Narrate decisions, not syntax. Short sentences.
- Avoid long silences: if you need 30 seconds to think, say "let me think for a moment about X."
- Do not talk constantly while you need to focus; announce the pause.

## 3. Clarifying questions (templates)
- "Can the input be empty or null?"
- "What size are we talking about, roughly?"
- "Are values unique? Sorted? Can there be negatives?"
- "If there are multiple valid answers, any one, or a specific one?"
- "Should I optimize for time or memory?"
- "Can I assume the input is valid?"
For FDE practical rounds add: "What happens on API failure or timeouts?", "Is the data sensitive?", "Who consumes this output?"

## 4. Handling hints
- Hints are not failures; interviewers expect to give them. Taking a hint gracefully is a positive signal.
- Acknowledge: "Thanks, that suggests thinking about it as a graph problem."
- Restate how the hint changes your approach before continuing.
- Do not ignore the hint or become defensive. Do not fake having thought of it already.
- If you are stuck, ask a targeted question: "Would it help to consider a sorted order?" rather than "I don't know."
- Fewer hints is better, but a solved problem with hints beats an unsolved one.

## 5. Recovering from blanking
1. Breathe; say "Let me step back."
2. Return to a small concrete example and solve it by hand; narrate the steps.
3. Write the brute force, even if slow; it often reveals the optimization.
4. List patterns that match (hash map, two pointers, BFS, DP) and test each quickly against the example.
5. Simplify: solve a smaller version (one dimension, no constraints), then add back.
6. Ask for a nudge honestly: "I'm stuck choosing between A and B; can you tell me if I'm in the right direction?"
7. Do not apologize repeatedly; keep a neutral, curious tone.
Practice blanking deliberately in mocks so the recovery routine is automatic.

## 6. Testing your code verbally
- Trace the example line by line with variable values: "i = 0, seen = {}, ..."
- Test: normal case, empty, single element, duplicates, max boundaries, negative or zero, already sorted/reverse sorted, large input (performance).
- Watch for off-by-one, wrong loop bounds, mutated input, integer overflow (less in Python), uninitialized variables, shadowed names.
- When you find a bug, say so calmly and fix it: "I see the bug; the index should be i - 1."
- State complexity: "Time O(n log n) for sort, space O(n) for the map."
- Mention what you would test with unit tests if time remained.

## 7. Other round communication
- **System design**: state requirements and scale first, draw high-level boxes, then deep-dive on 1-2 components the interviewer cares about; state trade-offs explicitly ("this gives consistency but costs latency"). Check in: "Does this direction look good, or should I go deeper elsewhere?"
- **FDE case**: summarize their problem, ask discovery questions, state assumptions, propose phased plan.
- **Behavioral**: signpost: "I'll cover the context, what I did, and the result."
- **Remote**: look at the camera when summarizing, keep notes visible, share the screen only as needed, test mic and editor beforehand, close notifications.

## 8. Language and tone
- Prefer "we could" and "my instinct is... because" over "obviously".
- Admit gaps: "I haven't used X; here's how I'd reason about it."
- Disagree politely if the interviewer suggests something suboptimal: "Interesting; one concern is Y, how do you see it?"
- Be concise: answer the question asked, then pause.

## 9. Asking questions at the end
Interviewers form an impression from this. Prepare 3-5, tailored; avoid questions answered on the careers page.
- "What does success look like in the first 6 months in this role?"
- "What are the biggest technical or customer challenges the team is facing?"
- "How does the team handle on-call, incident review, and technical debt?"
- "How do engineers get feedback and grow? What does a typical week look like?"
- For FDE: "How are customer engagements staffed and how much time is spent on-site versus remote? How do field learnings reach the product team? What does a typical deployment look like end to end?"
- "What do you enjoy most and find hardest about working here?"
- Ask the recruiter: "What are the next steps and timeline?"
Avoid: compensation specifics with interviewers (use the recruiter), negative questions about the interviewer's personal life, or "no questions."

## 10. Practice drills
- Explain a solved LeetCode problem to a rubber duck in 3 minutes.
- Record one problem per week; review for silence, filler, unclear explanation.
- With a friend: they give only vague problem statements; you must clarify.
- Deliberately practice receiving hints: friend gives one hint after 10 minutes.
