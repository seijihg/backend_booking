# Design: Filter Customers by Salon ID

## Overview

Add query parameter filtering to the `GET /customers/` endpoint to retrieve customers associated with a specific salon.

## Current State

### Endpoint
- **URL**: `GET /customers/`
- **View**: `CustomerListCreateAPIView`
- **Behavior**: Returns ALL customers in the database

### Model Relationship
```python
class Customer(CommonInfo, TimeStampedModel):
    full_name = models.CharField(max_length=150, blank=True)
    salons = models.ManyToManyField(Salon, related_name="customers")
```

The `Customer` model has a **many-to-many** relationship with `Salon` via the `salons` field.

## Proposed Change

### API Design

| Method | Endpoint | Query Params | Description |
|--------|----------|--------------|-------------|
| GET | `/customers/` | `salon={id}` | Filter customers by salon ID |
| GET | `/customers/` | (none) | Return all customers (existing behavior) |

### Request Examples

```bash
# Get customers for salon ID 1
GET /customers/?salon=1

# Get customers for salon ID 5
GET /customers/?salon=5

# Get all customers (unchanged behavior)
GET /customers/
```

### Response Format

No changes to response format. Returns array of customer objects:

```json
[
  {
    "id": 1,
    "full_name": "John Doe",
    "phone_number": "+1234567890",
    "salons": [1, 2],
    "created": "2024-01-01T00:00:00Z",
    "modified": "2024-01-01T00:00:00Z"
  }
]
```

## Implementation

### Option A: Override `get_queryset()` (Recommended)

```python
class CustomerListCreateAPIView(ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        salon_id = self.request.query_params.get("salon")
        if salon_id:
            queryset = queryset.filter(salons__id=salon_id)
        return queryset
```

**Pros**:
- Simple and explicit
- No additional dependencies
- Maintains backward compatibility

### Option B: Use `django-filter` Library

```python
from django_filters import rest_framework as filters


class CustomerFilter(filters.FilterSet):
    salon = filters.NumberFilter(field_name="salons__id")

    class Meta:
        model = Customer
        fields = ["salon"]


class CustomerListCreateAPIView(ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filterset_class = CustomerFilter
```

**Pros**:
- Extensible for future filters
- Standardized filtering approach

**Cons**:
- Requires additional dependency (`django-filter`)
- Overkill for single filter

## Recommendation

**Use Option A** - Override `get_queryset()` method.

Rationale:
1. Single filter requirement doesn't justify new dependency
2. Keeps implementation simple and maintainable
3. Aligns with existing project patterns (no `django-filter` in requirements)

## Error Handling

| Scenario | Behavior |
|----------|----------|
| `salon=invalid` (non-integer) | Return empty array `[]` |
| `salon=999` (non-existent) | Return empty array `[]` |
| `salon=` (empty value) | Return all customers |

### Optional: Add Validation

For stricter validation, optionally return 400 Bad Request for invalid salon IDs:

```python
def get_queryset(self):
    queryset = super().get_queryset()
    salon_id = self.request.query_params.get("salon")
    if salon_id:
        try:
            salon_id = int(salon_id)
        except ValueError:
            raise ValidationError({"salon": "Must be a valid integer"})
        queryset = queryset.filter(salons__id=salon_id)
    return queryset
```

## Testing Considerations

1. **Filter by existing salon** - Returns matching customers
2. **Filter by non-existent salon** - Returns empty array
3. **No filter parameter** - Returns all customers (backward compatible)
4. **Invalid salon ID format** - Handles gracefully
5. **Customer with multiple salons** - Appears in results for each associated salon

## Files to Modify

| File | Change |
|------|--------|
| `customer/views.py` | Add `get_queryset()` override |

## Migration Required

No database migration required. This is a read-only query enhancement.

## Rollback Plan

Remove the `get_queryset()` method override to restore original behavior.
