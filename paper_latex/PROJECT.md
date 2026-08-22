# Project: AquaVolt-AI Springer Nature Research Paper

## Architecture
- **Document Class**: Springer Nature `sn-jnl.cls` (`\documentclass[pdflatex,sn-mathphys-num]{sn-jnl}`)
- **Bibliography Style**: `sn-mathphys-num.bst`, `sn-bibliography.bib` (45 real verified citations)
- **Target Output**: `sn-article.pdf` (20+ pages, 7,000+ substantive words, 0 fatal errors)
- **Layout Structure**:
  - Frontmatter: Title, Authors (Umer Tanveer, Kiran Falak Sher, Ahmad Khan), Affiliations (Dept of Computer Science), Structured Abstract (250 words: Background, Methods, Results, Conclusion), Keywords
  - Section 1: Introduction (1,500+ words)
  - Section 2: Materials and Methods (2,000+ words with formal PIML Arrhenius & Nernst Redox equations, 1D Richards vadose model, U-Net downscaling loss, Verra VM0042/AMS-III.H carbon formulas)
  - Section 3: Results and Validation (1,500+ words with 5 tables & 5 figures integrated)
  - Section 4: Discussion (1,500+ words)
  - Section 5: Conclusion
  - Backmatter: 7 Mandatory Declarations (Funding, Acknowledgement, Conflict of Interest, Data Availability, Ethics Statement, Author's Contribution, Generative AI Statement)
  - Bibliography: 45 references cited in-text

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Template & Frontmatter | `sn-jnl.cls`, author metadata, 2 affiliations, 4-part structured abstract, keywords | M1 | Survey E1 |
| 2 | Introduction Expansion | 1,500+ words covering global methane, Indus Basin, AWD agronomy, MRV gap, PIML paradigm, contributions | M1 | Survey E1, E2 |
| 3 | Materials & Methods | 2,000+ words with formal equations (Arrhenius, Nernst Redox, 1D Richards, U-Net PIML loss, Verra VM0042) | M1 | Survey E2 |
| 4 | Visuals Integration | 5 academic PNG figures embedded with complete captions & in-text references | M1 | Survey E3 |
| 5 | Tabular Data Integration | 5 academic tables embedded (SOTA, Sensors, ML performance, 8-year ledger, Statistical tests) | M1 | Survey E2, E3 |
| 6 | Results & Validation | 1,500+ words analyzing 8-year dataset, -53.60% avoided methane, ML benchmarks, 168h kinetics, economics | M1 | Survey E2 |
| 7 | Discussion Expansion | 1,500+ words on physical plausibility, atmospheric decoupling, climate resilience, policy, limitations | M1 | Survey E2 |
| 8 | Conclusion & Declarations | Concise synthesis + all 7 mandatory Springer Nature declarations | M1 | Survey E1 |
| 9 | 100% In-Text Citations | All 45 references in `sn-bibliography.bib` cited using `\cite{...}` | M1 | Survey E3 |
| 10 | LaTeX & BibTeX Build | Full compilation with 0 errors, 20+ pages output, 7,000+ words verified | M2 | Survey E1 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Complete Manuscript Writeup | Draft full 7,000+ word publication-grade `sn-article.tex` containing all sections, equations, 5 figures, 5 tables, 45 citations, and 7 declarations | Survey completed | PLANNED |
| M2 | Peer Review, Challenge & Forensic Verification Gate | Multi-agent gate (2 Reviewers, 2 Challengers, 1 Forensic Auditor) validating compilation, 0 errors, word count >7,000, 20+ pages, 100% citations, 5 figures/tables, and authentic scientific claims | M1 | PLANNED |

## Code Layout
- `sn-article.tex`: Main Springer Nature LaTeX manuscript
- `sn-jnl.cls`: Springer Nature class definition
- `sn-bibliography.bib`: 45 real academic references
- `figures/`: High-resolution PNG figures (fig1 to fig5)
