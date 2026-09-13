import json
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Set

logger = logging.getLogger("entity_service")


class VaspVerificationStatus(str, Enum):
    OFFICIAL_SOURCE = "OFFICIAL_SOURCE"
    TRUSTED_PUBLIC_LABEL = "TRUSTED_PUBLIC_LABEL"
    BLOCKCHAIN_INTELLIGENCE_SOURCE = "BLOCKCHAIN_INTELLIGENCE_SOURCE"
    MULTI_SOURCE_CONFIRMED = "MULTI_SOURCE_CONFIRMED"
    MANUALLY_VERIFIED = "MANUALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"


VASP_ENTITY_TYPES = {
    "centralized_exchange",
    "VASP",
    "custodial_wallet",
    "custodial_service",
    "payment_processor",
    "exchange",  # backward compatibility
}


class VaspRecord:
    """
    Represents an independently documented Virtual Asset Service Provider (VASP)
    organization, complete with jurisdiction, registration, KYC policy, and LEA contact info.
    """

    def __init__(
        self,
        vasp_id: str,
        name: str,
        entity_type: str = "centralized_exchange",
        jurisdiction: str = "Global",
        country: str = "Global",
        website: str = "",
        kyc_status: str = "MANDATORY_KYC",
        known_addresses: Optional[List[str]] = None,
        known_clusters: Optional[List[str]] = None,
        supported_chains: Optional[List[str]] = None,
        compliance_contact: str = "",
        verification_source: str = "Public Ledger Label",
        verification_status: str = "TRUSTED_PUBLIC_LABEL",
        last_verified: Optional[str] = None,
        confidence: str = "HIGH",
        notes: str = "",
    ):
        self.vasp_id = vasp_id.strip()
        self.name = name.strip()
        self.entity_type = entity_type
        self.jurisdiction = jurisdiction
        self.country = country
        self.website = website
        self.kyc_status = kyc_status
        self.known_addresses = [a.lower().strip() for a in (known_addresses or [])]
        self.known_clusters = known_clusters or []
        self.supported_chains = supported_chains or ["ethereum"]
        self.compliance_contact = compliance_contact
        self.verification_source = verification_source
        self.verification_status = verification_status
        self.last_verified = last_verified
        self.confidence = confidence.upper()
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vaspId": self.vasp_id,
            "name": self.name,
            "type": self.entity_type,
            "jurisdiction": self.jurisdiction,
            "country": self.country,
            "website": self.website,
            "kycStatus": self.kyc_status,
            "knownAddresses": self.known_addresses,
            "knownClusters": self.known_clusters,
            "supportedChains": self.supported_chains,
            "complianceContact": self.compliance_contact,
            "verificationSource": self.verification_source,
            "verificationStatus": self.verification_status,
            "lastVerified": self.last_verified,
            "confidence": self.confidence,
            "notes": self.notes,
        }


class KnownEntity:
    """
    Represents an on-chain address attribution mapping (wallet address -> entity identity).
    Distinguishes specific address evidence from generalized VASP organizational records.
    """

    def __init__(
        self,
        address: str,
        entity_name: str,
        entity_type: str = "centralized_exchange",
        source: str = "Public Ledger Label",
        source_url: str = "",
        confidence: str = "HIGH",
        verified: bool = True,
        last_verified: Optional[str] = None,
        vasp_id: Optional[str] = None,
        verification_status: str = "TRUSTED_PUBLIC_LABEL",
    ):
        self.address = address.lower().strip()
        self.entity_name = entity_name
        self.entity_type = entity_type
        self.source = source
        self.source_url = source_url
        self.confidence = confidence.upper() if confidence else "HIGH"
        self.verified = verified
        self.last_verified = last_verified
        self.vasp_id = vasp_id
        self.verification_status = verification_status

    def is_vasp(self) -> bool:
        """Returns True if this entity qualifies as a regulated VASP or centralized exchange."""
        return self.entity_type in VASP_ENTITY_TYPES

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "entityName": self.entity_name,
            "entityType": self.entity_type,
            "source": self.source,
            "sourceUrl": self.source_url,
            "confidence": self.confidence,
            "verified": self.verified,
            "lastVerified": self.last_verified,
            "isVasp": self.is_vasp(),
            "vaspId": self.vasp_id,
            "verificationStatus": self.verification_status,
        }


class EntityService:
    """
    Manages known cryptocurrency entity attribution (Exchanges, VASPs, DEX routers, Bridges, Mixers)
    and the comprehensive Verified VASP Directory with regulatory compliance metadata.
    """

    def __init__(self, data_path: Optional[Path] = None, vasp_dir_path: Optional[Path] = None):
        self._entities: Dict[str, KnownEntity] = {}
        self._vasps: Dict[str, VaspRecord] = {}
        self._address_to_vasp_id: Dict[str, str] = {}

        root_dir = Path(__file__).resolve().parent.parent.parent
        self._data_path = data_path or (root_dir / "data" / "known_entities.json")
        self._vasp_dir_path = vasp_dir_path or (root_dir / "data" / "vasp_directory.json")

        self.load_entities()
        self.load_vasp_directory()

    def load_entities(self) -> int:
        """Loads and indexes the known entity dataset from disk."""
        self._entities.clear()
        if not self._data_path.exists():
            logger.warning(f"Known entities file not found at {self._data_path}. Initializing empty.")
            return 0

        try:
            with open(self._data_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                if isinstance(raw_data, list):
                    for item in raw_data:
                        addr = item.get("address", "").lower().strip()
                        if addr:
                            self._entities[addr] = KnownEntity(
                                address=addr,
                                entity_name=item.get("entityName", "Unknown Entity"),
                                entity_type=item.get("entityType", "centralized_exchange"),
                                source=item.get("source", "Public Attribution Dataset"),
                                source_url=item.get("sourceUrl", ""),
                                confidence=item.get("confidence", "HIGH"),
                                verified=item.get("verified", True),
                                last_verified=item.get("lastVerified", None),
                                vasp_id=item.get("vaspId"),
                                verification_status=item.get("verificationStatus", "TRUSTED_PUBLIC_LABEL"),
                            )
            logger.info(f"Loaded {len(self._entities)} verified entity attribution records.")
            return len(self._entities)
        except Exception as e:
            logger.error(f"Failed to load known entities from {self._data_path}: {e}")
            return 0

    def load_vasp_directory(self) -> int:
        """Loads the official Verified VASP Directory with regulatory compliance metadata."""
        self._vasps.clear()
        self._address_to_vasp_id.clear()

        if not self._vasp_dir_path.exists():
            logger.warning(f"VASP directory file not found at {self._vasp_dir_path}.")
            return 0

        try:
            with open(self._vasp_dir_path, "r", encoding="utf-8") as f:
                raw_vasps = json.load(f)
                if isinstance(raw_vasps, list):
                    for item in raw_vasps:
                        vid = item.get("vasp_id", "").strip()
                        if vid:
                            record = VaspRecord(
                                vasp_id=vid,
                                name=item.get("name", "Unknown VASP"),
                                entity_type=item.get("type", "centralized_exchange"),
                                jurisdiction=item.get("jurisdiction", "Global"),
                                country=item.get("country", "Global"),
                                website=item.get("website", ""),
                                kyc_status=item.get("kyc_status", "MANDATORY_KYC"),
                                known_addresses=item.get("known_addresses", []),
                                known_clusters=item.get("known_clusters", []),
                                supported_chains=item.get("supported_chains", ["ethereum"]),
                                compliance_contact=item.get("compliance_contact", ""),
                                verification_source=item.get("verification_source", "Public Records"),
                                verification_status=item.get("verification_status", "TRUSTED_PUBLIC_LABEL"),
                                last_verified=item.get("last_verified"),
                                confidence=item.get("confidence", "HIGH"),
                                notes=item.get("notes", ""),
                            )
                            self._vasps[vid] = record

                            # Index all addresses belonging to this VASP
                            for addr in record.known_addresses:
                                self._address_to_vasp_id[addr] = vid
            logger.info(f"Loaded {len(self._vasps)} verified VASP directory records.")
            return len(self._vasps)
        except Exception as e:
            logger.error(f"Failed to load VASP directory from {self._vasp_dir_path}: {e}")
            return 0

    def get_entity(self, address: str) -> Optional[KnownEntity]:
        """Looks up a wallet address in the known entities dataset."""
        if not address:
            return None
        return self._entities.get(address.lower().strip())

    def is_known_entity(self, address: str) -> bool:
        """Returns True if the address matches a known entity."""
        if not address:
            return False
        return address.lower().strip() in self._entities

    def is_vasp(self, address: str) -> bool:
        """Returns True if the address is a known VASP / centralized exchange."""
        entity = self.get_entity(address)
        if entity and entity.is_vasp():
            return True
        # Also check direct VASP directory address index
        clean_addr = address.lower().strip() if address else ""
        return clean_addr in self._address_to_vasp_id

    def get_vasp(self, vasp_id: str) -> Optional[VaspRecord]:
        """Retrieves a VASP organizational record by VASP ID."""
        if not vasp_id:
            return None
        return self._vasps.get(vasp_id.strip())

    def get_vasp_by_address(self, address: str) -> Optional[VaspRecord]:
        """Finds the corresponding VASP record linked to a given address."""
        if not address:
            return None
        clean = address.lower().strip()
        vid = self._address_to_vasp_id.get(clean)
        if vid:
            return self._vasps.get(vid)
        # Check if known entity name matches any VASP name
        entity = self.get_entity(clean)
        if entity:
            for vasp in self._vasps.values():
                if vasp.name.lower() in entity.entity_name.lower() or entity.entity_name.lower() in vasp.name.lower():
                    return vasp
        return None

    def get_all_entities(self) -> List[Dict[str, Any]]:
        """Returns all loaded entities as dictionaries."""
        return [e.to_dict() for e in self._entities.values()]

    def get_vasp_entities(self) -> List[Dict[str, Any]]:
        """Returns only entities classified as VASPs or centralized exchanges."""
        return [e.to_dict() for e in self._entities.values() if e.is_vasp()]

    def get_all_vasps(self) -> List[Dict[str, Any]]:
        """Returns all VASP records in the Verified VASP Directory."""
        return [v.to_dict() for v in self._vasps.values()]


entity_service = EntityService()
