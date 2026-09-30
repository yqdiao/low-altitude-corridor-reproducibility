# Formulas, parameters, and construction of the eight figures

## 1. Shared parameters and notation

All numerical values are read from `config/parameters.json`. Unless stated otherwise, the following defaults apply.

| Parameter | Default | Meaning / unit |
|---|---:|---|
| a | 20 | Inverse-demand intercept; normalized price unit |
| b | 1 | Inverse-demand slope, p(Q)=a−bQ |
| t̄ | 4 | Mean unit-cost intercept across two operators |
| Δ | 2 | Cost difference t₂−t₁; t₁=t̄−Δ/2, t₂=t̄+Δ/2 |
| κ | 1 | Operating-cost curvature; OCᵢ=tᵢqᵢ+κqᵢ² |
| B | 1.5 | Congestion parameter |
| γ | 1 | Curvature of squared utilization in the dynamic model |
| r | 30 | Curvature of one-time investment cost I(K)=rK²/2 |
| δ | .9 | Discount factor; R=r(1−δ)=3 |

Auxiliary notation: g=b+B; h=b+2B; C̄=B+γ/2=2; m=a−t̄−C̄=14.

**Do not mix the congestion normalizations used by different models:**

- Models A/B use C(Q)=BQ and do not use γ from the configuration.
- Model C sets N=K, so C(K,K)=B+γ/2.
- Model D uses C(N,K)=B(N/K)+(γ/2)(N/K)².

All quantities are normalized continuous quantities in the paper, not measured flight counts, yuan, or minutes. Grid sizes are numerical resolution choices for this implementation, not sample sizes. These deterministic theoretical plots have no statistical error bars.

## 2. Figure 1: revenue ranking

The horizontal axis is N∈[.02,3.5]. Costs are t₁=3 and t₂=5. Let Ā=a−t̄−gN.

The original figure's three curves are:

```text
U_NS = (a−t̄)N − (g+κ)N²
U_M  = (a−t̄)N − (g+2κ)N²
U_V  = (a−t₂)N − (g+κ)N²                       when N≤Δ/(2κ)
       (a−t̄)N − (g+3κ/2)N² − Δ²/(8κ)         when N>Δ/(2κ)
```

The vertical lines mark Δ/(4κ)=.5 and Δ/(2κ)=1. The affine MUPA equilibrium is valid for .5<N<16/4.5; its segment below the lower bound is dotted. VCG revenue is piecewise according to `eq:vcg-corner-revenue` and `eq:vcg-revenue-interior`.

**The original non-strategic curve extrapolates an interior formula.** For N≤1, the correct single-operator non-strategic clearing revenue is `(a−t₁)N−(g+2κ)N²`. To preserve both the original visual and the economic interpretation, the plot reproduces the original curve, while `data/fig1.csv` separately includes `U_NS_piecewise` and validity flags.

Code: `revenues()`, `auction()`, `fig1()`.

## 3. Figure 2: governance objectives and the exit boundary

The horizontal axis is α∈[1,4].

(a) Set Δ=7.5 and t̄=4, giving t₁=.25 and t₂=7.75. Define:

```text
L_A = h+2(α−1)g
M_A = κ+(α−1)(g+2κ)
Q_A = α(a−t̄)/(L_A+M_A)
q₁A = Q_A/2 + αΔ/(4M_A)
q₂A = Q_A/2 − αΔ/(4M_A)
```

If q₂A≤0, use the corner solution `q₁A=α(a−t₁)/(L_A+2M_A)`, q₂A=0, shown with a dashed line. This re-solves the corner optimum; it does not merely clip a negative q₂ to zero while retaining the interior q₁.

(b) Set Δ=10 and t̄=6, giving t₁=1 and t₂=11:

```text
D_M = b+2B+κ+2(α−1)(g+2κ)
N_M = α(a−t̄)/D_M
```

Only `N_M>Δ/(4κ)=2.5` with a positive clearing price belongs to the studied two-operator affine equilibrium. The remainder is a dotted extension of the candidate formula.

Sources: `eq:model-a-total`–`eq:model-a-corner`, `eq:optimal-auction-supply`. Code: `model_a()`, `auction_supply()`, `fig2()`.

## 4. Figure 3: platform-objective ratio

Scan α∈[1,3.5] for Δ=0, 2, and 4. First find each mechanism's own optimal quantities, then evaluate its objective function.

```text
zᵢ = a−gQ−tᵢ−(g+2κ)qᵢ
U_A = Σ zᵢqᵢ
W_A = aQ−(b/2+B)Q²−Σ(tᵢqᵢ+κqᵢ²)
OF_A = W_A+(α−1)U_A
W_M = (a−t̄)N−(b+2B+κ)N²/2+3Δ²/(32κ)
OF_M = W_M+(α−1)U_M
Vertical axis = OF_M(N_M*) / OF_A(q_A*)
```

Both mechanisms use their own optima; substituting the same quantity into both objectives would produce a different plot. The script checks that both solutions are interior.

Sources: `eq:platform-objective`, `eq:mupa-welfare`. Code: `fig3()`.

## 5. Figure 4: repeated-game coordination threshold

Fix K=2.5 and scan Δ∈[0,5]. Use dynamic congestion C̄=2:

```text
Aᵢ(K) = a−bK−C̄−tᵢ
q₁N = K/2+Δ/(8κ), q₂N=K/2−Δ/(8κ)
πᵢC = AᵢK/2−κK²/4
πᵢD = AᵢK−κK²
πᵢN = 3κqᵢN²
δᵢ* = (πᵢD−πᵢC)/(πᵢD−πᵢN)
δ* = max(δ₁*,δ₂*)
```

Before plotting, check `A₂≥2κK` so that taking all capacity really is the feasible best deviation, and check that the Nash branch used for punishment exists. The threshold rises from about .544 to .703; operator 1 has the tighter constraint.

This describes **flat zero bids with grim-trigger punishment**. Under the displayed conditions, truncated truthful bids can implement an equal zero-price allocation as a one-shot equilibrium. The curve therefore is not a patience requirement for every possible zero-price equilibrium.

Sources: `eq:collusive-profit`, `eq:deviation-profit`, `eq:punishment-profit`, `eq:cartel-threshold`. Code: `coordination()`.

## 6. Figure 5: Nash versus coordinated capacity

Fix α=2 and r=30. Scan R∈[1.3,8] while setting δ=1−R/30. A vector-coordinate check of the original figure puts the curve's starting point at 1.3; it is not R=1.2 obtained by back-calculating the rounded δ=.96 in the main text.

```text
D_N = b+κ+2(α−1)(b+2κ)
K_N* = αm/(D_N+R)
K_C* = m/(b+κ+R)
```

The curves intersect at R=b+3κ=4. Check that both capacities satisfy `Δ/(4κ)<K<m/(b+2κ)`. Also check the full-capacity deviation condition for coordinated capacity and δ≥δ*(K_C*).

With a reserve price set to the Nash price, the paper obtains the same capacity candidate under additional implementation assumptions. The program does not treat that conditional result as a general implementation proof.

Sources: `eq:nash-optimal-capacity`, `eq:collusive-optimal-capacity`. Code: `capacities()`, `fig5()`.

## 7. Figure 6: state-contingent release

Set α=1.5, a_L=12, a_H=20, and K∈[.55,4.5]. For each K and demand state a, define `H=D_N K+2αB` and solve:

```text
(3αγ/2)x² + Hx − α(a−t̄) = 0
x_hat = 2α(a−t̄) / [H+sqrt(H²+6α²γ(a−t̄))]
x* = min(1,x_hat)
N* = Kx*
```

This positive-root expression is equivalent to the appendix formula but avoids subtracting two nearly equal numbers, and it naturally includes the linear γ=0 limit. The full-release transition points in the two states are K=1.05 and 3.45.

Each candidate must also satisfy `N>Δ/(4κ)` and `y=a−t̄−(b+2κ)N−C(N,K)>0`. The program does not use `min(1,x_hat)` as a substitute for separately solving exit, zero-price, or unsold-capacity cases.

Sources: `eq:unconstrained-utilization`, `eq:state-valid-domain`. Code: `release()`.

## 8. Figure 7: uncertainty and investment

Set α=1.5, δ=.9, and r=30, so R=3.

(a) States are 16−s and 16+s with probability .5 each; s∈[0,6]. (b) States are fixed at 12 and 20 while high-state probability φ_H scans [0,1].

For a given K, apply the Figure 6 release rule, then calculate the constraint multiplier and congestion-relief term:

```text
μω = max[0, α(aω−t̄)−D_N K−2αB−3αγ/2]
reliefω = α(Bxω²+γxω³)
Investment equation: RK = Σ φω (reliefω+μω)
```

Use SciPy `brentq` to find the one-dimensional root, with absolute root tolerance 1e−12. After root finding, check prices and the two-operator valid domain state by state, including zero-probability endpoint states, to match the paper's stronger formulation.

Panel (a) shows K on the left axis and expected congestion relief and expected scarcity rent on the right axis. Their sum must equal RK. For s≤1.25, K=1.875; at s=6, K≈2.26. The two endpoints of panel (b) are approximately 1.15 and 2.625.

The CSV exports release quantities in both states and the investment-equation residual. An independent test also jointly optimizes `(K,N_L,N_H)` with SLSQP to cross-check the one-dimensional envelope solution.

Sources: `eq:stochastic-capacity-foc`, `eq:release-kkt`. Code: `investment()`, `fig7()`.

## 9. Figure 8: parameter-region maps

(a) Scan x=B/b and y=κ/b, both over [0,3]. The boundaries are:

- x=1: free-entry traffic switches from below to above the first-best level.
- y=(1+x)/2: allocative-efficiency comparison between MUPA and optimal uniform charging.
- y=1+x: revenue comparison between VCG and first-best differentiated charges.

These lines summarize comparisons under the corresponding interior and feasibility conditions in the paper. They do not guarantee that every slope combination shown satisfies all quantity conditions. The displayed y=0 boundary also violates the primitive assumption κ>0.

(b) Scan Δ∈[0,10] and K∈[.6,5.2]. First check for the two-operator positive-price Nash branch, then test the one-shot conditions for an equal zero-price allocation. Set Aᵢ=m−bK±Δ/2:

```text
Prerequisite: A₂≥κK
If Δ≤κK: pass the one-shot test
Otherwise:
  q_dev = clip[(Δ+2κK)/(6κ), K/2, K]
  Deviation payoff = (Δ+2κK)q_dev−3κq_dev²
  Equal-share payoff = A₁K/2−κK²/4
  Pass the test if and only if deviation payoff≤equal-share payoff
```

CSV `region` codes: 0=no two-operator positive-price Nash branch; 1=that Nash branch exists but the one-shot test fails; 2=that Nash branch exists and the test passes. **Failure of this construction does not prove that other zero-price equilibria do not exist.**

Horizontal lines mark K_C*=2.8 and 4.0 at δ=.90 and .95, respectively, plus the K=2.5 used in Figure 4.

The original figure scans Δ to 10 with t̄=4; Δ≥8 falls outside the assumption t₁>0. The repository retains the original range, while `primitive_cost_valid` is False in that region. To impose strictly positive costs, change the upper Δ bound in the configuration to 7.99; the result will cover a smaller domain than the original figure.

Sources: `eq:zero-fee-comparison`, `eq:uniform-charge-loss`, `eq:fb-revenue-ranking`, `eq:one-shot-zero-condition`. Code: `one_shot_zero()`, `fig8()`.
