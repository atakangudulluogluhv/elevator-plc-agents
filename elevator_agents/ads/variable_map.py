import pyads

# --- Inputs (Python reads from PLCStudent port 852) ---
IN_BTN_LEVEL = ["GVL.ixButtonAtLevel1", "GVL.ixButtonAtLevel2", "GVL.ixButtonAtLevel3"]
IN_SENSOR_LEVEL = ["GVL.ixSensorAtLevel1", "GVL.ixSensorAtLevel2", "GVL.ixSensorAtLevel3"]
IN_BTN_GREEN = "GVL.ixButtGreen"
IN_BTN_RED = "GVL.ixButtRed"
IN_BTN_INSIDE = ["GVL.ixButtInsideElevat1", "GVL.ixButtInsideElevat2", "GVL.ixButtInsideElevat3"]
IN_DOOR_CLOSED = "GVL.ixDoorClosed"
IN_DOOR_OPEN = "GVL.ixDoorOpen"

ALL_INPUTS = IN_BTN_LEVEL + IN_SENSOR_LEVEL + [IN_BTN_GREEN, IN_BTN_RED] + IN_BTN_INSIDE + [IN_DOOR_CLOSED, IN_DOOR_OPEN]

# --- Outputs (Python writes to PLCStudent port 852) ---
OUT_LAMP_LEVEL = ["GVL.qxLampAtLevel1", "GVL.qxLampAtLevel2", "GVL.qxLampAtLevel3"]
OUT_MOTOR_UP = "GVL.qxMotorUp"
OUT_MOTOR_DOWN = "GVL.qxMotorDown"
OUT_LAMP_INSIDE = ["GVL.qxLampElevat1", "GVL.qxLampElevat2", "GVL.qxLampElevat3"]
OUT_DOOR_CLOSE = "GVL.qxDoorClose"
OUT_DISPLAY = "GVL.qiDispElevat"

BOOL_OUTPUTS = OUT_LAMP_LEVEL + [OUT_MOTOR_UP, OUT_MOTOR_DOWN] + OUT_LAMP_INSIDE + [OUT_DOOR_CLOSE]

# pyads type mappings
TYPE_BOOL = pyads.PLCTYPE_BOOL
TYPE_UINT = pyads.PLCTYPE_UINT
