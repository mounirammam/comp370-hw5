# COMP 370/570 – Homework 5: Conceptual Questions

## 1. Use case for the technical exercise

**Stakeholder:** The NYC Mayor's Office of Operations, together with the 13-member 311 oversight working group of City Council (sponsored by the council members who represent outer-borough districts).

**Situation:** Council members keep hearing from constituents that "nothing gets fixed in our neighbourhood." Some say their noise, heat/hot-water, and illegal-parking complaints sit open for days, while similar complaints in Manhattan get closed in hours. The city has committed in its equity agenda to delivering services evenly across neighbourhoods, but right now nobody can check the claim quickly. Answering it today means filing a request with the data team and waiting a week for a one-off spreadsheet.

**What they need:**
1. A quick, repeatable way to find out *which kinds of complaints dominate in each borough* during a given period. Agencies use this to plan staffing, e.g. whether HPD needs more heat inspectors in the Bronx in January. That's the CLI tool (Task 1) and the analysis built on it (Task 3).
2. A self-serve dashboard where an official can pick any two zipcodes (say, the one a constituent lives in and a comparison zipcode) and see month by month how long 311 incidents take to close in each, compared to the citywide average (Task 4). Officials would bring it to oversight hearings and budget negotiations, and use it to target follow-up: "Zipcode 10456 has been 2× the city average for six straight months. Which agency is driving that?"

**Why it is worth doing:** The data is already public (NYC Open Data), so there's no new collection cost. Making it explorable turns anecdotes into evidence and gives the city a way to measure whether interventions narrow the gap. It also lets the city answer press and public-records requests about service equity in minutes instead of weeks.

**Success criteria:** An official with no technical training can answer "is zipcode A served more slowly than zipcode B, and since when?" in under a minute. The dashboard updates in under 5 seconds and can be refreshed by re-running the pre-processing script when new data is published.

---

## 2. Refining "We'd like to understand how much characters talk across the My Little Pony series."

I refine the question one ambiguity at a time. At each step I name the vague part, make an operational decision (there's no stakeholder to ask, so I choose and justify), and rewrite the question.

**Step 0: Original question.**
> We'd like to understand how much characters talk across the My Little Pony series.

**Step 1: Which data / what is "the series"?**
"The series" could mean *Friendship is Magic*, the newer *G5* shows, the movies, or the comics. We have a transcript dataset for *Friendship is Magic* (`clean_dialog.csv`, used in HW4: 36,859 lines over 197 episodes with columns `title, writer, pony, dialog`). So I fix the scope to that.
> How much do characters talk across the 197 episodes of *My Little Pony: Friendship is Magic*, as recorded in the `clean_dialog.csv` transcripts?

**Step 2: Who counts as a "character"?**
The `pony` column has 842 distinct speakers. Many of them are one-off background ponies, groups ("Crowd", "All"), the "Narrator", or combined speakers ("Twilight and Spike"). Including all of them would bury the answer. Following HW4, I focus on the six main characters (the "Mane Six": Twilight Sparkle, Rainbow Dash, Pinkie Pie, Applejack, Rarity, Fluttershy). I match on the exact speaker name, so lines attributed to multiple speakers are excluded and lines from groups or the narrator are not counted.
> How much do each of the Mane Six talk across the 197 episodes of *Friendship is Magic*?

**Step 3: What does "how much ... talk" mean (the measurement)?**
Options include number of lines, number of words, or screen time. Screen time isn't in the data. A "line" in the transcript is one uninterrupted speech turn, but turns vary a lot in length, so I use **words spoken** as the primary measure (whitespace-tokenized words in the `dialog` field) and **number of lines** as a secondary measure.
> How many words (and lines) does each of the Mane Six speak across the 197 episodes of *Friendship is Magic*?

**Step 4: Absolute or relative?**
Raw counts are hard to interpret ("Rarity spoke 41,000 words": is that a lot?). "How much" really asks about each character's *share* of the conversation. I report each character's words as a **percentage of all words spoken in the series by any speaker**. Lines are reported the same way.
> What percentage of all words (and lines) of dialogue in *Friendship is Magic* is spoken by each of the Mane Six?

**Step 5: What does "across the series" mean, total or over time?**
"Across" could mean one aggregate number or how the share changes through the show. A stakeholder interested in character presence would likely want both. I compute the overall share, plus the share **per season** (episodes grouped by season, in air order) so we can see if a character's role grows or shrinks.
> **Final data science question:** For each of the six main characters of *My Little Pony: Friendship is Magic* (Twilight Sparkle, Rainbow Dash, Pinkie Pie, Applejack, Rarity, Fluttershy), what percentage of all words and of all dialogue lines in the `clean_dialog.csv` transcripts did they speak, (a) over the whole series (197 episodes) and (b) per season? Only lines attributed solely to that character count.

That question is operationally clear. Two analysts given the same CSV would compute the same numbers.

---

## 3. Why state maintenance is hard in a Jupyter notebook

A notebook *looks* like a linear script, but its actual state is the Python kernel's memory. That memory reflects the order you happened to run cells in, not the order they appear on the page.

- **Out-of-order execution.** You can run cell 7, then cell 3, then edit and re-run cell 5. The variables now in memory came from a sequence nobody can see. The `In [n]` counters hint at it but are easy to miss, and they're lost once you re-run.
- **Hidden state from deleted or edited cells.** If you define `df_clean` in a cell and later delete or rewrite that cell, `df_clean` still exists in the kernel. Downstream code keeps working for you but will crash (or silently use different logic) for anyone who runs the notebook fresh.
- **Mutation in place.** Cells like `df['x'] = df['x'] * 100` or `df.dropna(inplace=True)` change state every time they run. Running a cell twice gives a different result than running it once, so a cell isn't a self-contained unit.
- **Saved outputs disagree with the code.** The `.ipynb` stores outputs from whenever each cell last ran. The charts and numbers you see may have come from an older version of the code or data, and nothing warns you.
- **Long-running kernels and external state.** Imported modules that you've since edited aren't reloaded. Files written by earlier runs, environment variables, and the working directory all persist across sessions in ways that aren't recorded in the notebook.

The only reliable defence is discipline: regularly use "Restart kernel & Run All", avoid in-place mutation, and keep each cell idempotent. The tool doesn't enforce any of this, which is why state management in notebooks is hard.

---

## 4. Why a Jupyter notebook beats a README for sharing a data science project with future data scientists

A README *describes* an analysis. A notebook *is* the analysis, with the description woven in. For a future data scientist, that difference matters for several reasons:

1. **Code, narrative and results live together.** A notebook interleaves markdown explanation ("we drop negative response times because..."), the exact code that does it, and the output it produced (tables, plots, counts). A README can only point at scripts and paste static screenshots, which go stale. The reader has to assemble the story themselves.
2. **It is executable and verifiable.** A future data scientist can re-run the notebook top to bottom, confirm they get the same numbers, and check that the claims follow from the code. Instructions in a README ("run `clean.py`, then `model.py --flag`...") can be wrong, incomplete, or out of date, and nothing tests them.
3. **It shows intermediate steps, not just conclusions.** Data scientists care about *how* you got there: what the raw data looked like, what got filtered, distributions, sanity checks, dead ends. A notebook keeps those intermediate outputs visible. A README usually reports only the final result.
4. **It is a ready starting point for further work.** Someone extending the project can change a parameter (a date range, a zipcode) in one cell and immediately see how the downstream results change. Exploration starts from the original author's working state instead of from a blank script.
5. **Rich output.** Inline interactive plots, rendered dataframes and widgets communicate much more than text. GitHub also renders `.ipynb` files, so the outputs can be read even without running anything.

(A good project still has a short README telling people how to set up the environment and which notebook to open. But as the record of *the analysis itself* for a technical audience, the notebook is far more useful.)
