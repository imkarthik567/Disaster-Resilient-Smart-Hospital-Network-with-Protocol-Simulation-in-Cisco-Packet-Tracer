#!/usr/bin/env python3
"""
Unit Test Suite: Medical Sensor Application & Clinical Gateway Verification
Validates sbc/sensor_node.py, sbc/alarm.py, sbc/gateway.py, and sbc/README.md
against clinical threshold specifications, QoS C1 DiffServ rules, and Packet Tracer constraints.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sbc.alarm import (
    evaluate_vitals, create_alarm_frame, AlarmLevel, VitalThresholds,
    TOS_QOS_C1_CRITICAL, TOS_QOS_C4_WARNING, TOS_QOS_BEST_EFFORT
)
from sbc.sensor_node import BedsideSensorNode, sample_vitals
from sbc.gateway import ClinicalGateway
from sbc.errdetect import SensorFrame, CHECK_CRC16, CHECK_2D_PARITY, ErrorInjector

SENSOR_NODE_PY = os.path.join(PROJECT_ROOT, "sbc", "sensor_node.py")
ALARM_PY = os.path.join(PROJECT_ROOT, "sbc", "alarm.py")
GATEWAY_PY = os.path.join(PROJECT_ROOT, "sbc", "gateway.py")
README_MD = os.path.join(PROJECT_ROOT, "sbc", "README.md")

def test_alarm_threshold_evaluation():
    """Verify vital threshold classification and DiffServ QoS DSCP ToS byte assignment."""
    # 1. Normal vitals
    lvl_norm, desc_norm, tos_norm = evaluate_vitals(hr=72, spo2=98.5, temp=37.0, nurse_pressed=False)
    assert lvl_norm == AlarmLevel.NORMAL
    assert tos_norm == TOS_QOS_BEST_EFFORT
    assert "NORMAL" in desc_norm

    # 2. Warning vitals (mild tachycardia)
    lvl_warn, desc_warn, tos_warn = evaluate_vitals(hr=125, spo2=98.0, temp=37.0)
    assert lvl_warn == AlarmLevel.WARNING
    assert tos_warn == TOS_QOS_C4_WARNING

    # 3. Critical: Severe Bradycardia (HR=35)
    lvl_crit1, desc_crit1, tos_crit1 = evaluate_vitals(hr=35, spo2=98.0, temp=37.0)
    assert lvl_crit1 == AlarmLevel.CRITICAL
    assert tos_crit1 == TOS_QOS_C1_CRITICAL  # 0xB8 (DSCP EF = 46)
    assert "Bradycardia" in desc_crit1

    # 4. Critical: Severe Hypoxia (SpO2=84%)
    lvl_crit2, desc_crit2, tos_crit2 = evaluate_vitals(hr=80, spo2=84.0, temp=37.0)
    assert lvl_crit2 == AlarmLevel.CRITICAL
    assert tos_crit2 == TOS_QOS_C1_CRITICAL
    assert "Hypoxia" in desc_crit2

    # 5. Critical: Emergency Nurse Call Button
    lvl_btn, desc_btn, tos_btn = evaluate_vitals(hr=75, spo2=99.0, temp=37.0, nurse_pressed=True)
    assert lvl_btn == AlarmLevel.CRITICAL
    assert tos_btn == TOS_QOS_C1_CRITICAL
    assert "Nurse Call" in desc_btn

    print("  [PASS] test_alarm_threshold_evaluation (Normal, Warning, Critical QoS C1 DSCP EF verified)")

def test_sensor_node_telemetry_emission():
    """Verify BedsideSensorNode routine and emergency alarm telemetry emission and CSV logging."""
    node = BedsideSensorNode(node_id="SBC-ICU-101", patient_id="ICU-101")

    # Routine emission
    f_norm, wire_norm, log_norm = node.emit_telemetry_tick(simulate_anomaly=False)
    assert f_norm.patient_id == "ICU-101"
    assert f_norm.check_type == CHECK_CRC16
    assert "ROUTINE_TELEMETRY" in log_norm
    assert "SBC-ICU-101" in log_norm

    # Emergency alarm emission
    f_alarm, wire_alarm, log_alarm = node.emit_telemetry_tick(simulate_anomaly=True)
    assert "EMERGENCY_ALARM" in log_alarm
    assert "CRITICAL_C1" in log_alarm
    assert "QoS_TOS=0xB8" in log_alarm

    print("  [PASS] test_sensor_node_telemetry_emission (Routine and emergency alarm emission verified)")

def test_gateway_ingestion_and_self_healing():
    """Verify ClinicalGateway frame validation, 2D parity self-healing, and alarm forwarding."""
    gateway = ClinicalGateway(node_id="GATEWAY-SBC-01", bind_port=5005)

    # 1. Ingest clean frame
    f_clean = SensorFrame(seq_num=10, patient_id="ICU-101", value=75.0, payload=b"TELEMETRY|HR=75|SPO2=98.0", check_type=CHECK_CRC16)
    ok1, dec1, log1 = gateway.process_raw_frame(f_clean.encode())
    assert ok1 is True
    assert "VALID_OK" in log1

    # 2. Ingest frame with 1-bit corruption protected by 2D parity -> Self-Healing!
    f_2d = SensorFrame(seq_num=11, patient_id="ICU-101", value=78.0, payload=b"TELEMETRY|HR=78|SPO2=99.0", check_type=CHECK_2D_PARITY)
    corrupted_wire = ErrorInjector.flip_bit(f_2d.encode(), bit_index=26 * 8 + 4)
    ok2, dec2, log2 = gateway.process_raw_frame(corrupted_wire)
    assert ok2 is True  # Decoded successfully due to self-healing!
    assert "HEALED_OK" in log2
    assert gateway.total_healed >= 1

    # 3. Ingest corrupted frame (unrecoverable CRC error) -> Discarded
    bad_wire = ErrorInjector.flip_bit(f_clean.encode(), bit_index=15)
    ok3, dec3, log3 = gateway.process_raw_frame(bad_wire)
    assert ok3 is False
    assert "DISCARDED" in log3
    assert gateway.total_corrupted >= 1

    # 4. Ingest emergency alarm -> Immediate C1 forward
    f_alarm = SensorFrame(seq_num=12, patient_id="ICU-101", sensor_type=99, value=160.0, payload=b"ALARM|LVL=2|Cardiac Arrest", check_type=CHECK_CRC16)
    ok4, dec4, log4 = gateway.process_raw_frame(f_alarm.encode())
    assert ok4 is True
    assert "CRITICAL_ALARM" in log4
    assert gateway.total_alarms >= 1

    # 5. Generate and send patient summary
    summary = gateway.generate_and_send_summary("ICU-101")
    assert summary is not None
    assert b"SUMMARY|PT=ICU-101" in summary
    assert gateway.total_summaries_sent >= 1

    print("  [PASS] test_gateway_ingestion_and_self_healing (Validation, 1-bit self-healing & forwarding verified)")

def test_patient_log_bulk_transfer_mode():
    """Verify bulk patient history transfer using GBN vs Selective Repeat."""
    node = BedsideSensorNode(node_id="SBC-ICU-101", patient_id="ICU-101")

    # Run 40 records under 10% loss for both GBN and SR
    m_gbn, _ = node.run_patient_log_transfer("GBN", total_records=40, loss_rate=0.10)
    m_sr, _ = node.run_patient_log_transfer("SR", total_records=40, loss_rate=0.10)

    # Assert both achieved 100% in-order delivery
    assert m_gbn['delivered_chunks'] == 40
    assert m_sr['delivered_chunks'] == 40

    # Selective Repeat must incur fewer retransmissions than Go-Back-N under loss!
    assert m_sr['frames_retransmitted'] <= m_gbn['frames_retransmitted']
    assert m_sr['protocol_efficiency_pct'] >= m_gbn['protocol_efficiency_pct']

    print("  [PASS] test_patient_log_bulk_transfer_mode (GBN vs SR bulk log transfer verified)")

def test_sbc_readme_device_matrix():
    """Verify sbc/README.md documents all devices, scripts, and startup parameters."""
    with open(README_MD, "r", encoding="utf-8") as f:
        readme_text = f.read()

    devices = ["SBC-ICU-101", "SBC-SURG-102", "SBC-CLINIC-201", "Server-EHR"]
    for dev in devices:
        assert dev in readme_text, f"Missing device documentation for {dev} in sbc/README.md"

    scripts = ["sensor_node.py", "alarm.py", "gateway.py", "arq.py", "errdetect.py", "adapter_pt.py"]
    for sc in scripts:
        assert sc in readme_text, f"Missing script reference {sc} in sbc/README.md"

    assert "172.16.7.138" in readme_text  # ICU SBC IP
    assert "172.16.7.168" in readme_text  # Surgery SBC IP
    assert "172.16.7.202" in readme_text  # Clinic SBC IP
    assert "172.16.7.195" in readme_text  # Records Server IP
    assert "main.py" in readme_text

    print("  [PASS] test_sbc_readme_device_matrix (All devices, IPs, and startup params documented)")

def run_all_tests():
    print("=" * 70)
    print("  RUNNING MEDICAL SENSOR APP & GATEWAY VERIFICATION SUITE")
    print("=" * 70)
    test_alarm_threshold_evaluation()
    test_sensor_node_telemetry_emission()
    test_gateway_ingestion_and_self_healing()
    test_patient_log_bulk_transfer_mode()
    test_sbc_readme_device_matrix()
    print("=" * 70)
    print("  ALL 5 MEDICAL SENSOR APPLICATION TESTS PASSED")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
