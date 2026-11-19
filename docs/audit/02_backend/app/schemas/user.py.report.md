# Comprehensive Principal Software Audit & Technical Documentation
# File: `backend/app/schemas/user.py`
# Component: Identity & Access Management (IAM) Subsystem
# Release Version: 1.1.0-RC3 · ABDM / NRCES v4.1 Compliance

---

## Layer A: Executive TL;DR & Architectural Roster

### Executive Summary
`backend/app/schemas/user.py` defines the core Pydantic v2 domain schemas for platform identity modeling, account registration, profile updates, and serialization within the NIRMAYA EMR platform. It binds external authentication providers (Supabase Auth UID) to internal UUID4 identifiers, enforces RFC-compliant email formatting, provides regex validation for international and national telephone numbers, and maps users to core RBAC roles (`UserRole`).

### Architectural Role & System Topology
```
           +-----------------------------------------------+
           |         Supabase Auth / OIDC Provider         |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |          UserCreate (supabase_uid, email)     |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |           User (SQLAlchemy ORM Model)         |
           +-----------------------------------------------+
                                  |
                                  v
           +-----------------------------------------------+
           |      UserResponse (id, is_active, is_verified)|
           +-----------------------------------------------+
```

### Key Import/Export Roster
- **Imports**:
  - `datetime` from `datetime`: Temporal tracking of creation and modification timestamps.
  - `Optional` from `typing`: Nullable attribute type hints.
  - `BaseModel, ConfigDict, EmailStr, Field` from `pydantic`: Schema validation primitives and RFC email types.
  - `UserRole` from `app.models.enums`: Platform role enumeration (`ADMIN`, `DOCTOR`, `PATIENT`, `LAB_TECHNICIAN`).
- **Exports**:
  - `UserBase`: Core demographic and identity attributes (`email`, `full_name`, `phone_number`, `role`).
  - `UserCreate`: Registration payload accepting optional `supabase_uid`.
  - `UserUpdate`: Mutable fields for user profile updates.
  - `UserResponse`: Output serialization model containing database primary key and active/verified states.

---

## Layer B: Plain-Language Developer Walkthrough

1. **Shared Attributes (`UserBase`)**: Contains essential contact and identification parameters required across both creation requests and serialized responses, including validated email address (`EmailStr`), full name with minimum length of 2 characters, phone number regex pattern, and authorization role defaulting to `UserRole.PATIENT`.
2. **Registration Payload (`UserCreate`)**: Extends `UserBase` to accept an optional `supabase_uid` string linking external OAuth/OIDC identities to internal accounts.
3. **Profile Mutations (`UserUpdate`)**: Permits partial modification of user profile properties. Notably includes `role`, `is_active`, and `is_verified` as optional fields.
4. **Client Serialization (`UserResponse`)**: Outputs complete account representations including internal UUID4 identifier, Supabase linkage, account active status, verification flag, and creation/modification timestamps.

---

## Layer C: Technical Deep Dive & Invariant Analysis

### Invariant 1: Mass Assignment & Privilege Escalation in UserUpdate (CWE-915)
In `UserUpdate`, administrative attributes (`role: Optional[UserRole] = None`, `is_active: Optional[bool] = None`, `is_verified: Optional[bool] = None`) are co-located in the same schema with standard demographic fields (`full_name`, `phone_number`, `email`). If a general-purpose user profile update route (such as `PUT /users/me` or `PATCH /api/v1/profile`) binds directly to `UserUpdate`, an unprivileged user can craft a request body containing `{"role": "ADMIN", "is_verified": true}` to escalate privileges. Architectural remediation requires splitting this schema into `UserProfileUpdate` (restricted to self-service fields) and `UserAdminUpdate` (restricted to administrators).

### Invariant 2: Citizen PII Exposure in String Representations (CWE-532 / CWE-312)
`UserBase` contains sensitive personally identifiable information (`full_name`, `phone_number`, `email`). When instances of `UserCreate`, `UserUpdate`, or `UserResponse` are passed to logging calls or error handlers, Python's default Pydantic string representation emits plaintext telephone numbers and legal names. To prevent accidental leakage into centralized log collectors (Datadog, CloudWatch, Loki), sensitive demographic fields should be configured with `repr=False`.

---

## Layer D: Findings Summary Table

| Finding ID | Severity | Category | Target Location | Description |
| :--- | :--- | :--- | :--- | :--- |
| `BE-SCH-USR-F01` | S1 | `[SEC]` | `user.py:52-54` | `UserUpdate` exposes `role`, `is_active`, and `is_verified`, risking privilege escalation via mass assignment |
| `BE-SCH-USR-F02` | S2 | `[SEC]` | `user.py:16-27` | `phone_number` and `full_name` lack `repr=False`, leaking citizen PII in string representations |
| `BE-SCH-USR-F03` | S3 | `[QUAL]` | `user.py:37-40, 60` | `supabase_uid` and `UserResponse.id` lack UUID format validation patterns |

---

## Layer E: Unapplied Unified Diff Patches for S0–S2 Findings

```diff
--- a/backend/app/schemas/user.py
+++ b/backend/app/schemas/user.py
@@ -19,11 +19,13 @@
         min_length=2,
         max_length=255,
         description="Full legal name of the user",
+        repr=False,
         examples=["Rahul Sharma"],
     )
     phone_number: Optional[str] = Field(
         default=None,
         pattern=r"^\+?[0-9\s\-()]{7,20}$",
+        repr=False,
         description="E.164 or national formatted phone number",
         examples=["+919876543210"],
     )
@@ -43,15 +45,21 @@
 class UserUpdate(BaseModel):
-    """Schema for updating an existing user's attributes."""
+    """Schema for self-service user profile updates (non-administrative)."""
 
     email: Optional[EmailStr] = None
     full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
     phone_number: Optional[str] = Field(
         default=None,
         pattern=r"^\+?[0-9\s\-()]{7,20}$",
     )
+
+
+class UserAdminUpdate(UserUpdate):
+    """Administrative schema for modifying role and account status gates."""
+
     role: Optional[UserRole] = None
     is_active: Optional[bool] = None
     is_verified: Optional[bool] = None
```
