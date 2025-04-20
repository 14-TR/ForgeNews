"""
Unit tests for guardrails: relevance, safety, moderation, PII filtering, and execute_guardrails.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from core.guardrails import (
    relevance_classifier,
    safety_classifier,
    moderation_check,
    pii_filter,
    execute_guardrails,
)


def test_relevance_classifier_defaults_to_true():
    assert relevance_classifier("any input") is True


def test_safety_classifier_defaults_to_true():
    assert safety_classifier("harmless text") is True


def test_moderation_check_defaults_to_true():
    assert moderation_check("clean content") is True


def test_pii_filter_no_changes_for_clean_text():
    text = "No PII here"
    assert pii_filter(text) == text


def test_execute_guardrails_all_pass(monkeypatch):
    # All classifiers return True by default
    assert execute_guardrails("input") is True


def test_execute_guardrails_relevance_fail(monkeypatch):
    monkeypatch.setattr('core.guardrails.relevance_classifier', lambda x: False)
    assert execute_guardrails("input") is False


def test_execute_guardrails_safety_fail(monkeypatch):
    monkeypatch.setattr('core.guardrails.relevance_classifier', lambda x: True)
    monkeypatch.setattr('core.guardrails.safety_classifier', lambda x: False)
    assert execute_guardrails("input") is False


def test_execute_guardrails_moderation_fail(monkeypatch):
    monkeypatch.setattr('core.guardrails.relevance_classifier', lambda x: True)
    monkeypatch.setattr('core.guardrails.safety_classifier', lambda x: True)
    monkeypatch.setattr('core.guardrails.moderation_check', lambda x: False)
    assert execute_guardrails("input") is False
 