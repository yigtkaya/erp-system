# Purchasing Module - Product Requirements Document

## Overview

The Purchasing module manages the complete procurement process from requisition to goods receipt. It handles supplier management, purchase orders, and inventory receiving, providing the necessary tools to efficiently procure materials and products without financial complexity.

## Features

### Supplier Management

- **Supplier Records**: Maintain supplier information with unique codes
- **Supplier Evaluation**: Track supplier ratings and performance
- **Contact Information**: Store multiple contact points and addresses
- **Lead Time Tracking**: Record supplier lead times for planning purposes

### Purchase Requisitions

- **Requisition Creation**: Allow users to request purchases of materials and products
- **Approval Workflow**: Support for request submission and approval processes
- **Status Tracking**: Follow requisitions through their lifecycle (Draft, Submitted, Approved, Rejected, Converted, Cancelled)
- **Department Assignment**: Associate requisitions with specific departments

### Purchase Orders

- **PO Generation**: Create purchase orders manually or from approved requisitions
- **Order Status Tracking**: Monitor orders through their stages (Draft, Requested, Approved, Rejected, Sent, Partial, Received, Cancelled)
- **Approval Process**: Require approval for orders above certain thresholds
- **Documentation**: Associate POs with supplier references and notes

### Receiving Process

- **Goods Receipt**: Record the receipt of ordered goods
- **Partial Receipts**: Support for receiving partial shipments
- **Quality Verification**: Record accepted and rejected quantities
- **Document Upload**: Store delivery notes and supporting documentation
- **Storage Location**: Track where received items are stored

### Supplier Product Management

- **Supplier Product Information**: Track supplier-specific product details
- **Lead Time Management**: Record supplier lead times for planning purposes
- **Minimum Order Quantities**: Track minimum quantities for each supplier-product combination
- **Supplier Product Codes**: Maintain supplier's internal product codes

## Technical Requirements

### Models

- `Supplier`: Supplier information and performance metrics
- `PurchaseOrder`: Core purchase order information
- `PurchaseOrderItem`: Line items for purchase orders
- `PurchaseRequisition`: Internal purchase requests
- `PurchaseRequisitionItem`: Line items for requisitions
- `GoodsReceipt`: Record of goods received
- `GoodsReceiptItem`: Line items for received goods
- `SupplierProductInfo`: Supplier-specific product information

### Business Logic

- Validation rules for dates and quantities
- Update of purchase order status based on goods receipts
- Automatic requisition to purchase order conversion
- Inventory integration for goods received

### Integration Points

- Core module for user information and departments
- Inventory module for product information and stock updates
- Manufacturing module for material requirements

## Security Considerations

- Role-based permissions for requisition and PO creation/approval
- Audit trail for all purchasing activities
- Segregation of duties between requisition, approval, and receipt functions

## Future Enhancements

- Advanced supplier evaluation metrics
- Automated request for quotation (RFQ) process
- Electronic document exchange with suppliers
- Contract management for long-term supplier agreements
- Supplier portal for order confirmation and delivery updates
- Advanced receiving workflows with quality control integration

## Removed Features

The following features have been removed to focus on procurement logistics:

- Currency and exchange rate management
- Pricing and cost tracking
- Financial calculations and totals
- Payment terms management
- Tax calculations
- Supplier price lists and pricing agreements

The module now focuses purely on **procurement tracking and supplier management** without financial complexity.
