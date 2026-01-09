# Testing Patterns

**Analysis Date:** 2026-01-09

## Test Framework

**Runner:**
- No formal test framework (no pytest, unittest)
- Manual tests embedded in source modules

**Assertion Library:**
- Manual validation using conditional statements
- Pattern: `"✅ PASS" if condition else "❌ FAIL"`

**Run Commands:**
```bash
python src/compactness.py           # Run compactness tests
python src/data_loader.py           # Run data loader tests
python src/position_classifier.py   # Run classifier tests
python src/markers.py               # Visual marker test
python src/pitch.py                 # Visual pitch test
```

## Test File Organization

**Location:**
- Embedded in source files (`if __name__ == "__main__":` blocks)
- No separate `tests/` directory

**Naming:**
- No naming convention (tests in source modules)

**Structure:**
```
src/
  compactness.py        # 10 test cases (lines 200-335)
  data_loader.py        # Data generation tests (lines 123-139)
  position_classifier.py # Classification tests (lines 146-174)
  markers.py            # Visual test grid (lines 113-134)
  pitch.py              # Visual pitch test (lines 209-223)
  shape_lines.py        # Integration test (lines 150-210)
```

## Test Structure

**Suite Organization:**
```python
if __name__ == "__main__":
    print("=" * 60)
    print("MODULE TESTS")
    print("=" * 60)

    print("\n--- Test 1: Description ---")
    # arrange
    test_data = create_test_data()

    # act
    result = function_under_test(test_data)

    # assert
    status = "✅ PASS" if result > expected else "❌ FAIL"
    print(f"  {status}")
```

**Patterns:**
- Print statements for output
- Status indicators: `"✅ PASS"`, `"❌ FAIL"`
- Visual tests save PNG files for manual inspection

## Mocking

**Framework:**
- None (no mocking library)

**Patterns:**
- Synthetic data generation: `generate_synthetic_tracking()`
- Hardcoded test fixtures inline

**What to Mock:**
- Not applicable (no mocking framework)

**What NOT to Mock:**
- Not applicable

## Fixtures and Factories

**Test Data:**
```python
# Factory pattern in test code
def create_test_positions():
    return {
        1: (20.0, 34.0),  # GK
        2: (30.0, 20.0),  # LB
        # ... more positions
    }
```

**Location:**
- Inline in test blocks
- Synthetic data generators in `src/data_loader.py`

## Coverage

**Requirements:**
- No coverage requirements
- No coverage tool configured

**Configuration:**
- Not applicable

**View Coverage:**
- Not available

## Test Types

**Unit Tests:**
- `src/compactness.py` - 10 test cases for CI calculation
- `src/position_classifier.py` - Classification validation
- Scope: Single function in isolation

**Integration Tests:**
- `src/shape_lines.py` lines 150-210 - Full pipeline test
- Tests multiple modules together

**Visual Tests:**
- `src/markers.py` - 5x5 marker grid rendering
- `src/pitch.py` - Pitch rendering to PNG
- Manual inspection required

**E2E Tests:**
- None (manual testing via Streamlit UI)

## Common Patterns

**Async Testing:**
- Not applicable (synchronous codebase)

**Error Testing:**
```python
# Edge case testing in compactness.py
print("\n--- Test 9: Edge case - insufficient players ---")
sparse_positions = {1: (50.0, 34.0), 2: (60.0, 30.0)}  # Only 2 players
result = compute_ci(sparse_positions, is_home=True)
status = "✅ PASS" if result['ci'] == 0 else "❌ FAIL"
```

**Snapshot Testing:**
- Not used

## Recommended Improvements

**Short-term:**
- Add pytest as test framework
- Extract test blocks into `tests/` directory
- Add `assert` statements instead of print checks

**Long-term:**
- Add coverage reporting
- Add CI pipeline with test automation
- Add integration tests for Streamlit UI

---

*Testing analysis: 2026-01-09*
*Update when test patterns change*
