---
name: academic-research-writer
description: Write academic research documents following academic guidelines with peer-reviewed sources from Google Scholar, IEEE Xplore, PubMed, and other academic databases. Always verify source credibility and generate IEEE standard references. Use for research papers, literature reviews, technical reports, theses, dissertations, conference papers, and academic proposals requiring proper citations and scholarly rigor.
---

# Academic Research Writer

This skill enables creation of high-quality academic research documents with proper scholarly standards, verified peer-reviewed sources, and IEEE-format citations.

## Core Principles
- **Academic Rigor:** Follow scholarly writing conventions and maintain objectivity.
- **Source Verification:** Use only peer-reviewed, credible academic sources.
- **Proper Citation:** Generate accurate IEEE-format references.
- **Research Integrity:** Ensure all claims are supported by verified sources.

---

## Workflow

### 1. Understanding Requirements
Clarify the research document type and requirements:
- Document type (research paper, literature review, thesis chapter, conference paper, etc.)
- Research topic and scope
- Target length and word count
- Specific guidelines (institution, journal, conference, IEEE 2-column format)
- Required sections
- Deadline considerations

### 2. Research Planning
Develop a research strategy:
- Identify key research questions
- Define search terms and keywords
- Determine relevant academic databases (Google Scholar, IEEE Xplore, PubMed, ACM Digital Library, ScienceDirect, arXiv)
- Establish inclusion/exclusion criteria for sources
- Plan document structure

### 3. Source Discovery and Verification

#### Finding Sources:
Use academic database searches and literature discovery tools:
- **Google Scholar:** `scholar.google.com`
- **IEEE Xplore:** `ieeexplore.ieee.org`
- **PubMed / NCBI:** `pubmed.ncbi.nlm.nih.gov`
- **ACM Digital Library:** `dl.acm.org`
- **arXiv:** `arxiv.org` (for preprints in computer science and quantitative biology)
- **Europe PMC & OpenAlex:** for broad open-access literature metadata

#### Search Strategy:
- Start with broad conceptual searches: `"distributed health interoperability"`
- Refine with specific technical terms: `"FHIR R4 cryptographic audit trail 2024"`
- Use quotation marks for exact phrases: `"zero-knowledge break-the-glass"`
- Combine terms strategically with boolean logic: `("ABDM" OR "national health") AND ("ECDH" OR "AES-GCM")`
- Prioritize recent publications (last 5–7 years unless historical seminal context is needed)

#### Verification Checklist:
For each source, verify:
- [ ] Published in a reputable peer-reviewed journal or IEEE/ACM conference proceedings
- [ ] Author credentials and verified institutional affiliation
- [ ] Publication venue reputation and impact factor
- [ ] Citation count and community adoption
- [ ] Methodology soundness and statistical rigor
- [ ] Direct relevance to the research question

#### Red Flags to Avoid:
- Predatory journals (unindexed, lack of rigorous peer review)
- Non-academic blogs, forums, or marketing whitepapers cited as scientific fact
- Unverified preprints with unvalidated empirical claims
- Pay-to-publish venues without legitimate editorial review

---

## 4. Document Structure

### Research Paper (IEEE Standard):
1. **Title:** Authoritative, specific, and descriptive of scientific contribution
2. **Abstract:** 150–250 words summarizing problem, methodology, findings, and empirical validation
3. **Index Terms / Keywords:** 5–10 authoritative terms
4. **Section I: Introduction:**
   - Background and real-world clinical/technical context
   - Problem statement and research gaps
   - Summary of explicit scientific contributions
   - Paper organization roadmap
5. **Section II: Related Work / Literature Survey:**
   - Thematic categorization of previous approaches
   - Comparative evaluation matrix (e.g., Table I: Summary of Related Approaches)
   - Identified architectural and empirical research gaps
6. **Section III: System Architecture & Mathematical Formulations:**
   - Threat model and adversary assumptions
   - Architecture topology and data flows
   - Mathematical formulations, cryptographic proofs, and algorithm pseudocode
7. **Section IV: Implementation Details:**
   - Environment, toolchain, execution constraints, and test vectors
8. **Section V: Results & Discussion:**
   - Empirical latency, throughput, and memory benchmarks
   - Statistical significance testing (e.g., Wilcoxon signed-rank, Student's $t$-test with $p < 0.001$)
   - Limitations and edge cases
9. **Section VI: Conclusion & Future Work:**
   - Summary of outcomes and operational impact
   - Avenues for subsequent research
10. **References:** Strict IEEE format

### Literature Review:
1. Title & Abstract
2. Introduction & Scope
3. Review Methodology & Inclusion Criteria
4. Thematic Analysis Sections
5. Synthesis, Gap Identification & Research Agenda
6. References (IEEE format)

---

## 5. Writing Guidelines

### Academic Tone:
- Use formal, objective, and precise scientific prose.
- Write in third person (or precise first-person plural for authors: "We formulate...", "Our evaluation demonstrates...").
- Use precise technical and mathematical terminology.
- Maintain a neutral, evidence-based stance.
- Use hedging language where appropriate (*suggests*, *indicates*, *exhibits*).

### Paragraph Structure:
- **Topic Sentence:** Establishes the core theoretical or empirical claim.
- **Supporting Evidence:** Empirical metrics, citations, mathematical proofs, or experimental observations.
- **Analysis & Interpretation:** Scholarly synthesis linking evidence back to research questions.
- **Transition:** Logical bridge to the next conceptual section.

### Citation Integration:
- Introduce sources with academic context.
- Use signal phrases: *"According to Smith et al. [1]...", "Prior investigations by Sharma and Patel [2] demonstrate that..."*
- Balance direct quotations (use extremely sparingly) with authoritative paraphrasing.
- Cite after every factual claim derived from external literature.
- Use consecutive bracketed numerals: `[1]`, `[2]`, `[3]–[5]`.

---

## 6. IEEE Reference Format

Format citations strictly according to IEEE standards:

### Journal Article:
```text
[1] A. Author, B. Author, and C. Author, "Title of article," Abbrev. Title of Journal, vol. x, no. x, pp. xxx-xxx, Month, Year, doi: 10.1109/XXX.2024.XXXXXX.
```

### Conference Paper:
```text
[2] A. Author and B. Author, "Title of paper," in Proc. Title of Conf., City, Country, Year, pp. xxx-xxx.
```

### Book:
```text
[3] A. Author, Title of Book, xth ed. City, State: Publisher, Year.
```

### Book Chapter:
```text
[4] A. Author, "Title of chapter," in Title of Book, xth ed., B. Editor, Ed. City, State: Publisher, Year, pp. xxx-xxx.
```

### Technical Report / Standard:
```text
[5] Title of Standard, Standard Number, Corporate Author/Organization, Year.
[6] A. Author, "Title of report," Organization/Institute, City, State, Rep. TR-XXX, Month, Year.
```

### Key IEEE Rules:
- Number references consecutively in order of their appearance in the text.
- For $\le 6$ authors, list all names. For $> 6$ authors, list the primary author followed by *et al.*
- Use initials for first and middle names (e.g., *S. Swarn*).
- Abbreviate standard journal names per IEEE guidelines (e.g., *IEEE Trans. Knowl. Data Eng.*).
- Include Digital Object Identifiers (DOI) whenever available.

---

## 7. Quality Assurance Checklist

Before finalizing any academic document:
- [ ] **Research Objective:** Clear research problem statement and explicit contributions articulated upfront.
- [ ] **Empirical Rigor:** Claims substantiated by quantitative benchmarks, mathematical models, or verified literature citations.
- [ ] **Citation Coverage:** Adequate scholarly breadth ($\ge 15–25$ peer-reviewed references for capstone/conference papers).
- [ ] **Reference Parity:** 100% agreement between in-text citations `[x]` and the numbered bibliographic reference list.
- [ ] **Tone & Integrity:** Formal academic voice, zero colloquialisms, zero emojis, and complete absence of uncredited claims.
- [ ] **Formatting:** Clean IEEE 2-column LaTeX (`.tex`) or publication Markdown (`.md`) with KaTeX/LaTeX mathematical rendering.

