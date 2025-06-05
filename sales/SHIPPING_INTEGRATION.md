# Shipping Module Integration

## Overview

The Shipping module has been successfully integrated into the ERP sales system. This module allows you to track shipments for sales order items, providing complete visibility into what has been shipped and what remains to be shipped.

## Key Features

### 1. Shipping Model

- **UUID Primary Key**: Uses UUID for better security and distributed systems
- **Shipping Number**: Unique identifier for each shipment
- **Date Tracking**: Records when items were shipped
- **Order Relationships**: Links to both SalesOrder and SalesOrderItem
- **Quantity Tracking**: Tracks how much was shipped in each shipment
- **Package Management**: Supports multiple packages per shipment
- **Notes**: Optional shipping notes for additional information

### 2. Validation & Business Logic

- **Quantity Validation**: Prevents shipping more than ordered
- **Automatic Status Updates**: Updates order item status when fully shipped
- **Unique Constraints**: Prevents duplicate shipments for same order/item combination

### 3. Enhanced SalesOrderItem Properties

- `shipped_quantity`: Total quantity shipped for this item
- `remaining_quantity`: Quantity still to be shipped
- `is_fully_shipped`: Boolean indicating if completely shipped
- `is_partially_shipped`: Boolean indicating partial shipment

## API Endpoints

The ShippingViewSet provides comprehensive REST API endpoints:

### Core CRUD Operations

- `GET /api/sales/shipments/` - List all shipments
- `POST /api/sales/shipments/` - Create new shipment
- `GET /api/sales/shipments/{id}/` - Get specific shipment
- `PUT/PATCH /api/sales/shipments/{id}/` - Update shipment
- `DELETE /api/sales/shipments/{id}/` - Delete shipment

### Specialized Endpoints

- `GET /api/sales/shipments/by_order/?order_id={id}` - Get shipments for an order
- `GET /api/sales/shipments/by_order_item/?order_item_id={id}` - Get shipments for order item with remaining quantity
- `POST /api/sales/shipments/create_shipment/` - Create shipment with validation
- `GET /api/sales/shipments/shipping_summary/` - Get shipping statistics
- `GET /api/sales/shipments/pending_shipments/` - Get items ready for shipment

## Database Structure

### Shipping Table Fields

```sql
- id: UUID (Primary Key)
- shipping_no: VARCHAR(50)
- shipping_date: DATE
- order_id: Foreign Key to SalesOrder
- order_item_id: Foreign Key to SalesOrderItem
- quantity: POSITIVE INTEGER
- package_number: POSITIVE INTEGER (default: 1)
- shipping_note: TEXT (optional)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

### Indexes

- shipping_date
- order_id
- order_item_id
- shipping_no

### Constraints

- Unique together: (shipping_no, order, order_item)
- Quantity validation: Cannot exceed ordered quantity

## Integration Points

### 1. Models Integration

- Added shipping-related properties to `SalesOrderItem`
- Foreign key relationships properly configured
- Validation at model level

### 2. Admin Integration

- Full Django admin support for managing shipments
- List display shows key information
- Filtering and searching capabilities
- Date hierarchy for easy navigation

### 3. Serializers Integration

- `ShippingSerializer`: Full CRUD operations
- `ShippingListSerializer`: Optimized for list views
- Related field serialization for better API responses

### 4. Views Integration

- Complete ViewSet with all standard operations
- Custom actions for business-specific operations
- Proper filtering and pagination
- Permission-based access control

## Usage Examples

### Creating a Shipment

```python
POST /api/sales/shipments/create_shipment/
{
    "shipping_no": "SHIP-2024-001",
    "shipping_date": "2024-05-26",
    "order": "order_uuid",
    "order_item": "order_item_uuid",
    "quantity": 50,
    "package_number": 2,
    "shipping_note": "Fragile items, handle with care"
}
```

### Getting Shipment Summary

```python
GET /api/sales/shipments/shipping_summary/
# Returns statistics for today, this week, and this month
```

### Checking Remaining Quantity

```python
GET /api/sales/shipments/by_order_item/?order_item_id={uuid}
# Returns shipments and remaining quantity information
```

## Automatic Status Management

The system automatically updates order item statuses:

- When an order item is fully shipped, status changes to `SHIPPED`
- Quantity validation prevents over-shipping
- Business logic maintains data integrity

## Migration Applied

Migration `0005_shipping.py` has been successfully applied, creating:

- Shipping table with all fields and constraints
- Proper indexes for performance
- Foreign key relationships

## Next Steps

1. **Frontend Integration**: Create UI components for shipping management
2. **Reporting**: Add shipping reports and analytics
3. **Notifications**: Implement shipping notifications
4. **Barcode Integration**: Add barcode scanning for shipments
5. **Carrier Integration**: Connect with shipping carriers for tracking

## Files Modified

1. `sales/models.py` - Added Shipping model and enhanced SalesOrderItem
2. `sales/admin.py` - Added ShippingAdmin configuration
3. `sales/serializers.py` - Added shipping serializers
4. `sales/views.py` - Added ShippingViewSet with custom actions
5. `sales/urls.py` - Added shipping URL patterns
6. `sales/migrations/0005_shipping.py` - Database migration

The shipping module is now fully integrated and ready for use!
