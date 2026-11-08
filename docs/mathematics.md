# From semantic revision to dynamics

Equation source: Mar & Grim (1991), [author-hosted PDF](https://pgrim.org/articles/patternandchaos.pdf),
*Noûs* 25(5), 659–693, DOI [10.2307/2215637](https://doi.org/10.2307/2215637).
Page numbers below use the printed journal pagination. The scan has a cover
sheet: printed page 662 is PDF page 5 (one-based).

## The value claimed is not the value assigned

Write `x` for the current estimate and `s(x)` for a self-attributed value. The
paper's parametric truth-value operator gives the revision

$$R_s(x)=1-|s(x)-x|.$$

For example, inserting `s(x)=0` gives `1-x`; inserting `s(x)=1-x` gives
`1-|1-2x|`. That second application of the operator changes the map. Directly
iterating the claimed value `s(x)` would be a different experiment.

The interval `[0,1]` is a stipulated space of semantic values. These values are
not automatically probabilities, confidence scores, or measurements of cognition.

| CLI name | Revision equation | Claimed value `s(x)` | Source pages |
|---|---|---|---|
| `liar` | $1-x$ | $0$ | 662–664 |
| `truth-teller` | $x$ | $1$ | 667 |
| `samesayer` | $1$ | $x$ | 667–668 |
| `k-sayer` | $1-(1-k)x$ | $kx$, $0\leq k\leq1$ | 668–669 |
| `minimalist` | $1-|\min(x,1-x)-x|$ | $\min(x,1-x)$ | 665–666 |
| `chaotic-liar` | $1-|1-2x|$ | $1-x$ | 670–672 |
| `curry` | $1-|\max(1-x,p)-x|$ | $\max(1-x,p)$, $0\leq p\leq1$ | 674–676 |

The following derivations and numerical comparisons are this project's checks
of those equations.

## Fixed points and stability

For the Simple Liar, `f(f(x))=x`. Its fixed point is `1/2`; every other exact
initial value has period two. Distances between two trajectories are preserved.
The derivative is `-1`, giving a log growth rate of zero.

For the k-Sayer, let `a=1-k`. Solving `x=1-a*x` gives

$$x^*=\frac{1}{2-k},\qquad x_n=x^*+(-a)^n(x_0-x^*).$$

For `0<k<=1` the error contracts; `k=0` is the neutral Liar boundary. With `k=1/2`
the fixed point is `2/3`, and the error halves and reverses sign at each step.
The Minimalist shares that fixed point, but near it the slope is `-2`: small
errors double instead of halve. Comparing the two maps separates the location
of a fixed point from its stability.

## Tent-map expansion is not an orbit classifier

The Chaotic Liar simplifies to

$$T(x)=\begin{cases}2x&x\leq1/2,\\2(1-x)&x>1/2.\end{cases}$$

On either open branch `|T'(x)|=2`. A differentiable length-`N` segment therefore
has average log derivative `log(2)`. The apex `x=1/2` has no ordinary derivative.
The exact fixed point `2/3` also has derivative magnitude 2: expansion does not
prevent that special orbit from being stationary. Our diagnostic is a finite-time
derivative product along a sampled trajectory, not a proof of chaotic behavior.

The implementation evaluates the piecewise form above. This avoids cancellation
in `1-abs(1-2*x)` near zero. The formulas agree in exact arithmetic, but their
rounding histories can differ in floating point. Data exports identify the code
by SHA-256 so the evaluation choice is reproducible.

If `x=m/2^b`, each exact tent step removes at least one factor of two from the
denominator until the orbit reaches an endpoint and then zero. Every finite
binary float in `[0,1]` has this form. A non-dyadic rational, such as `157/500`,
instead remains on a finite rational grid and must eventually recur; that grid
need not include its actual orbit's zero state. The notebook compares float32,
float64 and exact rational versions of the *same requested decimal input*.

## Curry boundary check

At `p=0` the Curry variation reduces to the tent map. At `p=1`, it gives

$$1-|\max(1-x,1)-x|=1-|1-x|=x.$$

Thus **the displayed equation is the identity at `p=1`**. The prose at the top
of printed page 675 describes convergence to 1 / the Samesayer instead. We
implement the equation and explicitly test this discrepancy. For the interior
example `p=3/4, x0=1/5`, exact revision reaches the cycle `17/20 ↔ 9/10`.

## Two sentences: the schedule changes the map

The Simple Dualist's component rules are `A(x,y)=1-y`, `B(x,y)=x` (pp. 676–677).
For simultaneous updates, `F(x,y)=(1-y,x)` and `F^4` is the identity. For the
paper's y-then-x revision, one sweep gives `(1-x,x)`: the previous `y` no longer
affects the result. These are different dynamical systems.

The later value-revision pair uses

$$A(x,y)=1-|y-x|,\qquad B(x,y)=1-|(1-x)-y|.$$

The component equations appear on p. 677; simultaneous behavior is discussed
on p. 678 and x-then-y revision on p. 679. This project also supplies y-then-x
as a comparison:

| Schedule | One complete step |
|---|---|
| simultaneous | $(A(x,y),B(x,y))$ |
| x-then-y | $(A(x,y),B(A(x,y),y))$ |
| y-then-x | $(A(x,B(x,y)),B(x,y))$ |

For simultaneous updates the outputs satisfy `x'+y' >= 1`: use
`|y-x|+|1-x-y| <= 1` for inputs in the unit square. Sequential updates need not
obey this same triangle constraint. A change in the plotted region can therefore
follow from update order alone.

The exact short decimal pair `(0.1,0.9)` under x-then-y revision eventually
repeats on a small rational grid. A denser orbit from a longer initial fraction
is a separate experiment. Neither visual density nor lack of recurrence during
a finite run establishes an attractor or a chaotic invariant measure.
