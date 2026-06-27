# Customer Support — workflow dataset

Realistic support tickets for an e-commerce + SaaS business, used by the
**Production Workflow** benchmark family (`tjb workflow customer-support`).

Each ticket is a real-shaped support request with a **grounded reference reply**
and the **knowledge-base context** the answer must stay faithful to. The
candidate model is scored by the DeepEval judge on whether its reply matches the
reference, grounded in the context — then it flows through the same proof stats
(Wilson CI + exact McNemar + measured cost) as every other benchmark.

## Schema (`tickets.json` → `tickets[]`)

| field | meaning |
|---|---|
| `id` | stable task id (`cs/…`) |
| `question` | the customer's message |
| `expected_intent` | ground-truth intent label (refund, delivery_delay, …) |
| `expected_response` | grounded reference reply the judge scores against |
| `knowledge_context` | KB snippets the answer must stay faithful to |
| `difficulty` | easy / medium / hard |
| `category` | Returns & Refunds, Shipping, Billing, Escalation, … |
| `priority` | low / normal / high / critical |

## Coverage (16 tickets)

Refund · Delivery delay · Wrong product · Password reset · Subscription
cancellation · Payment failed · Invoice request · Account locked · Shipping
status · Feature request · Bug report · Escalation · Complaint · Billing error
(double charge) · Order cancellation · GDPR data deletion.

Difficulty mix: easy (6) · medium (8) · hard (2). Priority spans low → critical,
including safety-sensitive cases (account unlock, GDPR erasure, payment) where
the reference reply deliberately **refuses unsafe actions** (no reading back
passwords, no card numbers) — so a cheaper model is judged on staying safe too.

## Run

```bash
# offline (no keys) — MockJudge, deterministic
tjb workflow customer-support --original anthropic:claude-opus-4-7 --mock --html

# live — DeepEval judge backed by DeepSeek (key from env)
TJBENCH_JUDGE=deepseek TJBENCH_JUDGE_METRIC=correctness \
tjb workflow customer-support \
  --original deepseek:deepseek-reasoner --candidate deepseek:deepseek-chat --limit 16 --html
```

The judge backend is selected via `TJBENCH_JUDGE` (offline `MockJudge` by
default). Adding a new suite is pure data: drop a dataset folder + JSON and
register it in `tjbench/workflows/__init__.py`.
