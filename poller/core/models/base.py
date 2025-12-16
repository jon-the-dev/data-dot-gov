"""
Base data models for government data structures.

Provides common base classes and utilities for data validation
and type safety across congressional and lobbying data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class BaseRecord:
    """Base class for all government data records"""

    # Common metadata fields
    record_type: str
    identifier: str
    created_at: Optional[datetime] = field(default_factory=datetime.utcnow)
    source_url: Optional[str] = None
    api_source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseRecord":
        """Create record from dictionary"""
        # Handle datetime fields
        if "created_at" in data and isinstance(data["created_at"], str):
            try:
                data["created_at"] = datetime.fromisoformat(data["created_at"])
            except ValueError:
                data["created_at"] = None

        # Filter data to only include fields that exist in the dataclass
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        return cls(**filtered_data)

    def __str__(self) -> str:
        """String representation"""
        return f"{self.__class__.__name__}(id={self.identifier})"

    def __repr__(self) -> str:
        """Detailed representation"""
        return f"{self.__class__.__name__}(identifier='{self.identifier}', type='{self.record_type}')"


@dataclass
class DataValidationError(Exception):
    """Exception raised when data validation fails"""

    message: str
    field: Optional[str] = None
    value: Any = None

    def __str__(self) -> str:
        if self.field:
            return f"Validation error in field '{self.field}': {self.message}"
        return f"Validation error: {self.message}"


def validate_required_field(value: Any, field_name: str) -> Any:
    """
    Validate that a required field has a value

    Args:
        value: Field value to validate
        field_name: Name of the field

    Returns:
        The validated value

    Raises:
        DataValidationError: If value is None or empty
    """
    if value is None:
        raise DataValidationError(
            f"Field '{field_name}' is required but was None", field_name, value
        )

    if isinstance(value, str) and not value.strip():
        raise DataValidationError(
            f"Field '{field_name}' is required but was empty", field_name, value
        )

    return value


def validate_enum_field(value: Any, field_name: str, allowed_values: list) -> Any:
    """
    Validate that a field value is in the allowed list

    Args:
        value: Field value to validate
        field_name: Name of the field
        allowed_values: List of allowed values

    Returns:
        The validated value

    Raises:
        DataValidationError: If value is not in allowed values
    """
    if value not in allowed_values:
        raise DataValidationError(
            f"Field '{field_name}' must be one of {allowed_values}, got '{value}'",
            field_name,
            value,
        )

    return value


def validate_congress_number(congress: Any) -> int:
    """
    Validate and normalize congress number

    Args:
        congress: Congress number to validate

    Returns:
        Validated congress number as integer

    Raises:
        DataValidationError: If congress number is invalid
    """
    if not isinstance(congress, (int, str)):
        raise DataValidationError(
            "Congress number must be an integer or string", "congress", congress
        )

    try:
        congress_int = int(congress)
    except ValueError:
        raise DataValidationError(
            f"Congress number must be numeric, got '{congress}'", "congress", congress
        )

    if congress_int < 1 or congress_int > 200:  # Reasonable bounds
        raise DataValidationError(
            f"Congress number {congress_int} is out of valid range (1-200)",
            "congress",
            congress,
        )

    return congress_int


def normalize_party_code(party: Optional[str]) -> Optional[str]:
    """
    Normalize party codes to standard format

    Args:
        party: Party code to normalize

    Returns:
        Normalized party code (D, R, I, or None)
    """
    if not party:
        return None

    party_upper = party.upper().strip()

    # Map common variations
    party_map = {
        "DEMOCRATIC": "D",
        "DEMOCRAT": "D",
        "DEM": "D",
        "REPUBLICAN": "R",
        "REP": "R",
        "INDEPENDENT": "I",
        "IND": "I",
        "LIBERTARIAN": "L",
        "GREEN": "G",
    }

    return party_map.get(party_upper, party_upper)


def normalize_chamber(chamber: Optional[str]) -> Optional[str]:
    """
    Normalize chamber names to standard format

    Args:
        chamber: Chamber name to normalize

    Returns:
        Normalized chamber name ('house' or 'senate')
    """
    if not chamber:
        return None

    chamber_lower = chamber.lower().strip()

    if chamber_lower in ["house", "h", "house of representatives"]:
        return "house"
    elif chamber_lower in ["senate", "s"]:
        return "senate"

    return chamber_lower
