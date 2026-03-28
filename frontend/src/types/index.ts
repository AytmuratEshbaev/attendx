// === Auth ===
export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  username: string;
  email: string | null;
  role: "super_admin" | "admin" | "teacher";
  is_active: boolean;
  last_login_at: string | null;
}

// === Categories ===
export interface Category {
  id: number;
  name: string;
  description: string | null;
  parent_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface CategoryCreate {
  name: string;
  description?: string;
  parent_id?: number | null;
}

export interface CategoryUpdate {
  name?: string;
  description?: string;
  parent_id?: number | null;
}

// === Students ===
export interface Student {
  id: string;
  external_id: string | null;
  employee_no: string;
  name: string;
  class_name: string | null;
  category_id: number | null;
  category: { id: number; name: string } | null;
  parent_phone: string | null;
  face_registered: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface StudentCreate {
  name: string;
  class_name?: string;
  category_id?: number;
  parent_phone?: string;
  external_id?: string;
  employee_no?: string;
}

export type StudentUpdate = Partial<StudentCreate>;

export interface StudentImportResult {
  total: number;
  created: number;
  updated: number;
  errors: string[];
}

// === Attendance ===
export interface DeviceLiveEvent {
  device_name: string;
  employee_no: string;
  student_name: string;
  event_time: string;
  event_type: "entry" | "exit";
  verify_mode: string;
  picture_url: string | null;
}

export interface AttendanceRecord {
  id: string;
  student_id: string;
  student_name: string;
  class_name: string;
  category_name: string | null;
  device_name: string | null;
  event_time: string;
  event_type: "entry" | "exit";
  verify_mode: string;
  picture_url?: string | null;
}

export interface AttendanceStats {
  total_students: number;
  present_today: number;
  absent_today: number;
  attendance_percentage: number;
  by_class: Record<
    string,
    {
      total: number;
      present: number;
      absent: number;
      percentage: number;
    }
  >;
}

export interface DailyAttendance {
  date: string;
  present: number;
  absent: number;
  percentage: number;
}

// === Devices ===
export interface Device {
  id: number;
  name: string;
  ip_address: string;
  port: number;
  username: string;
  is_entry: boolean;
  is_active: boolean;
  last_online_at: string | null;
  model: string | null;
  serial_number: string | null;
}

export interface DeviceCreate {
  name: string;
  ip_address: string;
  port?: number;
  username?: string;
  password: string;
  is_entry?: boolean;
}

export interface DeviceHealth {
  id: number;
  name: string;
  is_online: boolean;
  last_online_at: string | null;
  response_time_ms: number | null;
}

// === Webhooks ===
export interface Webhook {
  id: string;
  url: string;
  events: string[];
  is_active: boolean;
  description: string | null;
  created_at: string;
}

export interface WebhookLog {
  id: string;
  webhook_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  response_status: number | null;
  attempts: number;
  success: boolean;
  delivery_id: string | null;
  duration_ms: number | null;
  error_message: string | null;
  created_at: string;
}

// === Users ===
export interface UserCreate {
  username: string;
  email?: string;
  password: string;
  role: "super_admin" | "admin" | "teacher";
}

export interface UserUpdate {
  email?: string;
  role?: "super_admin" | "admin" | "teacher";
  is_active?: boolean;
}

// === Webhooks Extended ===
export interface WebhookStats {
  total_webhooks: number;
  active_webhooks: number;
  total_deliveries: number;
  successful_deliveries: number;
  failed_deliveries: number;
}

export interface CircuitBreakerState {
  state: "closed" | "open" | "half_open";
  failure_count: number;
  last_failure_at: string | null;
}

// === API Response ===
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  meta: {
    timestamp: string;
    request_id?: string;
  };
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  meta: { timestamp: string };
  pagination: {
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
  };
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  meta: { timestamp: string };
}

// === Timetables ===
export interface Timetable {
  id: number;
  name: string;
  description: string | null;
  timetable_type: "recurring" | "one_time";
  is_active: boolean;
  // Recurring
  weekdays: string[] | null;
  start_time: string | null;
  end_time: string | null;
  // One-time
  date_from: string | null;
  date_to: string | null;
  ot_start_time: string | null;
  ot_end_time: string | null;
  created_at: string;
  updated_at: string;
}

export interface RecurringTimetableCreate {
  timetable_type: "recurring";
  name: string;
  description?: string;
  weekdays: string[];
  start_time: string;
  end_time: string;
  is_active?: boolean;
}

export interface OneTimeTimetableCreate {
  timetable_type: "one_time";
  name: string;
  description?: string;
  date_from: string;
  date_to: string;
  ot_start_time: string;
  ot_end_time: string;
  is_active?: boolean;
}

export type TimetableCreate = RecurringTimetableCreate | OneTimeTimetableCreate;

export interface TimetableUpdate {
  name?: string;
  description?: string;
  is_active?: boolean;
  weekdays?: string[];
  start_time?: string;
  end_time?: string;
  date_from?: string;
  date_to?: string;
  ot_start_time?: string;
  ot_end_time?: string;
}

// === AccessGroups ===
export interface DeviceBrief {
  id: number;
  name: string;
  ip_address: string;
  is_active: boolean;
}

export interface StudentBrief {
  id: string;
  name: string;
  employee_no: string | null;
  class_name: string | null;
  face_registered: boolean;
}

export interface AccessGroupMembership {
  id: number;
  student_id: string;
  student: StudentBrief;
  sync_status: "pending" | "synced" | "failed";
  sync_error: string | null;
  synced_at: string | null;
}

export interface AccessGroup {
  id: number;
  name: string;
  description: string | null;
  timetable_id: number | null;
  timetable: Timetable | null;
  is_active: boolean;
  devices: DeviceBrief[];
  students: AccessGroupMembership[];
  created_at: string;
  updated_at: string;
}

export interface AccessGroupCreate {
  name: string;
  description?: string;
  timetable_id?: number | null;
  is_active?: boolean;
}

export interface AccessGroupUpdate {
  name?: string;
  description?: string;
  timetable_id?: number | null;
  is_active?: boolean;
}

export interface SyncResult {
  synced: number;
  failed: number;
  devices: number;
}

// === Filters ===
export interface AttendanceFilters {
  class_name: string;
  date_from: string;
  date_to: string;
  event_type: string;
  device_name: string;
}
