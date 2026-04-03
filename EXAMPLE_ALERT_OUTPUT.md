# Example Alert Outputs - Improved Explainability

This document shows example alert outputs from the improved detection system, demonstrating enhanced explainability for SOC analysts.

---

## Example 1: Critical Malware Detection (Known Signature)

### Scenario
A file with a known malware hash is detected in HTTP traffic from an external source.

### Alert Output (JSON)
```json
{
  "timestamp": 1706634000.123,
  "file": {
    "name": "invoice.pdf.exe",
    "size": 45612,
    "hash": "44d88612fea8a8f36de82e1278abb02f",
    "type": "application/octet-stream"
  },
  "session": {
    "src_ip": "203.45.67.89",
    "dst_ip": "10.0.50.15",
    "protocol": "HTTP"
  },
  "detection": {
    "verdict": "malicious",
    "severity": "critical",
    "risk_score": 0.95,
    "action": "block",
    "confidence": 0.92,
    "reasoning": {
      "primary_factors": [
        {
          "layer": "signature",
          "description": "Matched known malware: TrojanDownloader.Win32.Agent (family: trojan, sha256: 44d88612fea8a8f3...)",
          "contribution": 0.500,
          "severity": "critical",
          "confidence": 1.0
        }
      ],
      "supporting_factors": [
        {
          "layer": "heuristic",
          "type": "suspicious_extension",
          "description": "Suspicious or double file extension",
          "contribution": 0.150,
          "severity": "high",
          "confidence": 0.85
        },
        {
          "layer": "ml",
          "description": "Feature analysis indicates 87.5% probability of malware",
          "contribution": 0.306,
          "severity": "high",
          "confidence": 0.875,
          "features": [
            "Contains PE executable header",
            "High entropy: 7.82/8.0",
            "Suspicious strings: 12"
          ]
        }
      ],
      "context_adjustments": [
        {
          "factor": "external_source",
          "description": "File originated from external IP (203.45.67.89)",
          "adjustment": "+0.10"
        },
        {
          "factor": "dangerous_extension",
          "description": "File has potentially dangerous extension",
          "adjustment": "+0.15"
        },
        {
          "factor": "capped_modifier",
          "description": "Context modifier capped at 0.3",
          "adjustment": "capped from 0.25"
        }
      ],
      "score_breakdown": {
        "base_score": 0.850,
        "context_modifier": 0.100,
        "final_score": 0.950
      },
      "analyst_notes": [
        "CRITICAL: Immediate action required - known malware detected",
        "Recommended: Block traffic, quarantine file, investigate source",
        "Pattern match detected - consider validating against latest signature database to rule out false positive"
      ],
      "summary": "Known malware detected via signature match (severity: critical)"
    }
  }
}
```

### Console Output
```
[CRITICAL] THREAT DETECTED: invoice.pdf.exe - MALICIOUS (severity: critical, risk: 0.95, confidence: 0.92)
  Summary: Known malware detected via signature match (severity: critical)
```

### SOC Analyst View
**What happened:** Known malware (TrojanDownloader.Win32.Agent) detected via hash match  
**Why it's critical:** Signature database match with 100% confidence  
**What to do:** Immediate block and quarantine, investigate the source IP for other compromised systems  
**Additional context:** File uses double extension (.pdf.exe) and came from external IP

---

## Example 2: Suspicious File (Multiple Heuristic Indicators)

### Scenario
A legitimate compressed archive triggers multiple heuristic alerts but has no signature match.

### Alert Output (JSON)
```json
{
  "timestamp": 1706634100.456,
  "file": {
    "name": "software_update.zip",
    "size": 2048576,
    "hash": "a1b2c3d4e5f6...",
    "type": "application/zip"
  },
  "session": {
    "src_ip": "192.168.1.100",
    "dst_ip": "10.0.50.15",
    "protocol": "HTTP"
  },
  "detection": {
    "verdict": "suspicious",
    "severity": "medium",
    "risk_score": 0.52,
    "action": "alert",
    "confidence": 0.65,
    "reasoning": {
      "primary_factors": [
        {
          "layer": "heuristic",
          "type": "high_entropy",
          "description": "High entropy (7.92/8.0) suggests encryption/packing",
          "contribution": 0.075,
          "severity": "medium",
          "confidence": 0.75
        }
      ],
      "supporting_factors": [
        {
          "layer": "heuristic",
          "type": "suspicious_strings",
          "description": "Contains suspicious API calls or commands",
          "contribution": 0.075,
          "severity": "medium",
          "confidence": 0.75,
          "strings": [
            {"pattern": "CreateProcess", "context": "...kernel32.CreateProcess..."},
            {"pattern": "VirtualAlloc", "context": "...call VirtualAlloc..."}
          ]
        },
        {
          "layer": "ml",
          "description": "Feature analysis indicates 52.0% probability of malware",
          "contribution": 0.182,
          "severity": "medium",
          "confidence": 0.52,
          "features": [
            "High entropy: 7.92/8.0",
            "High byte diversity: 0.94"
          ]
        }
      ],
      "context_adjustments": [],
      "score_breakdown": {
        "base_score": 0.520,
        "context_modifier": 0.000,
        "final_score": 0.520
      },
      "analyst_notes": [
        "Suspicious indicators present - monitor and collect more context",
        "Suggested: Check if file type and source are expected for this user",
        "High entropy detected - verify if file is legitimately compressed/encrypted or if it indicates packing/obfuscation",
        "ML classification has low confidence - manual review recommended"
      ],
      "summary": "Suspicious characteristics detected (severity: medium)"
    }
  }
}
```

### Console Output
```
[WARNING] THREAT DETECTED: software_update.zip - SUSPICIOUS (severity: medium, risk: 0.52, confidence: 0.65)
  Summary: Suspicious characteristics detected (severity: medium)
```

### SOC Analyst View
**What happened:** Compressed file with high entropy and suspicious strings detected  
**Why it's flagged:** Multiple weak indicators suggest potential threat, but no definitive evidence  
**What to do:** Alert only - verify if this file type and source are expected for this user  
**Additional context:** Could be legitimate compressed software or packed malware - needs manual review

---

## Example 3: High Risk (ML Confidence, No Signature)

### Scenario
Script-based malware with no known signature but high ML confidence.

### Alert Output (JSON)
```json
{
  "timestamp": 1706634200.789,
  "file": {
    "name": "update_script.js",
    "size": 8192,
    "hash": "x9y8z7w6v5u4...",
    "type": "application/javascript"
  },
  "session": {
    "src_ip": "185.220.101.42",
    "dst_ip": "10.0.50.20",
    "protocol": "HTTP"
  },
  "detection": {
    "verdict": "malicious",
    "severity": "high",
    "risk_score": 0.82,
    "action": "block",
    "confidence": 0.89,
    "reasoning": {
      "primary_factors": [
        {
          "layer": "ml",
          "description": "Feature analysis indicates 92.0% probability of malware",
          "contribution": 0.368,
          "severity": "high",
          "confidence": 0.92,
          "features": [
            "Suspicious strings: 15",
            "High byte diversity: 0.88"
          ]
        },
        {
          "layer": "heuristic",
          "type": "suspicious_strings",
          "description": "Contains suspicious API calls or commands",
          "contribution": 0.063,
          "severity": "medium",
          "confidence": 0.70,
          "strings": [
            {"pattern": "eval(", "context": "...eval(atob(payload))..."},
            {"pattern": "exec(", "context": "...exec(shellcode)..."},
            {"pattern": "base64_decode", "context": "...decode(encrypted)..."}
          ]
        }
      ],
      "supporting_factors": [
        {
          "layer": "heuristic",
          "type": "obfuscation",
          "description": "Excessive encoding or obfuscation detected",
          "contribution": 0.063,
          "severity": "medium",
          "confidence": 0.70
        }
      ],
      "context_adjustments": [
        {
          "factor": "external_source",
          "description": "File originated from external IP (185.220.101.42)",
          "adjustment": "+0.10"
        }
      ],
      "score_breakdown": {
        "base_score": 0.720,
        "context_modifier": 0.100,
        "final_score": 0.820
      },
      "analyst_notes": [
        "HIGH PRIORITY: Likely malware - recommend immediate quarantine",
        "Suggested: Review threat intelligence for similar samples",
        "High entropy detected - verify if file is legitimately compressed/encrypted or if it indicates packing/obfuscation"
      ],
      "summary": "ML analysis indicates potential threat (severity: high)"
    }
  }
}
```

### Console Output
```
[HIGH] THREAT DETECTED: update_script.js - MALICIOUS (severity: high, risk: 0.82, confidence: 0.89)
  Summary: ML analysis indicates potential threat (severity: high)
```

### SOC Analyst View
**What happened:** JavaScript file with heavy obfuscation and suspicious patterns  
**Why it's flagged:** ML classifier shows 92% malware probability with high confidence  
**What to do:** Block and quarantine immediately, submit to sandbox for behavioral analysis  
**Additional context:** Contains eval(), base64 encoding, and shell execution patterns - typical of malicious scripts

---

## Example 4: Likely Benign (Low Risk, High Confidence)

### Scenario
A legitimate PDF document with normal characteristics.

### Alert Output (JSON)
```json
{
  "timestamp": 1706634300.123,
  "file": {
    "name": "report_2024.pdf",
    "size": 524288,
    "hash": "f1e2d3c4b5a6...",
    "type": "application/pdf"
  },
  "session": {
    "src_ip": "192.168.1.50",
    "dst_ip": "10.0.50.10",
    "protocol": "HTTP"
  },
  "detection": {
    "verdict": "benign",
    "severity": "low",
    "risk_score": 0.15,
    "action": "allow",
    "confidence": 0.88,
    "reasoning": {
      "primary_factors": [],
      "supporting_factors": [
        {
          "layer": "ml",
          "description": "Feature analysis indicates 15.0% probability of malware",
          "contribution": 0.053,
          "severity": "medium",
          "confidence": 0.85,
          "features": []
        }
      ],
      "context_adjustments": [],
      "score_breakdown": {
        "base_score": 0.150,
        "context_modifier": 0.000,
        "final_score": 0.150
      },
      "analyst_notes": [],
      "summary": "File classified as benign (severity: low) based on combined signals"
    }
  }
}
```

### Console Output
```
(No console output for benign files)
```

### SOC Analyst View
**What happened:** Standard PDF file with expected characteristics  
**Why it passed:** All detection layers indicate benign content with high confidence  
**What to do:** Allow - no action required  
**Additional context:** Normal file from internal network with expected structure

---

## Example 5: Monitor Category (Borderline Case)

### Scenario
A file with weak indicators that doesn't meet the suspicious threshold but is worth logging.

### Alert Output (JSON)
```json
{
  "timestamp": 1706634400.567,
  "file": {
    "name": "config.json",
    "size": 4096,
    "hash": "q1w2e3r4t5y6...",
    "type": "application/json"
  },
  "session": {
    "src_ip": "192.168.1.75",
    "dst_ip": "10.0.50.25",
    "protocol": "HTTP"
  },
  "detection": {
    "verdict": "monitor",
    "severity": "low",
    "risk_score": 0.35,
    "action": "monitor",
    "confidence": 0.72,
    "reasoning": {
      "primary_factors": [],
      "supporting_factors": [
        {
          "layer": "heuristic",
          "type": "suspicious_strings",
          "description": "Contains suspicious API calls or commands",
          "contribution": 0.050,
          "severity": "medium",
          "confidence": 0.60,
          "strings": [
            {"pattern": "bitcoin", "context": "...bitcoin_wallet_address..."}
          ]
        },
        {
          "layer": "ml",
          "description": "Feature analysis indicates 35.0% probability of malware",
          "contribution": 0.123,
          "severity": "medium",
          "confidence": 0.35,
          "features": [
            "Suspicious strings: 3"
          ]
        }
      ],
      "context_adjustments": [],
      "score_breakdown": {
        "base_score": 0.350,
        "context_modifier": 0.000,
        "final_score": 0.350
      },
      "analyst_notes": [
        "Low risk but worth monitoring - log for future correlation"
      ],
      "summary": "File classified as monitor (severity: low) based on combined signals"
    }
  }
}
```

### Console Output
```
(No console output for monitor-level files)
```

### SOC Analyst View
**What happened:** Configuration file with cryptocurrency-related strings  
**Why it's flagged:** Contains keywords that could indicate malware, but context suggests legitimate use  
**What to do:** Monitor only - log for correlation with other events  
**Additional context:** May be a legitimate cryptocurrency application configuration - worth tracking but not blocking

---

## Key Improvements Demonstrated

### 1. **Multi-Level Severity**
- **Critical:** Known malware requiring immediate action
- **High:** Likely threat with strong indicators
- **Medium:** Suspicious but not definitive
- **Low:** Worth tracking but likely benign

### 2. **Detailed Score Breakdown**
- Base score from detection layers
- Context modifiers with explanations
- Final score calculation shown step-by-step
- Individual layer contributions visible

### 3. **Confidence Levels**
- Overall confidence in the verdict
- Per-layer confidence scores
- Confidence affects threshold application
- Helps analysts understand certainty

### 4. **Actionable Analyst Notes**
- Specific next steps recommended
- Context about why indicators triggered
- Validation suggestions
- Links to threat intelligence (future enhancement)

### 5. **Explainable Reasoning**
- Primary factors that drove the decision
- Supporting factors that contributed
- Context adjustments with justifications
- One-line summary for quick assessment

### 6. **Appropriate Actions**
- **Block:** Known malware
- **Quarantine:** High risk/suspicious with high confidence
- **Alert:** Suspicious with low confidence
- **Monitor:** Borderline cases worth tracking
- **Allow:** Benign content

---

## Usage for SOC Analysts

### Quick Triage (Console)
1. Check severity indicator: `[CRITICAL]`, `[HIGH]`, `[WARNING]`, `[INFO]`
2. Read summary line for immediate context
3. Decide if detailed investigation is needed

### Detailed Investigation (JSON Log)
1. Review `primary_factors` for main indicators
2. Check `confidence` to assess certainty
3. Read `analyst_notes` for recommended actions
4. Examine `score_breakdown` to understand the math
5. Validate `context_adjustments` are appropriate

### Tuning Detection Logic
1. Track false positives by analyzing `reasoning`
2. Adjust thresholds in config based on `risk_score` patterns
3. Review `layer_confidences` to identify weak detection layers
4. Use `score_breakdown` to balance layer weights

---

## Configuration Options for Tuning

```json
{
  "risk_weights": {
    "signature": 0.40,
    "heuristic": 0.25,
    "ml": 0.35
  },
  "malicious_threshold": 0.80,
  "high_risk_threshold": 0.65,
  "suspicious_threshold": 0.50,
  "monitor_threshold": 0.25,
  "max_context_modifier": 0.30,
  "trusted_domains": ["company.com", "partner.org"]
}
```

### Tuning Guidance
- **High false positives:** Increase thresholds (e.g., `suspicious_threshold: 0.60`)
- **Missing threats:** Decrease thresholds or increase ML weight
- **External source bias:** Reduce `max_context_modifier`
- **Signature false positives:** Reduce `signature` weight to 0.35
- **Script-heavy environment:** Increase `heuristic` weight for better coverage
