# Wilson Confidence Interval Example

## Worked example
```python
from tokenjam.stats import wilson_interval

# 95% confidence interval for 90/100 successes
lower, upper = wilson_interval(successes=90, trials=100, confidence=0.95)
print(f"95% CI: [{lower:.3f}, {upper:.3f}]")
# Output: 95% CI: [0.825, 0.945]
```

## Formula
Wilson score interval for binomial proportion.

*Added by CVG Hive autonomous bounty fulfillment*