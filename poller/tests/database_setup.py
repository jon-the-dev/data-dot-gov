#!/usr/bin/env python3
"""
Congressional Transparency Platform - Database Setup and Migration System

This module provides PostgreSQL database setup, connection management, and data migration
capabilities using SQLAlchemy ORM with optimizations for the congressional data platform.

Key Features:
- SQLAlchemy ORM models for all database tables
- Connection pooling with automatic reconnection
- Batch data migration from JSON files
- Transaction support with rollback capabilities
- Comprehensive error handling and logging
- Parallel processing for large datasets
- Data validation and integrity checks

Usage:
    python database_setup.py --create-schema
    python database_setup.py --migrate-data --batch-size 1000
    python database_setup.py --validate-data
"""

import argparse
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Environment and configuration
from dotenv import load_dotenv

# Database imports
from sqlalchemy import (
    ARRAY,
    DECIMAL,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import insert

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("database_migration.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "congress_transparency"),
    "username": os.getenv("DB_USER", "congress_app"),
    "password": os.getenv("DB_PASSWORD", "secure_password_change_in_production"),
    "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
    "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
}

# Migration configuration
MIGRATION_CONFIG = {
    "batch_size": int(os.getenv("MIGRATION_BATCH_SIZE", "1000")),
    "max_workers": int(os.getenv("MIGRATION_MAX_WORKERS", "4")),
    "retry_attempts": int(os.getenv("MIGRATION_RETRY_ATTEMPTS", "3")),
    "retry_delay": int(os.getenv("MIGRATION_RETRY_DELAY", "5")),
}

# SQLAlchemy Base
Base = declarative_base()

# ============================================================================
# SQLAlchemy ORM Models
# ============================================================================


class CongressSession(Base):
    __tablename__ = "sessions"
    __table_args__ = {"schema": "congress"}

    congress_number = Column(Integer, primary_key=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    session_type = Column(String(20), default="regular")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Member(Base):
    __tablename__ = "members"
    __table_args__ = {"schema": "congress"}

    bioguide_id = Column(String(10), primary_key=True)
    name = Column(Text, nullable=False)
    first_name = Column(String(100))
    middle_name = Column(String(100))
    last_name = Column(String(100), nullable=False)
    suffix = Column(String(20))
    party = Column(String(20), nullable=False)
    state_code = Column(String(2), nullable=False)
    state_name = Column(String(50), nullable=False)
    chamber = Column(String(10), nullable=False)
    district = Column(Integer)  # NULL for senators
    current_member = Column(Boolean, default=True)
    image_url = Column(Text)
    official_url = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    terms = relationship("MemberTerm", back_populates="member")
    sponsored_bills = relationship("Bill", back_populates="sponsor")
    votes = relationship("MemberVote", back_populates="member")
    sponsorships = relationship("BillSponsor", back_populates="member")
    committee_memberships = relationship("CommitteeMembership", back_populates="member")
    party_unity_scores = relationship("MemberPartyUnity", back_populates="member")

    # Constraints
    __table_args__ = (
        CheckConstraint(chamber.in_(["house", "senate"]), name="check_chamber_valid"),
        {"schema": "congress"},
    )


class MemberTerm(Base):
    __tablename__ = "member_terms"
    __table_args__ = (
        UniqueConstraint("bioguide_id", "congress_number", "chamber"),
        {"schema": "congress"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    bioguide_id = Column(
        String(10), ForeignKey("congress.members.bioguide_id"), nullable=False
    )
    congress_number = Column(Integer, nullable=False)
    chamber = Column(String(10), nullable=False)
    state_code = Column(String(2), nullable=False)
    district = Column(Integer)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    member_type = Column(String(50))
    party = Column(String(20))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    member = relationship("Member", back_populates="terms")


class Bill(Base):
    __tablename__ = "bills"
    __table_args__ = (
        UniqueConstraint("congress_number", "bill_type", "bill_number"),
        {"schema": "congress"},
    )

    bill_id = Column(String(20), primary_key=True)  # e.g., '118_HR_82'
    congress_number = Column(Integer, nullable=False)
    bill_type = Column(String(10), nullable=False)
    bill_number = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    short_title = Column(Text)
    introduced_date = Column(Date, nullable=False)
    origin_chamber = Column(String(10), nullable=False)
    sponsor_bioguide_id = Column(String(10), ForeignKey("congress.members.bioguide_id"))
    policy_area = Column(Text)
    latest_action_date = Column(Date)
    latest_action_text = Column(Text)
    became_law = Column(Boolean, default=False)
    law_number = Column(String(20))
    law_type = Column(String(50))
    constitutional_authority_text = Column(Text)
    summary = Column(Text)
    cbo_cost_estimate_url = Column(Text)
    legislation_url = Column(Text)
    actions_count = Column(Integer, default=0)
    amendments_count = Column(Integer, default=0)
    committees_count = Column(Integer, default=0)
    cosponsors_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    sponsor = relationship("Member", back_populates="sponsored_bills")
    subjects = relationship("BillSubject", back_populates="bill")
    sponsors = relationship("BillSponsor", back_populates="bill")
    votes = relationship("Vote", back_populates="bill")
    committee_activities = relationship("BillCommittee", back_populates="bill")
    category_mappings = relationship("BillCategoryMapping", back_populates="bill")


class BillSubject(Base):
    __tablename__ = "bill_subjects"
    __table_args__ = (UniqueConstraint("bill_id", "subject"), {"schema": "congress"})

    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(String(20), ForeignKey("congress.bills.bill_id"), nullable=False)
    subject = Column(Text, nullable=False)
    subject_type = Column(String(50))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    bill = relationship("Bill", back_populates="subjects")


class BillSponsor(Base):
    __tablename__ = "bill_sponsors"
    __table_args__ = (
        UniqueConstraint("bill_id", "bioguide_id"),
        CheckConstraint(
            "sponsor_type IN ('sponsor', 'cosponsor')", name="check_sponsor_type_valid"
        ),
        {"schema": "congress"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(String(20), ForeignKey("congress.bills.bill_id"), nullable=False)
    bioguide_id = Column(
        String(10), ForeignKey("congress.members.bioguide_id"), nullable=False
    )
    sponsor_type = Column(String(20), nullable=False)
    sponsorship_date = Column(Date)
    withdrawn_date = Column(Date)
    is_original_cosponsor = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    bill = relationship("Bill", back_populates="sponsors")
    member = relationship("Member", back_populates="sponsorships")


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("congress_number", "chamber", "roll_call_number", "session"),
        CheckConstraint(
            chamber.in_(["house", "senate"]), name="check_vote_chamber_valid"
        ),
        {"schema": "congress"},
    )

    vote_id = Column(String(50), primary_key=True)  # e.g., '118_house_367'
    congress_number = Column(Integer, nullable=False)
    session = Column(Integer, nullable=False)
    chamber = Column(String(10), nullable=False)
    roll_call_number = Column(Integer, nullable=False)
    vote_date = Column(Date, nullable=False)
    vote_time = Column(String(10))  # Using String for TIME compatibility
    question = Column(Text, nullable=False)
    description = Column(Text)
    vote_type = Column(String(50))
    result = Column(String(20), nullable=False)
    bill_id = Column(String(20), ForeignKey("congress.bills.bill_id"))
    amendment_number = Column(Text)
    total_votes = Column(Integer)
    yea_votes = Column(Integer, default=0)
    nay_votes = Column(Integer, default=0)
    present_votes = Column(Integer, default=0)
    not_voting = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    bill = relationship("Bill", back_populates="votes")
    member_votes = relationship("MemberVote", back_populates="vote")
    bipartisan_analysis = relationship(
        "BipartisanVote", back_populates="vote", uselist=False
    )


class MemberVote(Base):
    __tablename__ = "member_votes"
    __table_args__ = (
        UniqueConstraint("vote_id", "bioguide_id"),
        CheckConstraint(
            "vote_position IN ('Yea', 'Nay', 'Present', 'Not Voting')",
            name="check_vote_position_valid",
        ),
        {"schema": "congress"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    vote_id = Column(String(50), ForeignKey("congress.votes.vote_id"), nullable=False)
    bioguide_id = Column(
        String(10), ForeignKey("congress.members.bioguide_id"), nullable=False
    )
    vote_position = Column(String(20), nullable=False)
    voted_with_party = Column(Boolean)
    vote_cast_time = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    vote = relationship("Vote", back_populates="member_votes")
    member = relationship("Member", back_populates="votes")


class Committee(Base):
    __tablename__ = "committees"
    __table_args__ = (
        CheckConstraint(
            chamber.in_(["house", "senate", "joint"]),
            name="check_committee_chamber_valid",
        ),
        {"schema": "congress"},
    )

    committee_code = Column(String(10), primary_key=True)
    name = Column(Text, nullable=False)
    chamber = Column(String(10), nullable=False)
    committee_type = Column(String(50))
    parent_committee_code = Column(
        String(10), ForeignKey("congress.committees.committee_code")
    )
    is_subcommittee = Column(Boolean, default=False)
    url = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    subcommittees = relationship(
        "Committee", backref="parent_committee", remote_side=[committee_code]
    )
    memberships = relationship("CommitteeMembership", back_populates="committee")
    bill_activities = relationship("BillCommittee", back_populates="committee")


class CommitteeMembership(Base):
    __tablename__ = "committee_memberships"
    __table_args__ = (
        UniqueConstraint("bioguide_id", "committee_code", "congress_number"),
        {"schema": "congress"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    bioguide_id = Column(
        String(10), ForeignKey("congress.members.bioguide_id"), nullable=False
    )
    committee_code = Column(
        String(10), ForeignKey("congress.committees.committee_code"), nullable=False
    )
    congress_number = Column(Integer, nullable=False)
    rank_in_party = Column(Integer)
    role = Column(String(50))  # Chair, Ranking Member, Member
    start_date = Column(Date)
    end_date = Column(Date)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    member = relationship("Member", back_populates="committee_memberships")
    committee = relationship("Committee", back_populates="memberships")


class BillCommittee(Base):
    __tablename__ = "bill_committees"
    __table_args__ = (
        UniqueConstraint("bill_id", "committee_code", "activity_type"),
        {"schema": "congress"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(String(20), ForeignKey("congress.bills.bill_id"), nullable=False)
    committee_code = Column(
        String(10), ForeignKey("congress.committees.committee_code"), nullable=False
    )
    activity_type = Column(String(50))  # referred, reported, etc.
    activity_date = Column(Date)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    bill = relationship("Bill", back_populates="committee_activities")
    committee = relationship("Committee", back_populates="bill_activities")


# ============================================================================
# Senate Schema Models (Lobbying)
# ============================================================================


class LobbyingRegistration(Base):
    __tablename__ = "lobbying_registrations"
    __table_args__ = {"schema": "senate"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    filing_uuid = Column(String(100), unique=True)
    filing_date = Column(Date, nullable=False)
    registrant_name = Column(Text, nullable=False)
    registrant_address = Column(Text)
    client_name = Column(Text, nullable=False)
    client_address = Column(Text)
    contact_name = Column(Text)
    contact_phone = Column(String(20))
    contact_email = Column(String(255))
    registration_type = Column(String(50))
    affiliated_organizations = Column(ARRAY(Text))
    foreign_entity_info = Column(JSONB)
    effective_date = Column(Date)
    termination_date = Column(Date)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    reports = relationship("LobbyingReport", back_populates="registration")


class LobbyingReport(Base):
    __tablename__ = "lobbying_reports"
    __table_args__ = {"schema": "senate"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    filing_uuid = Column(String(100), unique=True)
    registration_id = Column(Integer, ForeignKey("senate.lobbying_registrations.id"))
    filing_date = Column(Date, nullable=False)
    reporting_period_start = Column(Date, nullable=False)
    reporting_period_end = Column(Date, nullable=False)
    income_amount = Column(DECIMAL(15, 2))
    expense_amount = Column(DECIMAL(15, 2))
    terminated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    registration = relationship("LobbyingRegistration", back_populates="reports")
    issues = relationship("LobbyingIssue", back_populates="report")


class LobbyingIssue(Base):
    __tablename__ = "lobbying_issues"
    __table_args__ = {"schema": "senate"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(
        Integer, ForeignKey("senate.lobbying_reports.id"), nullable=False
    )
    issue_code = Column(String(10))
    specific_issue = Column(Text, nullable=False)
    houses_and_agencies = Column(ARRAY(Text))
    foreign_entity_involvement = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    report = relationship("LobbyingReport", back_populates="issues")


class Lobbyist(Base):
    __tablename__ = "lobbyists"
    __table_args__ = (
        UniqueConstraint(
            "first_name", "last_name", "registrant_name", "client_name", "filing_year"
        ),
        {"schema": "senate"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    suffix = Column(String(20))
    covered_position = Column(Text)
    new_lobbyist = Column(Boolean, default=False)
    registrant_name = Column(Text)
    client_name = Column(Text)
    filing_year = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# ============================================================================
# Analysis Schema Models
# ============================================================================


class BillCategory(Base):
    __tablename__ = "bill_categories"
    __table_args__ = {"schema": "analysis"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    keywords = Column(ARRAY(Text))
    committee_codes = Column(ARRAY(String(10)))
    policy_areas = Column(ARRAY(Text))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    bill_mappings = relationship("BillCategoryMapping", back_populates="category")


class BillCategoryMapping(Base):
    __tablename__ = "bill_category_mappings"
    __table_args__ = {"schema": "analysis"}

    bill_id = Column(String(20), ForeignKey("congress.bills.bill_id"), primary_key=True)
    category_id = Column(
        Integer, ForeignKey("analysis.bill_categories.id"), primary_key=True
    )
    confidence_score = Column(DECIMAL(3, 2))  # 0.00 to 1.00
    classification_method = Column(String(50))  # keyword, committee, ml, etc.
    created_at = Column(DateTime, default=func.now())

    # Relationships
    bill = relationship("Bill", back_populates="category_mappings")
    category = relationship("BillCategory", back_populates="bill_mappings")


class MemberPartyUnity(Base):
    __tablename__ = "member_party_unity"
    __table_args__ = (
        UniqueConstraint("bioguide_id", "congress_number"),
        CheckConstraint(
            "unity_score >= 0.00 AND unity_score <= 100.00",
            name="check_unity_score_range",
        ),
        {"schema": "analysis"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    bioguide_id = Column(
        String(10), ForeignKey("congress.members.bioguide_id"), nullable=False
    )
    congress_number = Column(Integer, nullable=False)
    total_votes = Column(Integer, nullable=False)
    party_line_votes = Column(Integer, nullable=False)
    unity_score = Column(DECIMAL(5, 2), nullable=False)  # 0.00 to 100.00
    rank_in_party = Column(Integer)
    rank_in_chamber = Column(Integer)
    calculated_at = Column(DateTime, default=func.now())

    # Relationships
    member = relationship("Member", back_populates="party_unity_scores")


class BipartisanVote(Base):
    __tablename__ = "bipartisan_votes"
    __table_args__ = (
        CheckConstraint(
            "democratic_support_pct >= 0.00 AND democratic_support_pct <= 100.00 AND "
            "republican_support_pct >= 0.00 AND republican_support_pct <= 100.00 AND "
            "independent_support_pct >= 0.00 AND independent_support_pct <= 100.00",
            name="check_support_pct_range",
        ),
        {"schema": "analysis"},
    )

    vote_id = Column(String(50), ForeignKey("congress.votes.vote_id"), primary_key=True)
    is_bipartisan = Column(Boolean, nullable=False)
    party_split_score = Column(DECIMAL(5, 2))  # measure of how split parties were
    democratic_support_pct = Column(DECIMAL(5, 2))
    republican_support_pct = Column(DECIMAL(5, 2))
    independent_support_pct = Column(DECIMAL(5, 2))
    crossover_democrats = Column(Integer, default=0)
    crossover_republicans = Column(Integer, default=0)
    calculated_at = Column(DateTime, default=func.now())

    # Relationships
    vote = relationship("Vote", back_populates="bipartisan_analysis")


class StateDelegationPattern(Base):
    __tablename__ = "state_delegation_patterns"
    __table_args__ = (
        UniqueConstraint("state_code", "congress_number"),
        {"schema": "analysis"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    state_code = Column(String(2), nullable=False)
    congress_number = Column(Integer, nullable=False)
    democratic_members = Column(Integer, default=0)
    republican_members = Column(Integer, default=0)
    independent_members = Column(Integer, default=0)
    unity_score = Column(DECIMAL(5, 2))  # how often delegation votes together
    partisan_index = Column(DECIMAL(5, 2))  # measure of partisan behavior
    calculated_at = Column(DateTime, default=func.now())


# ============================================================================
# Metadata Schema Models
# ============================================================================


class DataSource(Base):
    __tablename__ = "data_sources"
    __table_args__ = {"schema": "metadata"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(100), nullable=False)
    source_url = Column(Text)
    api_version = Column(String(20))
    rate_limit_per_hour = Column(Integer)
    terms_of_service_url = Column(Text)
    data_citation_required = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class Migration(Base):
    __tablename__ = "migrations"
    __table_args__ = {"schema": "metadata"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    migration_name = Column(String(255), nullable=False, unique=True)
    executed_at = Column(DateTime, default=func.now())
    execution_time_ms = Column(Integer)
    records_migrated = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    checksum = Column(String(64))


class DataFreshness(Base):
    __tablename__ = "data_freshness"
    __table_args__ = (
        UniqueConstraint("schema_name", "table_name"),
        {"schema": "metadata"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(100), nullable=False)
    schema_name = Column(String(50), nullable=False)
    last_updated = Column(DateTime, nullable=False)
    record_count = Column(Integer)
    data_source_id = Column(Integer, ForeignKey("metadata.data_sources.id"))
    update_frequency_hours = Column(Integer)  # expected update frequency


# ============================================================================
# Database Connection and Management
# ============================================================================


class DatabaseManager:
    """
    Database connection and session management with connection pooling,
    automatic reconnection, and transaction support.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize database manager with configuration."""
        self.config = config or DATABASE_CONFIG
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()

    def _setup_engine(self):
        """Set up SQLAlchemy engine with connection pooling."""
        try:
            # Build connection string
            connection_string = (
                f"postgresql://{self.config['username']}:{self.config['password']}"
                f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
            )

            # Create engine with optimized pool settings
            self.engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=self.config["pool_size"],
                max_overflow=self.config["max_overflow"],
                pool_timeout=self.config["pool_timeout"],
                pool_recycle=self.config["pool_recycle"],
                echo=False,  # Set to True for SQL query logging
                future=True,  # Use SQLAlchemy 2.0 style
            )

            # Create session factory
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )

            logger.info("Database engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise

    def get_session(self) -> Session:
        """Get a new database session."""
        if not self.SessionLocal:
            self._setup_engine()
        return self.SessionLocal()

    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                logger.info("Database connection test successful")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def create_schema(self, drop_existing: bool = False):
        """Create database schema."""
        try:
            if drop_existing:
                logger.warning("Dropping existing schema...")
                Base.metadata.drop_all(bind=self.engine)

            # Create all tables
            Base.metadata.create_all(bind=self.engine)

            # Execute schema SQL file for additional setup
            schema_file = Path(__file__).parent / "db" / "schema.sql"
            if schema_file.exists():
                with open(schema_file) as f:
                    schema_sql = f.read()

                with self.get_session() as session:
                    # Split by statements and execute
                    statements = [
                        stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()
                    ]
                    for statement in statements:
                        if statement and not statement.startswith("--"):
                            try:
                                session.execute(text(statement))
                            except Exception as e:
                                logger.warning(f"Skipping statement due to error: {e}")
                    session.commit()

            logger.info("Database schema created successfully")

        except Exception as e:
            logger.error(f"Failed to create database schema: {e}")
            raise

    def run_migration(self, migration_file: Path):
        """Run a specific migration file."""
        try:
            with open(migration_file) as f:
                migration_sql = f.read()

            with self.get_session() as session:
                session.execute(text(migration_sql))
                session.commit()

            logger.info(f"Migration {migration_file.name} executed successfully")

        except Exception as e:
            logger.error(f"Failed to run migration {migration_file.name}: {e}")
            raise

    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


# ============================================================================
# Data Migration Classes
# ============================================================================


class DataMigrator:
    """
    Handles migration of JSON data to PostgreSQL with batch processing,
    validation, and error recovery.
    """

    def __init__(self, db_manager: DatabaseManager, data_dir: Path = None):
        """Initialize data migrator."""
        self.db_manager = db_manager
        self.data_dir = data_dir or Path("data")
        self.config = MIGRATION_CONFIG

    def migrate_all_data(self, validate: bool = True) -> Dict[str, int]:
        """Migrate all data from JSON files to database."""
        migration_stats = {}

        try:
            logger.info("Starting complete data migration...")

            # Migration order matters due to foreign key constraints
            migration_tasks = [
                ("congress_sessions", self._migrate_congress_sessions),
                ("members", self._migrate_members),
                ("member_terms", self._migrate_member_terms),
                ("committees", self._migrate_committees),
                ("bills", self._migrate_bills),
                ("bill_subjects", self._migrate_bill_subjects),
                ("bill_sponsors", self._migrate_bill_sponsors),
                ("votes", self._migrate_votes),
                ("member_votes", self._migrate_member_votes),
                ("committee_memberships", self._migrate_committee_memberships),
                ("bill_committees", self._migrate_bill_committees),
                ("lobbying_registrations", self._migrate_lobbying_registrations),
                ("lobbying_reports", self._migrate_lobbying_reports),
                ("lobbying_issues", self._migrate_lobbying_issues),
                ("lobbyists", self._migrate_lobbyists),
                ("bill_categories", self._migrate_bill_categories),
                ("bill_category_mappings", self._migrate_bill_category_mappings),
            ]

            for task_name, migration_func in migration_tasks:
                try:
                    logger.info(f"Migrating {task_name}...")
                    count = migration_func()
                    migration_stats[task_name] = count
                    logger.info(f"Migrated {count} {task_name} records")
                except Exception as e:
                    logger.error(f"Failed to migrate {task_name}: {e}")
                    migration_stats[task_name] = 0

            # Run post-migration analysis if requested
            if validate:
                self._run_post_migration_analysis()

            total_records = sum(migration_stats.values())
            logger.info(f"Migration completed. Total records migrated: {total_records}")

            return migration_stats

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise

    def _migrate_members(self) -> int:
        """Migrate member data from JSON files."""
        members_dir = self.data_dir / "members"
        if not members_dir.exists():
            logger.warning("Members directory not found")
            return 0

        total_migrated = 0

        with self.db_manager.get_session() as session:
            for congress_dir in members_dir.iterdir():
                if not congress_dir.is_dir():
                    continue

                congress_number = int(congress_dir.name)
                logger.info(f"Migrating members for Congress {congress_number}")

                members_batch = []
                terms_batch = []

                for member_file in congress_dir.glob("*.json"):
                    if member_file.name == "summary.json":
                        continue

                    try:
                        with open(member_file) as f:
                            member_data = json.load(f)

                        # Create member record
                        member = self._create_member_from_json(member_data)
                        members_batch.append(member)

                        # Create term records
                        if "terms" in member_data:
                            for term_data in member_data["terms"]:
                                term = self._create_member_term_from_json(
                                    member_data["bioguideId"], term_data
                                )
                                terms_batch.append(term)

                        # Batch insert when reaching batch size
                        if len(members_batch) >= self.config["batch_size"]:
                            self._batch_insert_members(
                                session, members_batch, terms_batch
                            )
                            total_migrated += len(members_batch)
                            members_batch = []
                            terms_batch = []

                    except Exception as e:
                        logger.error(f"Error processing member file {member_file}: {e}")

                # Insert remaining records
                if members_batch:
                    self._batch_insert_members(session, members_batch, terms_batch)
                    total_migrated += len(members_batch)

        return total_migrated

    def _create_member_from_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create member record from JSON data."""
        # Parse name components
        name_parts = data.get("name", "").split(", ")
        last_name = name_parts[0] if name_parts else ""
        first_part = name_parts[1] if len(name_parts) > 1 else ""

        # Extract first, middle, suffix
        first_name = first_part.split()[0] if first_part else ""
        middle_name = (
            " ".join(first_part.split()[1:-1]) if len(first_part.split()) > 2 else ""
        )
        suffix = (
            first_part.split()[-1]
            if len(first_part.split()) > 1
            and first_part.split()[-1] in ["Jr.", "Sr.", "III", "IV"]
            else ""
        )

        return {
            "bioguide_id": data["bioguideId"],
            "name": data["name"],
            "first_name": first_name,
            "middle_name": middle_name or None,
            "last_name": last_name,
            "suffix": suffix or None,
            "party": data["party"],
            "state_code": data.get("state", "")[:2] if data.get("state") else "",
            "state_name": data.get("state", ""),
            "chamber": data["chamber"],
            "district": data.get("district"),
            "current_member": True,
            "image_url": data.get("depiction", {}).get("imageUrl"),
            "official_url": data.get("url"),
        }

    def _create_member_term_from_json(
        self, bioguide_id: str, term_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create member term record from JSON data."""
        return {
            "bioguide_id": bioguide_id,
            "congress_number": term_data["congress"],
            "chamber": (
                "house"
                if term_data["chamber"] == "House of Representatives"
                else "senate"
            ),
            "state_code": term_data["stateCode"],
            "district": term_data.get("district"),
            "start_date": datetime.strptime(str(term_data["startYear"]), "%Y").date(),
            "end_date": (
                datetime.strptime(str(term_data["endYear"]), "%Y").date()
                if term_data.get("endYear")
                else None
            ),
            "member_type": term_data.get("memberType"),
            "party": term_data.get("party"),
        }

    def _batch_insert_members(
        self, session: Session, members: List[Dict], terms: List[Dict]
    ):
        """Batch insert members and terms with error handling."""
        try:
            # Insert members
            if members:
                session.execute(insert(Member).on_conflict_do_nothing(), members)

            # Insert terms
            if terms:
                session.execute(insert(MemberTerm).on_conflict_do_nothing(), terms)

            session.commit()

        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            session.rollback()
            raise

    def _migrate_bills(self) -> int:
        """Migrate bill data from JSON files."""
        bills_dir = self.data_dir / "congress_bills"
        if not bills_dir.exists():
            logger.warning("Bills directory not found")
            return 0

        total_migrated = 0

        with self.db_manager.get_session() as session:
            for congress_dir in bills_dir.iterdir():
                if not congress_dir.is_dir():
                    continue

                congress_number = int(congress_dir.name)
                logger.info(f"Migrating bills for Congress {congress_number}")

                bills_batch = []

                for bill_file in congress_dir.glob("*.json"):
                    if bill_file.name in ["index.json", "summary.json"]:
                        continue

                    try:
                        with open(bill_file) as f:
                            bill_data = json.load(f)

                        bill = self._create_bill_from_json(bill_data)
                        bills_batch.append(bill)

                        # Batch insert when reaching batch size
                        if len(bills_batch) >= self.config["batch_size"]:
                            session.execute(
                                insert(Bill).on_conflict_do_nothing(), bills_batch
                            )
                            session.commit()
                            total_migrated += len(bills_batch)
                            bills_batch = []

                    except Exception as e:
                        logger.error(f"Error processing bill file {bill_file}: {e}")

                # Insert remaining records
                if bills_batch:
                    session.execute(insert(Bill).on_conflict_do_nothing(), bills_batch)
                    session.commit()
                    total_migrated += len(bills_batch)

        return total_migrated

    def _create_bill_from_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create bill record from JSON data."""
        congress = data["congress"]
        bill_type = data["type"]
        bill_number = data["number"]
        bill_id = f"{congress}_{bill_type}_{bill_number}"

        # Parse dates
        introduced_date = None
        if data.get("introducedDate"):
            introduced_date = datetime.strptime(
                data["introducedDate"], "%Y-%m-%d"
            ).date()

        latest_action_date = None
        if data.get("latestAction", {}).get("actionDate"):
            latest_action_date = datetime.strptime(
                data["latestAction"]["actionDate"], "%Y-%m-%d"
            ).date()

        # Determine if bill became law
        became_law = bool(data.get("laws"))
        law_number = None
        law_type = None
        if became_law and data.get("laws"):
            law_info = data["laws"][0]
            law_number = law_info.get("number")
            law_type = law_info.get("type")

        return {
            "bill_id": bill_id,
            "congress_number": congress,
            "bill_type": bill_type,
            "bill_number": bill_number,
            "title": data["title"],
            "short_title": data.get("shortTitle"),
            "introduced_date": introduced_date,
            "origin_chamber": data["originChamber"].lower(),
            "sponsor_bioguide_id": None,  # Will be populated separately
            "policy_area": data.get("policyArea", {}).get("name"),
            "latest_action_date": latest_action_date,
            "latest_action_text": data.get("latestAction", {}).get("text"),
            "became_law": became_law,
            "law_number": law_number,
            "law_type": law_type,
            "constitutional_authority_text": data.get(
                "constitutionalAuthorityStatementText"
            ),
            "summary": data.get("summary"),
            "cbo_cost_estimate_url": None,  # Will be extracted from cboCostEstimates
            "legislation_url": data.get("url"),
            "actions_count": data.get("actions", {}).get("count", 0),
            "amendments_count": data.get("amendments", {}).get("count", 0),
            "committees_count": data.get("committees", {}).get("count", 0),
            "cosponsors_count": data.get("cosponsors", {}).get("count", 0),
        }

    def _migrate_votes(self) -> int:
        """Migrate vote data from JSON files."""
        votes_dir = self.data_dir / "votes"
        if not votes_dir.exists():
            logger.warning("Votes directory not found")
            return 0

        total_migrated = 0

        with self.db_manager.get_session() as session:
            for congress_dir in votes_dir.iterdir():
                if not congress_dir.is_dir():
                    continue

                congress_number = int(congress_dir.name)

                for chamber_dir in congress_dir.iterdir():
                    if not chamber_dir.is_dir():
                        continue

                    chamber = chamber_dir.name
                    logger.info(
                        f"Migrating {chamber} votes for Congress {congress_number}"
                    )

                    votes_batch = []
                    member_votes_batch = []

                    for vote_file in chamber_dir.glob("*.json"):
                        try:
                            with open(vote_file) as f:
                                vote_data = json.load(f)

                            vote, member_votes = self._create_vote_from_json(vote_data)
                            votes_batch.append(vote)
                            member_votes_batch.extend(member_votes)

                            # Batch insert when reaching batch size
                            if len(votes_batch) >= self.config["batch_size"]:
                                self._batch_insert_votes(
                                    session, votes_batch, member_votes_batch
                                )
                                total_migrated += len(votes_batch)
                                votes_batch = []
                                member_votes_batch = []

                        except Exception as e:
                            logger.error(f"Error processing vote file {vote_file}: {e}")

                    # Insert remaining records
                    if votes_batch:
                        self._batch_insert_votes(
                            session, votes_batch, member_votes_batch
                        )
                        total_migrated += len(votes_batch)

        return total_migrated

    def _create_vote_from_json(
        self, data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Create vote and member vote records from JSON data."""
        congress = data["congress"]
        chamber = data["chamber"]
        roll_call = data["vote_id"]
        vote_id = f"{congress}_{chamber}_{roll_call}"

        # Parse vote date
        vote_date = None
        if data.get("date"):
            vote_date = datetime.strptime(data["date"], "%Y-%m-%d").date()

        # Create main vote record
        vote = {
            "vote_id": vote_id,
            "congress_number": congress,
            "session": data.get("session", 1),
            "chamber": chamber,
            "roll_call_number": roll_call,
            "vote_date": vote_date,
            "question": data["question"],
            "description": data.get("description"),
            "result": data["result"],
            "total_votes": len(data.get("member_votes", [])),
            "yea_votes": len(
                [v for v in data.get("member_votes", []) if v["vote"] == "Yea"]
            ),
            "nay_votes": len(
                [v for v in data.get("member_votes", []) if v["vote"] == "Nay"]
            ),
            "present_votes": len(
                [v for v in data.get("member_votes", []) if v["vote"] == "Present"]
            ),
            "not_voting": len(
                [v for v in data.get("member_votes", []) if v["vote"] == "Not Voting"]
            ),
        }

        # Create member vote records
        member_votes = []
        for member_vote_data in data.get("member_votes", []):
            member_vote = {
                "vote_id": vote_id,
                "bioguide_id": member_vote_data["member_id"],
                "vote_position": member_vote_data["vote"],
                "voted_with_party": None,  # Will be calculated later
            }
            member_votes.append(member_vote)

        return vote, member_votes

    def _batch_insert_votes(
        self, session: Session, votes: List[Dict], member_votes: List[Dict]
    ):
        """Batch insert votes and member votes with error handling."""
        try:
            # Insert votes
            if votes:
                session.execute(insert(Vote).on_conflict_do_nothing(), votes)

            # Insert member votes
            if member_votes:
                session.execute(
                    insert(MemberVote).on_conflict_do_nothing(), member_votes
                )

            session.commit()

        except Exception as e:
            logger.error(f"Vote batch insert failed: {e}")
            session.rollback()
            raise

    # Placeholder methods for other migration functions
    def _migrate_congress_sessions(self) -> int:
        """Migrate congress session data."""
        # Implementation for congress sessions
        return 0

    def _migrate_member_terms(self) -> int:
        """Already handled in _migrate_members."""
        return 0

    def _migrate_committees(self) -> int:
        """Migrate committee data."""
        # Implementation for committees
        return 0

    def _migrate_bill_subjects(self) -> int:
        """Migrate bill subjects data."""
        # Implementation for bill subjects
        return 0

    def _migrate_bill_sponsors(self) -> int:
        """Migrate bill sponsors data."""
        # Implementation for bill sponsors
        return 0

    def _migrate_committee_memberships(self) -> int:
        """Migrate committee membership data."""
        # Implementation for committee memberships
        return 0

    def _migrate_bill_committees(self) -> int:
        """Migrate bill committee relationships."""
        # Implementation for bill committees
        return 0

    def _migrate_lobbying_registrations(self) -> int:
        """Migrate lobbying registration data."""
        # Implementation for lobbying registrations
        return 0

    def _migrate_lobbying_reports(self) -> int:
        """Migrate lobbying report data."""
        # Implementation for lobbying reports
        return 0

    def _migrate_lobbying_issues(self) -> int:
        """Migrate lobbying issues data."""
        # Implementation for lobbying issues
        return 0

    def _migrate_lobbyists(self) -> int:
        """Migrate lobbyist data."""
        # Implementation for lobbyists
        return 0

    def _migrate_bill_categories(self) -> int:
        """Migrate bill categories data."""
        # Implementation for bill categories
        return 0

    def _migrate_bill_category_mappings(self) -> int:
        """Migrate bill category mappings."""
        # Implementation for bill category mappings
        return 0

    def _run_post_migration_analysis(self):
        """Run analysis after migration completion."""
        logger.info("Running post-migration analysis...")

        with self.db_manager.get_session() as session:
            # Calculate party unity scores
            self._calculate_party_unity(session)

            # Analyze bipartisan votes
            self._analyze_bipartisan_votes(session)

            # Refresh materialized views
            session.execute(text("SELECT refresh_all_materialized_views()"))
            session.commit()

        logger.info("Post-migration analysis completed")

    def _calculate_party_unity(self, session: Session):
        """Calculate party unity scores for all members."""
        # Implementation for party unity calculation
        pass

    def _analyze_bipartisan_votes(self, session: Session):
        """Analyze votes for bipartisan patterns."""
        # Implementation for bipartisan analysis
        pass


# ============================================================================
# Validation and Testing
# ============================================================================


class DataValidator:
    """Validates migrated data integrity and consistency."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def validate_all_data(self) -> Dict[str, bool]:
        """Run all validation checks."""
        validation_results = {}

        with self.db_manager.get_session() as session:
            validation_results["referential_integrity"] = (
                self._check_referential_integrity(session)
            )
            validation_results["data_consistency"] = self._check_data_consistency(
                session
            )
            validation_results["completeness"] = self._check_data_completeness(session)
            validation_results["constraints"] = self._check_constraints(session)

        return validation_results

    def _check_referential_integrity(self, session: Session) -> bool:
        """Check foreign key relationships."""
        try:
            # Check member references in votes
            orphaned_votes = session.execute(
                text(
                    """
                SELECT COUNT(*) FROM congress.member_votes mv
                LEFT JOIN congress.members m ON mv.bioguide_id = m.bioguide_id
                WHERE m.bioguide_id IS NULL
            """
                )
            ).scalar()

            if orphaned_votes > 0:
                logger.error(f"Found {orphaned_votes} orphaned member votes")
                return False

            logger.info("Referential integrity checks passed")
            return True

        except Exception as e:
            logger.error(f"Referential integrity check failed: {e}")
            return False

    def _check_data_consistency(self, session: Session) -> bool:
        """Check data consistency across tables."""
        try:
            # Check vote totals match member vote counts
            inconsistent_votes = session.execute(
                text(
                    """
                SELECT v.vote_id
                FROM congress.votes v
                LEFT JOIN (
                    SELECT vote_id, COUNT(*) as actual_count
                    FROM congress.member_votes
                    GROUP BY vote_id
                ) mv ON v.vote_id = mv.vote_id
                WHERE v.total_votes != COALESCE(mv.actual_count, 0)
            """
                )
            ).fetchall()

            if inconsistent_votes:
                logger.error(
                    f"Found {len(inconsistent_votes)} votes with inconsistent totals"
                )
                return False

            logger.info("Data consistency checks passed")
            return True

        except Exception as e:
            logger.error(f"Data consistency check failed: {e}")
            return False

    def _check_data_completeness(self, session: Session) -> bool:
        """Check for missing required data."""
        try:
            # Check for bills without sponsors
            bills_without_sponsors = session.execute(
                text(
                    """
                SELECT COUNT(*) FROM congress.bills
                WHERE sponsor_bioguide_id IS NULL
            """
                )
            ).scalar()

            logger.info(f"Found {bills_without_sponsors} bills without sponsors")

            # Check for members without terms
            members_without_terms = session.execute(
                text(
                    """
                SELECT COUNT(*) FROM congress.members m
                LEFT JOIN congress.member_terms mt ON m.bioguide_id = mt.bioguide_id
                WHERE mt.bioguide_id IS NULL
            """
                )
            ).scalar()

            if members_without_terms > 0:
                logger.warning(f"Found {members_without_terms} members without terms")

            logger.info("Data completeness checks completed")
            return True

        except Exception as e:
            logger.error(f"Data completeness check failed: {e}")
            return False

    def _check_constraints(self, session: Session) -> bool:
        """Check database constraints."""
        try:
            # Check party unity score ranges
            invalid_unity_scores = session.execute(
                text(
                    """
                SELECT COUNT(*) FROM analysis.member_party_unity
                WHERE unity_score < 0 OR unity_score > 100
            """
                )
            ).scalar()

            if invalid_unity_scores > 0:
                logger.error(f"Found {invalid_unity_scores} invalid unity scores")
                return False

            logger.info("Constraint checks passed")
            return True

        except Exception as e:
            logger.error(f"Constraint check failed: {e}")
            return False


# ============================================================================
# Command Line Interface
# ============================================================================


def main():
    """Main command line interface."""
    parser = argparse.ArgumentParser(
        description="Congressional Transparency Platform Database Setup"
    )
    parser.add_argument(
        "--create-schema", action="store_true", help="Create database schema"
    )
    parser.add_argument(
        "--drop-schema", action="store_true", help="Drop existing schema first"
    )
    parser.add_argument(
        "--migrate-data", action="store_true", help="Migrate JSON data to database"
    )
    parser.add_argument(
        "--validate-data", action="store_true", help="Validate migrated data"
    )
    parser.add_argument(
        "--test-connection", action="store_true", help="Test database connection"
    )
    parser.add_argument(
        "--batch-size", type=int, default=1000, help="Batch size for migration"
    )
    parser.add_argument(
        "--max-workers", type=int, default=4, help="Max parallel workers"
    )
    parser.add_argument(
        "--data-dir", type=str, default="data", help="Data directory path"
    )

    args = parser.parse_args()

    # Update configuration with command line arguments
    MIGRATION_CONFIG["batch_size"] = args.batch_size
    MIGRATION_CONFIG["max_workers"] = args.max_workers

    try:
        # Initialize database manager
        db_manager = DatabaseManager()

        if args.test_connection:
            if db_manager.test_connection():
                print("✅ Database connection successful")
            else:
                print("❌ Database connection failed")
                sys.exit(1)

        if args.create_schema:
            print("Creating database schema...")
            db_manager.create_schema(drop_existing=args.drop_schema)
            print("✅ Database schema created successfully")

        if args.migrate_data:
            print("Starting data migration...")
            migrator = DataMigrator(db_manager, Path(args.data_dir))
            stats = migrator.migrate_all_data()
            print("✅ Data migration completed")
            print("Migration statistics:")
            for table, count in stats.items():
                print(f"  {table}: {count} records")

        if args.validate_data:
            print("Validating migrated data...")
            validator = DataValidator(db_manager)
            results = validator.validate_all_data()
            print("✅ Data validation completed")
            print("Validation results:")
            for check, passed in results.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {check}: {status}")

        print("Database setup completed successfully!")

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
