# Security Patches - Code Snippets

This document contains the key security patches applied to the malware detection system. Use these patterns when extending the system.

---

## 1. Filename Sanitization (Path Traversal Prevention)

**File:** `file_extraction.py`

```python
def _sanitize_filename(self, filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks
    
    Args:
        filename: Original filename from untrusted source
        
    Returns:
        Sanitized filename safe for use
    """
    if not filename:
        return 'unknown'
    
    # Remove any path components to prevent directory traversal
    filename = os.path.basename(filename)
    
    # Remove dangerous characters and path separators
    # Allow only alphanumeric, dots, hyphens, underscores
    safe_chars = []
    for char in filename:
        if char.isalnum() or char in '.-_':
            safe_chars.append(char)
        else:
            safe_chars.append('_')
    
    filename = ''.join(safe_chars)
    
    # Prevent hidden files
    if filename.startswith('.'):
        filename = '_' + filename[1:]
    
    # Limit length
    if len(filename) > MAX_FILENAME_LENGTH:
        name, ext = os.path.splitext(filename)
        if ext:
            max_name_len = MAX_FILENAME_LENGTH - len(ext)
            filename = name[:max_name_len] + ext
        else:
            filename = filename[:MAX_FILENAME_LENGTH]
    
    # Ensure we have a valid filename
    if not filename or filename == '.' or filename == '..':
        filename = 'sanitized_file'
    
    return filename
```

**Usage:**
```python
# Always sanitize filenames from untrusted sources
filename = self._extract_filename_from_headers(headers)
filename = self._sanitize_filename(filename)  # CRITICAL
```

---

## 2. Path Traversal Prevention in File Operations

**File:** `response_handler.py`

```python
# Sanitize filename
original_name = self._sanitize_quarantine_name(original_name)

# Build path
quarantine_path = os.path.abspath(os.path.join(self.quarantine_dir, quarantine_name))
quarantine_dir_abs = os.path.abspath(self.quarantine_dir)

# Validate path is within allowed directory
if not quarantine_path.startswith(quarantine_dir_abs + os.sep):
    logger.error(f"Path traversal attempt detected: {quarantine_name}")
    return
```

**Why This Matters:**
- `os.path.abspath()` resolves `..` and symbolic links
- Comparison ensures file stays within quarantine directory
- Prevents writing to `/etc/passwd` or other system files

---

## 3. ReDoS Prevention with Input Size Limits

**File:** `file_extraction.py`

```python
# Define at module level
MAX_REGEX_INPUT_SIZE = 10 * 1024 * 1024  # 10MB

def _parse_multipart(self, headers: bytes, body: bytes, session_data: dict):
    # Limit size for regex operations to prevent ReDoS
    if len(headers) > MAX_REGEX_INPUT_SIZE or len(body) > self.max_file_size:
        logger.warning("Multipart data exceeds size limits")
        return files
    
    # Use bounded regex
    boundary_match = re.search(rb'boundary=([^;\r\n]{1,200})', headers)  # {1,200} bound
    if not boundary_match:
        return files
```

**Why This Matters:**
- Unbounded regex on large input = catastrophic backtracking
- Size limits prevent CPU exhaustion
- Bounded quantifiers prevent ReDoS patterns

---

## 4. Resource Limits for DoS Prevention

**File:** `file_extraction.py`

```python
# Limit number of multipart sections
parts = body.split(boundary)
if len(parts) > 1000:  # Reasonable limit
    logger.warning("Too many multipart sections, truncating")
    parts = parts[:1000]

# Limit email parts
part_count = 0
max_parts = 100
for part in msg.walk():
    part_count += 1
    if part_count > max_parts:
        logger.warning("Email has too many parts, stopping extraction")
        break
```

**Why This Matters:**
- Prevents "email bomb" attacks (1000s of attachments)
- Prevents memory exhaustion from excessive parts
- Maintains system availability

---

## 5. Secure File Permissions

**File:** `response_handler.py`

```python
import stat

# Create directory with restrictive permissions
os.makedirs(self.quarantine_dir, mode=0o700, exist_ok=True)
os.chmod(self.quarantine_dir, stat.S_IRWXU)  # Owner only: rwx------

# Write file and set permissions
with open(quarantine_path, 'wb') as f:
    f.write(file_data)

os.chmod(quarantine_path, stat.S_IRUSR | stat.S_IWUSR)  # Owner only: rw-------
```

**Why This Matters:**
- Prevents unauthorized users from reading malware samples
- Follows principle of least privilege
- Essential for compliance (PCI-DSS, SOC2)

---

## 6. Log Injection Prevention

**File:** `response_handler.py`, `detection_system.py`

```python
# Sanitize all user-controlled data before logging
filename_safe = str(file_info.get('filename', 'unknown')).replace('\n', '').replace('\r', '')[:100]
verdict_safe = str(risk_assessment.get('verdict', 'unknown')).replace('\n', '').replace('\r', '')[:50]

logger.warning(f"[{severity}] THREAT ALERT: {filename_safe} - {verdict_safe.upper()}")
```

**Why This Matters:**
- Prevents attacker from injecting fake log entries
- Prevents corruption of log analysis
- Essential for SIEM integration

---

## 7. Configuration Validation

**File:** `detection_system.py`

```python
def _load_config(self, config_path: str) -> dict:
    # Validate file exists and size
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    file_size = os.path.getsize(config_path)
    if file_size > MAX_CONFIG_SIZE:
        raise ValueError(f"Config file too large: {file_size} bytes")
    
    # Load and validate
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    self._validate_config(config)
    return config

def _validate_config(self, config: dict):
    # Validate mode
    mode = config.get('mode', 'PCAP')
    if mode not in ['PCAP', 'LIVE']:
        raise ValueError(f"Invalid mode: {mode}")
    
    # Validate numeric bounds
    num_workers = config.get('num_workers', 4)
    if not isinstance(num_workers, int) or num_workers < 1 or num_workers > 32:
        raise ValueError(f"Invalid num_workers: {num_workers}")
```

**Why This Matters:**
- Prevents crashes from malformed configs
- Enforces resource limits
- Fails fast with clear error messages

---

## 8. Input Size Validation (DoS Prevention)

**File:** `packet_capture.py`

```python
MAX_PCAP_SIZE = 1024 * 1024 * 1024  # 1GB
MAX_PACKET_COUNT = 10_000_000

def read_pcap(self, pcap_file: str, callback: Callable):
    # Check file size
    file_size = os.path.getsize(pcap_file)
    if file_size > MAX_PCAP_SIZE:
        raise ValueError(f"PCAP file exceeds maximum size of {MAX_PCAP_SIZE} bytes")
    
    packets = rdpcap(pcap_file)
    
    # Limit packet count
    if len(packets) > MAX_PACKET_COUNT:
        logger.warning(f"PCAP has {len(packets)} packets, limiting to {MAX_PACKET_COUNT}")
        packets = packets[:MAX_PACKET_COUNT]
```

**Why This Matters:**
- Prevents memory exhaustion from huge PCAP files
- Predictable resource usage
- Prevents DoS attacks

---

## 9. BPF Filter Validation (Injection Prevention)

**File:** `packet_capture.py`

```python
def _validate_bpf_filter(self, bpf_filter: str) -> bool:
    """Validate BPF filter to prevent injection attacks"""
    if not bpf_filter or len(bpf_filter) > 500:
        return False
    
    # Allow only safe characters
    allowed_chars = set('abcdefghijklmnopqrstuvwxyz0123456789 .-_()[]!&|<>=/')
    
    if not all(c.lower() in allowed_chars for c in bpf_filter):
        return False
    
    return True

# Usage
bpf_filter = self.config.get('bpf_filter', 'tcp')
if not self._validate_bpf_filter(bpf_filter):
    raise ValueError("Invalid BPF filter")
```

**Why This Matters:**
- Prevents filter injection attacks
- Whitelist approach is secure by default
- Clear validation errors

---

## 10. Bounded Data in Log Entries

**File:** `response_handler.py`

```python
MAX_LOG_ENTRY_SIZE = 1024 * 1024  # 1MB

# Build log with bounded fields
alert = {
    'file': {
        'name': str(file_info.get('filename', 'unknown'))[:500],  # Bounded
        'hash': str(file_info.get('hash', {}).get('sha256', 'unknown'))[:64],
    },
    'session': {
        'src_ip': str(session_data.get('src_ip', 'unknown'))[:45],
        'dst_ip': str(session_data.get('dst_ip', 'unknown'))[:45],
    },
    'detection': {
        'reasoning': risk_assessment.get('reasoning', [])[:10]  # Max 10 entries
    }
}

# Validate total size
alert_json = json.dumps(alert)
if len(alert_json) > MAX_LOG_ENTRY_SIZE:
    logger.warning("Alert too large, truncating")
    alert['detection']['reasoning'] = alert['detection']['reasoning'][:3]
```

**Why This Matters:**
- Prevents disk exhaustion from malicious log entries
- Predictable log file sizes
- Enables log rotation strategies

---

## 11. Queue Size Limits

**File:** `detection_system.py`

```python
# Define hard caps
MAX_QUEUE_SIZE = 10000
MAX_DETECTION_QUEUE_SIZE = 5000

# Enforce limits
queue_size = min(self.config.get('queue_size', MAX_QUEUE_SIZE), MAX_QUEUE_SIZE)
detection_queue_size = min(
    self.config.get('detection_queue_size', MAX_DETECTION_QUEUE_SIZE),
    MAX_DETECTION_QUEUE_SIZE
)

self.packet_queue = Queue(maxsize=queue_size)
self.detection_queue = Queue(maxsize=detection_queue_size)
```

**Why This Matters:**
- Prevents unbounded memory growth
- Config can't override security limits
- Graceful degradation under load

---

## 12. Proper Exception Handling

**File:** `detection_system.py`, all files

```python
# BEFORE - BAD
try:
    risky_operation()
except:
    pass  # Silent failure, debugging nightmare

# AFTER - GOOD
try:
    risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
except IOError as e:
    logger.error(f"I/O error: {e}", exc_info=True)
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
```

**Why This Matters:**
- Specific exceptions enable debugging
- `exc_info=True` provides stack traces
- Different handling for different error types

---

## Security Checklist for New Code

When adding new features, ensure:

- [ ] **Filename sanitization** - Use `_sanitize_filename()` on all external filenames
- [ ] **Path validation** - Use `os.path.abspath()` and verify paths before file operations
- [ ] **Size limits** - Enforce max sizes on all inputs (files, strings, arrays)
- [ ] **Regex bounds** - Use `{min,max}` in regex and limit input size
- [ ] **Log sanitization** - Remove `\n`, `\r` from logged user data
- [ ] **File permissions** - Use `0o700` for dirs, `0o600` for sensitive files
- [ ] **Config validation** - Validate all config values with type and range checks
- [ ] **Exception handling** - Catch specific exceptions, log with context
- [ ] **Resource limits** - Set hard caps on queues, threads, memory
- [ ] **Input validation** - Validate all external input (network, files, config)

---

## Testing Security Patches

### Test 1: Path Traversal
```python
# Should be sanitized to safe filename
assert _sanitize_filename("../../../../etc/passwd") == "etc_passwd"
assert _sanitize_filename("..\\..\\windows\\system32") == "windows_system32"
assert _sanitize_filename("test\0file.exe") == "test_file.exe"
```

### Test 2: Size Limits
```python
# Should reject oversized inputs
large_data = b'A' * (MAX_PCAP_SIZE + 1)
with pytest.raises(ValueError):
    read_pcap(large_pcap_file, callback)
```

### Test 3: Log Injection
```python
# Should sanitize newlines
malicious_filename = "test\nFAKE_LOG_ENTRY\nmalicious"
safe = sanitize_for_log(malicious_filename)
assert '\n' not in safe
assert '\r' not in safe
```

---

## Production Deployment Notes

1. **File Permissions**: Verify quarantine directory is `0o700` and owned by service user
2. **Resource Limits**: Set `ulimit` for process (memory, file descriptors)
3. **Monitoring**: Alert on quarantine directory size > 1GB
4. **Log Rotation**: Configure logrotate for all `.jsonl` files
5. **Updates**: Regular signature database updates via cron
6. **Backups**: Exclude quarantine directory from backups (contains malware)

---

## References

- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [CWE-22: Path Traversal](https://cwe.mitre.org/data/definitions/22.html)
- [CWE-400: Resource Exhaustion](https://cwe.mitre.org/data/definitions/400.html)
- [NIST SP 800-53 Security Controls](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf)

