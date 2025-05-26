# Sales Order Items - Batch Operations Guide

This guide explains how to use the enhanced batch operations for managing sales order items efficiently.

## Overview

The sales module now provides comprehensive batch operations for:

- **Batch Add**: Add multiple items to a sales order
- **Batch Update**: Update multiple items at once
- **Batch Delete**: Delete multiple items with safety checks
- **Batch Status Update**: Update status with validation
- **Batch Reschedule**: Reschedule delivery dates

## API Endpoints

### 1. Batch Add Items

Add multiple items to a sales order in a single operation.

**Endpoint**: `POST /api/sales/sales-order-items/batch_add_items/`

**Request Body**:

```json
{
  "sales_order_id": 1,
  "items": [
    {
      "product_id": 10,
      "quantity": 5,
      "delivery_date": "2024-02-15",
      "order_date": "2024-01-15",
      "kapsam_deadline_date": "2024-02-10",
      "notes": "Urgent delivery required",
      "status": "DRAFT"
    },
    {
      "product_id": 11,
      "quantity": 10,
      "delivery_date": "2024-02-20",
      "notes": "Standard delivery"
    }
  ]
}
```

**Required Fields**:

- `sales_order_id`: ID of the sales order
- `product_id`: Product ID
- `quantity`: Quantity (positive integer)
- `delivery_date`: Delivery date (YYYY-MM-DD)

**Optional Fields**:

- `order_date`: Defaults to current date
- `kapsam_deadline_date`: Kapsam deadline
- `notes`: Additional notes
- `status`: Defaults to "DRAFT"

**Response**:

```json
{
    "success": true,
    "message": "Successfully added 2 items to order SO-2024-001",
    "affected_count": 2,
    "details": {
        "sales_order_id": 1,
        "sales_order_number": "SO-2024-001",
        "created_items": [...]
    }
}
```

### 2. Batch Update Items

Update multiple items with the same data.

**Endpoint**: `POST /api/sales/sales-order-items/batch_update/`

**Request Body**:

```json
{
  "item_ids": [1, 2, 3, 4],
  "update_data": {
    "delivery_date": "2024-03-01",
    "kapsam_deadline_date": "2024-02-25",
    "status": "CONFIRMED",
    "notes": "Updated deadline due to material availability"
  }
}
```

**Allowed Update Fields**:

- `delivery_date`
- `kapsam_deadline_date`
- `notes`
- `quantity`
- `status`
- `order_date`

**Response**:

```json
{
  "success": true,
  "message": "Successfully updated 4 items",
  "affected_count": 4,
  "details": {
    "updated_fields": ["delivery_date", "kapsam_deadline_date", "status"],
    "requested_items": 4,
    "found_items": 4
  }
}
```

### 3. Batch Delete Items

Delete multiple items with safety checks.

**Endpoint**: `POST /api/sales/sales-order-items/batch_delete/`

**Request Body**:

```json
{
  "item_ids": [1, 2, 3],
  "confirm_deletion": true
}
```

**Safety Features**:

- Prevents deletion of shipped or delivered items
- Requires explicit confirmation
- Returns details of protected items if any

**Response**:

```json
{
  "success": true,
  "message": "Successfully deleted 3 items",
  "affected_count": 3,
  "details": {
    "requested_items": 3,
    "found_items": 3,
    "deleted_items": [
      {
        "id": 1,
        "sales_order__order_number": "SO-2024-001",
        "product__stock_code": "PROD-001"
      }
    ]
  }
}
```

### 4. Batch Status Update

Update status for multiple items with validation.

**Endpoint**: `POST /api/sales/sales-order-items/batch_status_update/`

**Request Body**:

```json
{
  "item_ids": [1, 2, 3],
  "new_status": "CONFIRMED",
  "force_update": false
}
```

**Status Transition Rules**:

- `DRAFT` → `CONFIRMED`, `CANCELLED`
- `CONFIRMED` → `IN_PRODUCTION`, `CANCELLED`
- `IN_PRODUCTION` → `READY`, `CANCELLED`
- `READY` → `SHIPPED`, `CANCELLED`
- `SHIPPED` → `DELIVERED`
- `CANCELLED` → `DRAFT` (reactivation)

**Force Update**: Set `force_update: true` to bypass validation rules.

**Response**:

```json
{
  "success": true,
  "message": "Successfully updated status for 3 items",
  "affected_count": 3,
  "details": {
    "new_status": "CONFIRMED",
    "force_update": false,
    "updated_items": [
      {
        "id": 1,
        "old_status": "DRAFT",
        "new_status": "CONFIRMED",
        "product_code": "PROD-001",
        "sales_order": "SO-2024-001"
      }
    ]
  }
}
```

### 5. Batch Reschedule

Reschedule delivery dates by a specific number of days.

**Endpoint**: `POST /api/sales/sales-order-items/batch_reschedule/`

**Request Body**:

```json
{
  "item_ids": [1, 2, 3],
  "days_offset": 7,
  "update_kapsam": true
}
```

**Parameters**:

- `days_offset`: Number of days to shift (positive for future, negative for past)
- `update_kapsam`: Whether to also update kapsam deadline dates

**Response**:

```json
{
  "success": true,
  "message": "Successfully rescheduled 3 items by 7 days",
  "affected_count": 3,
  "details": {
    "days_offset": 7,
    "update_kapsam": true,
    "rescheduled_items": [
      {
        "id": 1,
        "old_delivery_date": "2024-02-15",
        "new_delivery_date": "2024-02-22",
        "old_kapsam_date": "2024-02-10",
        "new_kapsam_date": "2024-02-17"
      }
    ]
  }
}
```

## Sales Order Specific Operations

You can also perform batch operations on items within a specific sales order:

### Update Items in a Sales Order

**Endpoint**: `POST /api/sales/sales-orders/{order_id}/batch_update_items/`

### Delete Items from a Sales Order

**Endpoint**: `POST /api/sales/sales-orders/{order_id}/batch_delete_items/`

### Add Items to a Sales Order

**Endpoint**: `POST /api/sales/sales-orders/{order_id}/add_items/`

**Request Body**:

```json
{
  "items": [
    {
      "product_id": 10,
      "quantity": 5,
      "delivery_date": "2024-02-15"
    }
  ]
}
```

## Error Handling

All batch operations return detailed error information:

```json
{
  "success": false,
  "message": "Error description",
  "affected_count": 0,
  "details": {
    "errors": ["Specific error messages"],
    "missing_ids": [1, 2],
    "protected_items": [3, 4]
  }
}
```

## Examples

### Example 1: Add Multiple Items to a New Order

```python
import requests

# Add multiple items to sales order ID 1
data = {
    "sales_order_id": 1,
    "items": [
        {
            "product_id": 10,
            "quantity": 5,
            "delivery_date": "2024-02-15",
            "kapsam_deadline_date": "2024-02-10"
        },
        {
            "product_id": 11,
            "quantity": 3,
            "delivery_date": "2024-02-20"
        }
    ]
}

response = requests.post(
    "http://localhost:8000/api/sales/sales-order-items/batch_add_items/",
    json=data,
    headers={"Authorization": "Bearer your_token"}
)
```

### Example 2: Update Delivery Dates for Multiple Items

```python
# Extend delivery dates by 1 week for multiple items
data = {
    "item_ids": [1, 2, 3, 4, 5],
    "days_offset": 7,
    "update_kapsam": true
}

response = requests.post(
    "http://localhost:8000/api/sales/sales-order-items/batch_reschedule/",
    json=data,
    headers={"Authorization": "Bearer your_token"}
)
```

### Example 3: Bulk Status Change

```python
# Confirm multiple draft items
data = {
    "item_ids": [1, 2, 3],
    "new_status": "CONFIRMED",
    "force_update": false
}

response = requests.post(
    "http://localhost:8000/api/sales/sales-order-items/batch_status_update/",
    json=data,
    headers={"Authorization": "Bearer your_token"}
)
```

### Example 4: Safe Bulk Delete

```python
# Delete multiple items with confirmation
data = {
    "item_ids": [1, 2, 3],
    "confirm_deletion": true
}

response = requests.post(
    "http://localhost:8000/api/sales/sales-order-items/batch_delete/",
    json=data,
    headers={"Authorization": "Bearer your_token"}
)
```

## Best Practices

1. **Always validate item IDs**: Check that items exist before performing operations
2. **Use transactions**: All batch operations are wrapped in database transactions
3. **Check permissions**: Ensure users have proper permissions for the operations
4. **Handle partial failures**: Review response details for items that couldn't be processed
5. **Respect status transitions**: Use `force_update: false` unless you need to bypass rules
6. **Backup before bulk deletes**: Consider creating backups before large delete operations

## Performance Considerations

- Batch operations are optimized for performance using Django's bulk operations
- Large batches (>1000 items) should be split into smaller chunks
- Database transactions ensure data integrity
- Consider using background tasks for very large operations

## Legacy Support

The existing `create_bulk` method is still available for backward compatibility, but the new `batch_add_items` method is recommended for new implementations.
