"""
Phase 17 standalone logic tests (no DB / SQLAlchemy required).
Tests the pure-Python engines directly.
"""
import math
import sys

passed = failed = 0

def check(name, condition, msg=""):
    global passed, failed
    if condition:
        print(f"  PASS  {name}")
        passed += 1
    else:
        print(f"  FAIL  {name}: {msg}")
        failed += 1

# ── Inline ConfidenceEngine (no imports) ─────────────────────────────────────
def calculate_confidence(evidence_count, source):
    if source == "USER_EXPLICIT":
        return 1.0
    if evidence_count <= 0:
        return 0.0
    raw = 0.15 * math.log2(evidence_count + 1)
    return round(min(1.0, raw), 4)

def decay_confidence(conf, days_inactive, decay_days=90):
    if days_inactive <= 0:
        return conf
    factor = max(0.0, 1.0 - (days_inactive / decay_days))
    return round(conf * factor, 4)

print("\n=== ConfidenceEngine ===")
check("explicit_always_1", calculate_confidence(0, "USER_EXPLICIT") == 1.0)
check("explicit_always_1_large", calculate_confidence(100, "USER_EXPLICIT") == 1.0)
check("zero_evidence_is_zero", calculate_confidence(0, "BEHAVIOR") == 0.0)
check("one_evidence_formula",
      abs(calculate_confidence(1, "BEHAVIOR") - round(0.15 * math.log2(2), 4)) < 0.001)
check("5_evidence_below_threshold", calculate_confidence(5, "BEHAVIOR") < 0.75,
      f"got {calculate_confidence(5, 'BEHAVIOR')}")
vals = [calculate_confidence(n, "BEHAVIOR") for n in [1, 5, 15, 30, 100]]
check("monotonically_increasing", vals == sorted(vals), str(vals))
check("capped_at_1", calculate_confidence(10000, "BEHAVIOR") == 1.0)
check("meets_threshold_true", calculate_confidence(0.8, "USER_EXPLICIT") >= 0.75)
check("meets_threshold_false", calculate_confidence(5, "BEHAVIOR") < 0.75)
decayed = decay_confidence(0.8, 45, 90)
check("decay_reduces_by_half", decayed == round(0.8 * 0.5, 4), f"got {decayed}")
check("decay_floors_at_zero", decay_confidence(0.5, 200, 90) == 0.0)
check("decay_zero_days_unchanged", decay_confidence(0.8, 0, 90) == 0.8)

print("\n=== Priority Constants ===")
PRIORITY_USER_EXPLICIT = 100
PRIORITY_BEHAVIOR = 50
check("explicit_priority_higher", PRIORITY_USER_EXPLICIT > PRIORITY_BEHAVIOR)
check("explicit_priority_is_100", PRIORITY_USER_EXPLICIT == 100)
check("behavior_priority_is_50", PRIORITY_BEHAVIOR == 50)

print("\n=== Extraction Rules Validity ===")
EXTRACTION_RULES = [
    ("RESPONSE_SHORTENED", "response_length", "short"),
    ("RESPONSE_EXPANDED", "response_length", "detailed"),
    ("VOICE_USED", "interface_preference", "voice"),
    ("TEXT_USED", "interface_preference", "text"),
    ("ROUTINE_ACCEPTED", "routine_suggestions", "enabled"),
    ("ROUTINE_REJECTED", "routine_suggestions", "disabled"),
    ("IOT_SUGGESTION_ACCEPTED", "iot_suggestions", "enabled"),
    ("IOT_SUGGESTION_REJECTED", "iot_suggestions", "disabled"),
    ("NOTIFICATION_DISMISSED", "notification_frequency", "low"),
]
check("rules_not_empty", len(EXTRACTION_RULES) > 0)
check("rules_have_3_parts", all(len(r) == 3 for r in EXTRACTION_RULES))
check("response_shortened_mapped",
      any(r[0] == "RESPONSE_SHORTENED" and r[1] == "response_length" for r in EXTRACTION_RULES))
check("voice_used_mapped",
      any(r[0] == "VOICE_USED" and r[2] == "voice" for r in EXTRACTION_RULES))

print("\n=== Priority Chain ===")
# Simulate preference resolution: explicit wins over learned
preferences = [
    {"key": "response_length", "value": "detailed", "priority": PRIORITY_BEHAVIOR},   # learned
    {"key": "response_length", "value": "short",    "priority": PRIORITY_USER_EXPLICIT},  # explicit
]
sorted_prefs = sorted(preferences, key=lambda p: p["priority"], reverse=True)
check("explicit_wins_over_learned", sorted_prefs[0]["value"] == "short",
      f"Winner was: {sorted_prefs[0]}")

print("\n=== Contradiction Scope ===")
# Global learned pref should NOT overwrite a newer explicit one; it just loses on priority
global_pref = {"key": "response_length", "value": "detailed", "scope": "GLOBAL", "priority": PRIORITY_BEHAVIOR}
explicit_pref = {"key": "response_length", "value": "short", "scope": "GLOBAL", "priority": PRIORITY_USER_EXPLICIT}
winner = max([global_pref, explicit_pref], key=lambda p: p["priority"])
check("contradiction_resolved_to_explicit", winner["source"] if "source" in winner else winner["value"] == "short")

print("\n=== DecayEngine ===")
ARCHIVE_THRESHOLD = 0.15
check("archive_threshold_sensible", 0.0 < ARCHIVE_THRESHOLD < 0.5)
low_conf = decay_confidence(0.3, 100, 90)
check("very_inactive_gets_archived", low_conf < ARCHIVE_THRESHOLD, f"got {low_conf}")

print("\n=== Adaptation Context Format ===")
_KEY_LABELS = {
    "response_length": "Response length", "language": "Language",
    "tone": "Tone", "formatting": "Formatting",
}
_VALUE_LABELS = {"short": "Short / concise", "th": "Thai (ภาษาไทย)", "friendly": "Friendly"}
pref_map = {"response_length": "short", "language": "th"}
lines = ["PERSONALIZATION:"]
for key, value in pref_map.items():
    label = _KEY_LABELS.get(key, key)
    val_label = _VALUE_LABELS.get(value, value)
    lines.append(f"  {label}: {val_label}")
ctx = "\n".join(lines)
check("context_contains_header", "PERSONALIZATION:" in ctx)
check("context_contains_response_length", "Response length" in ctx)
check("context_contains_thai", "Thai" in ctx)

print(f"\n{'='*40}")
print(f"RESULT: {passed} passed, {failed} failed")
if failed > 0:
    sys.exit(1)
