Here’s a clean, low-risk homepage layout blueprint (Daily Mail–style) that will also eliminate duplicates across sections.

⸻

Homepage V1 Blueprint (Daily Mail–Style)

1) Non-negotiables
	•	One article appears once, max on the homepage.
	•	All blocks pull from one sorted master list (newestFirst).
	•	Every block consumes from the remaining pool via a shared usedIds set.
	•	Keep it local-first (ports 3000/8000) and only push to Render later.

⸻

2) Layout Structure (Top → Bottom)

A) Top Bar + Header
	•	Existing HomepageHeader
	•	Add a small subnav row (optional): Local | AI | Money | Property | Jobs

B) Lead Strip (Hero + Right Stack)

Row 1 (two columns):
	•	Left (Hero): 1 big story (image + headline + excerpt)
	•	Right (Stack): 4 compact headlines (small thumb optional)

Selection logic:
	•	Hero: first “local” (or Cheshire scoped), else newest
	•	Right stack: next 4 newest excluding hero

C) “Top Stories” Grid (optional but good)
	•	4 cards (2x2)
	•	Either “featured” flag, or fallback to next newest

D) Two Topic Blocks (AI + Money)

Two columns:
	•	AI & Tech: 6 items (compact cards)
	•	Money & Finance: 6 items

Each block pulls from remaining pool and filters by section/category.

E) “Latest” Rail
	•	10–20 latest items, compact list (no huge images)
	•	Infinite scroll later (not now)

F) Footer
	•	Existing NewsFooter

⸻

3) Data Pipeline Blueprint (Dedupe Engine)

Step 1 — Create one master list
	•	newestFirst = articles sorted by publishedDate desc

Step 2 — Allocate blocks in strict order

Use a single helper that “takes” articles from the pool and marks them as used:

Concept (no code yet):
	•	takeOne(predicate) → finds first match not used, marks used
	•	takeMany(n, predicate) → finds first n matches not used, marks used

Order:
	1.	hero = takeOne(isLocal) || takeOne(alwaysTrue)
	2.	rightStack = takeMany(4, alwaysTrue)
	3.	topStories = takeMany(4, isFeatured), if less than 4 → fill with newest
	4.	aiBlock = takeMany(6, isAI)
	5.	moneyBlock = takeMany(6, isMoney)
	6.	latest = takeMany(20, alwaysTrue)

This guarantees zero repeats.

⸻

4) UI Components (Minimal New Work)

You already have most components. You only need one small wrapper:

New wrapper component:

HomepageLeadRow
	•	Left: reuses HeroStoryCard
	•	Right: new CompactHeadlineList (simple mapping with links)

Everything else can reuse:
	•	TopStoriesGrid
	•	CompactArticleCard

⸻

5) Visual Match to Your Screenshot

Your screenshot shows:
	•	strong left hero
	•	right side stacked items
	•	then multi-row section blocks

This blueprint matches that pattern exactly, without redesigning the entire codebase.

⸻

6) What We Do Next (Very Controlled)

Next change should be ONLY:
	1.	Implement the “allocation order” (dedupe engine) inside HomePageV1
	2.	Replace current stacked sections with the lead row + right stack
	3.	Verify no repeats

No monetisation yet until layout is stable.

⸻

If you want, I’ll give you the exact “block allocation” code snippet for HomePageV1.jsx (safe, small, and readable) that replaces the broken regex/perl attempt—one patch at a time.
