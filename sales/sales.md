# Sales Module Frontend Design Specifications

## Overview

This document outlines the frontend design and user interface specifications for the Sales module in the ERP system. The module focuses on order tracking and logistics without pricing functionality.

## Main Navigation Structure

```
Sales Module
├── Dashboard
├── Sales Orders
│   ├── All Orders
│   ├── Create New Order
│   └── Order Details
├── Quotations
│   ├── All Quotations
│   ├── Create New Quotation
│   └── Quotation Details
└── Reports
    ├── Order Status Overview
    ├── Overdue Orders
    └── Sales Activity
```

## 1. Sales Dashboard

### Layout

- **Top Row**: Key metrics cards
- **Middle**: Quick action buttons
- **Bottom**: Recent activity and alerts

### Key Components

#### Dashboard Cards

```jsx
- Total Active Orders: 156
- Orders This Month: 42
- Overdue Orders: 8 (⚠️ Alert style)
- Pending Quotations: 23
- Quotations This Week: 15
- Conversion Rate: 65% (Quotes → Orders)
```

#### Quick Actions

```jsx
[+ New Order] [+ New Quotation] [View Overdue] [Export Data]
```

#### Recent Activity Table (last 10 items)

```jsx
Order #SO-2024-001 | Customer ABC Corp | Draft → Confirmed | 2 min ago
Quote #QU-2024-045 | Customer XYZ Ltd | Sent to Customer | 1 hour ago
```

#### Alerts Section

```jsx
⚠️ 8 orders are overdue delivery
📋 5 quotations expire this week
🔄 3 quotations ready for follow-up
```

## 2. Sales Orders Page

### List View Layout

#### Header Section

```jsx
Sales Orders [+ New Order] [Import] [Export]
```

#### Filters Bar

```jsx
Status: [All ▼] Customer: [Select ▼] Salesperson: [Select ▼]
Date Range: [This Month ▼] Search: [Order # or Customer...]
```

#### Status Filter Tabs

```jsx
[All (156)] [Draft (23)] [Confirmed (45)] [In Production (67)]
[Ready (12)] [Shipped (8)] [Delivered (89)] [Cancelled (4)]
```

#### Data Table

```jsx
┌─────────────┬──────────────┬──────────────┬─────────────┬──────────────┬─────────────┬─────────────┐
│ Order #     │ Customer     │ Order Date   │ Delivery    │ Status       │ Items       │ Actions     │
│             │              │              │ Date        │              │ Count       │             │
├─────────────┼──────────────┼──────────────┼─────────────┼──────────────┼─────────────┼─────────────┤
│ SO-2024-001 │ ABC Corp     │ 2024-01-15   │ 2024-02-15  │ 🟡 Confirmed │ 5 items     │ [View][Edit]│
│ SO-2024-002 │ XYZ Ltd      │ 2024-01-14   │ 2024-02-10  │ 🔵 In Prod   │ 3 items     │ [View]      │
│ SO-2024-003 │ DEF Inc      │ 2024-01-13   │ 2024-01-20  │ 🔴 Overdue   │ 2 items     │ [View][📧]  │
└─────────────┴──────────────┴──────────────┴─────────────┴──────────────┴─────────────┴─────────────┘
```

#### Pagination

```jsx
Showing 1-20 of 156 orders [< Previous] [1][2][3]...[8] [Next >]
```

### Status Color Coding

- 🔘 **Draft**: Gray
- 🟡 **Confirmed**: Yellow
- 🔵 **In Production**: Blue
- 🟢 **Ready**: Green
- 🟠 **Shipped**: Orange
- ✅ **Delivered**: Green checkmark
- 🔴 **Overdue**: Red
- ❌ **Cancelled**: Red X

## 3. Create/Edit Order Form

### Form Layout

#### Header

```jsx
Create New Sales Order [Save Draft] [Save & Confirm] [Cancel]
```

#### Main Information Section

```jsx
┌─────────────────────────────────────────────────────────────────────────┐
│ ORDER INFORMATION                                                       │
├─────────────────────────────────────────────────────────────────────────┤
│ Order Number: [SO-2024-XXX] (auto-generated)                          │
│ Customer: [Select Customer ▼] ( + Add New Customer)                    │
│ Order Date: [2024-01-15] Delivery Date: [2024-02-15]                  │
│ Customer PO#: [Optional field]                                          │
│ Status: [Draft ▼]                                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Order Items Section

```jsx
┌─────────────────────────────────────────────────────────────────────────┐
│ ORDER ITEMS                                            [+ Add Item]     │
├─────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────┬─────────────┬─────────────┬──────────────┬─────────────┐ │
│ │ Product     │ Description │ Quantity    │ Delivery     │ Actions     │ │
│ │             │             │             │ Date         │             │ │
│ ├─────────────┼─────────────┼─────────────┼──────────────┼─────────────┤ │
│ │ PRD-001     │ Widget A    │ [100    ]   │ [2024-02-15] │ [Edit][🗑️] │ │
│ │ Widgets     │ Standard    │             │              │             │ │
│ │             │ Widget      │             │              │             │ │
│ ├─────────────┼─────────────┼─────────────┼──────────────┼─────────────┤ │
│ │ + Add New Item                                                       │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Addresses Section

```jsx
┌─────────────────────────────────────────────────────────────────────────┐
│ SHIPPING & BILLING                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│ Shipping Address:           │ Billing Address:                          │
│ [Text area for address]     │ [Text area for address]                   │
│ [📋 Copy from Customer]      │ [📋 Copy from Customer] [📋 Same as Ship] │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Notes Section

```jsx
┌─────────────────────────────────────────────────────────────────────────┐
│ NOTES                                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ [Large text area for additional notes and instructions]                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## 4. Order Details View

### Layout

#### Header with Actions

```jsx
Order SO-2024-001 - ABC Corp
[Edit Order] [Duplicate] [Print] [Email Customer] [Change Status ▼]
```

#### Status Timeline

```jsx
Draft → Confirmed → In Production → Ready → Shipped → Delivered
  ✅      ✅         🔵 Current      ⭕      ⭕        ⭕
```

#### Order Information Cards

```jsx
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│ Order Details   │ Customer Info   │ Delivery Info   │ Salesperson     │
│ Order: SO-001   │ ABC Corp        │ Planned:        │ John Smith      │
│ Date: Jan 15    │ Contact: Jane   │ Feb 15, 2024    │ Sales Rep       │
│ PO#: PO-ABC-123 │ Phone: xxx-xxx  │ Status: On Time │ ext: 1234       │
│ Items: 5        │ Email: jane@... │ 📍 Shipping     │ 📧 Email        │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

#### Order Items Table

```jsx
ORDER ITEMS
┌─────────────┬──────────────────┬─────────────┬──────────────┬─────────────┐
│ Product     │ Description      │ Quantity    │ Delivery     │ Notes       │
│             │                  │ Ordered     │ Date         │             │
├─────────────┼──────────────────┼─────────────┼──────────────┼─────────────┤
│ PRD-001     │ Standard Widget  │ 100 units   │ Feb 15, 2024 │ Rush order  │
│ PRD-002     │ Premium Widget   │ 50 units    │ Feb 20, 2024 │             │
│ PRD-003     │ Widget Parts     │ 200 units   │ Feb 15, 2024 │ Spare parts │
└─────────────┴──────────────────┴─────────────┴──────────────┴─────────────┘
```

#### Activity Log

```jsx
ACTIVITY LOG
Jan 15, 10:30 AM - Order created by John Smith
Jan 15, 02:15 PM - Order confirmed by manager
Jan 16, 09:00 AM - Sent to production
Jan 18, 11:45 AM - Production started for PRD-001
```

## 5. Quotations Page

### Similar structure to Orders with key differences:

#### Additional filters for quotations

```jsx
Status: [All ▼] Valid Until: [This Week ▼]
```

#### Status tabs

```jsx
[All(89)][Draft(12)][Sent(34)][Accepted(25)][Rejected(8)][Expired(10)];
```

#### Additional columns in table

```jsx
│ Quote #     │ Customer     │ Quote Date   │ Valid Until │ Status      │ Actions        │
│ QU-2024-001 │ ABC Corp     │ 2024-01-10   │ 2024-02-10  │ ✅ Accepted │ [View][Convert]│
│ QU-2024-002 │ XYZ Ltd      │ 2024-01-08   │ 2024-01-22  │ 📤 Sent     │ [View][Follow] │
│ QU-2024-003 │ DEF Inc      │ 2024-01-05   │ 2024-01-20  │ ⏰ Expired  │ [View][Renew]  │
```

#### Quick Actions

```jsx
[Convert to Order] - for accepted quotations
[Send Reminder] - for sent quotations
[Mark as Expired] - for overdue quotations
```

## 6. Mobile-Responsive Design

### Mobile Layout Considerations

```jsx
// Stack cards vertically on mobile
// Collapsible sections
// Swipe actions for common tasks
// Bottom sheet for forms
// Floating action button for "Add New"
```

#### Mobile Order Card

```jsx
┌─────────────────────────────────┐
│ SO-2024-001 | 🟡 Confirmed      │
│ ABC Corp                        │
│ Due: Feb 15 (⚠️ 3 days)         │
│ 5 items | John Smith           │
│ [View Details] [Quick Actions]  │
└─────────────────────────────────┘
```

## 7. Key UI Components

### Status Indicators

```jsx
// Status badges with colors and icons
<StatusBadge status="confirmed" />
// → 🟡 Confirmed

// Progress indicators for order workflow
<OrderProgress currentStep="in_production" />
// → Draft ✅ Confirmed ✅ In Production 🔵 Ready ⭕ Shipped ⭕
```

### Smart Filters

```jsx
// Quick filter chips
[Today] [This Week] [Overdue] [My Orders] [VIP Customers]

// Advanced filter panel (collapsible)
Date Range: [Custom range picker]
Customer: [Multi-select dropdown]
Products: [Search and select]
Salesperson: [Multi-select]
```

### Bulk Actions

```jsx
// Checkbox selection with bulk operations
☑️ Select All (23 items selected)
[Change Status] [Send Email] [Export Selected] [Delete]
```

## 8. Integration Points

### Cross-Module Navigation

```jsx
// From order view, link to:
- Customer Details (Core module)
- Product Information (Inventory module)
- Work Orders (Manufacturing module)
- Delivery Schedule (Logistics)

// Example: Product link in order items
PRD-001 → [View in Inventory] [Check Stock] [View Specs]
```

## 9. Reporting Dashboard

### Visual charts and metrics

```jsx
📊 Orders by Status (Pie chart)
📈 Monthly Order Trends (Line chart)
📊 Top Customers (Bar chart)
📅 Delivery Performance (Timeline)

// Exportable reports
[📄 Order Summary] [📋 Customer Report] [📊 Performance Dashboard]
```

## 10. Technical Specifications

### API Endpoints

- `GET /api/sales/sales-orders/` - List all orders
- `POST /api/sales/sales-orders/` - Create new order
- `GET /api/sales/sales-orders/{id}/` - Get order details
- `PUT /api/sales/sales-orders/{id}/` - Update order
- `POST /api/sales/sales-orders/{id}/confirm/` - Confirm order
- `POST /api/sales/sales-orders/{id}/cancel/` - Cancel order
- `POST /api/sales/sales-orders/create_with_items/` - Create order with items

- `GET /api/sales/sales-quotations/` - List all quotations
- `POST /api/sales/sales-quotations/` - Create new quotation
- `GET /api/sales/sales-quotations/{id}/` - Get quotation details
- `PUT /api/sales/sales-quotations/{id}/` - Update quotation
- `POST /api/sales/sales-quotations/{id}/convert_to_order/` - Convert to order

## 11. API Documentation

### Sales Orders API

#### List Sales Orders

**GET** `/api/sales/sales-orders/`

**Query Parameters:**

```
?status=DRAFT&customer=1&salesperson=2&search=SO-2024&ordering=-order_date&page=1&page_size=20
```

**Response:**

```json
{
  "count": 156,
  "next": "http://localhost:8000/api/sales/sales-orders/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "order_number": "SO-2024-001",
      "customer": {
        "id": 1,
        "name": "ABC Corp",
        "code": "ABC001",
        "email": "contact@abccorp.com",
        "phone": "+1-555-0123",
        "address": "123 Business St, City, State 12345"
      },
      "customer_id": 1,
      "order_date": "2024-01-15",
      "delivery_date": "2024-02-15",
      "status": "CONFIRMED",
      "customer_po_number": "PO-ABC-123",
      "salesperson": {
        "id": 2,
        "username": "john.smith",
        "first_name": "John",
        "last_name": "Smith",
        "email": "john@company.com"
      },
      "shipping_address": "123 Business St, City, State 12345",
      "billing_address": "123 Business St, City, State 12345",
      "notes": "Rush order - customer needs by Feb 15",
      "is_overdue": false,
      "items": [
        {
          "id": 1,
          "sales_order": 1,
          "product": {
            "id": 1,
            "product_code": "PRD-001",
            "name": "Standard Widget",
            "description": "High quality standard widget",
            "product_type": "MONTAGED",
            "unit_of_measure": "PCS"
          },
          "product_id": 1,
          "quantity": 100,
          "delivery_date": "2024-02-15",
          "notes": "Standard specifications"
        }
      ],
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T14:15:00Z"
    }
  ]
}
```

#### Create Sales Order

**POST** `/api/sales/sales-orders/`

**Request Body:**

```json
{
  "order_number": "SO-2024-002",
  "customer_id": 1,
  "order_date": "2024-01-16",
  "delivery_date": "2024-02-20",
  "status": "DRAFT",
  "customer_po_number": "PO-ABC-124",
  "shipping_address": "456 Delivery Ave, City, State 12345",
  "billing_address": "123 Business St, City, State 12345",
  "notes": "Standard delivery terms"
}
```

**Response:** (201 Created)

```json
{
  "id": 2,
  "order_number": "SO-2024-002",
  "customer": {
    "id": 1,
    "name": "ABC Corp",
    "code": "ABC001",
    "email": "contact@abccorp.com",
    "phone": "+1-555-0123",
    "address": "123 Business St, City, State 12345"
  },
  "customer_id": 1,
  "order_date": "2024-01-16",
  "delivery_date": "2024-02-20",
  "status": "DRAFT",
  "customer_po_number": "PO-ABC-124",
  "salesperson": {
    "id": 2,
    "username": "john.smith",
    "first_name": "John",
    "last_name": "Smith",
    "email": "john@company.com"
  },
  "shipping_address": "456 Delivery Ave, City, State 12345",
  "billing_address": "123 Business St, City, State 12345",
  "notes": "Standard delivery terms",
  "is_overdue": false,
  "items": [],
  "created_at": "2024-01-16T09:15:00Z",
  "updated_at": "2024-01-16T09:15:00Z"
}
```

#### Get Sales Order Details

**GET** `/api/sales/sales-orders/{id}/`

**Response:**

```json
{
  "id": 1,
  "order_number": "SO-2024-001",
  "customer": {
    "id": 1,
    "name": "ABC Corp",
    "code": "ABC001",
    "email": "contact@abccorp.com",
    "phone": "+1-555-0123",
    "address": "123 Business St, City, State 12345"
  },
  "customer_id": 1,
  "order_date": "2024-01-15",
  "delivery_date": "2024-02-15",
  "status": "CONFIRMED",
  "customer_po_number": "PO-ABC-123",
  "salesperson": {
    "id": 2,
    "username": "john.smith",
    "first_name": "John",
    "last_name": "Smith",
    "email": "john@company.com"
  },
  "shipping_address": "123 Business St, City, State 12345",
  "billing_address": "123 Business St, City, State 12345",
  "notes": "Rush order - customer needs by Feb 15",
  "is_overdue": false,
  "items": [
    {
      "id": 1,
      "sales_order": 1,
      "product": {
        "id": 1,
        "product_code": "PRD-001",
        "name": "Standard Widget",
        "description": "High quality standard widget",
        "product_type": "MONTAGED",
        "unit_of_measure": "PCS"
      },
      "product_id": 1,
      "quantity": 100,
      "delivery_date": "2024-02-15",
      "notes": "Standard specifications"
    },
    {
      "id": 2,
      "sales_order": 1,
      "product": {
        "id": 2,
        "product_code": "PRD-002",
        "name": "Premium Widget",
        "description": "High-end premium widget",
        "product_type": "MONTAGED",
        "unit_of_measure": "PCS"
      },
      "product_id": 2,
      "quantity": 50,
      "delivery_date": "2024-02-20",
      "notes": "Premium grade"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T14:15:00Z"
}
```

#### Update Sales Order

**PUT** `/api/sales/sales-orders/{id}/`

**Request Body:**

```json
{
  "order_number": "SO-2024-001",
  "customer_id": 1,
  "order_date": "2024-01-15",
  "delivery_date": "2024-02-12",
  "status": "CONFIRMED",
  "customer_po_number": "PO-ABC-123-UPDATED",
  "shipping_address": "123 Business St, City, State 12345",
  "billing_address": "123 Business St, City, State 12345",
  "notes": "Updated: Rush order - customer needs by Feb 12"
}
```

**Response:** (200 OK)

```json
{
  "id": 1,
  "order_number": "SO-2024-001",
  "customer": {
    "id": 1,
    "name": "ABC Corp",
    "code": "ABC001",
    "email": "contact@abccorp.com",
    "phone": "+1-555-0123",
    "address": "123 Business St, City, State 12345"
  },
  "customer_id": 1,
  "order_date": "2024-01-15",
  "delivery_date": "2024-02-12",
  "status": "CONFIRMED",
  "customer_po_number": "PO-ABC-123-UPDATED",
  "salesperson": {
    "id": 2,
    "username": "john.smith",
    "first_name": "John",
    "last_name": "Smith",
    "email": "john@company.com"
  },
  "shipping_address": "123 Business St, City, State 12345",
  "billing_address": "123 Business St, City, State 12345",
  "notes": "Updated: Rush order - customer needs by Feb 12",
  "is_overdue": false,
  "items": [...],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-16T11:20:00Z"
}
```

#### Confirm Sales Order

**POST** `/api/sales/sales-orders/{id}/confirm/`

**Request Body:** (Empty)

```json
{}
```

**Response:** (200 OK)

```json
{
  "id": 1,
  "order_number": "SO-2024-001",
  "customer": {...},
  "status": "CONFIRMED",
  "...": "...(other fields remain same)"
}
```

**Error Response:** (400 Bad Request)

```json
{
  "error": "Only draft orders can be confirmed"
}
```

#### Cancel Sales Order

**POST** `/api/sales/sales-orders/{id}/cancel/`

**Request Body:** (Empty)

```json
{}
```

**Response:** (200 OK)

```json
{
  "id": 1,
  "order_number": "SO-2024-001",
  "customer": {...},
  "status": "CANCELLED",
  "...": "...(other fields remain same)"
}
```

**Error Response:** (400 Bad Request)

```json
{
  "error": "Cannot cancel delivered or already cancelled orders"
}
```

#### Create Order with Items

**POST** `/api/sales/sales-orders/create_with_items/`

**Request Body:**

```json
{
  "order_number": "SO-2024-003",
  "customer_id": 1,
  "order_date": "2024-01-17",
  "delivery_date": "2024-02-25",
  "status": "DRAFT",
  "customer_po_number": "PO-ABC-125",
  "shipping_address": "123 Business St, City, State 12345",
  "billing_address": "123 Business St, City, State 12345",
  "notes": "Bulk order with multiple items",
  "items": [
    {
      "product_id": 1,
      "quantity": 200,
      "delivery_date": "2024-02-25",
      "notes": "First batch"
    },
    {
      "product_id": 2,
      "quantity": 100,
      "delivery_date": "2024-02-28",
      "notes": "Second batch"
    }
  ]
}
```

**Response:** (201 Created)

```json
{
  "id": 3,
  "order_number": "SO-2024-003",
  "customer": {
    "id": 1,
    "name": "ABC Corp",
    "code": "ABC001",
    "email": "contact@abccorp.com",
    "phone": "+1-555-0123",
    "address": "123 Business St, City, State 12345"
  },
  "customer_id": 1,
  "order_date": "2024-01-17",
  "delivery_date": "2024-02-25",
  "status": "DRAFT",
  "customer_po_number": "PO-ABC-125",
  "salesperson": {
    "id": 2,
    "username": "john.smith",
    "first_name": "John",
    "last_name": "Smith",
    "email": "john@company.com"
  },
  "shipping_address": "123 Business St, City, State 12345",
  "billing_address": "123 Business St, City, State 12345",
  "notes": "Bulk order with multiple items",
  "is_overdue": false,
  "items": [
    {
      "id": 3,
      "sales_order": 3,
      "product": {
        "id": 1,
        "product_code": "PRD-001",
        "name": "Standard Widget",
        "description": "High quality standard widget",
        "product_type": "MONTAGED",
        "unit_of_measure": "PCS"
      },
      "product_id": 1,
      "quantity": 200,
      "delivery_date": "2024-02-25",
      "notes": "First batch"
    },
    {
      "id": 4,
      "sales_order": 3,
      "product": {
        "id": 2,
        "product_code": "PRD-002",
        "name": "Premium Widget",
        "description": "High-end premium widget",
        "product_type": "MONTAGED",
        "unit_of_measure": "PCS"
      },
      "product_id": 2,
      "quantity": 100,
      "delivery_date": "2024-02-28",
      "notes": "Second batch"
    }
  ],
  "created_at": "2024-01-17T08:45:00Z",
  "updated_at": "2024-01-17T08:45:00Z"
}
```

### Sales Quotations API

#### List Sales Quotations

**GET** `/api/sales/sales-quotations/`

**Query Parameters:**

```
?status=SENT&customer=1&salesperson=2&search=QU-2024&ordering=-quotation_date&page=1&page_size=20
```

**Response:**

```json
{
  "count": 89,
  "next": "http://localhost:8000/api/sales/sales-quotations/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "quotation_number": "QU-2024-001",
      "customer": {
        "id": 1,
        "name": "ABC Corp",
        "code": "ABC001",
        "email": "contact@abccorp.com",
        "phone": "+1-555-0123",
        "address": "123 Business St, City, State 12345"
      },
      "customer_id": 1,
      "quotation_date": "2024-01-10",
      "valid_until": "2024-02-10",
      "status": "SENT",
      "salesperson": {
        "id": 2,
        "username": "john.smith",
        "first_name": "John",
        "last_name": "Smith",
        "email": "john@company.com"
      },
      "notes": "Standard quotation for widget requirements",
      "converted_to_order": null,
      "is_expired": false,
      "items": [
        {
          "id": 1,
          "quotation": 1,
          "product": {
            "id": 1,
            "product_code": "PRD-001",
            "name": "Standard Widget",
            "description": "High quality standard widget",
            "product_type": "MONTAGED",
            "unit_of_measure": "PCS"
          },
          "product_id": 1,
          "quantity": 150,
          "notes": "Standard grade required"
        }
      ],
      "created_at": "2024-01-10T09:00:00Z",
      "updated_at": "2024-01-10T15:30:00Z"
    }
  ]
}
```

#### Create Sales Quotation

**POST** `/api/sales/sales-quotations/`

**Request Body:**

```json
{
  "quotation_number": "QU-2024-002",
  "customer_id": 2,
  "quotation_date": "2024-01-18",
  "valid_until": "2024-02-18",
  "status": "DRAFT",
  "notes": "Quotation for XYZ Ltd requirements"
}
```

**Response:** (201 Created)

```json
{
  "id": 2,
  "quotation_number": "QU-2024-002",
  "customer": {
    "id": 2,
    "name": "XYZ Ltd",
    "code": "XYZ001",
    "email": "orders@xyzltd.com",
    "phone": "+1-555-0456",
    "address": "456 Industrial Blvd, City, State 12345"
  },
  "customer_id": 2,
  "quotation_date": "2024-01-18",
  "valid_until": "2024-02-18",
  "status": "DRAFT",
  "salesperson": {
    "id": 2,
    "username": "john.smith",
    "first_name": "John",
    "last_name": "Smith",
    "email": "john@company.com"
  },
  "notes": "Quotation for XYZ Ltd requirements",
  "converted_to_order": null,
  "is_expired": false,
  "items": [],
  "created_at": "2024-01-18T11:20:00Z",
  "updated_at": "2024-01-18T11:20:00Z"
}
```

#### Get Quotation Details

**GET** `/api/sales/sales-quotations/{id}/`

**Response:**

```json
{
  "id": 1,
  "quotation_number": "QU-2024-001",
  "customer": {
    "id": 1,
    "name": "ABC Corp",
    "code": "ABC001",
    "email": "contact@abccorp.com",
    "phone": "+1-555-0123",
    "address": "123 Business St, City, State 12345"
  },
  "customer_id": 1,
  "quotation_date": "2024-01-10",
  "valid_until": "2024-02-10",
  "status": "ACCEPTED",
  "salesperson": {
    "id": 2,
    "username": "john.smith",
    "first_name": "John",
    "last_name": "Smith",
    "email": "john@company.com"
  },
  "notes": "Standard quotation for widget requirements",
  "converted_to_order": null,
  "is_expired": false,
  "items": [
    {
      "id": 1,
      "quotation": 1,
      "product": {
        "id": 1,
        "product_code": "PRD-001",
        "name": "Standard Widget",
        "description": "High quality standard widget",
        "product_type": "MONTAGED",
        "unit_of_measure": "PCS"
      },
      "product_id": 1,
      "quantity": 150,
      "notes": "Standard grade required"
    },
    {
      "id": 2,
      "quotation": 1,
      "product": {
        "id": 3,
        "product_code": "PRD-003",
        "name": "Widget Accessories",
        "description": "Accessory kit for widgets",
        "product_type": "RAW",
        "unit_of_measure": "SET"
      },
      "product_id": 3,
      "quantity": 25,
      "notes": "Accessory kit"
    }
  ],
  "created_at": "2024-01-10T09:00:00Z",
  "updated_at": "2024-01-12T14:20:00Z"
}
```

#### Update Quotation

**PUT** `/api/sales/sales-quotations/{id}/`

**Request Body:**

```json
{
  "quotation_number": "QU-2024-001",
  "customer_id": 1,
  "quotation_date": "2024-01-10",
  "valid_until": "2024-02-15",
  "status": "ACCEPTED",
  "notes": "Updated: Customer accepted quotation with extended validity"
}
```

**Response:** (200 OK)

```json
{
  "id": 1,
  "quotation_number": "QU-2024-001",
  "customer": {...},
  "quotation_date": "2024-01-10",
  "valid_until": "2024-02-15",
  "status": "ACCEPTED",
  "salesperson": {...},
  "notes": "Updated: Customer accepted quotation with extended validity",
  "converted_to_order": null,
  "is_expired": false,
  "items": [...],
  "created_at": "2024-01-10T09:00:00Z",
  "updated_at": "2024-01-18T16:45:00Z"
}
```

#### Convert Quotation to Order

**POST** `/api/sales/sales-quotations/{id}/convert_to_order/`

**Request Body:** (Empty)

```json
{}
```

**Response:** (201 Created)

```json
{
  "id": 4,
  "order_number": "SO-2024-004",
  "customer": {
    "id": 1,
    "name": "ABC Corp",
    "code": "ABC001",
    "email": "contact@abccorp.com",
    "phone": "+1-555-0123",
    "address": "123 Business St, City, State 12345"
  },
  "customer_id": 1,
  "order_date": "2024-01-18",
  "delivery_date": "2024-02-17",
  "status": "CONFIRMED",
  "customer_po_number": null,
  "salesperson": {
    "id": 2,
    "username": "john.smith",
    "first_name": "John",
    "last_name": "Smith",
    "email": "john@company.com"
  },
  "shipping_address": "123 Business St, City, State 12345",
  "billing_address": "123 Business St, City, State 12345",
  "notes": "Created from quotation QU-2024-001",
  "is_overdue": false,
  "items": [
    {
      "id": 5,
      "sales_order": 4,
      "product": {
        "id": 1,
        "product_code": "PRD-001",
        "name": "Standard Widget",
        "description": "High quality standard widget",
        "product_type": "MONTAGED",
        "unit_of_measure": "PCS"
      },
      "product_id": 1,
      "quantity": 150,
      "delivery_date": "2024-02-17",
      "notes": "Standard grade required"
    },
    {
      "id": 6,
      "sales_order": 4,
      "product": {
        "id": 3,
        "product_code": "PRD-003",
        "name": "Widget Accessories",
        "description": "Accessory kit for widgets",
        "product_type": "RAW",
        "unit_of_measure": "SET"
      },
      "product_id": 3,
      "quantity": 25,
      "delivery_date": "2024-02-17",
      "notes": "Accessory kit"
    }
  ],
  "created_at": "2024-01-18T17:30:00Z",
  "updated_at": "2024-01-18T17:30:00Z"
}
```

**Error Responses:**

```json
{
  "error": "Only accepted quotations can be converted to orders"
}
```

```json
{
  "error": "Quotation already converted to order"
}
```

### Sales Order Items API

#### Create Sales Order Item

**POST** `/api/sales/sales-order-items/`

**Request Body:**

```json
{
  "sales_order": 1,
  "product_id": 2,
  "quantity": 75,
  "delivery_date": "2024-02-18",
  "notes": "Additional item for existing order"
}
```

**Response:** (201 Created)

```json
{
  "id": 7,
  "sales_order": 1,
  "product": {
    "id": 2,
    "product_code": "PRD-002",
    "name": "Premium Widget",
    "description": "High-end premium widget",
    "product_type": "MONTAGED",
    "unit_of_measure": "PCS"
  },
  "product_id": 2,
  "quantity": 75,
  "delivery_date": "2024-02-18",
  "notes": "Additional item for existing order"
}
```

### Sales Quotation Items API

#### Create Sales Quotation Item

**POST** `/api/sales/sales-quotation-items/`

**Request Body:**

```json
{
  "quotation": 2,
  "product_id": 1,
  "quantity": 125,
  "notes": "Customer requirement for standard widgets"
}
```

**Response:** (201 Created)

```json
{
  "id": 3,
  "quotation": 2,
  "product": {
    "id": 1,
    "product_code": "PRD-001",
    "name": "Standard Widget",
    "description": "High quality standard widget",
    "product_type": "MONTAGED",
    "unit_of_measure": "PCS"
  },
  "product_id": 1,
  "quantity": 125,
  "notes": "Customer requirement for standard widgets"
}
```

### Error Responses

#### Validation Errors (400 Bad Request)

```json
{
  "customer_id": ["This field is required."],
  "delivery_date": ["Delivery date cannot be before order date."],
  "quantity": ["Quantity must be positive."]
}
```

#### Authentication Error (401 Unauthorized)

```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### Permission Error (403 Forbidden)

```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### Not Found Error (404 Not Found)

```json
{
  "detail": "Not found."
}
```

### Status Choices

#### Order Status

```json
[
  "DRAFT",
  "CONFIRMED",
  "IN_PRODUCTION",
  "READY",
  "SHIPPED",
  "DELIVERED",
  "CANCELLED"
]
```

#### Quotation Status

```json
["DRAFT", "SENT", "ACCEPTED", "REJECTED", "EXPIRED"]
```

## Design Principles

This frontend design emphasizes:

- **Efficiency**: Quick data entry and navigation
- **Clarity**: Clear status indicators and workflow visibility
- **Workflow Optimization**: Streamlined processes for sales teams
- **Professional Appearance**: Clean, modern ERP interface
- **Mobile Accessibility**: Responsive design for field sales
- **Integration**: Seamless navigation between related modules

The focus is on order tracking and logistics management without pricing complexity, providing a clean and efficient interface for sales operations.
