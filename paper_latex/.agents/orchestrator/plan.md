# Execution Plan: AquaVolt-AI Manuscript Overhaul

## Overview
Transform `sn-article.tex` into a top-tier Q1 journal publication following Springer Nature guidelines, incorporating `the-agency-ai` role-based critique and `tencentdb-agent-memory` L2/L3 knowledge graph preservation.

## Phase 1: Exploration, Multi-Agent Critique & Memory Graph Construction
- Dispatch `teamwork_preview_explorer` agents acting as:
  1. Lead Reviewer / Q1 Editor (Audit abstract, intro, flow, tone, claims)
  2. Methods Auditor (Audit PIML math, statistical rigor, equations, dataset descriptions)
  3. Formatting & Memory Specialist (Build L2/L3 knowledge graph of core claims, check Springer Nature TeX formatting)
- Aggregate reports into:
  - `peer_review_report.md` (initial review findings)
  - `memory_knowledge_graph.md` (L0-L3 memory tiers of thesis anchors)

## Phase 2: Aggressive Rewrite of `sn-article.tex`
- Dispatch `teamwork_preview_worker` to overhaul `sn-article.tex` paragraph by paragraph:
  - Elevate academic phrasing and remove conversational or weak expressions.
  - Strengthen mathematical derivations and notation consistency.
  - Integrate L2/L3 thesis anchors (Zero-cost hardware, SOTA outperformance, 9-day imputation).
  - Update `peer_review_report.md` with action items resolved.

## Phase 3: Review, Verification & Compilation
- Dispatch `teamwork_preview_reviewer` to review rewritten text against Q1 standards and ensure no lost facts.
- Dispatch `teamwork_preview_worker` or `teamwork_preview_challenger` to compile `sn-article.tex` to PDF and verify latex compilation logs.

## Phase 4: Forensic Audit & Final Signoff
- Dispatch `teamwork_preview_auditor` to conduct integrity audit.
- Finalize `peer_review_report.md` and `handoff.md`.
