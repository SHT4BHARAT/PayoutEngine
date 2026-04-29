# ADR 001: Store all money as paise (integer), never float

**Date**: 2026-04-27  
**Status**: Accepted

## Context
Financial systems that use floats eventually lose money due to IEEE 754 rounding. For example, `0.1 + 0.2 == 0.30000000000000004` in Python.

## Decision
All monetary values are stored and computed as **paise** (1 INR = 100 paise) using `BigIntegerField`. No `FloatField`. No `DecimalField` in the hot path.

## Consequences
- Frontend divides by 100 for display only
- API always sends/receives integers
- No rounding errors possible in storage or computation