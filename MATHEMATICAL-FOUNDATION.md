# Mathematical and Theoretical Foundation

## Abstract

This document provides the complete mathematical and theoretical foundation underlying the NFL betting framework. The system implements a research-validated approach to optimal sports betting, combining empirical findings from the Wharton School of the University of Pennsylvania with classical Kelly Criterion theory and expected value mathematics. The framework prioritizes mathematical rigor, risk management, and long-term profitability through systematic application of proven academic research.

## 1. Primary Research Foundation

### 1.1 Wharton School Empirical Study

The framework's core methodology is derived from "An Investigation of Sports Betting Selection and Sizing" by Beggy et al. (2023), conducted at the Wharton School of the University of Pennsylvania. This study represents the most comprehensive empirical validation of Kelly Criterion applications in sports betting, analyzing over 10,000 betting opportunities across 11+ years of European soccer data.

**Key Empirical Findings:**

1. **Half Kelly Optimality**: Testing multiple Kelly fractions (0.25, 0.50, 0.75, 1.00), the study found that Half Kelly (f = 0.50) provided optimal risk-adjusted returns across all market conditions.

2. **Conservative Threshold Superiority**: Expected value thresholds of 10% significantly outperformed aggressive thresholds of 2.5% and 5% in long-term profitability analysis.

3. **Full Kelly Bankruptcy Risk**: Full Kelly betting (f = 1.00) led to bankruptcy in 100% of test scenarios, demonstrating the critical importance of fractional Kelly approaches.

4. **Sustained High Returns**: The Half Kelly + 10% EV threshold combination generated an average of 80% annual returns over the study period.

### 1.2 Research Validation Metrics

The Wharton study's methodology provides robust empirical support for the implemented strategy:

- **Sample Size**: 10,275+ betting opportunities analyzed
- **Time Period**: 11+ years of market data
- **Market Coverage**: European soccer betting across multiple leagues and seasons
- **Statistical Significance**: Results showed consistent superiority across different market conditions and time periods

## 2. Mathematical Framework

### 2.1 Kelly Criterion Theory

The Kelly Criterion, originally developed by Kelly (1956) for optimal information transmission, was adapted by financial mathematicians for capital allocation problems. The criterion determines the optimal fraction of capital to wager to maximize the expected logarithmic growth of wealth.

**Original Kelly Formula:**

```math
f = \frac{bp - q}{b}
```

Where:

- f = fraction of bankroll to bet
- b = net odds received (payout/stake - 1)
- p = probability of winning
- q = probability of losing (1-p)

**Mathematical Derivation:**

The Kelly Criterion maximizes the expectation of the logarithm of wealth:

```math
E[\log(W_n)] = p \times \log(1 + bf) + q \times \log(1 - f)
```

Taking the derivative with respect to f and setting equal to zero:

```math
\frac{dE[\log(W_n)]}{df} = p \times \frac{b}{1 + bf} - \frac{q}{1 - f} = 0
```

Solving for f yields the Kelly formula above.

**Framework Implementation:**

The system implements a modified Kelly approach using the empirically-validated 50% coefficient:

```math
f_{half} = 0.5 \times \frac{bp - q}{b}
```

This modification, based on the Wharton research findings, provides superior risk-adjusted returns compared to full Kelly while maintaining growth optimization properties.

### 2.2 Expected Value Theory

Expected Value represents the long-term average outcome of a bet if repeated infinitely under identical conditions. For binary outcome events, the expected value formula is:

**Standard EV Formula:**

```math
EV = (Win\_Probability \times Payout) - (Loss\_Probability \times Stake)
```

**Per-Dollar EV (Framework Implementation):**

```math
EV_{per\_dollar} = \left(p \times \frac{1}{contract\_price}\right) - 1
```

**EV Percentage:**

```math
EV\% = EV_{per\_dollar} \times 100
```

**Threshold Application:**

Based on Wharton research findings, the framework implements a conservative 10% EV threshold:

```math
\text{Bet Decision} = \begin{cases}
\text{"BET"} & \text{if } EV\% \geq 10.0 \\
\text{"NO BET"} & \text{if } EV\% < 10.0
\end{cases}
```

This threshold filters out marginally profitable opportunities, focusing capital allocation on high-quality betting opportunities that demonstrated superior long-term profitability in empirical testing.

### 2.3 Event Contract Mathematics

Binary event contracts present a simplified mathematical structure compared to traditional sportsbook betting. Each contract pays exactly $1.00 if the event occurs and $0.00 if it doesn't.

**Contract Payout Structure:**

- Win: $1.00 per contract
- Loss: $0.00 per contract
- Cost: Contract price + Commission per contract

**Adjusted Pricing Model:**

The framework accounts for transaction costs through adjusted pricing:

```text
Adjusted_Price = Contract_Price + Commission_Per_Contract
```

This adjustment maintains mathematical accuracy by reflecting the true cost basis for Kelly Criterion calculations while preserving the correct payout odds for expected value computations.

**Mathematical Justification:**

Unlike traditional sportsbook vig (which is embedded in odds), event contract commissions represent separate transaction costs. The framework treats these correctly by:

1. Using adjusted price for cost basis calculations
2. Maintaining original contract price for payout odds
3. Ensuring Kelly fractions reflect true risk-reward ratios

## 3. Risk Management Theory

### 3.1 Bankroll Management Principles

The framework implements modern portfolio theory principles adapted for sports betting applications. Key theoretical foundations include:

**Capital Preservation:**
Maximum bet limits prevent catastrophic losses that could impair long-term growth potential. The 15% bankroll cap per bet provides additional safety beyond the Half Kelly approach.

**Geometric Mean Optimization:**
The Kelly Criterion maximizes geometric mean returns rather than arithmetic mean returns, which is mathematically optimal for compound growth scenarios typical in sports betting.

**Dynamic Sizing:**
Bet sizes automatically adjust based on current bankroll levels, ensuring optimal capital allocation regardless of prior outcomes.

### 3.2 Conservative Bet Selection Theory

The Wharton study demonstrated that conservative bet selection significantly outperforms aggressive approaches in long-term profitability metrics. The theoretical basis for this finding includes:

**Quality vs. Quantity Trade-off:**
Higher EV thresholds reduce bet frequency but increase average bet quality, leading to superior risk-adjusted returns.

**Vig Avoidance:**
Conservative thresholds help avoid marginally profitable opportunities where sportsbook edges can erode theoretical profits through various market inefficiencies.

**Variance Reduction:**
Fewer, higher-quality bets reduce portfolio variance while maintaining expected return characteristics.

## 4. Implementation-Specific Mathematical Adaptations

### 4.1 Whole Contract Constraint

Robinhood's platform requires whole contract purchases, creating a practical constraint not addressed in classical Kelly theory. The framework handles this through conservative rounding:

```math
\text{Whole\_Contracts} = \lfloor \frac{\text{Target\_Bet\_Amount}}{\text{Adjusted\_Price}} \rfloor \\
\text{Actual\_Bet\_Amount} = \text{Whole\_Contracts} \times \text{Adjusted\_Price}
```

**Mathematical Impact:**
This approach maintains the conservative nature of the strategy by never exceeding the mathematically optimal bet size due to rounding constraints.

### 4.2 Commission Integration Theory

The framework's approach to commission handling preserves the mathematical integrity of both Kelly and EV calculations:

**For Kelly Calculations:**
Uses adjusted price (including commission) to reflect true cost basis for optimal fraction determination.

**For EV Calculations:**
Maintains separation between payout odds and transaction costs to preserve accuracy of expected return computations.

**Theoretical Validation:**
This approach correctly models the economic reality where commission represents a fixed transaction cost rather than a modification of payout odds.

### 4.3 Price Normalization Mathematics

The framework handles dual price formats through mathematical normalization:

```math
\text{Normalized\_Price} = \begin{cases}
\frac{\text{price}}{100} & \text{if } \text{price} > 1.0 \\
\text{price} & \text{if } \text{price} \leq 1.0
\end{cases}
```

This ensures mathematical consistency regardless of input format while maintaining precision in all subsequent calculations.

## 5. Performance Expectations and Theoretical Bounds

### 5.1 Expected Return Characteristics

Based on the Wharton empirical research and theoretical foundations, the framework targets:

**Annual Return Expectation:** ~80% (empirically validated)
**Risk Profile:** Conservative approach designed to minimize ruin probability
**Scalability:** Optimal proportions maintained across varying bankroll sizes

### 5.2 Theoretical Performance Bounds

**Upper Bound:** Limited by market efficiency and available +EV opportunities
**Lower Bound:** Conservative thresholds and Half Kelly approach provide downside protection
**Variance Characteristics:** Reduced compared to Full Kelly while maintaining growth optimization

## 6. Research Integration and Validation

### 6.1 Multi-Source Theoretical Foundation

The framework integrates findings from multiple research streams:

1. **Wharton Empirical Study (2023):** Primary strategy validation
2. **Kelly Information Theory (1956):** Mathematical optimization foundation  
3. **Expected Value Theory:** Profitability assessment framework
4. **Modern Portfolio Theory:** Risk management principles

### 6.2 Mathematical Verification

All mathematical components have been verified through:

- Theoretical derivation validation
- Empirical backtesting against research findings
- Edge case analysis and testing
- Real-world cash flow verification

## 7. Conclusion

This framework represents a synthesis of rigorous academic research, classical mathematical theory, and practical implementation requirements. The mathematical foundation ensures optimal capital allocation while the empirical research provides validation for parameter selection and strategy effectiveness.

The strength of the approach lies in its combination of:

- **Theoretical Rigor:** Grounded in proven mathematical optimization
- **Empirical Validation:** Supported by comprehensive academic research
- **Practical Applicability:** Adapted for real-world implementation constraints
- **Risk Management:** Conservative parameters to ensure long-term sustainability

The mathematical and theoretical foundation provides a robust basis for systematic, research-validated sports betting decision-making.

## References

Beggy, J., Kim, D., Mucaj, K., Nordell, J., & Wyner, A. (2023). An Investigation
of Sports Betting Selection and Sizing. *Wharton School Student Research
Journal*, Spring Edition.

Kelly, J. L. (1956). A New Interpretation of Information Rate. *Bell System
Technical Journal*, 35(4), 917-926.

Baker, R. D., & McHale, I. G. (2013). Optimal Betting Under Parameter
Uncertainty: Improving the Kelly Criterion. *Decision Analysis*, 10(3), 189-199.
