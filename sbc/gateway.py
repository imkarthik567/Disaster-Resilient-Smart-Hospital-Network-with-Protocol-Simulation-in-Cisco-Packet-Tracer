#!/usr/bin/env python3
"""
================================================================================
Clinical Gateway & Telemetry Ingestion Node (SBC-CLINIC-201 / Server-EHR)
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Platform: Cisco Packet Tracer 8.x SBC-PT (Python 3) & Desktop Workstation
Features:
  1. Ingests bedside sensor telemetry from ICU/Surgery SBCs over UDP (port 5005)
  2. Validates frames via sbc.errdetect (CRC-16, 16-Bit Checksum, 2D Parity)
  3. Automatic 1-bit self-healing logging when 2D Parity is enabled
  4. Immediate emergency alarm forwarding to Records Server with QoS C1 marking
  5. Aggregates periodic vital statistics and forwards summaries to Records Server (172.16.7.195:5006)
  6. Standardized CSV event logging for automated report extraction
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

# BSD Socket import
try:
    import socket
    SOCKET_AVAILABLE = True
except ImportError:
    SOCKET_AVAILABLE = False

# Local module imports
try:
    from sbc.errdetect import SensorFrame, CHECK_CRC16, CHECK_2D_PARITY
    from sbc.alarm import AlarmLevel, TOS_QOS_C1_CRITICAL
except ImportError:
    from errdetect import SensorFrame, CHECK_CRC16, CHECK_2D_PARITY
    from alarm import AlarmLevel, TOS_QOS_C1_CRITICAL

# CSV Event Logger Helper
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
# CLINICAL GATEWAY CLASS
# ==============================================================================

class ClinicalGateway:
    """
    Ingestion gateway node deployed on SBC-CLINIC-201 or hospital server farm.
    Validates, logs, filters, and forwards patient vital streams.
    """
    def __init__(self, node_id="GATEWAY-SBC-01", bind_port=5005, records_server_ip="172.16.7.195", records_server_port=5006):
        self.node_id = node_id
        self.bind_port = int(bind_port)
        self.records_server_ip = records_server_ip
        self.records_server_port = int(records_server_port)

        self.sock = None
        self.forward_sock = None

        # Statistics & Storage
        self.total_received = 0
        self.total_valid = 0
        self.total_corrupted = 0
        self.total_healed = 0
        self.total_alarms = 0
        self.total_summaries_sent = 0

        # Patient vital history buffer: patient_id -> list of {'hr': float, 'spo2': float, 'ts': int}
        self.patient_buffers = {}
        self.event_log = []

        if SOCKET_AVAILABLE:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.sock.bind(("0.0.0.0", self.bind_port))
                self.sock.setblocking(False)

                self.forward_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            except Exception as e:
                self.sock = None
                self.forward_sock = None

    def process_raw_frame(self, raw_bytes):
        """
        Validates raw frame bytes, updates metrics, handles self-healing,
        and triggers immediate forwarding for alarms.
        """
        self.total_received += 1
        ok, frame, msg = SensorFrame.decode(raw_bytes)

        if not ok:
            # Corrupted frame rejected by error detection
            self.total_corrupted += 1
            log_line = log_csv_event(
                self.node_id, "FRAME_CORRUPTED", 0, "UNKNOWN",
                "RAW_BYTES=%d" % len(raw_bytes), "DISCARDED", msg
            )
            self.event_log.append(log_line)
            return False, None, log_line

        # Frame successfully decoded
        self.total_valid += 1
        is_healed = ("self-healed" in msg.lower())
        if is_healed:
            self.total_healed += 1

        payload_text = frame.payload.decode('utf-8', errors='replace')
        is_alarm = ("ALARM" in payload_text or frame.sensor_type == 99)

        # Parse vitals from payload
        hr = frame.value
        spo2 = 98.0
        temp = 37.0
        try:
            for part in payload_text.split("|"):
                if part.startswith("SPO2="):
                    spo2 = float(part.split("=")[1])
                elif part.startswith("TEMP="):
                    temp = float(part.split("=")[1])
        except Exception:
            pass

        vitals_str = "HR=%.1f;SPO2=%.1f;TEMP=%.1f" % (hr, spo2, temp)

        # Record vital in patient history buffer
        if frame.patient_id not in self.patient_buffers:
            self.patient_buffers[frame.patient_id] = []
        self.patient_buffers[frame.patient_id].append({
            'hr': hr,
            'spo2': spo2,
            'temp': temp,
            'timestamp': frame.timestamp
        })

        if is_alarm:
            self.total_alarms += 1
            status = "CRITICAL_ALARM"
            event_type = "ALARM_INGESTED"

            # Immediate forward to Records Server with QoS C1 ToS
            self.forward_to_records_server(raw_bytes, tos=TOS_QOS_C1_CRITICAL)
            detail = "FORWARDED_IMMEDIATE_C1;%s" % payload_text
        else:
            status = "HEALED_OK" if is_healed else "VALID_OK"
            event_type = "TELEMETRY_INGESTED"
            detail = msg

        log_line = log_csv_event(
            self.node_id, event_type, frame.seq_num, frame.patient_id, vitals_str, status, detail
        )
        self.event_log.append(log_line)
        return True, frame, log_line

    def forward_to_records_server(self, data_bytes, tos=0x00):
        """Forwards binary payload to hospital records server over UDP."""
        if self.forward_sock is not None:
            try:
                self.forward_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, tos)
                self.forward_sock.sendto(data_bytes, (self.records_server_ip, self.records_server_port))
                return True
            except Exception:
                return False
        return True

    def generate_and_send_summary(self, patient_id):
        """
        Computes vital statistics summary for patient_id and forwards to Records Server.
        """
        history = self.patient_buffers.get(patient_id, [])
        if not history:
            return None

        hr_vals = [entry['hr'] for entry in history]
        spo2_vals = [entry['spo2'] for entry in history]
        temp_vals = [entry['temp'] for entry in history]

        avg_hr = sum(hr_vals) / len(hr_vals)
        min_hr = min(hr_vals)
        max_hr = max(hr_vals)
        avg_spo2 = sum(spo2_vals) / len(spo2_vals)
        avg_temp = sum(temp_vals) / len(temp_vals)

        summary_payload = (
            "SUMMARY|PT=%s|COUNT=%d|AVG_HR=%.1f|MIN_HR=%.1f|MAX_HR=%.1f|AVG_SPO2=%.1f|AVG_TEMP=%.1f" % (
                patient_id, len(history), avg_hr, min_hr, max_hr, avg_spo2, avg_temp
            )
        ).encode('utf-8')

        # Forward summary to Records Server
        self.forward_to_records_server(summary_payload, tos=0x00)
        self.total_summaries_sent += 1

        vitals_summary = "AVG_HR=%.1f;AVG_SPO2=%.1f;SAMPLES=%d" % (avg_hr, avg_spo2, len(history))
        detail = "Target=%s:%d;SummaryPayloadLen=%d" % (
            self.records_server_ip, self.records_server_port, len(summary_payload)
        )

        log_line = log_csv_event(
            self.node_id, "SUMMARY_FORWARDED", 0, patient_id,
            vitals_summary, "FORWARDED_OK", detail
        )
        self.event_log.append(log_line)
        return summary_payload

    def get_metrics(self):
        """Returns gateway performance metrics."""
        return {
            "node_id": self.node_id,
            "total_received": self.total_received,
            "total_valid": self.total_valid,
            "total_corrupted": self.total_corrupted,
            "total_healed": self.total_healed,
            "total_alarms": self.total_alarms,
            "total_summaries_sent": self.total_summaries_sent,
            "active_patients": len(self.patient_buffers)
        }

# ==============================================================================
# MAIN EXECUTION CLI / DEMO
# ==============================================================================

def main():
    print("=" * 80)
    print("  CLINICAL TELEMETRY GATEWAY - INGESTION & FORWARDING ENGINE")
    print("  CSV Header: timestamp,node_id,event_type,seq_num,patient_id,vitals,status,detail")
    print("=" * 80)

    gateway = ClinicalGateway(node_id="GATEWAY-SBC-01", bind_port=5005)

    try:
        from sbc.errdetect import SensorFrame, CHECK_CRC16, CHECK_2D_PARITY, ErrorInjector
    except ImportError:
        from errdetect import SensorFrame, CHECK_CRC16, CHECK_2D_PARITY, ErrorInjector

    # 1. Clean frames
    for i in range(4):
        f = SensorFrame(seq_num=i, patient_id="ICU-101", value=72.0 + i, payload=b"TELEMETRY|HR=72|SPO2=99.0", check_type=CHECK_CRC16)
        gateway.process_raw_frame(f.encode())

    # 2. Self-healing 2D parity frame
    f_2d = SensorFrame(seq_num=4, patient_id="ICU-101", value=76.0, payload=b"TELEMETRY|HR=76|SPO2=98.5", check_type=CHECK_2D_PARITY)
    wire_2d = f_2d.encode()
    corrupted_wire = ErrorInjector.flip_bit(wire_2d, bit_index=26 * 8 + 3)
    gateway.process_raw_frame(corrupted_wire)

    # 3. Emergency Alarm frame
    f_alarm = SensorFrame(seq_num=5, patient_id="ICU-101", sensor_type=99, value=155.0, payload=b"ALARM|LVL=2|Tachycardia|HR=155|SPO2=86.0", check_type=CHECK_CRC16)
    gateway.process_raw_frame(f_alarm.encode())

    # 4. Corrupted frame (CRC mismatch)
    f_corrupt = SensorFrame(seq_num=6, patient_id="ICU-101", value=70.0, payload=b"TELEMETRY|HR=70|SPO2=99.0", check_type=CHECK_CRC16)
    corrupted_crc_wire = ErrorInjector.flip_bit(f_corrupt.encode(), bit_index=15)
    gateway.process_raw_frame(corrupted_crc_wire)

    # 5. Generate and forward summary to Records Server
    print("\n--- Generating Periodic Patient Telemetry Summary ---")
    gateway.generate_and_send_summary("ICU-101")

    print("\n" + "=" * 80)
    print("  GATEWAY INGESTION METRICS SUMMARY")
    print("=" * 80)
    for k, v in gateway.get_metrics().items():
        print("  %-24s: %s" % (k, str(v)))
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
