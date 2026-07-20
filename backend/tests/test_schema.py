"""Tests for extraction schema validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError


class TestEnumValidation:
    def test_valid_issue_category_values(self):
        from app.schema import IssueCategory

        assert IssueCategory("billing").value == "billing"
        assert IssueCategory("technical").value == "technical"
        assert IssueCategory("shipping").value == "shipping"
        assert IssueCategory("account").value == "account"
        assert IssueCategory("product").value == "product"
        assert IssueCategory("other").value == "other"

    def test_invalid_issue_category_raises(self):
        from app.schema import IssueCategory

        with pytest.raises(ValueError):
            IssueCategory("invalid_category")

    def test_valid_urgency_values(self):
        from app.schema import Urgency

        assert Urgency("low").value == "low"
        assert Urgency("medium").value == "medium"
        assert Urgency("high").value == "high"
        assert Urgency("critical").value == "critical"

    def test_invalid_urgency_raises(self):
        from app.schema import Urgency

        with pytest.raises(ValueError):
            Urgency("unknown")

    def test_valid_sentiment_values(self):
        from app.schema import Sentiment

        assert Sentiment("frustrated").value == "frustrated"
        assert Sentiment("neutral").value == "neutral"
        assert Sentiment("satisfied").value == "satisfied"
        assert Sentiment("angry").value == "angry"

    def test_invalid_sentiment_raises(self):
        from app.schema import Sentiment

        with pytest.raises(ValueError):
            Sentiment("happy")

    def test_valid_resolution_status_values(self):
        from app.schema import ResolutionStatus

        assert ResolutionStatus("unresolved").value == "unresolved"
        assert ResolutionStatus("pending").value == "pending"
        assert ResolutionStatus("resolved").value == "resolved"
        assert ResolutionStatus("escalated").value == "escalated"

    def test_invalid_resolution_status_raises(self):
        from app.schema import ResolutionStatus

        with pytest.raises(ValueError):
            ResolutionStatus("closed")


class TestTicketExtractionValidation:
    def test_valid_extraction_passes(self, valid_extraction_dict):
        from app.schema import TicketExtraction

        ticket = TicketExtraction(**valid_extraction_dict)
        assert ticket.ticket_id == "TKT-001"
        assert ticket.customer.name == "John Doe"
        assert ticket.issue.category.value == "technical"
        assert ticket.issue.urgency.value == "high"
        assert ticket.sentiment.value == "frustrated"
        assert ticket.resolution_status.value == "unresolved"

    def test_invalid_category_raises(self):
        from app.schema import TicketExtraction

        with pytest.raises(ValidationError):
            TicketExtraction(
                ticket_id="TKT-001",
                customer={"name": "John", "account_id": None},
                issue={"category": "bogus", "urgency": "high"},
                sentiment="frustrated",
                entities={"order_ids": [], "dates_mentioned": [], "amounts_mentioned": []},
                resolution_status="unresolved",
            )

    def test_invalid_urgency_raises(self):
        from app.schema import TicketExtraction

        with pytest.raises(ValidationError):
            TicketExtraction(
                ticket_id="TKT-001",
                customer={"name": None, "account_id": None},
                issue={"category": "billing", "urgency": "extreme"},
                sentiment="neutral",
                entities={},
                resolution_status="unresolved",
            )

    def test_missing_required_fields_raises(self):
        from app.schema import TicketExtraction

        with pytest.raises(ValidationError):
            TicketExtraction(
                customer={},
                issue={},
            )

    def test_missing_ticket_id_raises(self):
        from app.schema import TicketExtraction

        with pytest.raises(ValidationError):
            TicketExtraction(
                customer={"name": None, "account_id": None},
                issue={"category": "billing", "urgency": "low"},
                sentiment="neutral",
                entities={},
                resolution_status="unresolved",
            )

    def test_missing_entities_raises(self):
        from app.schema import TicketExtraction

        with pytest.raises(ValidationError):
            TicketExtraction(
                ticket_id="TKT-001",
                customer={"name": None, "account_id": None},
                issue={"category": "billing", "urgency": "low"},
                sentiment="neutral",
                resolution_status="unresolved",
            )


class TestCustomerValidation:
    def test_customer_with_all_fields(self):
        from app.schema import Customer

        c = Customer(name="Alice", account_id="ACC-001")
        assert c.name == "Alice"
        assert c.account_id == "ACC-001"

    def test_customer_with_optional_fields_none(self):
        from app.schema import Customer

        c = Customer()
        assert c.name is None
        assert c.account_id is None

    def test_customer_partial_fields(self):
        from app.schema import Customer

        c = Customer(name="Bob")
        assert c.name == "Bob"
        assert c.account_id is None


class TestIssueValidation:
    def test_issue_required_fields_only(self):
        from app.schema import Issue, IssueCategory, Urgency

        issue = Issue(category=IssueCategory.billing, urgency=Urgency.high)
        assert issue.category.value == "billing"
        assert issue.urgency.value == "high"
        assert issue.subcategory is None
        assert issue.product_or_service is None

    def test_issue_all_fields(self):
        from app.schema import Issue, IssueCategory, Urgency

        issue = Issue(
            category=IssueCategory.technical,
            subcategory="network",
            product_or_service="router",
            urgency=Urgency.critical,
        )
        assert issue.subcategory == "network"
        assert issue.product_or_service == "router"


class TestEntitiesValidation:
    def test_entities_default_empty(self):
        from app.schema import Entities

        e = Entities()
        assert e.order_ids == []
        assert e.dates_mentioned == []
        assert e.amounts_mentioned == []

    def test_entities_with_values(self):
        from app.schema import Entities

        e = Entities(
            order_ids=["ORD-001", "ORD-002"],
            dates_mentioned=["2024-01-01"],
            amounts_mentioned=["$100", "$200"],
        )
        assert len(e.order_ids) == 2
        assert len(e.dates_mentioned) == 1
        assert len(e.amounts_mentioned) == 2


class TestNestedObjectValidation:
    def test_ticket_with_nested_objects(self, valid_extraction_dict):
        from app.schema import TicketExtraction

        ticket = TicketExtraction(**valid_extraction_dict)
        assert ticket.customer.name == "John Doe"
        assert ticket.issue.subcategory == "login failure"
        assert len(ticket.entities.order_ids) == 1

    def test_ticket_serialization(self, valid_extraction_dict):
        from app.schema import TicketExtraction

        ticket = TicketExtraction(**valid_extraction_dict)
        dumped = ticket.model_dump(mode="json")
        assert dumped["ticket_id"] == "TKT-001"
        assert dumped["customer"]["name"] == "John Doe"
        assert dumped["issue"]["category"] == "technical"
        assert dumped["sentiment"] == "frustrated"
        assert dumped["resolution_status"] == "unresolved"


class TestOptionalFields:
    def test_optional_fields_default_to_none(self):
        from app.schema import (
            Customer,
            Entities,
            Issue,
            IssueCategory,
            ResolutionStatus,
            Sentiment,
            TicketExtraction,
            Urgency,
        )

        ticket = TicketExtraction(
            ticket_id="TKT-001",
            customer=Customer(),
            issue=Issue(category=IssueCategory.other, urgency=Urgency.low),
            sentiment=Sentiment.neutral,
            entities=Entities(),
            resolution_status=ResolutionStatus.unresolved,
        )
        assert ticket.requested_action is None
        assert ticket.customer.name is None
        assert ticket.customer.account_id is None
        assert ticket.issue.subcategory is None
        assert ticket.issue.product_or_service is None

    def test_optional_fields_with_values(self):
        from app.schema import (
            Customer,
            Entities,
            Issue,
            IssueCategory,
            ResolutionStatus,
            Sentiment,
            TicketExtraction,
            Urgency,
        )

        ticket = TicketExtraction(
            ticket_id="TKT-001",
            customer=Customer(name="Alice", account_id="ACC-001"),
            issue=Issue(
                category=IssueCategory.billing,
                subcategory="refund",
                product_or_service="service",
                urgency=Urgency.high,
            ),
            sentiment=Sentiment.frustrated,
            entities=Entities(order_ids=["ORD-001"], dates_mentioned=["2024-01-01"]),
            requested_action="process refund",
            resolution_status=ResolutionStatus.pending,
        )
        assert ticket.requested_action == "process refund"
        assert ticket.customer.name == "Alice"
        assert ticket.issue.subcategory == "refund"
        assert len(ticket.entities.order_ids) == 1
