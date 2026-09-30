# Low-altitude corridor: reproducible figures

**Reproducible code, parameters, and plotting instructions for all eight figures** in the September 30, 2026 Overleaf version of *When Does Congestion Justify Access Charges? Pricing, Auctions, and Capacity Release in Low-Altitude Logistics Corridors*.

This repository independently implements the formulas in the paper and appendix and checks the numerical results against the original figures. The Overleaf file tree did not contain the original plotting scripts. This is therefore a **reconstruction from equations and numerical results**, not a recovery of the authors' original code or a claim of pixel-for-pixel or byte-for-byte identity. Extracted original figures are in `reference_figures/`; regenerated figures are in `figures/`.

## Reproduce all figures

Verified with Python 3.13, NumPy 2.4.6, SciPy 1.17.1, and Matplotlib 3.10.6.

```bash
git clone https://github.com/yqdiao/low-altitude-corridor-reproducibility.git
cd low-altitude-corridor-reproducibility
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python reproduce.py
python -m unittest discover -s tests -v
```

On Windows, activate the environment with `.venv\Scripts\activate`. Plotting does not require LaTeX, Overleaf or GitHub access, or downloads of measured data. Every figure comes from the paper's analytical formulas and one-dimensional numerical root finding. There is no random sampling and no random seed is needed.

To generate one figure or use another output directory:

```bash
python reproduce.py --figure 7
python reproduce.py --config config/parameters.json --output /tmp/corridor-results
```

Edit [config/parameters.json](config/parameters.json) to change parameters. Each grid's three numbers are `[start, end, number of points]`. Parameter changes may move a candidate solution outside the paper's assumed domain; the program reports an error or marks invalid data rather than treating an extrapolation as an equilibrium.

## Figure overview

| Figure | Filename | Horizontal axis / specific parameters | Method |
|---|---|---|---|
| 1 | `fig1_revenue_ranking` | N = 0.02–3.5; Δ=2 | Non-strategic bidding, piecewise VCG, and affine MUPA revenue |
| 2 | `fig2_mechanism_quantities` | α=1–4; A: Δ=7.5; B: Δ=10, mean cost=6 | Model A interior/exit solutions; Model B supply candidate and valid domain |
| 3 | `fig3_objective_ratio` | α=1–3.5; Δ=0, 2, 4 | OF_M / OF_A at each mechanism's own optimum |
| 4 | `fig4_coordination_threshold` | Δ=0–5; K=2.5 | Maximum repeated-game threshold across the two operators |
| 5 | `fig5_capacity_comparison` | R=1.3–8; α=2, r=30 | Nash and coordinated capacity; intersection at R=b+3κ=4 |
| 6 | `fig6_state_contingent_release` | K=0.55–4.5; α=1.5; a_L=12, a_H=20 | Positive root of the release first-order condition, capped at N≤K |
| 7 | `fig7_investment_uncertainty` | s=0–6 / high-state probability=0–1; α=1.5, δ=.9, r=30 | Statewise release plus the investment-envelope root |
| 8 | `fig8_regime_maps` | B/b and κ/b=0–3; Δ=0–10, K=.6–5.2 | Static thresholds plus a one-shot zero-price equilibrium test |

For formulas, parameter meanings, and a line-by-line account of each plot, see the [detailed figure guide](docs/figure_guide_zh.md). For source provenance and validation, see the [provenance and validation record](docs/provenance_and_validation.md).

## Repository contents

- `corridor/models.py`: model equations, piecewise solutions, validity checks, and numerical solvers.
- `reproduce.py`: plotting for eight figures and CSV exports.
- `config/parameters.json`: all numerical parameters, scan ranges, and grid sizes.
- `figures/`: eight vector PDFs and eight 300 dpi PNGs.
- `data/`: ten CSV files, including panel data, domain-validity flags, and root residuals.
- `reference_figures/`: eight original vector figures extracted from the compiled paper, plus source hashes.
- `tests/`: ten automated tests covering independent optimizers, accounting identities, paper values, and boundaries.
- `scripts/`: optional tools to extract original figures and audit curves in the original PDF.
- `reproduction_manifest.json`: runtime environment, parameter hash, and output SHA-256 hashes.
- `.github/workflows/reproduce.yml`: automated dependency installation, tests, and figure generation.

## Validated results and limits of the original figures

- Model A and MUPA values in the paper's welfare-decomposition table agree to three decimal places.
- The capacity curves in Figure 5 intersect at R=4. Figure 7 gives capacity 1.875 at low dispersion and approximately 2.26 at s=6.
- For Figures 1, 3, 4, 5, and 6, original PDF curve vertices were extracted and converted to data coordinates. The maximum absolute numerical error across 12 curve segments is below 4×10⁻⁶. See [reference_curve_audit.json](docs/reference_curve_audit.json).
- **Figure 1:** for N<Δ/(2κ)=1, the original non-strategic revenue curve extends its interior formula beyond the exit boundary. The CSV also contains the correctly piecewise `U_NS_piecewise`. The dotted MUPA segment at N≤.5 is an extrapolation as well.
- **Figure 8(b):** to match the original, the Δ range extends to 10. With mean cost 4, however, Δ≥8 implies t₁≤0, outside the paper's positive-cost assumption. The CSV marks these points with `primitive_cost_valid`. They should not be interpreted as economic cases satisfying all original assumptions.

Parameters describe a normalized illustrative scenario; they are **not empirical estimates for the Shenzhen corridor**. This repository does not modify the original Overleaf paper.

## Preview

![Revenue comparison](figures/fig1_revenue_ranking.png)
![Investment under uncertainty](figures/fig7_investment_uncertainty.png)
![Regime maps](figures/fig8_regime_maps.png)

## Optional: audit the original PDF curves again

```bash
python -m pip install -r requirements-audit.txt
python scripts/audit_reference_curves.py
# If you have the compiled paper PDF, extract its vector figures again:
python scripts/extract_reference_figures.py /path/to/paper.pdf
```

The optional tools use a saved PDF and do not need the original Overleaf edit link. The repository contains no access tokens, login details, or full paper text. No open-source license was chosen on the authors' behalf; redistribution rights for the code and paper figures remain with their respective rights holders.
