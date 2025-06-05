# Manufacturing API Examples and Dummy Data

## Table of Contents

1. [CRUD API Examples](#crud-api-examples)
2. [Dummy Data for Testing](#dummy-data-for-testing)
3. [API Response Examples](#api-response-examples)
4. [Error Handling Examples](#error-handling-examples)

## CRUD API Examples

### 1. BOM (Bill of Materials) Management

#### CREATE BOM Item

```http
POST /api/inventory/product-bom/
Content-Type: application/json
```

**Request:**

```json
{
  "parent_product_id": 15,
  "child_product_id": 23,
  "quantity": 2.5,
  "scrap_percentage": 5.0,
  "operation_sequence": 1,
  "notes": "Main structural component"
}
```

**Response (201 Created):**

```json
{
  "id": 45,
  "parent_product": {
    "id": 15,
    "stock_code": "ASM001",
    "product_name": "Main Assembly",
    "product_type": "MONTAGED"
  },
  "child_product": {
    "id": 23,
    "stock_code": "PRT001",
    "product_name": "Steel Bracket",
    "product_type": "SINGLE"
  },
  "quantity": "2.500",
  "scrap_percentage": "5.00",
  "operation_sequence": 1,
  "notes": "Main structural component",
  "unit_of_measure": "PCS",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### READ BOM Tree

```http
GET /api/manufacturing/products/15/bom-tree/
```

**Response (200 OK):**

```json
{
  "root_product": {
    "id": 15,
    "stock_code": "ASM001",
    "product_name": "Main Assembly",
    "product_type": "MONTAGED"
  },
  "items": [
    {
      "id": 45,
      "level": 1,
      "child_product": {
        "id": 23,
        "stock_code": "PRT001",
        "product_name": "Steel Bracket",
        "current_stock": 150
      },
      "quantity": "2.500",
      "scrap_percentage": "5.00",
      "total_quantity": "2.625",
      "children": []
    }
  ],
  "material_requirements": [
    {
      "product_id": 23,
      "stock_code": "PRT001",
      "total_required": "2.625",
      "available_stock": 150,
      "shortage": 0
    }
  ]
}
```

### 2. Work Order Management

#### CREATE Work Order

```http
POST /api/manufacturing/work-orders/create-from-sales-order/
Content-Type: application/json
```

**Request:**

```json
{
  "sales_order_item": 12,
  "planned_start_date": "2024-01-20T08:00:00Z",
  "priority": "HIGH",
  "notes": "Rush order for important customer"
}
```

**Response (201 Created):**

```json
{
  "id": 89,
  "work_order_number": "WO-2024-001234",
  "product": {
    "id": 15,
    "stock_code": "ASM001",
    "product_name": "Main Assembly"
  },
  "quantity_ordered": 10,
  "planned_start_date": "2024-01-20T08:00:00Z",
  "planned_end_date": "2024-01-25T17:00:00Z",
  "status": "PLANNED",
  "priority": "HIGH",
  "completion_percentage": 0,
  "is_overdue": false
}
```

#### READ Work Order Detail

```http
GET /api/manufacturing/work-orders/89/
```

**Response (200 OK):**

```json
{
  "id": 89,
  "work_order_number": "WO-2024-001234",
  "product": {
    "id": 15,
    "stock_code": "ASM001",
    "product_name": "Main Assembly"
  },
  "operations": [
    {
      "id": 156,
      "operation_sequence": 1,
      "operation_name": "CNC Machining",
      "machine": {
        "id": 5,
        "machine_code": "CNC001",
        "machine_type": "CNC_MILLING"
      },
      "setup_time_minutes": 120,
      "run_time_minutes": 2400,
      "status": "PLANNED"
    }
  ],
  "material_allocations": [
    {
      "id": 234,
      "material": {
        "id": 23,
        "stock_code": "PRT001",
        "product_name": "Steel Bracket"
      },
      "required_quantity": "26.250",
      "allocated_quantity": "26.250",
      "is_allocated": true
    }
  ]
}
```

### 3. Process Configuration Management

#### CREATE Process Config

```http
POST /api/manufacturing/process-configs/
Content-Type: application/json
```

**Request:**

```json
{
  "workflow": 78,
  "process": 12,
  "sequence_order": 1,
  "machine_type": "CNC_MILLING",
  "setup_time": 120,
  "cycle_time": 300,
  "connecting_count": 15
}
```

**Response (201 Created):**

```json
{
  "id": 234,
  "workflow": 78,
  "process_name": "CNC Milling Operation",
  "sequence_order": 1,
  "machine_type": "CNC_MILLING",
  "setup_time": 120,
  "cycle_time": 300,
  "status": "ACTIVE"
}
```

## Dummy Data for Testing

### Products Data

```json
{
  "products": [
    {
      "id": 15,
      "stock_code": "ASM001",
      "product_name": "Main Assembly",
      "product_type": "MONTAGED",
      "current_stock": 50,
      "unit_of_measure": "PCS",
      "inventory_category": "MAMUL"
    },
    {
      "id": 23,
      "stock_code": "PRT001",
      "product_name": "Steel Bracket",
      "product_type": "SINGLE",
      "current_stock": 150,
      "unit_of_measure": "PCS",
      "inventory_category": "MAMUL"
    },
    {
      "id": 24,
      "stock_code": "SUB001",
      "product_name": "Motor Sub-Assembly",
      "product_type": "SEMI",
      "current_stock": 25,
      "unit_of_measure": "PCS",
      "inventory_category": "MAMUL"
    }
  ]
}
```

### Machines Data

```json
{
  "machines": [
    {
      "id": 5,
      "machine_code": "CNC001",
      "machine_type": "CNC_MILLING",
      "brand": "Haas",
      "model": "VF-2",
      "axis_count": "AXIS_3",
      "spindle_speed_rpm": 8000,
      "tool_count": 20,
      "status": "AVAILABLE",
      "manufacturing_year": "2020-01-01",
      "serial_number": "VF2-2020-0123"
    },
    {
      "id": 6,
      "machine_code": "CNC002",
      "machine_type": "CNC_LATHE",
      "brand": "Mazak",
      "model": "QT-200",
      "axis_count": "AXIS_2",
      "spindle_speed_rpm": 4000,
      "tool_count": 12,
      "status": "IN_USE",
      "manufacturing_year": "2019-01-01",
      "serial_number": "QT200-2019-0089"
    }
  ]
}
```

### BOM Data

```json
{
  "bom_items": [
    {
      "id": 45,
      "parent_product_id": 15,
      "child_product_id": 23,
      "quantity": 2.5,
      "scrap_percentage": 5.0,
      "operation_sequence": 1,
      "notes": "Main structural component"
    },
    {
      "id": 46,
      "parent_product_id": 15,
      "child_product_id": 24,
      "quantity": 1.0,
      "scrap_percentage": 2.0,
      "operation_sequence": 2,
      "notes": "Motor assembly component"
    }
  ]
}
```

### Work Orders Data

```json
{
  "work_orders": [
    {
      "id": 89,
      "work_order_number": "WO-2024-001234",
      "product_id": 15,
      "quantity_ordered": 10,
      "planned_start_date": "2024-01-20T08:00:00Z",
      "planned_end_date": "2024-01-25T17:00:00Z",
      "status": "PLANNED",
      "priority": "HIGH",
      "sales_order": 8
    },
    {
      "id": 90,
      "work_order_number": "WO-2024-001235",
      "product_id": 23,
      "quantity_ordered": 50,
      "planned_start_date": "2024-01-18T08:00:00Z",
      "planned_end_date": "2024-01-20T17:00:00Z",
      "status": "IN_PROGRESS",
      "priority": "MEDIUM",
      "sales_order": 9
    }
  ]
}
```

### Sales Orders Data

```json
{
  "sales_orders": [
    {
      "id": 8,
      "order_number": "SO-2024-0056",
      "customer_id": 12,
      "items": [
        {
          "id": 12,
          "product_id": 15,
          "quantity": 10,
          "delivery_date": "2024-01-30T00:00:00Z",
          "status": "CONFIRMED"
        }
      ]
    }
  ]
}
```

### Process Configurations Data

```json
{
  "workflows": [
    {
      "id": 78,
      "product_id": 15,
      "version": "2.0",
      "status": "ACTIVE",
      "effective_date": "2024-02-01"
    }
  ],
  "process_configs": [
    {
      "id": 234,
      "workflow_id": 78,
      "process_id": 12,
      "sequence_order": 1,
      "machine_type": "CNC_MILLING",
      "setup_time": 120,
      "cycle_time": 300,
      "connecting_count": 15,
      "tool_id": 145,
      "fixture_id": 23
    },
    {
      "id": 235,
      "workflow_id": 78,
      "process_id": 13,
      "sequence_order": 2,
      "machine_type": "ASSEMBLY",
      "setup_time": 60,
      "cycle_time": 180,
      "connecting_count": 10
    }
  ]
}
```

## Error Handling Examples

### Validation Error (400 Bad Request)

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "quantity": ["This field must be greater than 0"],
      "parent_product_id": ["Product with this ID does not exist"]
    }
  }
}
```

### Business Rule Violation (422 Unprocessable Entity)

```json
{
  "success": false,
  "error": {
    "code": "BUSINESS_RULE_VIOLATION",
    "message": "Work order cannot be started in current status",
    "details": {
      "current_status": "DRAFT",
      "required_status": "RELEASED",
      "work_order_id": 89
    }
  }
}
```

### Resource Not Found (404 Not Found)

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Work order not found",
    "details": {
      "resource_type": "WorkOrder",
      "resource_id": 999
    }
  }
}
```

## SQL Insert Scripts for Dummy Data

### Insert Products

```sql
INSERT INTO products (id, stock_code, product_name, product_type, current_stock, unit_of_measure_id, inventory_category_id, is_active, created_at, modified_at) VALUES
(15, 'ASM001', 'Main Assembly', 'MONTAGED', 50, 1, 1, true, NOW(), NOW()),
(23, 'PRT001', 'Steel Bracket', 'SINGLE', 150, 1, 1, true, NOW(), NOW()),
(24, 'SUB001', 'Motor Sub-Assembly', 'SEMI', 25, 1, 1, true, NOW(), NOW()),
(25, 'MOT001', 'Electric Motor', 'STANDARD_PART', 30, 1, 1, true, NOW(), NOW());
```

### Insert Machines

```sql
INSERT INTO machines (id, machine_code, machine_type, brand, model, axis_count, spindle_speed_rpm, tool_count, status, manufacturing_year, serial_number, is_active, maintenance_interval, created_at, updated_at) VALUES
(5, 'CNC001', 'CNC_MILLING', 'Haas', 'VF-2', 'AXIS_3', 8000, 20, 'AVAILABLE', '2020-01-01', 'VF2-2020-0123', true, 90, NOW(), NOW()),
(6, 'CNC002', 'CNC_LATHE', 'Mazak', 'QT-200', 'AXIS_2', 4000, 12, 'AVAILABLE', '2019-01-01', 'QT200-2019-0089', true, 90, NOW(), NOW()),
(7, 'MILL001', 'DRILLING', 'Bridgeport', 'Series-1', 'AXIS_3', 3000, 1, 'AVAILABLE', '2018-01-01', 'BP-2018-0045', true, 60, NOW(), NOW());
```

### Insert BOM Items

```sql
INSERT INTO product_bom (id, parent_product_id, child_product_id, quantity, scrap_percentage, operation_sequence, notes, created_at, updated_at) VALUES
(45, 15, 23, 2.500, 5.00, 1, 'Main structural component', NOW(), NOW()),
(46, 15, 24, 1.000, 2.00, 2, 'Motor assembly component', NOW(), NOW()),
(47, 24, 25, 1.000, 0.00, 1, 'Electric motor for sub-assembly', NOW(), NOW());
```

### Insert Work Orders

```sql
INSERT INTO work_orders (id, work_order_number, product_id, quantity_ordered, planned_start_date, planned_end_date, status, priority, sales_order_id, created_at, updated_at) VALUES
(89, 'WO-2024-001234', 15, 10, '2024-01-20 08:00:00', '2024-01-25 17:00:00', 'PLANNED', 'HIGH', 8, NOW(), NOW()),
(90, 'WO-2024-001235', 23, 50, '2024-01-18 08:00:00', '2024-01-20 17:00:00', 'IN_PROGRESS', 'MEDIUM', 9, NOW(), NOW());
```

### Insert Manufacturing Processes

```sql
INSERT INTO manufacturing_process (id, process_code, name, machine_type, standard_setup_time, standard_runtime, created_at, updated_at) VALUES
(12, 'MILL001', 'CNC Milling Operation', 'CNC_MILLING', 120, 15, NOW(), NOW()),
(13, 'ASM001', 'Assembly Process', 'ASSEMBLY', 60, 10, NOW(), NOW()),
(14, 'INSP001', 'Quality Inspection', 'INSPECTION', 30, 5, NOW(), NOW());
```

### Insert Product Workflows

```sql
INSERT INTO product_workflow (id, product_id, version, status, effective_date, created_at, updated_at) VALUES
(78, 15, '2.0', 'ACTIVE', '2024-02-01', NOW(), NOW()),
(79, 23, '1.0', 'ACTIVE', '2024-01-01', NOW(), NOW());
```

### Insert Process Configurations

```sql
INSERT INTO process_config (id, workflow_id, process_id, sequence_order, version, status, machine_type, axis_count, setup_time, cycle_time, connecting_count, created_at, updated_at) VALUES
(234, 78, 12, 1, '1.0', 'ACTIVE', 'CNC_MILLING', 'AXIS_3', 120, 300, 15, NOW(), NOW()),
(235, 78, 13, 2, '1.0', 'ACTIVE', 'ASSEMBLY', NULL, 60, 180, 10, NOW(), NOW()),
(236, 78, 14, 3, '1.0', 'ACTIVE', 'INSPECTION', NULL, 30, 120, 5, NOW(), NOW());
```

## Frontend Integration Examples

### React Hook for BOM Management

```typescript
const useBOM = (productId: string) => {
  const [bomTree, setBomTree] = useState<BOMTree | null>(null);
  const [loading, setLoading] = useState(false);

  const loadBOMTree = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/manufacturing/products/${productId}/bom-tree/`
      );
      const data = await response.json();
      setBomTree(data);
    } catch (error) {
      console.error("Failed to load BOM tree:", error);
    } finally {
      setLoading(false);
    }
  };

  const addBOMItem = async (bomItem: CreateBOMItemRequest) => {
    const response = await fetch("/api/inventory/product-bom/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(bomItem),
    });

    if (response.ok) {
      loadBOMTree(); // Refresh the tree
    }
  };

  return { bomTree, loading, loadBOMTree, addBOMItem };
};
```

### API Service Class

```typescript
class ManufacturingAPI {
  private baseURL = "/api/manufacturing";

  async createWorkOrder(data: CreateWorkOrderRequest): Promise<WorkOrder> {
    const response = await fetch(
      `${this.baseURL}/work-orders/create-from-sales-order/`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getWorkOrders(filters?: WorkOrderFilters): Promise<WorkOrderList> {
    const params = new URLSearchParams(filters as any);
    const response = await fetch(`${this.baseURL}/work-orders/?${params}`);
    return response.json();
  }
}
```

This comprehensive guide provides complete CRUD examples, dummy data, and integration patterns for your manufacturing system frontend implementation.
