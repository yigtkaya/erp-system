# Frontend Implementation Guide - Inventory Module

## Overview

This guide provides comprehensive instructions for implementing the frontend interface for the ERP Inventory Module. The module manages products, raw materials, tools, holders, fixtures, and control gauges with full CRUD operations, search, filtering, and pagination.

## API Base URL

```
/api/inventory/
```

## Authentication

All API endpoints require authentication. Include the JWT token in the Authorization header:

```javascript
const headers = {
  Authorization: `Bearer ${token}`,
  "Content-Type": "application/json",
};
```

## Core Entities

### 1. Products

**Endpoint**: `/api/inventory/products/`

#### Product Data Structure

```typescript
interface Product {
  id: string;
  stock_code: string;
  product_name: string;
  project_name?: string;
  product_type: "MONTAGED" | "SEMI" | "SINGLE" | "STANDARD_PART";
  multicode?: number;
  description?: string;
  current_stock: number;
  reserved_stock: number;
  available_stock: number; // calculated field
  unit_of_measure: string;
  unit_of_measure_name: string;
  customer?: string;
  inventory_category: string;
  inventory_category_name: string;
  is_active: boolean;
  tags?: string[];
  reorder_point?: number;
  lead_time_days?: number;
  current_technical_drawing?: TechnicalDrawing;
  transactions: StockTransaction[];
  created_at: string;
  modified_at: string;
}

interface TechnicalDrawing {
  id: string;
  version: string;
  drawing_code: string;
  effective_date: string;
  is_current: boolean;
  revision_notes?: string;
  approved_by_username?: string;
  approved_at?: string;
  drawing_url?: string;
  created_at: string;
  modified_at: string;
}

interface StockTransaction {
  id: string;
  transaction_date: string;
  transaction_type: string;
  transaction_type_display: string;
  quantity: number;
  unit_cost?: number;
  category_name: string;
  location?: string;
  batch_number?: string;
  reference?: string;
  notes?: string;
  created_by_username?: string;
  created_at: string;
}
```

#### Product API Operations

```javascript
// Get all products with pagination and filtering
const getProducts = async (params = {}) => {
  const queryString = new URLSearchParams({
    page: params.page || 1,
    page_size: params.pageSize || 25,
    ...(params.search && { search: params.search }),
    ...(params.product_type && { product_type: params.product_type }),
    ...(params.inventory_category__name && {
      inventory_category__name: params.inventory_category__name,
    }),
    ...(params.is_active !== undefined && { is_active: params.is_active }),
    ...(params.ordering && { ordering: params.ordering }),
  });

  const response = await fetch(`/api/inventory/products/?${queryString}`, {
    headers,
  });
  return response.json();
};

// Get single product
const getProduct = async (id) => {
  const response = await fetch(`/api/inventory/products/${id}/`, {
    headers,
  });
  return response.json();
};

// Create product
const createProduct = async (productData) => {
  const response = await fetch("/api/inventory/products/", {
    method: "POST",
    headers,
    body: JSON.stringify(productData),
  });
  return response.json();
};

// Update product
const updateProduct = async (id, productData) => {
  const response = await fetch(`/api/inventory/products/${id}/`, {
    method: "PUT",
    headers,
    body: JSON.stringify(productData),
  });
  return response.json();
};

// Delete product
const deleteProduct = async (id) => {
  const response = await fetch(`/api/inventory/products/${id}/`, {
    method: "DELETE",
    headers,
  });
  return response.ok;
};

// Get product stock history
const getProductStockHistory = async (id) => {
  const response = await fetch(`/api/inventory/products/${id}/stock_history/`, {
    headers,
  });
  return response.json();
};
```

### 2. Raw Materials

**Endpoint**: `/api/inventory/raw-materials/`

#### Raw Material Data Structure

```typescript
interface RawMaterial {
  id: string;
  stock_code: string;
  material_name: string;
  current_stock: number;
  reserved_stock: number;
  available_stock: number; // calculated field
  unit: string;
  unit_name: string;
  inventory_category?: string;
  category_name?: string;
  material_type:
    | "STEEL"
    | "ALUMINUM"
    | "STAINLESS"
    | "BRASS"
    | "COPPER"
    | "PLASTIC"
    | "OTHER";

  // Specifications
  width?: number;
  height?: number;
  thickness?: number;
  diameter_mm?: number;
  weight_per_unit?: number;

  // Inventory management
  reorder_point?: number;
  lead_time_days?: number;

  // Additional info
  description?: string;
  is_active: boolean;
  tags?: string[];
  created_at: string;
  modified_at: string;
}
```

#### Raw Material API Operations

```javascript
// Similar structure to products but for raw materials
const getRawMaterials = async (params = {}) => {
  const queryString = new URLSearchParams({
    page: params.page || 1,
    page_size: params.pageSize || 25,
    ...(params.search && { search: params.search }),
    ...(params.material_type && { material_type: params.material_type }),
    ...(params.inventory_category__name && {
      inventory_category__name: params.inventory_category__name,
    }),
    ...(params.is_active !== undefined && { is_active: params.is_active }),
    ...(params.ordering && { ordering: params.ordering }),
  });

  const response = await fetch(`/api/inventory/raw-materials/?${queryString}`, {
    headers,
  });
  return response.json();
};

// Create raw material with image upload
const createRawMaterial = async (materialData, imageFile = null) => {
  const formData = new FormData();

  // Add all material data
  Object.keys(materialData).forEach((key) => {
    if (materialData[key] !== null && materialData[key] !== undefined) {
      formData.append(key, materialData[key]);
    }
  });

  // Add image if provided
  if (imageFile) {
    formData.append("technical_image", imageFile);
  }

  const response = await fetch("/api/inventory/raw-materials/", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      // Don't set Content-Type for FormData
    },
    body: formData,
  });
  return response.json();
};
```

### 3. Tools

**Endpoint**: `/api/inventory/tools/`

#### Tool Data Structure

```typescript
interface Tool {
  id: string;
  stock_code: string;
  supplier_name: string;
  product_code: string;
  unit_price_tl: number;
  unit_price_euro: number;
  unit_price_usd: number;
  tool_insert_code: string;
  tool_material: string;
  tool_diameter: number;
  tool_length: number;
  tool_width: number;
  tool_height: number;
  tool_angle: number;
  tool_radius: number;
  tool_connection_diameter: number;
  tool_type: string;
  status: "AVAILABLE" | "IN_USE" | "MAINTENANCE" | "BROKEN" | "RETIRED";
  row: number;
  column: number;
  table_id: string;
  description?: string;
  quantity: number;
  created_at: string;
  modified_at: string;
}
```

### 4. Tool Usage

**Endpoint**: `/api/inventory/tool-usages/`

#### Tool Usage Data Structure

```typescript
interface ToolUsage {
  id: string;
  tool: string;
  tool_stock_code: string;
  issued_date: string;
  returned_date?: string;
  issued_by?: string;
  issued_by_username?: string;
  returned_to?: string;
  returned_to_username?: string;
  usage_count: number;
  condition_before: "NEW" | "GOOD" | "FAIR" | "POOR" | "BROKEN";
  condition_after?: "NEW" | "GOOD" | "FAIR" | "POOR" | "BROKEN";
  notes?: string;
  created_at: string;
  modified_at: string;
}
```

### 5. Holders

**Endpoint**: `/api/inventory/holders/`

#### Holder Data Structure

```typescript
interface Holder {
  id: string;
  stock_code: string;
  supplier_name: string;
  product_code: string;
  unit_price_tl: number;
  unit_price_euro: number;
  unit_price_usd: number;
  holder_type: string;
  pulley_type: string;
  water_cooling: boolean;
  distance_cooling: boolean;
  tool_connection_diameter: number;
  holder_type_enum: string;
  status: "AVAILABLE" | "IN_USE" | "MAINTENANCE" | "BROKEN" | "RETIRED";
  row: number;
  column: number;
  table_id: string;
  description?: string;
  quantity: number;
  created_at: string;
  modified_at: string;
}
```

### 6. Fixtures

**Endpoint**: `/api/inventory/fixtures/`

#### Fixture Data Structure

```typescript
interface Fixture {
  id: string;
  code: string;
  name?: string;
  status: "ACTIVE" | "INACTIVE";
  created_at: string;
  modified_at: string;
}
```

### 7. Control Gauges

**Endpoint**: `/api/inventory/control-gauges/`

#### Control Gauge Data Structure

```typescript
interface ControlGauge {
  id: string;
  stock_code: string;
  stock_name: string;
  stock_type?: string;
  serial_number?: string;
  brand?: string;
  model?: string;
  measuring_range?: string;
  resolution?: string;
  calibration_made_by?: string;
  calibration_date?: string;
  calibration_per_year: string;
  upcoming_calibration_date?: string;
  certificate_no?: string;
  status:
    | "UYGUN"
    | "KULLANILMIYOR"
    | "HURDA"
    | "KAYIP"
    | "BAKIMDA"
    | "KALIBRASYONDA";
  current_location?: string;
  scrap_lost_date?: string;
  description?: string;
  created_at: string;
  modified_at: string;
}
```

## Frontend Implementation Examples

### React Component Examples

#### Product List Component

```jsx
import React, { useState, useEffect } from "react";

const ProductList = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 25,
    total: 0,
  });
  const [filters, setFilters] = useState({
    search: "",
    product_type: "",
    inventory_category__name: "",
    is_active: true,
    ordering: "stock_code",
  });

  useEffect(() => {
    fetchProducts();
  }, [pagination.page, filters]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const params = {
        page: pagination.page,
        page_size: pagination.pageSize,
        ...filters,
      };

      const data = await getProducts(params);
      setProducts(data.results);
      setPagination((prev) => ({
        ...prev,
        total: data.count,
      }));
    } catch (error) {
      console.error("Error fetching products:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPagination((prev) => ({ ...prev, page: 1 })); // Reset to first page
  };

  const handlePageChange = (newPage) => {
    setPagination((prev) => ({ ...prev, page: newPage }));
  };

  return (
    <div className="product-list">
      {/* Search and Filters */}
      <div className="filters">
        <input
          type="text"
          placeholder="Search products..."
          value={filters.search}
          onChange={(e) => handleFilterChange("search", e.target.value)}
        />

        <select
          value={filters.product_type}
          onChange={(e) => handleFilterChange("product_type", e.target.value)}
        >
          <option value="">All Product Types</option>
          <option value="MONTAGED">Montaged</option>
          <option value="SEMI">Semi</option>
          <option value="SINGLE">Single</option>
          <option value="STANDARD_PART">Standard Part</option>
        </select>

        <select
          value={filters.ordering}
          onChange={(e) => handleFilterChange("ordering", e.target.value)}
        >
          <option value="stock_code">Stock Code</option>
          <option value="product_name">Product Name</option>
          <option value="current_stock">Current Stock</option>
          <option value="-created_at">Newest First</option>
        </select>
      </div>

      {/* Product Table */}
      <div className="product-table">
        {loading ? (
          <div>Loading...</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Stock Code</th>
                <th>Product Name</th>
                <th>Type</th>
                <th>Current Stock</th>
                <th>Available Stock</th>
                <th>Category</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <ProductRow key={product.id} product={product} />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      <Pagination
        current={pagination.page}
        total={pagination.total}
        pageSize={pagination.pageSize}
        onChange={handlePageChange}
      />
    </div>
  );
};

const ProductRow = ({ product }) => {
  const getStockStatus = (product) => {
    if (product.available_stock <= 0) return "out-of-stock";
    if (
      product.reorder_point &&
      product.available_stock <= product.reorder_point
    ) {
      return "low-stock";
    }
    return "in-stock";
  };

  return (
    <tr className={`stock-${getStockStatus(product)}`}>
      <td>{product.stock_code}</td>
      <td>{product.product_name}</td>
      <td>{product.product_type}</td>
      <td>{product.current_stock}</td>
      <td>{product.available_stock}</td>
      <td>{product.inventory_category_name}</td>
      <td>
        <span className={`status ${product.is_active ? "active" : "inactive"}`}>
          {product.is_active ? "Active" : "Inactive"}
        </span>
      </td>
      <td>
        <button onClick={() => viewProduct(product.id)}>View</button>
        <button onClick={() => editProduct(product.id)}>Edit</button>
        <button onClick={() => viewStockHistory(product.id)}>History</button>
      </td>
    </tr>
  );
};
```

#### Product Form Component

```jsx
import React, { useState, useEffect } from "react";

const ProductForm = ({ productId = null, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    stock_code: "",
    product_name: "",
    project_name: "",
    product_type: "SINGLE",
    description: "",
    unit_of_measure: "",
    customer: "",
    inventory_category: "",
    reorder_point: "",
    lead_time_days: "",
    is_active: true,
    tags: [],
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (productId) {
      fetchProduct();
    }
  }, [productId]);

  const fetchProduct = async () => {
    try {
      const product = await getProduct(productId);
      setFormData(product);
    } catch (error) {
      console.error("Error fetching product:", error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    try {
      let result;
      if (productId) {
        result = await updateProduct(productId, formData);
      } else {
        result = await createProduct(formData);
      }

      onSave(result);
    } catch (error) {
      if (error.response?.data) {
        setErrors(error.response.data);
      }
      console.error("Error saving product:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: null }));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="product-form">
      <div className="form-group">
        <label>Stock Code *</label>
        <input
          type="text"
          value={formData.stock_code}
          onChange={(e) => handleChange("stock_code", e.target.value)}
          className={errors.stock_code ? "error" : ""}
          required
        />
        {errors.stock_code && (
          <span className="error-text">{errors.stock_code}</span>
        )}
      </div>

      <div className="form-group">
        <label>Product Name *</label>
        <input
          type="text"
          value={formData.product_name}
          onChange={(e) => handleChange("product_name", e.target.value)}
          className={errors.product_name ? "error" : ""}
          required
        />
        {errors.product_name && (
          <span className="error-text">{errors.product_name}</span>
        )}
      </div>

      <div className="form-group">
        <label>Product Type *</label>
        <select
          value={formData.product_type}
          onChange={(e) => handleChange("product_type", e.target.value)}
          required
        >
          <option value="MONTAGED">Montaged</option>
          <option value="SEMI">Semi</option>
          <option value="SINGLE">Single</option>
          <option value="STANDARD_PART">Standard Part</option>
        </select>
      </div>

      <div className="form-group">
        <label>Project Name</label>
        <input
          type="text"
          value={formData.project_name}
          onChange={(e) => handleChange("project_name", e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Description</label>
        <textarea
          value={formData.description}
          onChange={(e) => handleChange("description", e.target.value)}
          rows="3"
        />
      </div>

      <div className="form-group">
        <label>Reorder Point</label>
        <input
          type="number"
          step="0.01"
          min="0"
          value={formData.reorder_point}
          onChange={(e) => handleChange("reorder_point", e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Lead Time (Days)</label>
        <input
          type="number"
          min="0"
          value={formData.lead_time_days}
          onChange={(e) => handleChange("lead_time_days", e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>
          <input
            type="checkbox"
            checked={formData.is_active}
            onChange={(e) => handleChange("is_active", e.target.checked)}
          />
          Active
        </label>
      </div>

      <div className="form-actions">
        <button type="button" onClick={onCancel} disabled={loading}>
          Cancel
        </button>
        <button type="submit" disabled={loading}>
          {loading ? "Saving..." : productId ? "Update" : "Create"}
        </button>
      </div>
    </form>
  );
};
```

### Stock History Component

```jsx
const StockHistory = ({ productId, rawMaterialId }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchHistory();
  }, [productId, rawMaterialId]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      let data;
      if (productId) {
        data = await getProductStockHistory(productId);
      } else if (rawMaterialId) {
        data = await getRawMaterialStockHistory(rawMaterialId);
      }
      setHistory(data);
    } catch (error) {
      console.error("Error fetching stock history:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading history...</div>;

  return (
    <div className="stock-history">
      <h3>Stock Transaction History</h3>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Type</th>
            <th>Quantity</th>
            <th>Category</th>
            <th>Reference</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          {history.map((transaction, index) => (
            <tr key={index}>
              <td>{new Date(transaction.date).toLocaleDateString()}</td>
              <td>{transaction.type}</td>
              <td
                className={transaction.quantity >= 0 ? "positive" : "negative"}
              >
                {transaction.quantity}
              </td>
              <td>{transaction.category}</td>
              <td>{transaction.reference}</td>
              <td>{transaction.notes}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

## CSS Styling Guidelines

### Stock Status Colors

```css
.stock-in-stock {
  background-color: #f0f9ff;
}

.stock-low-stock {
  background-color: #fef3c7;
}

.stock-out-of-stock {
  background-color: #fee2e2;
}

.status.active {
  color: #10b981;
  font-weight: bold;
}

.status.inactive {
  color: #ef4444;
  font-weight: bold;
}

.quantity.positive {
  color: #10b981;
}

.quantity.negative {
  color: #ef4444;
}
```

## Error Handling

### API Error Handling

```javascript
const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;

    switch (status) {
      case 400:
        // Validation errors
        return { type: "validation", errors: data };
      case 401:
        // Unauthorized - redirect to login
        window.location.href = "/login";
        return { type: "auth", message: "Session expired" };
      case 403:
        // Forbidden
        return { type: "permission", message: "Access denied" };
      case 404:
        // Not found
        return { type: "notfound", message: "Resource not found" };
      case 500:
        // Server error
        return { type: "server", message: "Server error occurred" };
      default:
        return { type: "unknown", message: "An error occurred" };
    }
  } else if (error.request) {
    // Network error
    return { type: "network", message: "Network error" };
  } else {
    // Other error
    return { type: "unknown", message: error.message };
  }
};
```

## Validation Rules

### Frontend Validation

```javascript
const validateProduct = (formData) => {
  const errors = {};

  if (!formData.stock_code) {
    errors.stock_code = "Stock code is required";
  } else if (formData.stock_code.length < 3) {
    errors.stock_code = "Stock code must be at least 3 characters";
  } else if (!/^[A-Za-z0-9\-\.]+$/.test(formData.stock_code)) {
    errors.stock_code =
      "Stock code can only contain letters, numbers, hyphens, and periods";
  }

  if (!formData.product_name) {
    errors.product_name = "Product name is required";
  }

  if (!formData.product_type) {
    errors.product_type = "Product type is required";
  }

  if (formData.reorder_point && formData.reorder_point < 0) {
    errors.reorder_point = "Reorder point must be positive";
  }

  if (formData.lead_time_days && formData.lead_time_days < 0) {
    errors.lead_time_days = "Lead time must be positive";
  }

  return errors;
};
```

## Performance Optimization

### Debounced Search

```javascript
import { useMemo } from "react";
import { debounce } from "lodash";

const useDebounceSearch = (searchTerm, delay = 300) => {
  const debouncedSearch = useMemo(
    () =>
      debounce((term) => {
        // Perform search
        fetchData({ search: term });
      }, delay),
    [delay]
  );

  useEffect(() => {
    debouncedSearch(searchTerm);
    return () => {
      debouncedSearch.cancel();
    };
  }, [searchTerm, debouncedSearch]);
};
```

### Virtual Scrolling for Large Lists

For handling large datasets, consider implementing virtual scrolling:

```javascript
import { FixedSizeList as List } from "react-window";

const VirtualizedProductList = ({ products }) => {
  const Row = ({ index, style }) => (
    <div style={style}>
      <ProductRow product={products[index]} />
    </div>
  );

  return (
    <List height={600} itemCount={products.length} itemSize={50} width="100%">
      {Row}
    </List>
  );
};
```

## Testing Examples

### Unit Tests

```javascript
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ProductList from "./ProductList";

describe("ProductList", () => {
  beforeEach(() => {
    // Mock API calls
    global.fetch = jest.fn();
  });

  test("renders product list", async () => {
    const mockProducts = {
      results: [
        {
          id: "1",
          stock_code: "P001",
          product_name: "Test Product",
          product_type: "SINGLE",
          current_stock: 100,
          available_stock: 90,
          is_active: true,
        },
      ],
      count: 1,
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockProducts,
    });

    render(<ProductList />);

    await waitFor(() => {
      expect(screen.getByText("Test Product")).toBeInTheDocument();
    });
  });

  test("filters products by search term", async () => {
    // Test search functionality
    render(<ProductList />);

    const searchInput = screen.getByPlaceholderText("Search products...");
    fireEvent.change(searchInput, { target: { value: "test" } });

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("search=test"),
        expect.any(Object)
      );
    });
  });
});
```

## Deployment Notes

1. **Environment Variables**: Ensure API base URL is configurable
2. **CORS**: Backend must allow frontend domain
3. **Authentication**: Implement token refresh logic
4. **Error Boundaries**: Wrap components in error boundaries
5. **Loading States**: Always show loading indicators for async operations
6. **Accessibility**: Follow WCAG guidelines for accessibility

## Additional Resources

- **API Documentation**: Available at `/api/docs/` when backend is running
- **Postman Collection**: Export from DRF browsable API
- **Type Definitions**: Consider using OpenAPI generator for TypeScript types

This guide provides a comprehensive foundation for implementing the inventory module frontend. Adjust styling, component structure, and state management patterns according to your specific frontend framework and design system.
