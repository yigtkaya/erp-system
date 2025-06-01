# Machines Page Frontend Implementation Guide

## Overview

This guide provides a comprehensive implementation plan for the machines page frontend in your ERP system. The page will integrate with both the **Maintenance** and **Manufacturing** modules to provide complete machine management functionality.

## Backend API Endpoints Available

### Equipment/Machines (Maintenance Module)

- **Base URL**: `/api/maintenance/equipment/`
- **Methods**: GET, POST, PUT, PATCH, DELETE
- **Filters**: `work_center`, `status`
- **Search**: `code`, `name`, `serial_number`
- **Custom Actions**:
  - `GET /api/maintenance/equipment/{id}/maintenance_history/` - Get maintenance history

### Work Centers (Manufacturing Module)

- **Base URL**: `/api/manufacturing/work-centers/`
- **Methods**: GET, POST, PUT, PATCH, DELETE
- **Filters**: `production_line`, `is_active`
- **Search**: `code`, `name`
- **Custom Actions**:
  - `GET /api/manufacturing/work-centers/{id}/downtime_history/` - Get downtime history

### Machine Downtime (Manufacturing Module)

- **Base URL**: `/api/manufacturing/machine-downtimes/`
- **Methods**: GET, POST, PUT, PATCH, DELETE
- **Filters**: `work_center`, `category`, `reported_by`

### Maintenance Work Orders

- **Base URL**: `/api/maintenance/work-orders/`
- **Methods**: GET, POST, PUT, PATCH, DELETE
- **Filters**: `equipment`, `maintenance_type`, `priority`, `status`
- **Search**: `work_order_number`, `equipment__name`, `description`
- **Custom Actions**:
  - `POST /api/maintenance/work-orders/{id}/start/` - Start work order
  - `POST /api/maintenance/work-orders/{id}/complete/` - Complete work order

### Maintenance Tasks

- **Base URL**: `/api/maintenance/maintenance-tasks/`
- **Methods**: GET, POST, PUT, PATCH, DELETE
- **Filters**: `work_order`, `status`
- **Custom Actions**:
  - `POST /api/maintenance/maintenance-tasks/{id}/complete/` - Complete task

### Maintenance Logs

- **Base URL**: `/api/maintenance/maintenance-logs/`
- **Methods**: GET, POST, PUT, PATCH, DELETE
- **Filters**: `equipment`, `maintenance_type`, `work_order`
- **Search**: `description`

## Data Models Structure

### Equipment (Machine) Model

```typescript
interface Equipment {
  id: number;
  code: string;
  name: string;
  description?: string;
  model?: string;
  serial_number?: string;
  manufacturer?: string;
  purchase_date?: string;
  warranty_end_date?: string;
  status: "ACTIVE" | "INACTIVE" | "MAINTENANCE" | "REPAIR" | "DISPOSED";
  location?: string;
  work_center?: WorkCenter;
  work_center_id?: number;
  work_center_display?: WorkCenter;
  parent_equipment?: Equipment;
  maintenance_interval_days: number;
  last_maintenance_date?: string;
  next_maintenance_date?: string;
  created_at: string;
  updated_at: string;
}
```

### Enhanced Machine Model (with Manufacturing Specifications)

```typescript
interface Machine {
  id: number;
  machine_code: string;
  machine_type:
    | "CNC_MILLING"
    | "CNC_LATHE"
    | "DRILLING"
    | "GRINDING"
    | "WELDING"
    | "ASSEMBLY"
    | "INSPECTION"
    | "OTHER";
  brand?: string;
  model?: string;
  axis_count?: "AXIS_2" | "AXIS_3" | "AXIS_4" | "AXIS_5" | "AXIS_6" | "MULTI";
  internal_cooling?: number;
  motor_power_kva?: number;
  holder_type?: string;
  spindle_motor_power_10_percent_kw?: number;
  spindle_motor_power_30_percent_kw?: number;
  power_hp?: number;
  spindle_speed_rpm?: number;
  tool_count?: number;
  nc_control_unit?: string;
  manufacturing_year?: string;
  serial_number?: string;
  machine_weight_kg?: number;
  max_part_size?: string;
  description?: string;
  status: "AVAILABLE" | "IN_USE" | "MAINTENANCE" | "BROKEN" | "RETIRED";
  maintenance_interval: number;
  last_maintenance_date?: string;
  next_maintenance_date?: string;
  maintenance_notes?: string;
  work_center?: WorkCenter;
  work_center_id?: number;
  work_center_display?: WorkCenter;
  created_at: string;
  updated_at: string;
}
```

### Machine Type Enum

```typescript
enum MachineType {
  CNC_MILLING = "CNC_MILLING",
  CNC_LATHE = "CNC_LATHE",
  DRILLING = "DRILLING",
  GRINDING = "GRINDING",
  WELDING = "WELDING",
  ASSEMBLY = "ASSEMBLY",
  INSPECTION = "INSPECTION",
  OTHER = "OTHER",
}

const MachineTypeLabels = {
  [MachineType.CNC_MILLING]: "CNC Milling",
  [MachineType.CNC_LATHE]: "CNC Lathe",
  [MachineType.DRILLING]: "Drilling",
  [MachineType.GRINDING]: "Grinding",
  [MachineType.WELDING]: "Welding",
  [MachineType.ASSEMBLY]: "Assembly",
  [MachineType.INSPECTION]: "Inspection",
  [MachineType.OTHER]: "Other",
};
```

### Axis Count Enum

```typescript
enum AxisCount {
  AXIS_2 = "AXIS_2",
  AXIS_3 = "AXIS_3",
  AXIS_4 = "AXIS_4",
  AXIS_5 = "AXIS_5",
  AXIS_6 = "AXIS_6",
  MULTI = "MULTI",
}

const AxisCountLabels = {
  [AxisCount.AXIS_2]: "2-Axis",
  [AxisCount.AXIS_3]: "3-Axis",
  [AxisCount.AXIS_4]: "4-Axis",
  [AxisCount.AXIS_5]: "5-Axis",
  [AxisCount.AXIS_6]: "6-Axis",
  [AxisCount.MULTI]: "Multi-Axis",
};
```

### Machine Status Enum

```typescript
enum MachineStatus {
  AVAILABLE = "AVAILABLE",
  IN_USE = "IN_USE",
  MAINTENANCE = "MAINTENANCE",
  BROKEN = "BROKEN",
  RETIRED = "RETIRED",
}

const MachineStatusLabels = {
  [MachineStatus.AVAILABLE]: "Available",
  [MachineStatus.IN_USE]: "In Use",
  [MachineStatus.MAINTENANCE]: "Under Maintenance",
  [MachineStatus.BROKEN]: "Broken",
  [MachineStatus.RETIRED]: "Retired",
};
```

### Work Center Model

```typescript
interface WorkCenter {
  id: number;
  code: string;
  name: string;
  description?: string;
  production_line: ProductionLine;
  capacity_per_hour: number;
  setup_time_minutes: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
```

### Maintenance Work Order Model

```typescript
interface MaintenanceWorkOrder {
  id: number;
  work_order_number: string;
  equipment: Equipment;
  equipment_id: number;
  equipment_display: Equipment;
  maintenance_type:
    | "PREVENTIVE"
    | "CORRECTIVE"
    | "PREDICTIVE"
    | "BREAKDOWN"
    | "SAFETY";
  description: string;
  reported_by: User;
  reported_by_display: User;
  assigned_to?: User;
  assigned_to_id?: number;
  assigned_to_display?: User;
  priority: "LOW" | "MEDIUM" | "HIGH" | "URGENT";
  status:
    | "PLANNED"
    | "SCHEDULED"
    | "IN_PROGRESS"
    | "COMPLETED"
    | "CANCELLED"
    | "ON_HOLD";
  planned_start_date: string;
  planned_end_date: string;
  actual_start_date?: string;
  actual_end_date?: string;
  total_downtime_hours?: number;
  schedule?: number;
  tasks: MaintenanceTask[];
  created_at: string;
  updated_at: string;
}
```

### Maintenance Task Model

```typescript
interface MaintenanceTask {
  id: number;
  work_order: number;
  task_description: string;
  detailed_instructions?: string;
  estimated_hours: number;
  actual_hours?: number;
  assigned_to?: User;
  assigned_to_display?: User;
  status: "PENDING" | "IN_PROGRESS" | "COMPLETED" | "SKIPPED";
  completion_date?: string;
  requires_parts: boolean;
}
```

### Maintenance Log Model

```typescript
interface MaintenanceLog {
  id: number;
  equipment: Equipment;
  equipment_id: number;
  equipment_display: Equipment;
  work_order?: MaintenanceWorkOrder;
  work_order_display?: MaintenanceWorkOrder;
  maintenance_type:
    | "PREVENTIVE"
    | "CORRECTIVE"
    | "PREDICTIVE"
    | "BREAKDOWN"
    | "SAFETY";
  maintenance_date: string;
  performed_by: User;
  performed_by_display: User;
  description: string;
  hours_spent: number;
  cost?: number;
  created_at: string;
  updated_at: string;
}
```

### Machine Downtime Model

```typescript
interface MachineDowntime {
  id: number;
  work_center: WorkCenter;
  start_time: string;
  end_time?: string;
  reason: string;
  category:
    | "MAINTENANCE"
    | "BREAKDOWN"
    | "SETUP"
    | "NO_OPERATOR"
    | "NO_MATERIAL"
    | "OTHER";
  notes?: string;
  reported_by: User;
  duration_minutes?: number;
}
```

## Page Structure and Components

### 1. Main Machines Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Machines Management                                         │
├─────────────────────────────────────────────────────────────┤
│ [+ Add Machine] [Import] [Export] [Filters ▼] [Search...]  │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│ │   Active    │ │ Maintenance │ │   Repair    │ │ Inactive│ │
│ │     45      │ │      3      │ │      1      │ │    2    │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Machines Table                           │
│ [Code] [Name] [Status] [Work Center] [Next Maintenance]     │
│ [Actions: View | Edit | Maintenance | Downtime]            │
└─────────────────────────────────────────────────────────────┘
```

### 2. Component Breakdown

#### A. MachinesPage (Main Container)

```typescript
// components/machines/MachinesPage.tsx
interface MachinesPageProps {}

const MachinesPage: React.FC<MachinesPageProps> = () => {
  const [machines, setMachines] = useState<Equipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<MachineFilters>({});
  const [searchTerm, setSearchTerm] = useState("");

  // State management for modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedMachine, setSelectedMachine] = useState<Equipment | null>(
    null
  );

  return (
    <div className="machines-page">
      <MachineHeader />
      <MachineStats machines={machines} />
      <MachineFilters onFiltersChange={setFilters} />
      <MachineTable
        machines={machines}
        onEdit={handleEdit}
        onView={handleView}
        onMaintenance={handleMaintenance}
        onDowntime={handleDowntime}
      />

      {/* Modals */}
      <AddMachineModal
        show={showAddModal}
        onClose={() => setShowAddModal(false)}
      />
      <EditMachineModal
        show={showEditModal}
        machine={selectedMachine}
        onClose={() => setShowEditModal(false)}
      />
    </div>
  );
};
```

#### B. MachineStats (Status Cards)

```typescript
// components/machines/MachineStats.tsx
interface MachineStatsProps {
  machines: Machine[];
}

const MachineStats: React.FC<MachineStatsProps> = ({ machines }) => {
  const stats = useMemo(() => {
    const statusCounts = {
      available: machines.filter((m) => m.status === "AVAILABLE").length,
      in_use: machines.filter((m) => m.status === "IN_USE").length,
      maintenance: machines.filter((m) => m.status === "MAINTENANCE").length,
      broken: machines.filter((m) => m.status === "BROKEN").length,
      retired: machines.filter((m) => m.status === "RETIRED").length,
    };

    const maintenanceOverdue = machines.filter((m) => {
      if (!m.next_maintenance_date) return false;
      return new Date(m.next_maintenance_date) < new Date();
    }).length;

    const utilizationRate =
      machines.length > 0
        ? ((statusCounts.in_use / machines.length) * 100).toFixed(1)
        : "0";

    return {
      ...statusCounts,
      total: machines.length,
      maintenanceOverdue,
      utilizationRate: parseFloat(utilizationRate),
    };
  }, [machines]);

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
      <StatCard
        title="Total Machines"
        count={stats.total}
        color="gray"
        icon="🏭"
      />
      <StatCard
        title="Available"
        count={stats.available}
        color="green"
        icon="✅"
        percentage={(stats.available / stats.total) * 100}
      />
      <StatCard
        title="In Use"
        count={stats.in_use}
        color="blue"
        icon="⚙️"
        percentage={(stats.in_use / stats.total) * 100}
      />
      <StatCard
        title="Maintenance"
        count={stats.maintenance}
        color="yellow"
        icon="🔧"
        percentage={(stats.maintenance / stats.total) * 100}
      />
      <StatCard
        title="Broken"
        count={stats.broken}
        color="red"
        icon="⚠️"
        percentage={(stats.broken / stats.total) * 100}
      />
      <StatCard
        title="Overdue Maintenance"
        count={stats.maintenanceOverdue}
        color={stats.maintenanceOverdue > 0 ? "red" : "green"}
        icon="📅"
        isAlert={stats.maintenanceOverdue > 0}
      />
    </div>
  );
};
```

#### Enhanced StatCard Component

```typescript
// components/ui/StatCard.tsx
interface StatCardProps {
  title: string;
  count: number;
  color: "gray" | "green" | "blue" | "yellow" | "red";
  icon?: string;
  percentage?: number;
  isAlert?: boolean;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  count,
  color,
  icon,
  percentage,
  isAlert = false,
}) => {
  const colorClasses = {
    gray: "bg-gray-50 border-gray-200 text-gray-800",
    green: "bg-green-50 border-green-200 text-green-800",
    blue: "bg-blue-50 border-blue-200 text-blue-800",
    yellow: "bg-yellow-50 border-yellow-200 text-yellow-800",
    red: "bg-red-50 border-red-200 text-red-800",
  };

  return (
    <div
      className={`
      relative overflow-hidden rounded-lg border p-4 
      ${colorClasses[color]}
      ${isAlert ? "ring-2 ring-red-500 ring-opacity-50" : ""}
      transition-all duration-200 hover:shadow-md
    `}
    >
      {icon && (
        <div className="absolute top-2 right-2 text-2xl opacity-20">{icon}</div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium opacity-75">{title}</p>
          <p className="text-3xl font-bold">{count}</p>
          {percentage !== undefined && (
            <p className="text-xs opacity-60 mt-1">
              {percentage.toFixed(1)}% of total
            </p>
          )}
        </div>

        {icon && <div className="text-3xl opacity-30">{icon}</div>}
      </div>

      {isAlert && count > 0 && (
        <div className="absolute -top-1 -right-1">
          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
        </div>
      )}
    </div>
  );
};
```

#### Machine Type Distribution Chart

```typescript
// components/machines/MachineTypeChart.tsx
interface MachineTypeChartProps {
  machines: Machine[];
}

const MachineTypeChart: React.FC<MachineTypeChartProps> = ({ machines }) => {
  const typeDistribution = useMemo(() => {
    const distribution = machines.reduce((acc, machine) => {
      const type = machine.machine_type;
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(distribution).map(([type, count]) => ({
      type,
      label: MachineTypeLabels[type] || type,
      count,
      percentage: ((count / machines.length) * 100).toFixed(1),
    }));
  }, [machines]);

  return (
    <div className="bg-white p-6 rounded-lg border">
      <h3 className="text-lg font-semibold mb-4">Machine Type Distribution</h3>
      <div className="space-y-3">
        {typeDistribution.map(({ type, label, count, percentage }) => (
          <div key={type} className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-500 rounded"></div>
              <span className="text-sm font-medium">{label}</span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <span>{count} machines</span>
              <span className="text-xs">({percentage}%)</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

#### C. MachineTable (Data Grid)

```typescript
// components/machines/MachineTable.tsx
interface MachineTableProps {
  machines: Machine[];
  onEdit: (machine: Machine) => void;
  onView: (machine: Machine) => void;
  onMaintenance: (machine: Machine) => void;
  onDowntime: (machine: Machine) => void;
}

const MachineTable: React.FC<MachineTableProps> = ({
  machines,
  onEdit,
  onView,
  onMaintenance,
  onDowntime,
}) => {
  const columns = [
    {
      header: "Machine Code",
      accessor: "machine_code",
      sortable: true,
    },
    {
      header: "Type",
      accessor: "machine_type",
      render: (type: string) => MachineTypeLabels[type] || type,
      sortable: true,
    },
    {
      header: "Brand",
      accessor: "brand",
      render: (brand: string) => brand || "N/A",
    },
    {
      header: "Model",
      accessor: "model",
      render: (model: string) => model || "N/A",
    },
    {
      header: "Status",
      accessor: "status",
      render: (status: string) => <MachineStatusBadge status={status} />,
      sortable: true,
    },
    {
      header: "Work Center",
      accessor: "work_center",
      render: (workCenter: WorkCenter) => workCenter?.name || "N/A",
    },
    {
      header: "Axis Count",
      accessor: "axis_count",
      render: (axisCount: string) =>
        axisCount ? AxisCountLabels[axisCount] : "N/A",
    },
    {
      header: "Next Maintenance",
      accessor: "next_maintenance_date",
      render: (date: string) => {
        if (!date) return "N/A";
        const maintenanceDate = new Date(date);
        const today = new Date();
        const isOverdue = maintenanceDate < today;

        return (
          <span
            className={isOverdue ? "text-red-600 font-medium" : "text-gray-600"}
          >
            {formatDate(date)}
            {isOverdue && " (Overdue)"}
          </span>
        );
      },
      sortable: true,
    },
    {
      header: "Actions",
      accessor: "actions",
      render: (_, machine: Machine) => (
        <ActionButtons
          machine={machine}
          onEdit={onEdit}
          onView={onView}
          onMaintenance={onMaintenance}
          onDowntime={onDowntime}
        />
      ),
    },
  ];

  return (
    <div className="machine-table">
      <DataTable
        columns={columns}
        data={machines}
        defaultSort={{ column: "machine_code", direction: "asc" }}
        pagination={true}
        pageSize={20}
      />
    </div>
  );
};
```

#### Enhanced MachineStatusBadge Component

```typescript
// components/machines/MachineStatusBadge.tsx
interface MachineStatusBadgeProps {
  status: string;
}

const MachineStatusBadge: React.FC<MachineStatusBadgeProps> = ({ status }) => {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case "AVAILABLE":
        return { color: "green", icon: "✓", label: "Available" };
      case "IN_USE":
        return { color: "blue", icon: "⚙", label: "In Use" };
      case "MAINTENANCE":
        return { color: "yellow", icon: "🔧", label: "Maintenance" };
      case "BROKEN":
        return { color: "red", icon: "⚠", label: "Broken" };
      case "RETIRED":
        return { color: "gray", icon: "📦", label: "Retired" };
      default:
        return { color: "gray", icon: "?", label: status };
    }
  };

  const config = getStatusConfig(status);

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${config.color}-100 text-${config.color}-800`}
    >
      <span className="mr-1">{config.icon}</span>
      {config.label}
    </span>
  );
};
```

#### D. MachineFilters (Filter Panel)

```typescript
// components/machines/MachineFilters.tsx
interface MachineFiltersProps {
  onFiltersChange: (filters: MachineFilters) => void;
}

interface MachineFilters {
  status?: string;
  work_center?: string;
  maintenance_due?: boolean;
  search?: string;
}

const MachineFilters: React.FC<MachineFiltersProps> = ({ onFiltersChange }) => {
  const [workCenters, setWorkCenters] = useState<WorkCenter[]>([]);
  const [filters, setFilters] = useState<MachineFilters>({
    status: "",
    work_center: "",
    maintenance_due: false,
  });

  const handleFilterChange = (key: string, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  useEffect(() => {
    // Fetch work centers for filter dropdown
    const fetchWorkCenters = async () => {
      try {
        const response = await api.get("/manufacturing/work-centers/");
        setWorkCenters(response.data.results || response.data);
      } catch (error) {
        console.error("Failed to fetch work centers:", error);
      }
    };
    fetchWorkCenters();
  }, []);

  return (
    <div className="filters-panel mb-4 p-4 bg-gray-50 rounded-lg">
      <div className="grid grid-cols-4 gap-4">
        <Select
          label="Status"
          value={filters.status}
          onChange={(value) => handleFilterChange("status", value)}
          options={[
            { value: "", label: "All Statuses" },
            { value: "ACTIVE", label: "Active" },
            { value: "MAINTENANCE", label: "Maintenance" },
            { value: "REPAIR", label: "Repair" },
            { value: "INACTIVE", label: "Inactive" },
            { value: "DISPOSED", label: "Disposed" },
          ]}
        />

        <Select
          label="Work Center"
          value={filters.work_center}
          onChange={(value) => handleFilterChange("work_center", value)}
          options={[
            { value: "", label: "All Work Centers" },
            ...workCenters.map((wc) => ({ value: wc.id, label: wc.name })),
          ]}
        />

        <Checkbox
          label="Maintenance Due"
          checked={filters.maintenance_due}
          onChange={(checked) => handleFilterChange("maintenance_due", checked)}
        />

        <Button
          variant="secondary"
          onClick={() => {
            const resetFilters = {
              status: "",
              work_center: "",
              maintenance_due: false,
            };
            setFilters(resetFilters);
            onFiltersChange(resetFilters);
          }}
        >
          Clear Filters
        </Button>
      </div>
    </div>
  );
};
```

### 3. Machine Detail Modal/Page

#### A. MachineDetailModal

```typescript
// components/machines/MachineDetailModal.tsx
interface MachineDetailModalProps {
  machine: Machine;
  show: boolean;
  onClose: () => void;
  onEdit?: (machine: Machine) => void;
}

const MachineDetailModal: React.FC<MachineDetailModalProps> = ({
  machine,
  show,
  onClose,
  onEdit,
}) => {
  const [activeTab, setActiveTab] = useState("details");
  const [maintenanceHistory, setMaintenanceHistory] = useState([]);
  const [downtimeHistory, setDowntimeHistory] = useState([]);

  const tabs = [
    { id: "details", label: "Basic Details" },
    { id: "specifications", label: "Technical Specs" },
    { id: "maintenance", label: "Maintenance History" },
    { id: "downtime", label: "Downtime History" },
  ];

  useEffect(() => {
    if (machine.id && show) {
      fetchMaintenanceHistory();
      fetchDowntimeHistory();
    }
  }, [machine.id, show]);

  const fetchMaintenanceHistory = async () => {
    try {
      const response = await api.get(
        `/maintenance/equipment/${machine.id}/maintenance_history/`
      );
      setMaintenanceHistory(response.data.logs || []);
    } catch (error) {
      console.error("Failed to fetch maintenance history:", error);
    }
  };

  const fetchDowntimeHistory = async () => {
    try {
      const response = await api.get(
        `/manufacturing/machine-downtimes/?work_center=${machine.work_center?.id}`
      );
      setDowntimeHistory(response.data.results || []);
    } catch (error) {
      console.error("Failed to fetch downtime history:", error);
    }
  };

  return (
    <Modal show={show} onClose={onClose} size="xl">
      <Modal.Header>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">
              {machine.machine_code} - {MachineTypeLabels[machine.machine_type]}
            </h2>
            <p className="text-sm text-gray-600">
              {machine.brand} {machine.model}
            </p>
          </div>
          <MachineStatusBadge status={machine.status} />
        </div>
      </Modal.Header>

      <Modal.Body>
        <TabNavigation
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />

        {activeTab === "details" && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="font-medium text-lg">Basic Information</h3>
                <div className="space-y-2">
                  <DetailRow
                    label="Machine Code"
                    value={machine.machine_code}
                  />
                  <DetailRow
                    label="Type"
                    value={MachineTypeLabels[machine.machine_type]}
                  />
                  <DetailRow label="Brand" value={machine.brand || "N/A"} />
                  <DetailRow label="Model" value={machine.model || "N/A"} />
                  <DetailRow
                    label="Serial Number"
                    value={machine.serial_number || "N/A"}
                  />
                  <DetailRow
                    label="Manufacturing Year"
                    value={
                      machine.manufacturing_year
                        ? new Date(machine.manufacturing_year).getFullYear()
                        : "N/A"
                    }
                  />
                  <DetailRow
                    label="Work Center"
                    value={machine.work_center?.name || "N/A"}
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="font-medium text-lg">Status & Maintenance</h3>
                <div className="space-y-2">
                  <DetailRow
                    label="Status"
                    value={<MachineStatusBadge status={machine.status} />}
                  />
                  <DetailRow
                    label="Maintenance Interval"
                    value={`${machine.maintenance_interval} days`}
                  />
                  <DetailRow
                    label="Last Maintenance"
                    value={
                      machine.last_maintenance_date
                        ? formatDate(machine.last_maintenance_date)
                        : "Never"
                    }
                  />
                  <DetailRow
                    label="Next Maintenance"
                    value={
                      machine.next_maintenance_date ? (
                        <span
                          className={
                            new Date(machine.next_maintenance_date) < new Date()
                              ? "text-red-600 font-medium"
                              : "text-gray-600"
                          }
                        >
                          {formatDate(machine.next_maintenance_date)}
                          {new Date(machine.next_maintenance_date) <
                            new Date() && " (Overdue)"}
                        </span>
                      ) : (
                        "Not scheduled"
                      )
                    }
                  />
                </div>
              </div>
            </div>

            {machine.description && (
              <div>
                <h3 className="font-medium text-lg mb-2">Description</h3>
                <p className="text-gray-600 bg-gray-50 p-3 rounded">
                  {machine.description}
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === "specifications" && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="font-medium text-lg">Machine Configuration</h3>
                <div className="space-y-2">
                  <DetailRow
                    label="Axis Count"
                    value={
                      machine.axis_count
                        ? AxisCountLabels[machine.axis_count]
                        : "N/A"
                    }
                  />
                  <DetailRow
                    label="Tool Count"
                    value={machine.tool_count || "N/A"}
                  />
                  <DetailRow
                    label="Holder Type"
                    value={machine.holder_type || "N/A"}
                  />
                  <DetailRow
                    label="NC Control Unit"
                    value={machine.nc_control_unit || "N/A"}
                  />
                  <DetailRow
                    label="Max Part Size"
                    value={machine.max_part_size || "N/A"}
                  />
                  <DetailRow
                    label="Machine Weight"
                    value={
                      machine.machine_weight_kg
                        ? `${machine.machine_weight_kg} kg`
                        : "N/A"
                    }
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="font-medium text-lg">Power & Performance</h3>
                <div className="space-y-2">
                  <DetailRow
                    label="Motor Power"
                    value={
                      machine.motor_power_kva
                        ? `${machine.motor_power_kva} KVA`
                        : "N/A"
                    }
                  />
                  <DetailRow
                    label="Power (HP)"
                    value={machine.power_hp ? `${machine.power_hp} HP` : "N/A"}
                  />
                  <DetailRow
                    label="Spindle Speed"
                    value={
                      machine.spindle_speed_rpm
                        ? `${machine.spindle_speed_rpm} RPM`
                        : "N/A"
                    }
                  />
                  <DetailRow
                    label="Spindle Power (10%)"
                    value={
                      machine.spindle_motor_power_10_percent_kw
                        ? `${machine.spindle_motor_power_10_percent_kw} KW`
                        : "N/A"
                    }
                  />
                  <DetailRow
                    label="Spindle Power (30%)"
                    value={
                      machine.spindle_motor_power_30_percent_kw
                        ? `${machine.spindle_motor_power_30_percent_kw} KW`
                        : "N/A"
                    }
                  />
                  <DetailRow
                    label="Internal Cooling"
                    value={
                      machine.internal_cooling
                        ? `${machine.internal_cooling} bars`
                        : "N/A"
                    }
                  />
                </div>
              </div>
            </div>

            {machine.maintenance_notes && (
              <div>
                <h3 className="font-medium text-lg mb-2">Maintenance Notes</h3>
                <p className="text-gray-600 bg-gray-50 p-3 rounded whitespace-pre-wrap">
                  {machine.maintenance_notes}
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === "maintenance" && (
          <MaintenanceHistoryTab
            history={maintenanceHistory}
            machineId={machine.id}
            onRefresh={fetchMaintenanceHistory}
          />
        )}

        {activeTab === "downtime" && (
          <DowntimeHistoryTab
            history={downtimeHistory}
            workCenterId={machine.work_center?.id}
            onRefresh={fetchDowntimeHistory}
          />
        )}
      </Modal.Body>

      <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
        {onEdit && (
          <Button variant="primary" onClick={() => onEdit(machine)}>
            Edit Machine
          </Button>
        )}
      </Modal.Footer>
    </Modal>
  );
};
```

#### DetailRow Component

```typescript
// components/ui/DetailRow.tsx
interface DetailRowProps {
  label: string;
  value: React.ReactNode;
}

const DetailRow: React.FC<DetailRowProps> = ({ label, value }) => {
  return (
    <div className="flex justify-between items-center py-1">
      <span className="text-sm font-medium text-gray-500">{label}:</span>
      <span className="text-sm text-gray-900">{value}</span>
    </div>
  );
};
```

### 4. Add/Edit Machine Forms

#### A. AddMachineModal

```typescript
// components/machines/AddMachineModal.tsx
interface AddMachineModalProps {
  show: boolean;
  onClose: () => void;
  onSuccess?: (machine: Machine) => void;
}

const AddMachineModal: React.FC<AddMachineModalProps> = ({
  show,
  onClose,
  onSuccess,
}) => {
  const [formData, setFormData] = useState<Partial<Machine>>({
    machine_code: "",
    machine_type: "CNC_MILLING",
    brand: "",
    model: "",
    axis_count: "",
    status: "AVAILABLE",
    maintenance_interval: 90,
  });

  const [workCenters, setWorkCenters] = useState<WorkCenter[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("basic");

  useEffect(() => {
    // Fetch work centers
    const fetchWorkCenters = async () => {
      try {
        const response = await api.get("/manufacturing/work-centers/");
        setWorkCenters(response.data.results || response.data);
      } catch (error) {
        console.error("Failed to fetch work centers:", error);
      }
    };
    fetchWorkCenters();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.post("/manufacturing/machines/", formData);
      onSuccess?.(response.data);
      onClose();
      toast.success("Machine added successfully");
    } catch (error) {
      toast.error("Failed to add machine");
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: "basic", label: "Basic Info" },
    { id: "specifications", label: "Technical Specs" },
    { id: "maintenance", label: "Maintenance" },
  ];

  return (
    <Modal show={show} onClose={onClose} size="xl">
      <Modal.Header>
        <h2>Add New Machine</h2>
      </Modal.Header>

      <form onSubmit={handleSubmit}>
        <Modal.Body>
          <TabNavigation
            tabs={tabs}
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />

          {activeTab === "basic" && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Machine Code *"
                  value={formData.machine_code}
                  onChange={(value) =>
                    setFormData({ ...formData, machine_code: value })
                  }
                  placeholder="MC001"
                  required
                />

                <Select
                  label="Machine Type *"
                  value={formData.machine_type}
                  onChange={(value) =>
                    setFormData({ ...formData, machine_type: value })
                  }
                  options={Object.entries(MachineTypeLabels).map(
                    ([value, label]) => ({
                      value,
                      label,
                    })
                  )}
                  required
                />

                <Input
                  label="Brand"
                  value={formData.brand}
                  onChange={(value) =>
                    setFormData({ ...formData, brand: value })
                  }
                  placeholder="Haas, Fanuc, etc."
                />

                <Input
                  label="Model"
                  value={formData.model}
                  onChange={(value) =>
                    setFormData({ ...formData, model: value })
                  }
                  placeholder="VF-2SS"
                />

                <Input
                  label="Serial Number"
                  value={formData.serial_number}
                  onChange={(value) =>
                    setFormData({ ...formData, serial_number: value })
                  }
                  placeholder="SN123456789"
                />

                <Select
                  label="Work Center"
                  value={formData.work_center_id}
                  onChange={(value) =>
                    setFormData({ ...formData, work_center_id: value })
                  }
                  options={[
                    { value: "", label: "Select Work Center" },
                    ...workCenters.map((wc) => ({
                      value: wc.id,
                      label: wc.name,
                    })),
                  ]}
                />

                <Select
                  label="Status"
                  value={formData.status}
                  onChange={(value) =>
                    setFormData({ ...formData, status: value })
                  }
                  options={Object.entries(MachineStatusLabels).map(
                    ([value, label]) => ({
                      value,
                      label,
                    })
                  )}
                />

                <DateInput
                  label="Manufacturing Year"
                  value={formData.manufacturing_year}
                  onChange={(value) =>
                    setFormData({ ...formData, manufacturing_year: value })
                  }
                />
              </div>

              <Textarea
                label="Description"
                value={formData.description}
                onChange={(value) =>
                  setFormData({ ...formData, description: value })
                }
                rows={3}
                placeholder="Machine description and notes"
              />
            </div>
          )}

          {activeTab === "specifications" && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <Select
                  label="Axis Count"
                  value={formData.axis_count}
                  onChange={(value) =>
                    setFormData({ ...formData, axis_count: value })
                  }
                  options={[
                    { value: "", label: "Select Axis Count" },
                    ...Object.entries(AxisCountLabels).map(
                      ([value, label]) => ({
                        value,
                        label,
                      })
                    ),
                  ]}
                />

                <Input
                  type="number"
                  label="Internal Cooling (bars)"
                  value={formData.internal_cooling}
                  onChange={(value) =>
                    setFormData({
                      ...formData,
                      internal_cooling: parseFloat(value),
                    })
                  }
                  step="0.01"
                />

                <Input
                  type="number"
                  label="Motor Power (KVA)"
                  value={formData.motor_power_kva}
                  onChange={(value) =>
                    setFormData({
                      ...formData,
                      motor_power_kva: parseFloat(value),
                    })
                  }
                  step="0.01"
                />

                <Input
                  label="Holder Type"
                  value={formData.holder_type}
                  onChange={(value) =>
                    setFormData({ ...formData, holder_type: value })
                  }
                  placeholder="CAT40, HSK63, etc."
                />

                <Input
                  type="number"
                  label="Spindle Power 10% (KW)"
                  value={formData.spindle_motor_power_10_percent_kw}
                  onChange={(value) =>
                    setFormData({
                      ...formData,
                      spindle_motor_power_10_percent_kw: parseFloat(value),
                    })
                  }
                  step="0.01"
                />

                <Input
                  type="number"
                  label="Spindle Power 30% (KW)"
                  value={formData.spindle_motor_power_30_percent_kw}
                  onChange={(value) =>
                    setFormData({
                      ...formData,
                      spindle_motor_power_30_percent_kw: parseFloat(value),
                    })
                  }
                  step="0.01"
                />

                <Input
                  type="number"
                  label="Power (HP)"
                  value={formData.power_hp}
                  onChange={(value) =>
                    setFormData({ ...formData, power_hp: parseFloat(value) })
                  }
                  step="0.01"
                />

                <Input
                  type="number"
                  label="Spindle Speed (RPM)"
                  value={formData.spindle_speed_rpm}
                  onChange={(value) =>
                    setFormData({
                      ...formData,
                      spindle_speed_rpm: parseInt(value),
                    })
                  }
                />

                <Input
                  type="number"
                  label="Tool Count"
                  value={formData.tool_count}
                  onChange={(value) =>
                    setFormData({ ...formData, tool_count: parseInt(value) })
                  }
                />

                <Input
                  label="NC Control Unit"
                  value={formData.nc_control_unit}
                  onChange={(value) =>
                    setFormData({ ...formData, nc_control_unit: value })
                  }
                  placeholder="Fanuc 0i-MF, Siemens 828D, etc."
                />

                <Input
                  type="number"
                  label="Machine Weight (kg)"
                  value={formData.machine_weight_kg}
                  onChange={(value) =>
                    setFormData({
                      ...formData,
                      machine_weight_kg: parseFloat(value),
                    })
                  }
                  step="0.01"
                />

                <Input
                  label="Max Part Size"
                  value={formData.max_part_size}
                  onChange={(value) =>
                    setFormData({ ...formData, max_part_size: value })
                  }
                  placeholder="500x400x300mm"
                />
              </div>
            </div>
          )}

          {activeTab === "maintenance" && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Input
                  type="number"
                  label="Maintenance Interval (Days) *"
                  value={formData.maintenance_interval}
                  onChange={(value) =>
                    setFormData({
                      ...formData,
                      maintenance_interval: parseInt(value),
                    })
                  }
                  required
                />

                <DateInput
                  label="Last Maintenance Date"
                  value={formData.last_maintenance_date}
                  onChange={(value) =>
                    setFormData({ ...formData, last_maintenance_date: value })
                  }
                />
              </div>

              <Textarea
                label="Maintenance Notes"
                value={formData.maintenance_notes}
                onChange={(value) =>
                  setFormData({ ...formData, maintenance_notes: value })
                }
                rows={4}
                placeholder="Special maintenance requirements, procedures, or notes"
              />
            </div>
          )}
        </Modal.Body>

        <Modal.Footer>
          <Button variant="secondary" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={loading}>
            Add Machine
          </Button>
        </Modal.Footer>
      </form>
    </Modal>
  );
};
```

### 5. Maintenance and Downtime Management

#### A. MaintenanceModal

```typescript
// components/machines/MaintenanceModal.tsx
interface MaintenanceModalProps {
  machine: Equipment;
  show: boolean;
  onClose: () => void;
}

const MaintenanceModal: React.FC<MaintenanceModalProps> = ({
  machine,
  show,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState("schedule");

  return (
    <Modal show={show} onClose={onClose} size="xl">
      <Modal.Header>
        <h2>Maintenance - {machine.code}</h2>
      </Modal.Header>

      <Modal.Body>
        <TabNavigation
          tabs={[
            { id: "schedule", label: "Schedule Maintenance" },
            { id: "history", label: "History" },
            { id: "workorders", label: "Work Orders" },
          ]}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />

        {activeTab === "schedule" && (
          <ScheduleMaintenanceForm machine={machine} />
        )}
        {activeTab === "history" && (
          <MaintenanceHistoryList machine={machine} />
        )}
        {activeTab === "workorders" && <WorkOrdersList machine={machine} />}
      </Modal.Body>
    </Modal>
  );
};
```

#### B. DowntimeModal

```typescript
// components/machines/DowntimeModal.tsx
interface DowntimeModalProps {
  machine: Equipment;
  show: boolean;
  onClose: () => void;
}

const DowntimeModal: React.FC<DowntimeModalProps> = ({
  machine,
  show,
  onClose,
}) => {
  const [formData, setFormData] = useState({
    reason: "",
    category: "BREAKDOWN",
    start_time: new Date().toISOString(),
    notes: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await api.post("/manufacturing/machine-downtimes/", {
        ...formData,
        work_center: machine.work_center?.id,
      });

      toast.success("Downtime recorded successfully");
      onClose();
    } catch (error) {
      toast.error("Failed to record downtime");
    }
  };

  return (
    <Modal show={show} onClose={onClose}>
      <Modal.Header>
        <h2>Record Downtime - {machine.code}</h2>
      </Modal.Header>

      <form onSubmit={handleSubmit}>
        <Modal.Body>
          <div className="space-y-4">
            <Select
              label="Category *"
              value={formData.category}
              onChange={(value) =>
                setFormData({ ...formData, category: value })
              }
              options={[
                { value: "BREAKDOWN", label: "Breakdown" },
                { value: "MAINTENANCE", label: "Maintenance" },
                { value: "SETUP", label: "Setup" },
                { value: "NO_OPERATOR", label: "No Operator" },
                { value: "NO_MATERIAL", label: "No Material" },
                { value: "OTHER", label: "Other" },
              ]}
              required
            />

            <Input
              label="Reason *"
              value={formData.reason}
              onChange={(value) => setFormData({ ...formData, reason: value })}
              required
            />

            <DateTimeInput
              label="Start Time *"
              value={formData.start_time}
              onChange={(value) =>
                setFormData({ ...formData, start_time: value })
              }
              required
            />

            <Textarea
              label="Notes"
              value={formData.notes}
              onChange={(value) => setFormData({ ...formData, notes: value })}
              rows={3}
            />
          </div>
        </Modal.Body>

        <Modal.Footer>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary">
            Record Downtime
          </Button>
        </Modal.Footer>
      </form>
    </Modal>
  );
};
```

## API Integration Hooks

### 1. useMachines Hook

```typescript
// hooks/useMachines.ts
export const useMachines = (filters?: MachineFilters) => {
  const [machines, setMachines] = useState<Equipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null,
    previous: null,
  });

  const fetchMachines = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();

      if (filters?.status) params.append("status", filters.status);
      if (filters?.work_center)
        params.append("work_center", filters.work_center);
      if (filters?.search) params.append("search", filters.search);

      const response = await api.get(`/maintenance/equipment/?${params}`);

      // Handle both paginated and non-paginated responses
      if (response.data.results) {
        setMachines(response.data.results);
        setPagination({
          count: response.data.count,
          next: response.data.next,
          previous: response.data.previous,
        });
      } else {
        setMachines(response.data);
      }

      setError(null);
    } catch (err) {
      setError("Failed to fetch machines");
      console.error("Error fetching machines:", err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchMachines();
  }, [fetchMachines]);

  const addMachine = async (machineData: Partial<Equipment>) => {
    try {
      const response = await api.post("/maintenance/equipment/", machineData);
      setMachines((prev) => [...prev, response.data]);
      return response.data;
    } catch (error) {
      console.error("Error adding machine:", error);
      throw error;
    }
  };

  const updateMachine = async (id: number, machineData: Partial<Equipment>) => {
    try {
      const response = await api.patch(
        `/maintenance/equipment/${id}/`,
        machineData
      );
      setMachines((prev) => prev.map((m) => (m.id === id ? response.data : m)));
      return response.data;
    } catch (error) {
      console.error("Error updating machine:", error);
      throw error;
    }
  };

  const deleteMachine = async (id: number) => {
    try {
      await api.delete(`/maintenance/equipment/${id}/`);
      setMachines((prev) => prev.filter((m) => m.id !== id));
    } catch (error) {
      console.error("Error deleting machine:", error);
      throw error;
    }
  };

  return {
    machines,
    loading,
    error,
    pagination,
    refetch: fetchMachines,
    addMachine,
    updateMachine,
    deleteMachine,
  };
};
```

### 2. useMaintenanceHistory Hook

```typescript
// hooks/useMaintenanceHistory.ts
export const useMaintenanceHistory = (machineId: number) => {
  const [history, setHistory] = useState<{
    work_orders: MaintenanceWorkOrder[];
    logs: MaintenanceLog[];
  }>({ work_orders: [], logs: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = useCallback(async () => {
    if (!machineId) return;

    try {
      setLoading(true);
      const response = await api.get(
        `/maintenance/equipment/${machineId}/maintenance_history/`
      );
      setHistory(response.data);
      setError(null);
    } catch (error) {
      console.error("Failed to fetch maintenance history:", error);
      setError("Failed to fetch maintenance history");
    } finally {
      setLoading(false);
    }
  }, [machineId]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  return { history, loading, error, refetch: fetchHistory };
};
```

### 3. useWorkCenters Hook

```typescript
// hooks/useWorkCenters.ts
export const useWorkCenters = () => {
  const [workCenters, setWorkCenters] = useState<WorkCenter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWorkCenters = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get("/manufacturing/work-centers/");
      setWorkCenters(response.data.results || response.data);
      setError(null);
    } catch (err) {
      setError("Failed to fetch work centers");
      console.error("Error fetching work centers:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWorkCenters();
  }, [fetchWorkCenters]);

  return {
    workCenters,
    loading,
    error,
    refetch: fetchWorkCenters,
  };
};
```

### 4. useMaintenanceWorkOrders Hook

```typescript
// hooks/useMaintenanceWorkOrders.ts
export const useMaintenanceWorkOrders = (equipmentId?: number) => {
  const [workOrders, setWorkOrders] = useState<MaintenanceWorkOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWorkOrders = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (equipmentId) params.append("equipment", equipmentId.toString());

      const response = await api.get(`/maintenance/work-orders/?${params}`);
      setWorkOrders(response.data.results || response.data);
      setError(null);
    } catch (err) {
      setError("Failed to fetch work orders");
      console.error("Error fetching work orders:", err);
    } finally {
      setLoading(false);
    }
  }, [equipmentId]);

  useEffect(() => {
    fetchWorkOrders();
  }, [fetchWorkOrders]);

  const createWorkOrder = async (
    workOrderData: Partial<MaintenanceWorkOrder>
  ) => {
    try {
      const response = await api.post(
        "/maintenance/work-orders/",
        workOrderData
      );
      setWorkOrders((prev) => [...prev, response.data]);
      return response.data;
    } catch (error) {
      console.error("Error creating work order:", error);
      throw error;
    }
  };

  const updateWorkOrder = async (
    id: number,
    data: Partial<MaintenanceWorkOrder>
  ) => {
    try {
      const response = await api.patch(`/maintenance/work-orders/${id}/`, data);
      setWorkOrders((prev) =>
        prev.map((wo) => (wo.id === id ? response.data : wo))
      );
      return response.data;
    } catch (error) {
      console.error("Error updating work order:", error);
      throw error;
    }
  };

  const startWorkOrder = async (id: number) => {
    try {
      const response = await api.post(`/maintenance/work-orders/${id}/start/`);
      setWorkOrders((prev) =>
        prev.map((wo) => (wo.id === id ? response.data : wo))
      );
      return response.data;
    } catch (error) {
      console.error("Error starting work order:", error);
      throw error;
    }
  };

  const completeWorkOrder = async (id: number) => {
    try {
      const response = await api.post(
        `/maintenance/work-orders/${id}/complete/`
      );
      setWorkOrders((prev) =>
        prev.map((wo) => (wo.id === id ? response.data : wo))
      );
      return response.data;
    } catch (error) {
      console.error("Error completing work order:", error);
      throw error;
    }
  };

  return {
    workOrders,
    loading,
    error,
    refetch: fetchWorkOrders,
    createWorkOrder,
    updateWorkOrder,
    startWorkOrder,
    completeWorkOrder,
  };
};
```

## Styling and UI Components

### 1. Status Badge Component

```typescript
// components/ui/StatusBadge.tsx
interface StatusBadgeProps {
  status: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case "ACTIVE":
        return { color: "green", label: "Active" };
      case "MAINTENANCE":
        return { color: "yellow", label: "Maintenance" };
      case "REPAIR":
        return { color: "red", label: "Repair" };
      case "INACTIVE":
        return { color: "gray", label: "Inactive" };
      case "DISPOSED":
        return { color: "red", label: "Disposed" };
      default:
        return { color: "gray", label: status };
    }
  };

  const config = getStatusConfig(status);

  return (
    <span
      className={`px-2 py-1 rounded-full text-xs font-medium bg-${config.color}-100 text-${config.color}-800`}
    >
      {config.label}
    </span>
  );
};
```

### 2. Action Buttons Component

```typescript
// components/machines/ActionButtons.tsx
interface ActionButtonsProps {
  machine: Equipment;
  onEdit: (machine: Equipment) => void;
  onView: (machine: Equipment) => void;
  onMaintenance: (machine: Equipment) => void;
  onDowntime: (machine: Equipment) => void;
}

const ActionButtons: React.FC<ActionButtonsProps> = ({
  machine,
  onEdit,
  onView,
  onMaintenance,
  onDowntime,
}) => {
  return (
    <div className="flex space-x-2">
      <Button
        size="sm"
        variant="outline"
        onClick={() => onView(machine)}
        title="View Details"
      >
        <EyeIcon className="w-4 h-4" />
      </Button>

      <Button
        size="sm"
        variant="outline"
        onClick={() => onEdit(machine)}
        title="Edit Machine"
      >
        <PencilIcon className="w-4 h-4" />
      </Button>

      <Button
        size="sm"
        variant="outline"
        onClick={() => onMaintenance(machine)}
        title="Maintenance"
      >
        <WrenchIcon className="w-4 h-4" />
      </Button>

      <Button
        size="sm"
        variant="outline"
        onClick={() => onDowntime(machine)}
        title="Record Downtime"
        className="text-red-600 hover:text-red-700"
      >
        <ExclamationTriangleIcon className="w-4 h-4" />
      </Button>
    </div>
  );
};
```

## Implementation Steps

### Phase 1: Basic Machine Management (Week 1)

1. **Setup basic page structure**

   - Create main MachinesPage component
   - Implement basic routing
   - Setup API service layer

2. **Implement machine listing**

   - Create MachineTable component
   - Add search and filtering
   - Implement pagination

3. **Add machine CRUD operations**
   - Create AddMachineModal
   - Create EditMachineModal
   - Implement delete functionality

### Phase 2: Enhanced Features (Week 2)

1. **Machine details and history**

   - Create MachineDetailModal
   - Implement maintenance history view
   - Add downtime history

2. **Status management**
   - Implement status change functionality
   - Add status-based filtering
   - Create status dashboard

### Phase 3: Maintenance Integration (Week 3)

1. **Maintenance scheduling**

   - Create maintenance scheduling forms
   - Integrate with work orders
   - Add maintenance calendar view

2. **Downtime tracking**
   - Implement downtime recording
   - Add downtime analytics
   - Create downtime reports

### Phase 4: Advanced Features (Week 4)

1. **Analytics and reporting**

   - Machine utilization reports
   - Maintenance cost tracking
   - Performance metrics

2. **Mobile responsiveness**
   - Optimize for mobile devices
   - Add touch-friendly interactions
   - Implement offline capabilities

## Testing Strategy

### 1. Unit Tests

- Test individual components
- Test API integration hooks
- Test utility functions

### 2. Integration Tests

- Test complete user workflows
- Test API interactions
- Test state management

### 3. E2E Tests

- Test critical user journeys
- Test cross-browser compatibility
- Test mobile responsiveness

## Performance Considerations

1. **Data Loading**

   - Implement pagination for large datasets
   - Use virtual scrolling for tables
   - Add loading states and skeletons

2. **Caching**

   - Cache machine data locally
   - Implement optimistic updates
   - Use React Query for server state

3. **Bundle Optimization**
   - Code splitting by routes
   - Lazy load heavy components
   - Optimize images and assets

## Security Considerations

1. **Authentication**

   - Verify user permissions for each action
   - Implement role-based access control
   - Secure API endpoints

2. **Data Validation**
   - Validate all form inputs
   - Sanitize user data
   - Implement proper error handling

This comprehensive guide provides everything needed to implement a robust machines management page that integrates seamlessly with your Django ERP system's maintenance and manufacturing modules.
