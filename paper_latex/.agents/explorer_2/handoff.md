# Handoff Report: Methods & Math Audit for AquaVolt-AI Manuscript

**Role**: Explorer 2 (Methods & Math Auditor)  
**Target File**: `C:\Users\umert\aquavolt-ai-pk\paper_latex\sn-article.tex`  
**Working Directory**: `C:\Users\umert\aquavolt-ai-pk\paper_latex\.agents\explorer_2`  
**Date**: August 3, 2026  

---

## 1. Observation

Direct observations from examining `sn-article.tex`, `sn-bibliography.bib`, and `generate_plots.py`:

1. **FAO-56 Equation Temporal Scale Mismatch (`sn-article.tex`, lines 126–128)**:
   - Verbatim LaTeX in manuscript:
     ```latex
     \begin{equation}
     ET_0 = \frac{0.408 \Delta (R_n - G) + \gamma \frac{900}{T + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}
     \end{equation}
     ```
   - Observed pipeline schedule in manuscript (`sn-article.tex`, lines 301–305):
     ```bash
     on:
       schedule:
         - cron: '0 * * * *' # Executes exactly at the top of every hour
     ```
   - The numerator constant $900$ is strictly for daily $\mathrm{ET}_0$, whereas the workflow runs hourly (where the FAO-56 constant is $37$).

2. **Omission of Soil Water Stress Factor $K_s$ (`sn-article.tex`, lines 132, 153)**:
   - Verbatim LaTeX in manuscript:
     ```latex
     ET_c = (K_{cb} + K_e) \times ET_0
     ```
   - Python implementation in `generate_plots.py` (line 54, line 121):
     `df['et0'] = df['etc'] / (df['ks'] * df['kc'])`
   - $K_s$ is used in code calculations but omitted from LaTeX equations.

3. **Absence of Vegetation Index to $K_{cb}$ Transfer Function (`sn-article.tex`, lines 137–147)**:
   - Text references $NDVI$ and $SAVI$ dictating $K_{cb}$ physical bounds, but provides no transfer equation.
   - Code in `generate_plots.py` (line 77) implements a logistic sigmoid transfer function:
     `kc_prior = 0.15 + 0.95 / (1 + np.exp(-12 * (ndvi_range - 0.4)))`

4. **PIML Loss Function Inconsistencies (`sn-article.tex`, line 158 & lines 338–353)**:
   - Verbatim LaTeX in manuscript (line 158):
     ```latex
     \mathcal{L}_{total} = MSE(y, \hat{y}) + \lambda \cdot \max(0, \widehat{ET_c} - ET_{max})^2
     ```
   - Code in Listing 2 (lines 344–352):
     ```python
     def forward(self, pred_etc, actual_etc, max_biological_etc):
         base_loss = self.mse(pred_etc, actual_etc)
         physical_violation = torch.relu(pred_etc - max_biological_etc)
         physics_loss = self.lambda_penalty * torch.mean(physical_violation**2)
         return base_loss + physics_loss
     ```
   - Both equation and code fail to penalize negative predictions ($\widehat{\mathrm{ET}}_c < 0$), violating text claims in Section 2.3.

5. **Missing 9-Day Imputation Mathematical Equations (`sn-article.tex`, Section 6, lines 223–240)**:
   - Manuscript asserts 9-day blackout PIML interpolation, but provides zero equations.

6. **Statistical Flaws & Insignificant Metrics (`sn-article.tex`, Table 1, lines 180–195)**:
   - Table 1 values: $\text{RMSE} = 0.3000\,\text{mm/day}$, $\text{MAE} = 0.2688\,\text{mm/day}$, $R = 0.2705$, $p = 0.3108$, $d = 0.4629$, $\text{NSE} = -5.0408$.
   - $p = 0.3108 > 0.05$ indicates correlation is statistically insignificant.
   - $\text{NSE} = -5.0408$ indicates prediction error exceeds observed variance.

7. **False Citation Benchmarking in Table 3 (`sn-article.tex`, Table 3, lines 260–273)**:
   - Table 3 cites `Jasechko2024` as "Pure LSTM/RNN" and `Gabriel2024` as "Spatial-Temporal GNNs".
   - `sn-bibliography.bib` entries reveal `Jasechko2024` is a groundwater decline study in *Nature*, and `Gabriel2024` is a computer science paper on maximum independent set algorithms.

---

## 2. Logic Chain

1. **Observation 1 & 2** $\rightarrow$ Equation (1) uses daily constant 900 for an hourly system, and Equation (2) omits $K_s$ while code relies on $K_s$. Therefore, physical baseline equations in Section 4 are mathematically incorrect and inconsistent with system implementation.
2. **Observation 3** $\rightarrow$ $NDVI$ to $K_{cb}$ transfer function exists in code (`generate_plots.py`) but is absent in LaTeX. Therefore, Section 4.2 has an incomplete evidence chain.
3. **Observation 4** $\rightarrow$ Equation (6) and Listing 2 only penalize upper bound overflow ($\widehat{\mathrm{ET}}_c > ET_{max}$) and ignore lower bound violations ($\widehat{\mathrm{ET}}_c < 0$). Therefore, the loss function fails to enforce the physical constraints claimed in Section 2.3.
4. **Observation 5** $\rightarrow$ Section 6 claims a 9-day PIML blackout imputation but provides zero mathematical equations. Therefore, the fault-tolerance claims lack technical formulation.
5. **Observation 6** $\rightarrow$ Table 1 reports $p = 0.3108$ (insignificant $R$) and $\text{NSE} = -5.0408$, while text claims "world-class predictive performance". Mathematical proof shows $\text{NSE} = 1 - \text{MSE}/\sigma^2_y$; when mid-summer observed variance $\sigma^2_y \to 0$, NSE becomes strongly negative despite small RMSE ($0.30\,\text{mm/day}$). Therefore, the text justification must be reframed around RMSE and low observed variance.
6. **Observation 7** $\rightarrow$ Table 3 attributes non-hydrology papers (`Jasechko2024`, `Gabriel2024`) as benchmark ET models. Therefore, Table 3 contains invalid baseline attributions that must be corrected.

---

## 3. Caveats

- **No Code Execution / Read-Only**: Analysis was conducted via static code inspection and LaTeX source auditing without modifying repository source files outside the `.agents/explorer_2/` directory.
- **Data Range Assumption**: Statistical proof for NSE collapse assumes a narrow temporal window (36 days in July–August) with low daily $ET_c$ variance ($\sigma^2_y \approx 0.015\,\text{mm}^2/\text{day}^2$).

---

## 4. Conclusion

The mathematical and methodological foundation of `sn-article.tex` requires targeted structural updates to achieve publication readiness for top-tier Springer Nature journals. The technical analysis report `analysis.md` provides exact, drop-in LaTeX code replacements for:
1. Hourly vs Daily FAO-56 Penman-Monteith formulations ($\mathrm{ET}_{0, \text{daily}}$ and $\mathrm{ET}_{0, \text{hourly}}$).
2. Dual crop coefficient equation with water stress factor $K_s$ ($\mathrm{ET}_c = (K_s K_{cb} + K_e) \mathrm{ET}_0$).
3. Sigmoid vegetation transfer function $K_{cb}^{\text{prior}}(NDVI)$.
4. Double-bounded PIML loss function $\mathcal{L}_{\text{total}}(\theta)$ penalizing both upper and lower physical violations.
5. Mathematical state-space persistence equations for the 9-day blackout imputation.
6. Explicit mathematical metric definitions and formal variance-based justification for $\text{NSE} = -5.0408$.

---

## 5. Verification Method

To independently verify these findings:
1. **Inspect Files**:
   - View `sn-article.tex` lines 126–160 (Equations 1–6), lines 180–195 (Table 1), lines 260–273 (Table 3), and lines 338–353 (Listing 2).
   - View `generate_plots.py` line 54, line 77, line 121.
   - View `sn-bibliography.bib` lines 66–72 (`Jasechko2024`) and lines 192–198 (`Gabriel2024`).
2. **Mathematical Verification**:
   - Check FAO-56 hourly constant ($37$) vs daily constant ($900$).
   - Check $\text{NSE} = 1 - \frac{\text{MSE}}{\sigma^2_y}$ with $\text{MSE} = 0.30^2 = 0.090$ and $\sigma^2_y = 0.015 \Rightarrow \text{NSE} = 1 - 6.0 = -5.00$.
3. **Invalidation Conditions**:
   - Findings 1–7 are invalidated if `sn-article.tex` already contains double-bounded loss functions, hourly $37$ FAO-56 constants, explicit $K_{cb}(NDVI)$ sigmoid equations, 9-day imputation formulas, and authentic SOTA citation benchmarks.
