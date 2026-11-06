# Academic Writing Conventions & Scholarly Style Guide

## 1. Voice and Objectivity
- **Formal Register:** Maintain an objective, disciplined, and scholarly voice. Avoid informal idioms, rhetorical questions, and emotional adjectives (*amazing, incredible, groundbreaking* without metric proof).
- **Hedging & Precision:** In empirical research, use qualified assertions:
  - Strongly proven: *"The empirical results establish that..."*
  - Statistically indicative: *"The observed latency distribution indicates that..."*
  - Theoretical limit: *"Under high contention, throughput tends to saturate at..."*
- **Mathematical Formulations:** Always define variables upon introduction. Use consistent mathematical notation across equations, figures, and algorithm listings.

## 2. Structural Composition
- **Abstract Structure:**
  1. *Background / Problem Context* (1–2 sentences)
  2. *Specific Technological Bottleneck / Research Gap* (1–2 sentences)
  3. *Proposed Architecture / Paradigm* (2–3 sentences)
  4. *Empirical Validation / Key Quantitative Results* (2 sentences)
  5. *Significance / Deployment Impact* (1 sentence)
- **Introduction Flow:**
  - Macro context $\rightarrow$ Specific engineering domain $\rightarrow$ Current limitations in literature $\rightarrow$ Articulation of core scientific contributions $\rightarrow$ Paper roadmap.
- **Related Works Structure:**
  - Group existing literature by architectural taxonomy rather than author-by-author summaries.
  - Conclude with a comparative table highlighting unaddressed challenges.

## 3. LaTeX and Mathematical Formatting
- Use standard IEEE Transactions environments:
  - `\begin{equation} ... \end{equation}` for numbered core formulas.
  - `\begin{table*}[t] ... \end{table*}` for 2-column wide comparative matrices.
  - KaTeX rendering for Markdown equivalents: `$$...$$` on dedicated display lines.

