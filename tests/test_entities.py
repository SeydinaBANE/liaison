"""Tests de l'extraction d'entites."""

from __future__ import annotations

from liaison.entities import extract_customer_id

_NAMES = {"acme": 1, "globex": 2}


def test_extract_numeric_id() -> None:
    assert extract_customer_id("quel est l'encours du client 2 ?", _NAMES) == 2


def test_extract_by_known_name() -> None:
    assert extract_customer_id("y a-t-il un litige chez Acme ?", _NAMES) == 1


def test_returns_none_when_unresolved() -> None:
    assert extract_customer_id("bonjour, comment ca va ?", _NAMES) is None
