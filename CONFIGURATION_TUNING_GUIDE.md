# Detection Configuration Tuning Guide

This guide helps SOC teams tune the malware detection system based on their specific environment and false positive/negative rates.

---

## Quick Start: Common Scenarios

### High False Positive Rate (Too Many Alerts)

If you're getting too many false positives on legitimate files:

```json
{
  "malicious_threshold": 0.85,      // Increase from 0.80
  "suspicious_threshold": 0.60,     // Increase from 0.50
  "entropy_threshold": 7.8,         // Increase from 7.5
  "max_context_modifier": 0.20,    // Decrease from 0.30
  "risk_weights": {
    "signature": 0.45,               // Increase signature weight
    "heuristic": 0.20,               // Decrease heuristic weight
    "ml": 0.35
  }
}
```

**Rationale:** Higher thresholds reduce sensitivity, lower heuristic weight reduces noise from weak indicators.

### Missing Threats (False Negatives)

If known threats are slipping through:

```json
{
  "malicious_threshold": 0.75,      // Decrease from 0.80
  "suspicious_threshold": 0.40,     // Decrease from 0.50
  "entropy_threshold": 7.2,         // Decrease from 7.5
  "risk_weights": {
    "signature": 0.35,
    "heuristic": 0.30,               // Increase heuristic weight
    "ml": 0.35
  }
}
```

**Rationale:** Lower thresholds increase sensitivity, higher heuristic weight catches more behavioral indicators.

### Script-Heavy Environment (Development/DevOps)

If you have many legitimate scripts triggering alerts:

```json
{
  "entropy_threshold": 7.8,
  "suspicious_threshold": 0.55,
  "risk_weights": {
    "signature": 0.50,               // Trust signatures more
    "heuristic": 0.15,               // Reduce heuristic sensitivity
    "ml": 0.35
  },
  "trusted_domains": [
    "github.com",
    "npmjs.org",
    "pypi.org",
    "company-repo.internal"
  ]
}
```

### High-Security Environment (Financial/Healthcare)

If you need maximum security with manual review capacity:

```json
{
  "malicious_threshold": 0.70,      // Lower threshold
  "high_risk_threshold": 0.55,
  "suspicious_threshold": 0.35,
  "monitor_threshold": 0.15,
  "risk_weights": {
    "signature": 0.40,
    "heuristic": 0.30,
    "ml": 0.30
  },
  "enable_blocking": true,           // Enable automatic blocking
  "max_context_modifier": 0.35      // Allow more context influence
}
```

---

## Configuration Parameters Explained

### Detection Layer Weights

**`risk_weights.signature`** (default: 0.40)
- Weight for signature-based detection (hash matches, pattern matches)
- Higher values trust known signatures more
- **Increase to 0.45-0.50** if you have high-quality signature database
- **Decrease to 0.30-0.35** if experiencing signature false positives

**`risk_weights.heuristic`** (default: 0.25)
- Weight for behavioral heuristics (entropy, file type, strings)
- Higher values catch more unknown threats but may increase false positives
- **Increase to 0.30-0.35** for better zero-day detection
- **Decrease to 0.15-0.20** in environments with many legitimate packed files

**`risk_weights.ml`** (default: 0.35)
- Weight for ML classification
- Higher values trust ML predictions more
- **Increase to 0.40-0.45** if ML model is well-trained on your data
- **Decrease to 0.25-0.30** if ML generates many false positives

**Note:** Weights are automatically adjusted based on layer confidence at runtime.

---

### Risk Thresholds

**`malicious_threshold`** (default: 0.80)
- Risk score >= this value triggers "malicious" verdict
- Requires confidence > 0.6 for automatic blocking
- **Range:** 0.70-0.90
- **Higher = fewer false positives, more manual review**
- **Lower = more automatic blocking, higher false positive risk**

**`high_risk_threshold`** (default: 0.65)
- Risk score >= this value triggers "high_risk" verdict
- Triggers quarantine for investigation
- **Range:** 0.55-0.75
- **Use for files that need sandbox analysis**

**`suspicious_threshold`** (default: 0.50)
- Risk score >= this value triggers "suspicious" verdict
- Triggers alerts and logging
- **Range:** 0.35-0.65
- **Lower = more monitoring, higher = less noise**

**`monitor_threshold`** (default: 0.25)
- Risk score >= this value triggers "monitor" verdict
- Logs for correlation, no active blocking
- **Range:** 0.15-0.35
- **Use for threat hunting and trend analysis**

---

### Heuristic Parameters

**`entropy_threshold`** (default: 7.5)
- Shannon entropy threshold (0-8 scale)
- Files with entropy > threshold trigger high entropy indicator
- **Typical legitimate files:** 5.0-6.5 (text, code)
- **Compressed/encrypted:** 7.0-8.0
- **Packed malware:** 7.5-8.0

**Tuning guidance:**
- **7.2-7.4:** Aggressive detection, catches more packed malware
- **7.5-7.7:** Balanced (recommended)
- **7.8-8.0:** Conservative, reduces false positives on compressed files

---

### Context Modifiers

**`max_context_modifier`** (default: 0.30)
- Maximum additive risk adjustment from context factors
- Prevents over-weighting based on source IP, file extension, etc.
- **Range:** 0.15-0.40

**Context factors (additive):**
- External source IP: +0.10
- Dangerous file extension (.exe, .scr, etc.): +0.15
- Unknown email sender: +0.08

**Tuning guidance:**
- **0.15-0.20:** Reduce context influence (for environments with many external downloads)
- **0.30-0.35:** Standard influence
- **0.35-0.40:** High context influence (for controlled environments)

---

### Trust Lists

**`trusted_domains`** (array)
- Email domains that reduce suspicious scoring
- Applies -0.08 modifier for email attachments
- **Examples:**
  ```json
  [
    "company.com",
    "partner-corp.com",
    "microsoft.com",
    "github.com"
  ]
  ```

**Best practices:**
- Only add domains you fully control or highly trust
- Review quarterly to remove outdated entries
- Consider separate lists for email vs. download sources

---

## Tuning Workflow

### Step 1: Establish Baseline

1. Run system for 1-2 weeks with default settings
2. Collect metrics:
   - Total files analyzed
   - Benign / Suspicious / Malicious counts
   - False positive rate (manual review)
   - False negative rate (missed threats)

### Step 2: Analyze Results

Review logs (`logs/detections.jsonl`) and identify patterns:

```bash
# Count verdicts
cat logs/detections.jsonl | jq -r '.detection.verdict' | sort | uniq -c

# Find high-scoring benign files
cat logs/detections.jsonl | jq 'select(.detection.verdict=="malicious" and .detection.confidence < 0.7)'

# Check primary factors for false positives
cat logs/detections.jsonl | jq '.detection.reasoning.primary_factors[0].layer' | sort | uniq -c
```

### Step 3: Adjust Configuration

Based on analysis:

**High heuristic false positives:**
```json
{
  "entropy_threshold": 7.8,
  "risk_weights": {"heuristic": 0.20}
}
```

**Signature database needs improvement:**
```json
{
  "risk_weights": {"signature": 0.35, "ml": 0.40}
}
```

**Too many external source penalties:**
```json
{
  "max_context_modifier": 0.20
}
```

### Step 4: Validate Changes

1. Run system for another week
2. Compare metrics to baseline
3. Fine-tune further if needed

### Step 5: Document & Monitor

- Document your configuration and rationale
- Set up alerts for metric changes
- Review monthly and adjust seasonally

---

## Performance Tuning

### CPU Optimization

```json
{
  "num_workers": 8,              // Match CPU cores
  "num_detection_workers": 4     // Half of packet workers
}
```

### Memory Optimization

```json
{
  "stream_timeout": 180,         // Reduce from 300
  "min_stream_size": 2048,       // Increase from 1024
  "max_file_size": 52428800      // Reduce from 100MB
}
```

### Reduce Alert Volume

```json
{
  "suspicious_threshold": 0.60,  // Only alert on higher confidence
  "monitor_threshold": 0.30,     // Reduce monitoring noise
  "enable_blocking": true        // Auto-block malicious (vs manual review)
}
```

---

## Environment-Specific Recommendations

### Corporate Email Gateway

```json
{
  "entropy_threshold": 7.6,
  "risk_weights": {
    "signature": 0.45,
    "heuristic": 0.25,
    "ml": 0.30
  },
  "malicious_threshold": 0.80,
  "suspicious_threshold": 0.50,
  "trusted_domains": ["company.com", "partners.com"]
}
```

### Web Proxy (Mixed Traffic)

```json
{
  "entropy_threshold": 7.7,
  "risk_weights": {
    "signature": 0.40,
    "heuristic": 0.20,
    "ml": 0.40
  },
  "malicious_threshold": 0.85,
  "suspicious_threshold": 0.55,
  "max_context_modifier": 0.25
}
```

### Development Environment

```json
{
  "entropy_threshold": 7.8,
  "risk_weights": {
    "signature": 0.50,
    "heuristic": 0.15,
    "ml": 0.35
  },
  "malicious_threshold": 0.85,
  "suspicious_threshold": 0.60,
  "max_context_modifier": 0.20
}
```

### High-Security SOC

```json
{
  "entropy_threshold": 7.3,
  "risk_weights": {
    "signature": 0.40,
    "heuristic": 0.30,
    "ml": 0.30
  },
  "malicious_threshold": 0.75,
  "high_risk_threshold": 0.60,
  "suspicious_threshold": 0.40,
  "monitor_threshold": 0.20,
  "max_context_modifier": 0.35,
  "enable_blocking": true
}
```

---

## Advanced: A/B Testing

To scientifically determine optimal settings:

1. **Run two instances** with different configs
2. **Compare metrics** after 2 weeks:
   - Detection rate
   - False positive rate
   - Processing latency
3. **Choose winner** and continue iterating

Example A/B test:
- **Config A:** Default settings
- **Config B:** `malicious_threshold: 0.85, heuristic: 0.20`

Track:
```bash
# Count malicious verdicts
jq 'select(.detection.verdict=="malicious")' logs/detections.jsonl | wc -l

# Calculate average risk score
jq '.detection.risk_score' logs/detections.jsonl | awk '{sum+=$1; n++} END {print sum/n}'
```

---

## Monitoring & Alerts

Set up alerts for configuration drift:

```bash
# Alert if false positive rate > 10%
if [ $FP_RATE -gt 10 ]; then
    echo "False positive rate too high: $FP_RATE%"
    # Suggest increasing thresholds
fi

# Alert if no malicious detections in 24h (possible misconfiguration)
LAST_DETECTION=$(jq -r 'select(.detection.verdict=="malicious") | .timestamp' logs/detections.jsonl | tail -1)
if [ $(($(date +%s) - $LAST_DETECTION)) -gt 86400 ]; then
    echo "No malicious detections in 24h - verify configuration"
fi
```

---

## Troubleshooting

### Issue: All files marked as malicious

**Cause:** Thresholds too low or weights misconfigured

**Fix:**
```json
{
  "malicious_threshold": 0.80,  // Reset to default
  "risk_weights": {
    "signature": 0.40,
    "heuristic": 0.25,
    "ml": 0.35
  }
}
```

### Issue: No detections at all

**Cause:** Thresholds too high

**Fix:**
```json
{
  "malicious_threshold": 0.75,
  "suspicious_threshold": 0.45
}
```

### Issue: High CPU usage

**Cause:** Too many workers or inefficient settings

**Fix:**
```json
{
  "num_workers": 2,
  "num_detection_workers": 1,
  "min_stream_size": 4096
}
```

---

## Summary: Quick Reference

| Metric | Adjustment | Config Change |
|--------|-----------|---------------|
| High FP rate | Reduce sensitivity | Increase thresholds (+0.05-0.10) |
| High FN rate | Increase sensitivity | Decrease thresholds (-0.05-0.10) |
| Heuristic noise | Reduce heuristic | Decrease heuristic weight to 0.15-0.20 |
| Need better ML | Trust ML more | Increase ML weight to 0.40-0.45 |
| External download bias | Reduce context | Decrease max_context_modifier to 0.20 |
| Compression FPs | Increase threshold | Set entropy_threshold to 7.8-8.0 |

---

## Next Steps

1. **Start with defaults** for 1-2 weeks
2. **Measure baselines** (FP/FN rates, alert volume)
3. **Make small adjustments** (one parameter at a time)
4. **Validate changes** over 1 week
5. **Document your config** and rationale
6. **Review quarterly** and adjust for new threats

For questions or support, refer to:
- Risk analysis: `DETECTION_RISK_ANALYSIS.md`
- Example outputs: `EXAMPLE_ALERT_OUTPUT.md`
- Main documentation: `README.md`
