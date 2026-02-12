"""
Audit Log Integrity Verification.

Provides tamper detection through file checksums and periodic verification.
Critical for compliance (SOC 2, HIPAA) which require tamper-evident audit logs.
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AuditChecksum(BaseModel):
    """Checksum record for audit log verification."""

    timestamp: str
    file_path: str
    file_size: int
    line_count: int
    sha256: str
    verified_at: str


class AuditIntegrityManager:
    """
    Manages audit log integrity verification.

    Features:
    - Computes SHA256 checksums of audit log files
    - Stores checksums for tamper detection
    - Verifies log integrity on demand
    - Detects unauthorized modifications
    """

    def __init__(self, audit_log_path: Path, checksum_db: Path):
        """
        Initialize integrity manager.

        Args:
            audit_log_path: Path to audit log file
            checksum_db: Path to checksum database (JSON)
        """
        self.audit_log_path = audit_log_path
        self.checksum_db = checksum_db
        self.checksum_db.parent.mkdir(parents=True, exist_ok=True)

    def compute_checksum(self) -> AuditChecksum:
        """
        Compute SHA256 checksum of current audit log.

        Returns:
            AuditChecksum with file metadata and hash
        """
        if not self.audit_log_path.exists():
            raise FileNotFoundError(f"Audit log not found: {self.audit_log_path}")

        # Read file and compute hash
        sha256_hash = hashlib.sha256()
        line_count = 0

        with open(self.audit_log_path, "rb") as f:
            for line in f:
                sha256_hash.update(line)
                line_count += 1

        file_size = self.audit_log_path.stat().st_size

        return AuditChecksum(
            timestamp=datetime.now().isoformat(),
            file_path=str(self.audit_log_path),
            file_size=file_size,
            line_count=line_count,
            sha256=sha256_hash.hexdigest(),
            verified_at=datetime.now().isoformat(),
        )

    def save_checksum(self, checksum: AuditChecksum) -> None:
        """
        Save checksum to database.

        Args:
            checksum: Checksum to save
        """
        # Load existing checksums
        checksums = []
        if self.checksum_db.exists():
            with open(self.checksum_db) as f:
                checksums = [AuditChecksum(**record) for record in json.load(f)]

        # Append new checksum
        checksums.append(checksum)

        # Keep only last 100 checksums
        checksums = checksums[-100:]

        # Save
        with open(self.checksum_db, "w") as f:
            json.dump([c.model_dump() for c in checksums], f, indent=2)

        logger.info(f"Saved audit checksum: {checksum.sha256[:16]}...")

    def verify_integrity(self) -> tuple[bool, str | None]:
        """
        Verify audit log integrity against last known checksum.

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, "error message") if tampered or no baseline
        """
        # Compute current checksum
        try:
            current = self.compute_checksum()
        except FileNotFoundError as e:
            return False, str(e)

        # Load previous checksums
        if not self.checksum_db.exists():
            # No baseline - save current and return warning
            self.save_checksum(current)
            return True, "No baseline checksum - created initial checkpoint"

        with open(self.checksum_db) as f:
            records = json.load(f)

        if not records:
            self.save_checksum(current)
            return True, "No baseline checksum - created initial checkpoint"

        # Get last checksum
        last_record = AuditChecksum(**records[-1])

        # Compare checksums
        # Audit log should only grow (append-only), so:
        # - File size should increase or stay same
        # - Line count should increase or stay same
        # - If unchanged, SHA256 should match

        if current.file_size < last_record.file_size:
            return False, f"File size decreased: {last_record.file_size} -> {current.file_size} (possible truncation)"

        if current.line_count < last_record.line_count:
            return False, f"Line count decreased: {last_record.line_count} -> {current.line_count} (possible truncation)"

        if current.file_size == last_record.file_size:
            # File hasn't grown - checksum should match
            if current.sha256 != last_record.sha256:
                return False, f"Checksum mismatch (file modified): {last_record.sha256[:16]}... != {current.sha256[:16]}..."

        # Integrity verified - save new checkpoint
        self.save_checksum(current)
        return True, None

    def get_checksum_history(self, limit: int = 10) -> list[AuditChecksum]:
        """
        Get recent checksum history.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of recent checksums (newest first)
        """
        if not self.checksum_db.exists():
            return []

        with open(self.checksum_db) as f:
            records = json.load(f)

        checksums = [AuditChecksum(**r) for r in records]
        return list(reversed(checksums[-limit:]))


# Global integrity manager (initialized in main.py)
integrity_manager: AuditIntegrityManager | None = None


def get_integrity_manager(
    audit_log_path: Path = Path("/tmp/agenthub/audit.log"),
    checksum_db: Path = Path("/tmp/agenthub/audit_checksums.json"),
) -> AuditIntegrityManager:
    """Get or create global integrity manager."""
    global integrity_manager
    if integrity_manager is None:
        integrity_manager = AuditIntegrityManager(audit_log_path, checksum_db)
    return integrity_manager
