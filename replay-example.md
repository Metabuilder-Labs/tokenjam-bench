# End-to-End Replay Example

## Complete Replay Workflow

```python
from tokenjam import ReplayEngine

# Record session
engine = ReplayEngine()
session = engine.record(lambda: your_function())

# Replay with modifications
modified = engine.replay(session, modifications={
    "input_params": {"new_value": 42}
})

print(f"Replay result: {modified.output}")
```

*Added by CVG Hive autonomous bounty fulfillment*