# Customer API Sorting Feature Design

## Overview

Add query parameter-based sorting to the `GET /customers/` endpoint, allowing clients to sort results by any sortable field in ascending (`asc`) or descending (`desc`) order.

## Current State

### Endpoint
- **URL**: `GET /customers/`
- **View**: `CustomerListCreateAPIView`
- **Existing Query Params**: `salon` (filter by salon ID)

### Customer Model Fields
| Field | Type | Sortable |
|-------|------|----------|
| `id` | Integer (PK) | Yes |
| `full_name` | CharField | Yes |
| `phone_number` | PhoneNumberField | Yes |
| `created` | DateTime (auto) | Yes |
| `modified` | DateTime (auto) | Yes |

---

## Proposed Design

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sort_by` | string | `created` | Field to sort by |
| `order` | string | `desc` | Sort direction: `asc` or `desc` |

### Allowed Sort Fields
```python
ALLOWED_SORT_FIELDS = ["id", "full_name", "phone_number", "created", "modified"]
```

### API Examples

```bash
# Default: Sort by created descending (newest first)
GET /customers/

# Sort by full_name ascending (A-Z)
GET /customers/?sort_by=full_name&order=asc

# Sort by full_name descending (Z-A)
GET /customers/?sort_by=full_name&order=desc

# Sort by created ascending (oldest first)
GET /customers/?sort_by=created&order=asc

# Combined with existing salon filter
GET /customers/?salon=1&sort_by=full_name&order=asc
```

### Response Format

No changes to response structure. Only the order of results changes.

```json
[
  {
    "id": 1,
    "full_name": "Alice Smith",
    "phone_number": "+441234567890",
    "salons": [...],
    "created": "2024-01-15T10:30:00Z",
    "modified": "2024-01-15T10:30:00Z"
  },
  {
    "id": 2,
    "full_name": "Bob Johnson",
    "phone_number": "+441234567891",
    "salons": [...],
    "created": "2024-01-14T09:00:00Z",
    "modified": "2024-01-14T09:00:00Z"
  }
]
```

---

## Implementation Details

### Option 1: Inline Implementation (Recommended)

Modify `CustomerListCreateAPIView.get_queryset()` directly.

**Pros**:
- Simple, contained change
- No additional dependencies
- Easy to understand

**Cons**:
- Logic duplicated if other views need sorting

### Option 2: DRF OrderingFilter

Use Django REST Framework's built-in `OrderingFilter`.

**Pros**:
- Standard DRF pattern
- Reusable across views
- Well-documented

**Cons**:
- Uses `ordering` param (different from `sort_by`/`order`)
- Less control over defaults

### Option 3: Custom Filter Backend

Create a reusable filter backend.

**Pros**:
- Highly reusable
- Centralized logic
- Configurable per view

**Cons**:
- More complex for a single endpoint

---

## Recommended Implementation (Option 1)

### Code Changes

**File**: `customer/views.py`

```python
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from .models import Customer
from .serializers import CustomerSerializer


ALLOWED_SORT_FIELDS = ["id", "full_name", "phone_number", "created", "modified"]
DEFAULT_SORT_FIELD = "created"
DEFAULT_SORT_ORDER = "desc"


class CustomerListCreateAPIView(ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by salon
        salon_id = self.request.query_params.get("salon")
        if salon_id:
            queryset = queryset.filter(salons__id=salon_id)

        # Sorting
        sort_by = self.request.query_params.get("sort_by", DEFAULT_SORT_FIELD)
        order = self.request.query_params.get("order", DEFAULT_SORT_ORDER)

        # Validate sort field
        if sort_by not in ALLOWED_SORT_FIELDS:
            sort_by = DEFAULT_SORT_FIELD

        # Validate order direction
        if order not in ["asc", "desc"]:
            order = DEFAULT_SORT_ORDER

        # Apply ordering
        order_prefix = "-" if order == "desc" else ""
        queryset = queryset.order_by(f"{order_prefix}{sort_by}")

        return queryset


class CustomerDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
```

---

## Validation & Error Handling

### Invalid `sort_by` Field
- **Behavior**: Fallback to default (`created`)
- **No error returned**: Silent fallback for better UX

### Invalid `order` Value
- **Behavior**: Fallback to default (`desc`)
- **No error returned**: Silent fallback for better UX

### Alternative: Strict Validation (Optional)

If strict validation is preferred, return 400 Bad Request:

```python
from rest_framework.exceptions import ValidationError

if sort_by not in ALLOWED_SORT_FIELDS:
    raise ValidationError(
        {"sort_by": f"Invalid sort field. Allowed: {', '.join(ALLOWED_SORT_FIELDS)}"}
    )

if order not in ["asc", "desc"]:
    raise ValidationError({"order": "Invalid order. Allowed: 'asc', 'desc'"})
```

---

## Testing Plan

### Unit Tests

```python
class CustomerSortingTests(APITestCase):
    def setUp(self):
        # Create test customers with different names and dates
        self.customer_a = Customer.objects.create(
            full_name="Alice", phone_number="+441111111111"
        )
        self.customer_b = Customer.objects.create(
            full_name="Bob", phone_number="+442222222222"
        )
        self.customer_c = Customer.objects.create(
            full_name="Charlie", phone_number="+443333333333"
        )

    def test_default_sorting_created_desc(self):
        """Default sort: newest first"""
        response = self.client.get("/customers/")
        # Assert order is newest to oldest

    def test_sort_by_full_name_asc(self):
        """Sort A-Z by full_name"""
        response = self.client.get("/customers/?sort_by=full_name&order=asc")
        names = [c["full_name"] for c in response.data]
        self.assertEqual(names, ["Alice", "Bob", "Charlie"])

    def test_sort_by_full_name_desc(self):
        """Sort Z-A by full_name"""
        response = self.client.get("/customers/?sort_by=full_name&order=desc")
        names = [c["full_name"] for c in response.data]
        self.assertEqual(names, ["Charlie", "Bob", "Alice"])

    def test_invalid_sort_field_fallback(self):
        """Invalid field falls back to default"""
        response = self.client.get("/customers/?sort_by=invalid_field")
        self.assertEqual(response.status_code, 200)

    def test_invalid_order_fallback(self):
        """Invalid order falls back to desc"""
        response = self.client.get("/customers/?sort_by=full_name&order=invalid")
        self.assertEqual(response.status_code, 200)

    def test_sorting_with_salon_filter(self):
        """Sorting works with existing salon filter"""
        response = self.client.get("/customers/?salon=1&sort_by=full_name&order=asc")
        self.assertEqual(response.status_code, 200)
```

---

## Migration Notes

- **Database**: No schema changes required
- **Breaking Changes**: None (default behavior preserved)
- **Backward Compatibility**: Existing API calls continue to work

---

## Future Considerations

1. **Multi-field Sorting**: `?sort_by=full_name,created&order=asc,desc`
2. **Pagination**: If added later, sorting should be applied before pagination
3. **Index Optimization**: Consider database indexes if sorting on large datasets

---

## Summary

| Aspect | Decision |
|--------|----------|
| Parameters | `sort_by` and `order` |
| Default Sort | `created` descending |
| Invalid Input | Silent fallback to defaults |
| Implementation | Inline in `get_queryset()` |
| Breaking Changes | None |
