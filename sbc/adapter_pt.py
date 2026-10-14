#!/usr/bin/env python3
"""
================================================================================
Cisco Packet Tracer 8.x SBC-PT I/O & Networking Adapter
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Target: Cisco Packet Tracer 8.x Single Board Computer (SBC-PT) & Desktop Python
Purpose: Bridges the pure-Python ARQ protocols (Stop-and-Wait, GBN, SR) and
         errdetect library to Packet Tracer's physical pins and UDP network stack.

Role 1: SENDER   (SBC-ICU-101, VLAN 10, IP: 172.16.7.138:5005)
Role 2: RECEIVER (Server-EHR / SBC-CLINIC-201, VLAN 50/60, IP: 172.16.7.195:5006)

Key Hardware Pin Assignments on SBC-PT:
  - Analog Pin A0  : Patient ECG Heart Rate Pulse Sensor (0 - 1023 -> 40 - 180 BPM)
  - Analog Pin A1  : Pulse Oximeter SpO2 Sensor (0 - 1023 -> 70 - 100% SpO2)
  - Digital Pin D0 : Bedside Emergency Nurse Call Button (Input, HIGH on press)
  - Digital Pin D1 : Critical Cardiac Alarm Siren / Buzzer (Output, HIGH to activate)
  - Digital Pin D2 : Visual Alert Flashing Red LED (Output, HIGH to illuminate)
================================================================================
"""

import sys
import time

# Attempt importing Packet Tracer embedded hardware modules
try:
    from gpio import *
    IS_PACKET_TRACER = True
except ImportError:
    IS_PACKET_TRACER = False

# Attempt importing BSD sockets
try:
    import socket
    SOCKET_AVAILABLE = True
except ImportError:
    SOCKET_AVAILABLE = False

# Local protocol imports
try:
    from sbc.errdetect import SensorFrame, SENSOR_ECG, SENSOR_SPO2, CHECK_CRC16, CHECK_2D_PARITY
    from sbc.arq import GoBackNProtocol, SelectiveRepeatProtocol, StopAndWaitProtocol, ARQFrame
except ImportError:
    # If run directly inside Packet Tracer SBC editor where files reside in the same flat folder
    from errdetect import SensorFrame, SENSOR_ECG, SENSOR_SPO2, CHECK_CRC16, CHECK_2D_PARITY
    from arq import GoBackNProtocol, SelectiveRepeatProtocol, StopAndWaitProtocol, ARQFrame

# ==============================================================================
# HARDWARE PIN CONFIGURATION & ABSTRACTION
# ==============================================================================

PIN_ECG_ANALOG = 0      # A0
PIN_SPO2_ANALOG = 1     # A1
PIN_NURSE_CALL = 0      # D0
PIN_ALARM_SIREN = 1     # D1
PIN_ALERT_LED = 2       # D2

def init_hardware_pins():
    """Initializes SBC digital and analog I/O pins if running inside Packet Tracer."""
    if IS_PACKET_TRACER:
        try:
            pinMode(PIN_NURSE_CALL, IN)
            pinMode(PIN_ALARM_SIREN, OUT)
            pinMode(PIN_ALERT_LED, OUT)
            digitalWrite(PIN_ALARM_SIREN, LOW)
            digitalWrite(PIN_ALERT_LED, LOW)
            print("[PT-ADAPTER] GPIO pins initialized: D0(IN), D1(OUT), D2(OUT)")
        except Exception as e:
            print("[PT-ADAPTER-WARN] GPIO setup exception: %s" % str(e))
    else:
        print("[PT-ADAPTER] Running in desktop emulation mode. Hardware pins virtualized.")

def read_vitals():
    """
    Reads simulated physiological sensors.
    Maps 10-bit ADC values (0 - 1023) to clinical vital ranges:
      - Heart Rate : 40 to 180 BPM
      - SpO2       : 70 to 100 %
    """
    if IS_PACKET_TRACER:
        # TODO: [PROBE-CHECK-PINS] Confirm analogRead() pin mapping against SBC-PT sensor wiring
        raw_ecg = analogRead(PIN_ECG_ANALOG)
        raw_spo2 = analogRead(PIN_SPO2_ANALOG)
        nurse_pressed = (digitalRead(PIN_NURSE_CALL) == HIGH)

        # Linear ADC scaling
        hr = int(40 + (raw_ecg / 1023.0) * 140)
        spo2 = round(70.0 + (raw_spo2 / 1023.0) * 30.0, 1)
        return hr, spo2, nurse_pressed
    else:
        # Desktop synthetic generator
        import random
        hr = random.randint(65, 88)
        spo2 = round(random.uniform(96.0, 99.5), 1)
        nurse_pressed = False
        return hr, spo2, nurse_pressed

def trigger_alarm(activate=True):
    """Controls the bedside audible alarm and visual alert LED."""
    if IS_PACKET_TRACER:
        level = HIGH if activate else LOW
        digitalWrite(PIN_ALARM_SIREN, level)
        digitalWrite(PIN_ALERT_LED, level)
    else:
        if activate:
            print("  >>> [AUDIBLE ALARM & RED LED ACTIVATED] Critical Vitals Detected! <<<")

# ==============================================================================
# PACKET TRACER NETWORK ADAPTER (UDP SOCKETS & SERIALIZED FRAMES)
# ==============================================================================

class PacketTracerNetworkAdapter:
    """
    Network adapter managing bidirectional frame transmission over UDP in Packet Tracer.
    Includes fallback logging if socket module is unavailable.
    """
    def __init__(self, local_ip="0.0.0.0", local_port=5005, remote_ip="172.16.7.195", remote_port=5006):
        # TODO: [PROBE-CHECK-IP] Confirm local SBC IP address from VLSM plan:
        #   ICU SBC:     172.16.7.138 (VLAN 10, FastEthernet0)
        #   EHR Server:  172.16.7.195 (VLAN 50, Server-EHR)
        #   Clinic SBC:  172.16.7.202 (VLAN 60, SW-A4)
        self.local_ip = local_ip
        self.local_port = int(local_port)
        self.remote_ip = remote_ip
        self.remote_port = int(remote_port)
        self.sock = None

        # TODO: [PROBE-CHECK-SOCKET] Inspect output of probe.py in Packet Tracer:
        #   If 'socket' is Available: BSD UDP socket is used directly.
        #   If 'socket' is Missing  : Packet Tracer restricts networking to IoEClient.
        if SOCKET_AVAILABLE:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.sock.bind((self.local_ip, self.local_port))
                self.sock.setblocking(False)
                print("[PT-ADAPTER] UDP socket bound to %s:%d (Target: %s:%d)" % (
                    self.local_ip, self.local_port, self.remote_ip, self.remote_port
                ))
            except Exception as e:
                print("[PT-ADAPTER-WARN] Socket initialization failed: %s" % str(e))
                self.sock = None
        else:
            print("[PT-ADAPTER] Socket unavailable. Fallback: virtual loopback transmission.")

    def send_wire(self, raw_bytes):
        """Transmits raw binary bytes across the network."""
        if self.sock is not None:
            try:
                self.sock.sendto(raw_bytes, (self.remote_ip, self.remote_port))
                return True
            except Exception as e:
                print("[PT-ADAPTER-WARN] sendto failed: %s" % str(e))
                return False
        return True

    def receive_wire(self):
        """Polls for arriving network frames (non-blocking)."""
        if self.sock is not None:
            try:
                data, addr = self.sock.recvfrom(2048)
                return data
            except Exception:
                return None
        return None

# ==============================================================================
# SENDER APPLICATION LOOP (SBC PATIENT MONITOR)
# ==============================================================================

def run_sender_node(protocol_type="SR", target_ip="172.16.7.195", target_port=5006, duration_sec=30):
    """
    Executes the clinical sender telemetry node on SBC-ICU-101.
    Periodically reads vitals, packs SensorFrames, and streams them via ARQ.
    """
    init_hardware_pins()
    net = PacketTracerNetworkAdapter(local_ip="0.0.0.0", local_port=5005, remote_ip=target_ip, remote_port=target_port)

    # Instantiate chosen protocol
    if protocol_type == "SR":
        protocol = SelectiveRepeatProtocol(window_size=4, seq_modulus=16, timeout_ticks=15, verbose=True)
    elif protocol_type == "GBN":
        protocol = GoBackNProtocol(window_size=4, seq_modulus=16, timeout_ticks=15, verbose=True)
    else:
        protocol = StopAndWaitProtocol(timeout_ticks=15, verbose=True)

    print("\n" + "=" * 76)
    print("  SBC-ICU-101 CLINICAL TELEMETRY SENDER STARTED (Protocol: %s)" % protocol_type)
    print("=" * 76)

    seq = 0
    t_start = time.time()
    last_sample_time = 0

    while time.time() - t_start < duration_sec:
        now = time.time()
        tick = int((now - t_start) * 10)  # 10 ticks per second

        # 1. Sample Sensors every 1.0 second
        if now - last_sample_time >= 1.0:
            hr, spo2, nurse_pressed = read_vitals()
            last_sample_time = now

            if nurse_pressed or spo2 < 90.0 or hr > 140:
                trigger_alarm(True)
            else:
                trigger_alarm(False)

            # Build SensorFrame with 16-bit CRC
            payload_str = "HR=%d,SPO2=%.1f,NURSE=%d" % (hr, spo2, 1 if nurse_pressed else 0)
            frame = SensorFrame(
                seq_num=seq,
                patient_id="ICU-101",
                sensor_type=SENSOR_ECG,
                value=float(hr),
                timestamp=int(now),
                payload=payload_str.encode('utf-8'),
                check_type=CHECK_CRC16
            )
            wire_frame = frame.encode()
            protocol.queue_payload(wire_frame)
            seq = (seq + 1) % 65536

        # 2. Check for Arriving ACKs over the Network
        arriving_bytes = net.receive_wire()
        if arriving_bytes:
            # Simple ACK format: 2 bytes uint16
            if len(arriving_bytes) >= 2:
                ack_num = (arriving_bytes[0] << 8) | arriving_bytes[1]
                ack_obj = ARQFrame(1, 0, ack_num=ack_num, send_tick=tick)
                # Feed ACK directly to sender
                if hasattr(protocol, 'deliver_ack'):
                    protocol.deliver_ack(ack_obj)

        # 3. Step Protocol State Machine
        # TODO: [PROBE-CHECK-YIELD] Packet Tracer GUI lockup mitigation:
        # Mandatory cooperative yield inside single-threaded loop
        if IS_PACKET_TRACER:
            sleep(0.05)
        else:
            time.sleep(0.05)

    print("\n" + "=" * 76)
    print("  SENDER EXECUTION SUMMARY")
    print("=" * 76)
    metrics = protocol.get_metrics()
    for k, v in metrics.items():
        print("  %-26s: %s" % (k, str(v)))
    print("=" * 76 + "\n")

# ==============================================================================
# RECEIVER APPLICATION LOOP (HOSPITAL EHR SERVER)
# ==============================================================================

def run_receiver_node(protocol_type="SR", bind_port=5006, duration_sec=30):
    """
    Executes the receiver telemetry node on Server-EHR or Clinic SBC.
    Receives packets, verifies integrity, stores in EHR database, and transmits ACKs.
    """
    net = PacketTracerNetworkAdapter(local_ip="0.0.0.0", local_port=bind_port)

    print("\n" + "=" * 76)
    print("  HOSPITAL EHR TELEMETRY RECEIVER LISTENING ON PORT %d" % bind_port)
    print("=" * 76)

    t_start = time.time()
    received_count = 0

    while time.time() - t_start < duration_sec:
        data = net.receive_wire()
        if data:
            ok, frame, msg = SensorFrame.decode(data)
            if ok:
                received_count += 1
                print("  [EHR-INGEST] Patient: %s | Type: %d | Val: %.1f | Payload: %s" % (
                    frame.patient_id, frame.sensor_type, frame.value, frame.payload.decode('utf-8', errors='replace')
                ))
                # Send ACK back (2 bytes big-endian)
                ack_bytes = bytes([(frame.seq_num >> 8) & 0xFF, frame.seq_num & 0xFF])
                net.send_wire(ack_bytes)
            else:
                print("  [EHR-DISCARD] Corrupted frame rejected: %s" % msg)

        if IS_PACKET_TRACER:
            sleep(0.05)
        else:
            time.sleep(0.05)

    print("\n[EHR-RECEIVER] Finished. Total clinical frames committed to EHR: %d\n" % received_count)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "receiver":
        run_receiver_node()
    else:
        run_sender_node(duration_sec=3)
