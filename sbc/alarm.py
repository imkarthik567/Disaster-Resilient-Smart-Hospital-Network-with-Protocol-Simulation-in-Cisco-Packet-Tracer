#!/usr/bin/env python3
"""
================================================================================
Clinical Alarm & Threshold Evaluation Engine (QoS Class C1 Prioritization)
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Platform: Cisco Packet Tracer 8.x SBC-PT (Python 3) & Desktop Workstation
Purpose:
  1. Monitors physiological vital signs against established clinical thresholds.
  2. Raises high-priority alarm frames marked for QoS Class C1 (DSCP EF = 46).
  3. Activates local SBC physical actuators (Buzzer Siren D1, Visual LED D2).
  4. Provides structured alarm payload serialization compatible with SensorFrame.
================================================================================
"""

import sys
import time

# Hardware pin imports if running inside Packet Tracer
try:
    from gpio import *
    IS_PACKET_TRACER = True
except ImportError:
    IS_PACKET_TRACER = False

# Error detection library import
try:
    from sbc.errdetect import SensorFrame, CHECK_CRC16
except ImportError:
    from errdetect import SensorFrame, CHECK_CRC16

# ==============================================================================
# 1. CLINICAL VITAL THRESHOLDS & ALARM LEVELS
# ==============================================================================

class VitalThresholds:
    """Clinical thresholds for adult ICU patient vital signs."""
    # Heart Rate (BPM)
    HR_BRADYCARDIA = 50       # Low heart rate warning
    HR_TACHYCARDIA = 120      # High heart rate warning
    HR_CRITICAL_LOW = 40      # Severe sinus bradycardia / cardiac arrest
    HR_CRITICAL_HIGH = 150    # Ventricular tachycardia / fibrillation

    # Blood Oxygen Saturation - SpO2 (%)
    SPO2_WARNING = 92.0       # Mild hypoxemia
    SPO2_CRITICAL = 88.0      # Severe hypoxemia / respiratory distress

    # Body Temperature (Degrees Celsius)
    TEMP_HYPOTHERMIA = 35.5   # Core hypothermia
    TEMP_PYREXIA = 38.5       # High-grade fever
    TEMP_HYPERPYREXIA = 40.0  # Life-threatening hyperpyrexia

class AlarmLevel:
    NORMAL = 0     # Routine telemetry (Best Effort / C4)
    WARNING = 1    # Abnormal vitals (QoS C4 / AF21)
    CRITICAL = 2   # Life-threatening event (QoS C1 / DSCP EF = 46)

# ==============================================================================
# 2. QoS DSCP MARKINGS (DIFFSERV ALIGNMENT)
# ==============================================================================

# IPv4 ToS byte = DSCP value shifted left by 2 bits (bits 0-1 are ECN)
# C1: Life-Critical Telemetry -> DSCP EF (decimal 46 = 0x2E -> ToS = 46 << 2 = 184 = 0xB8)
# C4: Business / Warning Vitals -> DSCP AF21 (decimal 18 = 0x12 -> ToS = 18 << 2 = 72 = 0x48)
# Best Effort: DSCP 0 -> ToS = 0
TOS_QOS_C1_CRITICAL = 0xB8   # DSCP EF  (46) -> Matches ACL-QOS-C1-TELEMETRY
TOS_QOS_C4_WARNING = 0x48    # DSCP AF21 (18) -> Matches ACL-QOS-C4-ADMIN
TOS_QOS_BEST_EFFORT = 0x00   # DSCP CS0 (0)

# Hardware Actuator Pins
PIN_ALARM_SIREN = 1  # Digital Pin D1 (Buzzer Siren)
PIN_ALERT_LED = 2    # Digital Pin D2 (Flashing Red LED)

def trigger_hardware_actuators(level):
    """Controls physical buzzer and LED pins based on alarm level."""
    if IS_PACKET_TRACER:
        try:
            if level == AlarmLevel.CRITICAL:
                digitalWrite(PIN_ALARM_SIREN, HIGH)
                digitalWrite(PIN_ALERT_LED, HIGH)
            elif level == AlarmLevel.WARNING:
                digitalWrite(PIN_ALARM_SIREN, LOW)
                digitalWrite(PIN_ALERT_LED, HIGH)
            else:
                digitalWrite(PIN_ALARM_SIREN, LOW)
                digitalWrite(PIN_ALERT_LED, LOW)
        except Exception:
            pass

def evaluate_vitals(hr, spo2, temp, nurse_pressed=False):
    """
    Evaluates patient vitals and returns:
      (alarm_level: int, condition_desc: str, dscp_tos: int)
    """
    reasons = []

    # 1. Emergency Nurse Call Override
    if nurse_pressed:
        trigger_hardware_actuators(AlarmLevel.CRITICAL)
        return (
            AlarmLevel.CRITICAL,
            "EMERGENCY: Bedside Nurse Call Button Pressed",
            TOS_QOS_C1_CRITICAL
        )

    # 2. Critical Threshold Checks
    if hr <= VitalThresholds.HR_CRITICAL_LOW:
        reasons.append("Severe Bradycardia (HR=%d <= %d)" % (hr, VitalThresholds.HR_CRITICAL_LOW))
    elif hr >= VitalThresholds.HR_CRITICAL_HIGH:
        reasons.append("Ventricular Tachycardia (HR=%d >= %d)" % (hr, VitalThresholds.HR_CRITICAL_HIGH))

    if spo2 <= VitalThresholds.SPO2_CRITICAL:
        reasons.append("Severe Hypoxia (SpO2=%.1f%% <= %.1f%%)" % (spo2, VitalThresholds.SPO2_CRITICAL))

    if temp >= VitalThresholds.TEMP_HYPERPYREXIA:
        reasons.append("Hyperpyrexia (Temp=%.1fC >= %.1fC)" % (temp, VitalThresholds.TEMP_HYPERPYREXIA))

    if reasons:
        trigger_hardware_actuators(AlarmLevel.CRITICAL)
        return (
            AlarmLevel.CRITICAL,
            "CRITICAL: " + "; ".join(reasons),
            TOS_QOS_C1_CRITICAL
        )

    # 3. Warning Threshold Checks
    if hr < VitalThresholds.HR_BRADYCARDIA or hr > VitalThresholds.HR_TACHYCARDIA:
        reasons.append("Abnormal Heart Rate (%d bpm)" % hr)

    if spo2 < VitalThresholds.SPO2_WARNING:
        reasons.append("Mild Hypoxemia (SpO2=%.1f%%)" % spo2)

    if temp < VitalThresholds.TEMP_HYPOTHERMIA or temp > VitalThresholds.TEMP_PYREXIA:
        reasons.append("Abnormal Temp (%.1fC)" % temp)

    if reasons:
        trigger_hardware_actuators(AlarmLevel.WARNING)
        return (
            AlarmLevel.WARNING,
            "WARNING: " + "; ".join(reasons),
            TOS_QOS_C4_WARNING
        )

    # 4. Normal Hemodynamics
    trigger_hardware_actuators(AlarmLevel.NORMAL)
    return (
        AlarmLevel.NORMAL,
        "NORMAL: Stable Hemodynamics",
        TOS_QOS_BEST_EFFORT
    )

def create_alarm_frame(seq_num, patient_id, hr, spo2, temp, condition_desc, alarm_level, dscp_tos):
    """
    Constructs a prioritized SensorFrame with payload metadata and error protection.
    Returns: (SensorFrame, dscp_tos: int)
    """
    # Payload format: ALARM|LEVEL|DESC|HR|SPO2|TEMP
    payload_str = "ALARM|LVL=%d|%s|HR=%d|SPO2=%.1f|TEMP=%.1f" % (
        alarm_level, condition_desc, hr, spo2, temp
    )
    # Sensor type 99 indicates high-priority clinical alarm
    frame = SensorFrame(
        seq_num=seq_num,
        patient_id=patient_id,
        sensor_type=99 if alarm_level == AlarmLevel.CRITICAL else 1,
        value=float(hr),
        timestamp=int(time.time()),
        payload=payload_str.encode('utf-8'),
        check_type=CHECK_CRC16
    )
    return frame, dscp_tos
