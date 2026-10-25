"""RSA-2048 Cryptographic Manager for ABDM Demographic Data Encryption & Decryption.

Conforms to National Health Authority (NHA) ABDM specifications:
- Asymmetric Algorithm: RSA-2048
- Padding Scheme: OAEP (Optimal Asymmetric Encryption Padding)
- Hash Function: SHA-256
- Mask Generation Function (MGF): MGF1 with SHA-256
- Encoding: Base64 for transport over HTTP JSON payloads
"""

import base64
import json
import logging
from typing import Any, Dict, Optional, Tuple, Union

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

logger = logging.getLogger("nirmaya.abdm.crypto")


class ABDMRSAEncryptionManager:
    """Manages RSA-2048 public and private key operations for ABDM Gateway payloads."""

    def __init__(
        self,
        public_key_pem: Optional[str] = None,
        private_key_pem: Optional[str] = None,
    ) -> None:
        """Initialize with existing PEM keys, or generate an ephemeral 2048-bit key pair."""
        self._private_key: Optional[rsa.RSAPrivateKey] = None
        self._public_key: Optional[rsa.RSAPublicKey] = None

        if private_key_pem and private_key_pem.strip():
            try:
                self._private_key = serialization.load_pem_private_key(
                    private_key_pem.encode("utf-8"),
                    password=None,
                )  # type: ignore[assignment]
                self._public_key = self._private_key.public_key()
            except Exception as e:
                logger.warning(f"Failed to load provided private key PEM: {e}. Generating fallback key pair.")
                self._generate_key_pair()
        elif public_key_pem and public_key_pem.strip():
            try:
                self._public_key = serialization.load_pem_public_key(
                    public_key_pem.encode("utf-8"),
                )  # type: ignore[assignment]
            except Exception as e:
                logger.warning(f"Failed to load provided public key PEM: {e}. Generating fallback key pair.")
                self._generate_key_pair()
        else:
            self._generate_key_pair()

    def _generate_key_pair(self) -> None:
        """Generate a cryptographically secure RSA-2048 key pair."""
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self._public_key = self._private_key.public_key()

    @property
    def has_private_key(self) -> bool:
        """Check if private key is available for decryption."""
        return self._private_key is not None

    def get_public_key_pem(self) -> str:
        """Export RSA public key as PEM-formatted string."""
        if not self._public_key:
            raise ValueError("RSA public key is not initialized.")
        pem_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem_bytes.decode("utf-8")

    def get_private_key_pem(self) -> str:
        """Export RSA private key as PEM-formatted string (unencrypted PKCS8)."""
        if not self._private_key:
            raise ValueError("RSA private key is not initialized.")
        pem_bytes = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return pem_bytes.decode("utf-8")

    def get_public_key_fingerprint(self) -> str:
        """Return SHA-256 fingerprint of the SubjectPublicKeyInfo DER bytes."""
        if not self._public_key:
            raise ValueError("RSA public key is not initialized.")
        der_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        digest = hashes.Hash(hashes.SHA256())
        digest.update(der_bytes)
        return digest.finalize().hex()

    def encrypt_demographic_payload(self, payload: Union[Dict[str, Any], str]) -> str:
        """Encrypt demographic data dictionary or string using NHA standard RSA-OAEP SHA-256.

        Args:
            payload: Demographic dictionary or raw JSON string.

        Returns:
            Base64-encoded encrypted ciphertext string.
        """
        if not self._public_key:
            raise ValueError("Cannot encrypt: RSA public key is not available.")

        if isinstance(payload, dict):
            plaintext_bytes = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        else:
            plaintext_bytes = payload.encode("utf-8")

        # NHA ABDM standard: RSA-OAEP with SHA-256 and MGF1(SHA-256)
        ciphertext = self._public_key.encrypt(
            plaintext_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return base64.b64encode(ciphertext).decode("utf-8")

    def decrypt_demographic_payload(self, ciphertext_b64: str) -> Dict[str, Any]:
        """Decrypt Base64 RSA-OAEP ciphertext and parse as demographic JSON dictionary.

        Args:
            ciphertext_b64: Base64-encoded ciphertext string.

        Returns:
            Decrypted demographic dictionary.
        """
        if not self._private_key:
            raise ValueError("Cannot decrypt: RSA private key is not available.")

        try:
            ciphertext_bytes = base64.b64decode(ciphertext_b64)
            decrypted_bytes = self._private_key.decrypt(
                ciphertext_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return json.loads(decrypted_bytes.decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to decrypt or deserialize demographic payload: {e}")
            raise ValueError(f"RSA demographic decryption failed: {e}") from e


# Global singleton instance for application use
_default_encryption_manager: Optional[ABDMRSAEncryptionManager] = None


def get_abdm_encryption_manager() -> ABDMRSAEncryptionManager:
    """Obtain or lazily instantiate the application's ABDM encryption manager."""
    global _default_encryption_manager
    if _default_encryption_manager is None:
        from app.core.config import settings

        _default_encryption_manager = ABDMRSAEncryptionManager(
            public_key_pem=settings.ABDM_ENCRYPTION_PUBLIC_KEY,
            private_key_pem=settings.ABDM_ENCRYPTION_PRIVATE_KEY,
        )
    return _default_encryption_manager
