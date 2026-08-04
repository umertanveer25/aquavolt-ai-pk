# Project: AquaVolt-AI LaTeX Manuscript Overhaul

## Architecture
- Manuscript source: `sn-article.tex` (Springer Nature format)
- Bibliography: `sn-bibliography.bib`
- Class & Style: `sn-jnl.cls`, `sn-mathphys-num.bst`
- Figures: `fig1_prisma_final.png`, `fig2_process_final.png`, `fig3_countries_final.png`, `fig4_venues_final.png`, `figures/`
- Output artifacts:
  - `sn-article.tex` (Overhauled LaTeX source)
  - `sn-article.pdf` (Compiled 18-page publication-ready PDF)
  - `peer_review_report.md` (Exhaustive Q1 Reviewer 2 audit report)
  - `memory_knowledge_graph.md` (Persistent L2/L3 claims knowledge graph)
  - `graphify-out/GRAPH_REPORT.md` (Graphify codebase & manuscript knowledge graph)

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Exploration, Critique & Knowledge Graph | Audit manuscript, build L2/L3 memory graph, draft review report | none | DONE |
| 2 | Aggressive Manuscript Rewrite | Overhaul `sn-article.tex` section-by-section to Q1 standards | M1 | DONE |
| 3 | Verification & Compilation Check | Compile LaTeX to PDF, verify Q1 tone and zero regressions | M2 | DONE |
| 4 | Forensic Audit & Final Review | Audit for integrity, fake claims, and formatting compliance | M3 | DONE |

## Interface Contracts
- `memory_knowledge_graph.md` defines core thesis anchors:
  1. Zero-cost hardware ($0 infrastructure / low-power IoT constraints)
  2. SOTA outperformance (PIML / deep learning vs baseline statistical models)
  3. 9-day data imputation (continuous long-term missing sensor data recovery)
- `peer_review_report.md` documents line-by-line / section-by-section changes and justification.
- `sn-article.tex` maintains full Springer Nature (`sn-jnl.cls`) compatibility and compiles cleanly to an 18-page PDF (`sn-article.pdf`).
