#!/usr/bin/env python3
"""
================================================================================
Bedside Medical Patient Monitor Application (SBC-ICU-101 / SBC-SURG-102)
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Platform: Cisco Packet Tracer 8.x SBC-PT (Python 3) & Desktop Workstation
Features:
  1. Real-time patient telemetry generation (HR, SpO2, Temp, Patient ID)
  2. Integration with sbc.alarm for QoS C1 (DSCP EF = 46) prioritization
  3. Error-check protection via sbc.errdetect (CRC-16 or 2D Parity)
  4. Patient Log Transfer Mode: Bulk transfer via Go-Back-N or Selective Repeat
  5. Uniform CSV-style event logging for automated /sim parsing
================================================================================
"""

import sys
import time
import random

# Hardware pin imports if running inside Packet Tracer
try:
    from gpio import *
    IS_PACKET_TRACER = True
except ImportError:
    IS_PACKET_TRACER = False

# BSD Socket import
try:
    import socket
    SOCKET_AVAILABLE = True
except ImportError:
    SOCKET_AVAILABLE = False

# Local module imports
try:
    from sbc.errdetect import SensorFrame, SENSOR_ECG, SENSOR_SPO2, SENSOR_TEMP, CHECK_CRC16, CHECK_2D_PARITY
    from sbc.alarm import evaluate_vitals, create_alarm_frame, AlarmLevel, TOS_QOS_C1_CRITICAL
    from sbc.arq import GoBackNProtocol, SelectiveRepeatProtocol, StopAndWaitProtocol, SimulatedChannel, ARQSimulation
except ImportError:
    from errdetect import SensorFrame, SENSOR_ECG, SENSOR_SPO2, SENSOR_TEMP, CHECK_CRC16, CHECK_2D_PARITY
    from alarm import evaluate_vitals, create_alarm_frame, AlarmLevel, TOS_QOS_C1_CRITICAL
    from arq import GoBackNProtocol, SelectiveRepeatProtocol, StopAndWaitProtocol, SimulatedChannel, ARQSimulation

# ==============================================================================
# HARDWARE PINS & CLINICAL TELEMETRY SAMPLER
# ==============================================================================

PIN_ANALOG_ECG = 0   # Pin A0: ECG Heart Rate
PIN_ANALOG_SPO2 = 1  # Pin A1: SpO2 Pulse Oximeter
PIN_DIGITAL_NURSE = 0 # Pin D0: Emergency Nurse Call Button

def sample_vitals(patient_id="ICU-101", simulate_anomaly=False):
    """
    Samples physiological sensors.
    If simulate_anomaly is True or nurse button is pressed, returns critical vitals.
    """
    if IS_PACKET_TRACER:
        try:
            raw_ecg = analogRead(PIN_ANALOG_ECG)
            raw_spo2 = analogRead(PIN_ANALOG_SPO2)
            nurse_btn = (digitalRead(PIN_DIGITAL_NURSE) == HIGH)
            hr = int(40 + (raw_ecg / 1023.0) * 140)
            spo2 = round(70.0 + (raw_spo2 / 1023.0) * 30.0, 1)
            temp = 37.0
            return hr, spo2, temp, nurse_btn
        except Exception:
            pass

    # Desktop synthetic patient simulation
    if simulate_anomaly:
        hr = random.choice([38, 165])  # Severe Bradycardia or Ventricular Tachycardia
        spo2 = round(random.uniform(82.0, 87.5), 1)  # Severe Hypoxia
        temp = round(random.uniform(39.2, 40.2), 1)  # High Pyrexia
        nurse_btn = True
    else:
        hr = random.randint(68, 86)
        spo2 = round(random.uniform(97.0, 99.8), 1)
        temp = round(random.uniform(36.8, 37.3), 1)
        nurse_btn = False

    return hr, spo2, temp, nurse_btn

# ==============================================================================
# CSV EVENT LOGGER
# ==============================================================================

def log_csv_event(node_id, event_type, seq_num, patient_id, vitals_str, status_str, detail_str):
    """
    Emits a structured CSV-style log line formatted as:
      TIMESTAMP,NODE_ID,EVENT_TYPE,SEQ_NUM,PATIENT_ID,VITALS,STATUS,DETAIL
    """
    ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
    line = "%s,%s,%s,%d,%s,%s,%s,%s" % (
        ts, node_id, event_type, seq_num, patient_id, vitals_str, status_str, detail_str
    )
    print(line)
    return line

# ==============================================================================
# BEDSIDE SENSOR NODE APPLICATION CLASS
# ==============================================================================

class BedsideSensorNode:
    """
    Clinical bedside telemetry monitor running on SBC-ICU-101 or SBC-SURG-102.
    Emits periodic telemetry and prioritized QoS C1 alarm packets.
    """
    def __init__(self, node_id="SBC-ICU-101", patient_id="ICU-101", gateway_ip="172.16.7.195", gateway_port=5005):
        self.node_id = node_id
        self.patient_id = patient_id
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port

        self.seq_num = 0
        self.sock = None
        self.event_log = []

        if SOCKET_AVAILABLE:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            except Exception:
                self.sock = None

    def emit_telemetry_tick(self, simulate_anomaly=False):
        """Executes a 1-second vital sampling, alarm check, and network transmission."""
        hr, spo2, temp, nurse_btn = sample_vitals(self.patient_id, simulate_anomaly=simulate_anomaly)
        alarm_lvl, condition_desc, dscp_tos = evaluate_vitals(hr, spo2, temp, nurse_btn)

        vitals_str = "HR=%d;SPO2=%.1f;TEMP=%.1f" % (hr, spo2, temp)

        if alarm_lvl == AlarmLevel.CRITICAL:
            # Build prioritized Alarm Frame
            frame, tos = create_alarm_frame(
                self.seq_num, self.patient_id, hr, spo2, temp, condition_desc, alarm_lvl, dscp_tos
            )
            wire_bytes = frame.encode()
            event_type = "EMERGENCY_ALARM"
            status = "CRITICAL_C1"

            # Set IPv4 ToS byte to 0xB8 (DSCP EF) if socket supports it
            if self.sock is not None:
                try:
                    self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, TOS_QOS_C1_CRITICAL)
                    self.sock.sendto(wire_bytes, (self.gateway_ip, self.gateway_port))
                except Exception:
                    pass

            detail = "QoS_TOS=0x%02X;%s" % (TOS_QOS_C1_CRITICAL, condition_desc)

        else:
            # Build routine SensorFrame
            payload_str = "TELEMETRY|HR=%d|SPO2=%.1f|TEMP=%.1f" % (hr, spo2, temp)
            frame = SensorFrame(
                seq_num=self.seq_num,
                patient_id=self.patient_id,
                sensor_type=SENSOR_ECG,
                value=float(hr),
                timestamp=int(time.time()),
                payload=payload_str.encode('utf-8'),
                check_type=CHECK_CRC16
            )
            wire_bytes = frame.encode()
            event_type = "ROUTINE_TELEMETRY"
            status = "NORMAL_C4" if alarm_lvl == AlarmLevel.WARNING else "NORMAL_BE"

            if self.sock is not None:
                try:
                    self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, dscp_tos)
                    self.sock.sendto(wire_bytes, (self.gateway_ip, self.gateway_port))
                except Exception:
                    pass

            detail = condition_desc

        log_line = log_csv_event(
            self.node_id, event_type, self.seq_num, self.patient_id, vitals_str, status, detail
        )
        self.event_log.append(log_line)
        self.seq_num = (self.seq_num + 1) % 65536
        return frame, wire_bytes, log_line

    def run_patient_log_transfer(self, protocol_type="SR", total_records=100, loss_rate=0.10):
        """
        Transfers historical patient vital records using Go-Back-N or Selective Repeat.
        Generates comparative metrics and logs execution progress in CSV.
        """
        protocol_type = protocol_type.upper()
        log_csv_event(
            self.node_id, "LOG_TRANSFER_START", 0, self.patient_id,
            "TOTAL_RECORDS=%d" % total_records, "STARTING", "Protocol=%s;LossRate=%.2f" % (protocol_type, loss_rate)
        )

        # Generate synthetic historical patient log records
        records = []
        for i in range(total_records):
            rec = "REC#%04d|PT=%s|HR=%d|SPO2=%.1f|TEMP=%.1f|T=%d" % (
                i, self.patient_id, 70 + (i % 25), 98.0 - (i % 3) * 0.5, 36.8 + (i % 5) * 0.2, 1730000000 + i * 10
            )
            records.append(rec.encode('utf-8'))

        channel = SimulatedChannel(loss_prob=loss_rate, prop_delay=3, seed=42)

        if protocol_type == "GBN":
            proto = GoBackNProtocol(window_size=4, seq_modulus=16, timeout_ticks=15, verbose=False)
        elif protocol_type == "SR":
            proto = SelectiveRepeatProtocol(window_size=4, seq_modulus=16, timeout_ticks=15, verbose=False)
        else:
            proto = StopAndWaitProtocol(timeout_ticks=15, verbose=False)

        sim = ARQSimulation(proto, channel, max_ticks=50000)
        metrics, trace = sim.run_transfer(records)

        summary_detail = "FramesSent=%d;Retx=%d;Timeouts=%d;ElapsedTicks=%d;Eff=%.2f%%" % (
            metrics['frames_sent'],
            metrics['frames_retransmitted'],
            metrics['timeouts'],
            metrics['elapsed_ticks'],
            metrics['protocol_efficiency_pct']
        )

        status_str = "SUCCESS" if len(proto.delivered_chunks) == total_records else "FAILED"
        log_csv_event(
            self.node_id, "LOG_TRANSFER_COMPLETE", total_records, self.patient_id,
            "DELIVERED=%d/%d" % (len(proto.delivered_chunks), total_records),
            status_str,
            "Protocol=%s;%s" % (protocol_type, summary_detail)
        )

        return metrics, trace

# ==============================================================================
# MAIN EXECUTION CLI
# ==============================================================================

def main():
    print("=" * 80)
    print("  BEDSIDE MEDICAL SENSOR NODE - CLINICAL TELEMETRY EMITTER")
    print("  CSV Header: timestamp,node_id,event_type,seq_num,patient_id,vitals,status,detail")
    print("=" * 80)

    node = BedsideSensorNode(node_id="SBC-ICU-101", patient_id="ICU-101")

    # Run 5 routine ticks + 1 emergency tick
    for i in range(5):
        node.emit_telemetry_tick(simulate_anomaly=False)
        if IS_PACKET_TRACER:
            sleep(1.0)
        else:
            time.sleep(0.1)

    # Emergency tick
    node.emit_telemetry_tick(simulate_anomaly=True)

    # Demo patient log transfer with GBN and SR
    print("\n--- Running Comparative Patient Log Transfer Demo ---")
    m_gbn, _ = node.run_patient_log_transfer("GBN", total_records=50, loss_rate=0.10)
    m_sr, _ = node.run_patient_log_transfer("SR", total_records=50, loss_rate=0.10)

    print("\n" + "=" * 80)
    print("  LOG TRANSFER COMPARISON: GBN vs SELECTIVE REPEAT (50 Records, 10% Loss)")
    print("  GBN Efficiency: %6.2f%% | Retransmissions: %d | Timeouts: %d" % (
        m_gbn['protocol_efficiency_pct'], m_gbn['frames_retransmitted'], m_gbn['timeouts']
    ))
    print("  SR  Efficiency: %6.2f%% | Retransmissions: %d | Timeouts: %d" % (
        m_sr['protocol_efficiency_pct'], m_sr['frames_retransmitted'], m_sr['timeouts']
    ))
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
