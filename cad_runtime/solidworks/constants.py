# SolidWorks enum values used by this minimal runtime.
# Keep raw API numbers here so agent-generated plans never depend on magic values.

SW_DOC_PART = 1
SW_BODY_TYPE_SOLID = 0

# swEndConditions_e
SW_END_COND_BLIND = 0
SW_END_COND_THROUGH_ALL = 1

# Reference plane constraint value commonly used for offset plane creation.
# Verify against your SolidWorks API version if plane creation fails.
REF_PLANE_OFFSET = 8
