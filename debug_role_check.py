#!/usr/bin/env python3

# Test script to debug role checking
from enum import Enum

class SpaceRole(str, Enum):
    """Project space member roles"""
    OWNER = "owner"
    ADMIN = "admin" 
    MEMBER = "member"
    VIEWER = "viewer"

# Test the comparison
found_role = "owner"
required_role = SpaceRole.OWNER

print(f"found_role: {found_role}")
print(f"required_role: {required_role}")
print(f"required_role.value: {required_role.value}")
print(f"found_role == required_role.value: {found_role == required_role.value}")
print(f"type(found_role): {type(found_role)}")
print(f"type(required_role.value): {type(required_role.value)}")
