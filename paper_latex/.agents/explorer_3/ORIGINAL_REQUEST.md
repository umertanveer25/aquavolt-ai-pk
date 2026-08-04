## 2026-08-03T15:56:38Z
You are Explorer 3: Memory Graph & Formatting Specialist for the AquaVolt-AI LaTeX manuscript overhaul.

Working Directory: C:\Users\umert\aquavolt-ai-pk\paper_latex\.agents\explorer_3

Your task:
1. Read `C:\Users\umert\aquavolt-ai-pk\paper_latex\sn-article.tex` and the skill instructions at `C:\Users\umert\.gemini\config\skills\tencentdb-agent-memory\SKILL.md`.
2. Extract and construct a persistent 4-tier knowledge graph (`memory_knowledge_graph.md`) capturing:
   - L0 Raw: key quotes and claims from sn-article.tex.
   - L1 Atomic Facts: quantitative results, baseline metrics, computational cost, hardware specs.
   - L2 Scenarios: contextual frameworks (e.g., zero-cost hardware deployment scenario, continuous 9-day sensor outage scenario, SOTA deep learning comparison scenario).
   - L3 Core Thesis Anchors:
     1. Zero-cost hardware ($0 infrastructure / low-power IoT constraints)
     2. SOTA outperformance (PIML / deep learning vs baseline statistical models)
     3. 9-day data imputation (continuous long-term missing sensor data recovery)
3. Audit Springer Nature (`sn-jnl.cls`) TeX formatting, citations (`sn-bibliography.bib`), figures (`fig1` to `fig4`), and tables for LaTeX compliance.
4. Write `C:\Users\umert\aquavolt-ai-pk\paper_latex\memory_knowledge_graph.md` (and a copy in your workspace `C:\Users\umert\aquavolt-ai-pk\paper_latex\.agents\explorer_3\memory_knowledge_graph.md`) and your handoff `C:\Users\umert\aquavolt-ai-pk\paper_latex\.agents\explorer_3\handoff.md`.
5. When done, send a message back to parent with your findings summary and file paths.
