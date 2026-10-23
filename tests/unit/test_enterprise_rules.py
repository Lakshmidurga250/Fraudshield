"""Unit test verifying Enterprise Rule Engines and evaluate_rule functions."""

from enterprise.bin_network.rules_part_01 import BinRuleEnginePart01
from enterprise.fraud_vectors.rules_part_01 import SigRuleEnginePart01
from enterprise.compliance_rbi.rules_part_01 import RbiRuleEnginePart01


def test_bin_rule_engine_evaluation():
    """Verify that BIN rule engine evaluates known rule IDs accurately."""
    res = BinRuleEnginePart01.evaluate_rule("RULE_BIN_01_0001", amount=15000.0)
    assert res["found"] is True
    assert "triggered" in res
    assert "score" in res
    assert "action" in res


def test_bin_rule_engine_not_found():
    """Verify unknown rule IDs return safe fallback."""
    res = BinRuleEnginePart01.evaluate_rule("UNKNOWN_RULE", amount=500.0)
    assert res["found"] is False
    assert res["action"] == "PASS"


def test_signature_and_compliance_rules():
    """Verify fraud vector and RBI compliance rule engines."""
    sig_res = SigRuleEnginePart01.evaluate_rule("RULE_SIG_01_0001", amount=25000.0)
    assert sig_res["found"] is True

    rbi_res = RbiRuleEnginePart01.evaluate_rule("RULE_RBI_01_0001", amount=50000.0)
    assert rbi_res["found"] is True
