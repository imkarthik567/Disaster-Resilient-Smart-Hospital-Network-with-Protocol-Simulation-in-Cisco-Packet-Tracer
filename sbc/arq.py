#!/usr/bin/env python3
"""
================================================================================
Sliding-Window ARQ Protocol Engine (Stop-and-Wait, Go-Back-N, Selective Repeat)
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Platform: Cisco Packet Tracer 8.x SBC-PT (Python 3) & Desktop Simulation
Features:
  1. Unified event-driven interface for Stop-and-Wait, Go-Back-N, and Selective Repeat
  2. Strict sequence-number space constraints (SR: M >= 2N, GBN: M >= N+1)
  3. Cumulative ACKs (GBN) vs. Individual Selective ACKs (SR)
  4. Receiver out-of-order buffering and in-order delivery engine (SR)
  5. Accurate metric counters: sent, retransmitted, ACKs, timeouts, discards, ticks
  6. Abstract channel model with configurable loss, corruption, delay, bandwidth
  7. High-resolution timeline trace generator for technical documentation
================================================================================
"""

import sys
import random

# ==============================================================================
# 1. FRAME DEFINITIONS & DATA STRUCTURES
# ==============================================================================

FRAME_TYPE_DATA = 0
FRAME_TYPE_ACK = 1

class ARQFrame:
    """Represents a data or acknowledgement frame traversing the channel."""
    def __init__(self, frame_type, seq_num, payload=b"", ack_num=0, send_tick=0):
        self.frame_type = int(frame_type)
        self.seq_num = int(seq_num)
        self.payload = bytes(payload) if isinstance(payload, (bytes, bytearray)) else payload.encode('utf-8')
        self.ack_num = int(ack_num)
        self.send_tick = int(send_tick)

    def is_data(self):
        return self.frame_type == FRAME_TYPE_DATA

    def is_ack(self):
        return self.frame_type == FRAME_TYPE_ACK

    def __repr__(self):
        if self.is_data():
            return "DATA(seq=%d, len=%d)" % (self.seq_num, len(self.payload))
        else:
            return "ACK(ack=%d)" % self.ack_num


# ==============================================================================
# 2. ABSTRACT SIMULATED CHANNEL OBJECT
# ==============================================================================

class SimulatedChannel:
    """
    Abstract communication channel modeling loss, corruption, delay, and bandwidth.
    Uses discrete simulation ticks for clock synchronization.
    """
    def __init__(self, loss_prob=0.0, corruption_prob=0.0, prop_delay=5, bandwidth_bps=1000000, seed=42):
        self.loss_prob = float(loss_prob)
        self.corruption_prob = float(corruption_prob)
        self.prop_delay = int(prop_delay)
        self.bandwidth_bps = int(bandwidth_bps)
        self.rng = random.Random(seed)

        # Queues: list of dicts: {'deliver_tick': int, 'frame': ARQFrame, 'corrupted': bool}
        self.to_receiver_queue = []
        self.to_sender_queue = []

        # Channel Statistics
        self.total_frames_injected = 0
        self.total_frames_dropped = 0
        self.total_frames_corrupted = 0
        self.total_acks_injected = 0
        self.total_acks_dropped = 0

    def transmit_to_receiver(self, frame, current_tick):
        """Transmits a frame from sender toward receiver."""
        self.total_frames_injected += 1
        # Loss check
        if self.rng.random() < self.loss_prob:
            self.total_frames_dropped += 1
            return False, "DROPPED"

        # Corruption check
        is_corrupt = (self.rng.random() < self.corruption_prob)
        if is_corrupt:
            self.total_frames_corrupted += 1

        deliver_tick = current_tick + self.prop_delay
        self.to_receiver_queue.append({
            'deliver_tick': deliver_tick,
            'frame': frame,
            'corrupted': is_corrupt
        })
        return True, "IN_FLIGHT"

    def transmit_to_sender(self, ack_frame, current_tick):
        """Transmits an ACK frame from receiver toward sender."""
        self.total_acks_injected += 1
        # Loss check for ACK
        if self.rng.random() < self.loss_prob:
            self.total_acks_dropped += 1
            return False, "DROPPED"

        deliver_tick = current_tick + self.prop_delay
        self.to_sender_queue.append({
            'deliver_tick': deliver_tick,
            'frame': ack_frame,
            'corrupted': False
        })
        return True, "IN_FLIGHT"

    def deliver_to_receiver(self, current_tick):
        """Pops and returns all frames arriving at the receiver at current_tick."""
        arrived = []
        remaining = []
        for item in self.to_receiver_queue:
            if item['deliver_tick'] <= current_tick:
                arrived.append(item)
            else:
                remaining.append(item)
        self.to_receiver_queue = remaining
        return arrived

    def deliver_to_sender(self, current_tick):
        """Pops and returns all ACKs arriving at the sender at current_tick."""
        arrived = []
        remaining = []
        for item in self.to_sender_queue:
            if item['deliver_tick'] <= current_tick:
                arrived.append(item['frame'])
            else:
                remaining.append(item)
        self.to_sender_queue = remaining
        return arrived


# ==============================================================================
# 3. BASE ARQ PROTOCOL STATE MACHINE & INTERFACE
# ==============================================================================

class BaseARQProtocol:
    """Base class defining common interface, metrics counters, and logging."""
    def __init__(self, window_size=4, seq_modulus=16, timeout_ticks=25, verbose=False):
        self.window_size = int(window_size)
        self.seq_modulus = int(seq_modulus)
        self.timeout_ticks = int(timeout_ticks)
        self.verbose = verbose

        # Metrics Counters
        self.frames_sent = 0
        self.frames_retransmitted = 0
        self.acks_sent = 0
        self.timeouts = 0
        self.out_of_order_discards = 0
        self.out_of_order_buffered = 0
        self.duplicates_detected = 0
        self.elapsed_time = 0

        # Application-layer Delivery Buffers
        self.delivered_data = bytearray()
        self.delivered_chunks = []
        self.trace_log = []

    def log_event(self, tick, entity, message):
        line = "[T=%04d] %-8s: %s" % (tick, entity, message)
        self.trace_log.append(line)
        if self.verbose:
            print(line)

    def get_metrics(self):
        total_unique = len(self.delivered_chunks)
        efficiency = (total_unique / self.frames_sent * 100.0) if self.frames_sent > 0 else 0.0
        return {
            "window_size": self.window_size,
            "seq_modulus": self.seq_modulus,
            "frames_sent": self.frames_sent,
            "frames_retransmitted": self.frames_retransmitted,
            "acks_sent": self.acks_sent,
            "timeouts": self.timeouts,
            "out_of_order_discards": self.out_of_order_discards,
            "out_of_order_buffered": self.out_of_order_buffered,
            "duplicates_detected": self.duplicates_detected,
            "elapsed_ticks": self.elapsed_time,
            "delivered_bytes": len(self.delivered_data),
            "delivered_chunks": total_unique,
            "protocol_efficiency_pct": round(efficiency, 2)
        }


# ==============================================================================
# 4. PROTOCOL 1: STOP-AND-WAIT (SW)
# ==============================================================================

class StopAndWaitProtocol(BaseARQProtocol):
    """
    Stop-and-Wait ARQ Protocol (Window Size = 1).
    Alternating-bit sequence number space (M >= 2).
    """
    def __init__(self, timeout_ticks=25, verbose=False):
        super().__init__(window_size=1, seq_modulus=2, timeout_ticks=timeout_ticks, verbose=verbose)
        assert self.window_size == 1, "Stop-and-Wait window size must be 1"
        assert self.seq_modulus >= 2, "Stop-and-Wait requires sequence space M >= 2"

        # Sender State
        self.sender_seq = 0
        self.outstanding_frame = None  # (seq_num, payload, expire_tick)
        self.pending_queue = []

        # Receiver State
        self.receiver_expected_seq = 0

    def can_send(self):
        return self.outstanding_frame is None

    def queue_payload(self, payload):
        self.pending_queue.append(payload)

    def step(self, current_tick, channel):
        """Advances sender and receiver state machine for current_tick."""
        self.elapsed_time = current_tick

        # 1. Sender: Send next frame if idle
        if self.can_send() and self.pending_queue:
            payload = self.pending_queue.pop(0)
            frame = ARQFrame(FRAME_TYPE_DATA, self.sender_seq, payload=payload, send_tick=current_tick)
            self.frames_sent += 1
            self.outstanding_frame = (self.sender_seq, payload, current_tick + self.timeout_ticks)
            self.log_event(current_tick, "SENDER", "Transmit Frame #%d [Payload: %d bytes]" % (self.sender_seq, len(payload)))
            ok, status = channel.transmit_to_receiver(frame, current_tick)
            if not ok:
                self.log_event(current_tick, "CHANNEL", "Frame #%d dropped (channel loss)" % self.sender_seq)

        # 2. Channel -> Receiver: Deliver arriving frames
        arrived_frames = channel.deliver_to_receiver(current_tick)
        for item in arrived_frames:
            frame = item['frame']
            corrupted = item['corrupted']

            if corrupted:
                self.log_event(current_tick, "RECEIVER", "Frame #%d discarded due to bit corruption!" % frame.seq_num)
                continue

            if frame.seq_num == self.receiver_expected_seq:
                self.delivered_data.extend(frame.payload)
                self.delivered_chunks.append(frame.payload)
                self.log_event(current_tick, "RECEIVER", "In-order Frame #%d delivered to app. Sending ACK #%d" % (
                    frame.seq_num, frame.seq_num
                ))
                ack = ARQFrame(FRAME_TYPE_ACK, 0, ack_num=frame.seq_num, send_tick=current_tick)
                self.acks_sent += 1
                channel.transmit_to_sender(ack, current_tick)
                self.receiver_expected_seq = (self.receiver_expected_seq + 1) % self.seq_modulus
            else:
                self.duplicates_detected += 1
                self.log_event(current_tick, "RECEIVER", "Duplicate Frame #%d detected! Resending ACK #%d" % (
                    frame.seq_num, frame.seq_num
                ))
                ack = ARQFrame(FRAME_TYPE_ACK, 0, ack_num=frame.seq_num, send_tick=current_tick)
                self.acks_sent += 1
                channel.transmit_to_sender(ack, current_tick)

        # 3. Channel -> Sender: Deliver arriving ACKs
        arrived_acks = channel.deliver_to_sender(current_tick)
        for ack in arrived_acks:
            if self.outstanding_frame is not None and ack.ack_num == self.outstanding_frame[0]:
                self.log_event(current_tick, "SENDER", "ACK #%d received. Window released." % ack.ack_num)
                self.outstanding_frame = None
                self.sender_seq = (self.sender_seq + 1) % self.seq_modulus

        # 4. Sender: Check Timeout
        if self.outstanding_frame is not None:
            seq_num, payload, expire_tick = self.outstanding_frame
            if current_tick >= expire_tick:
                self.timeouts += 1
                self.frames_sent += 1
                self.frames_retransmitted += 1
                self.outstanding_frame = (seq_num, payload, current_tick + self.timeout_ticks)
                self.log_event(current_tick, "SENDER", "TIMEOUT on Frame #%d! Retransmitting..." % seq_num)
                frame = ARQFrame(FRAME_TYPE_DATA, seq_num, payload=payload, send_tick=current_tick)
                channel.transmit_to_receiver(frame, current_tick)

    def is_finished(self):
        return len(self.pending_queue) == 0 and self.outstanding_frame is None


# ==============================================================================
# 5. PROTOCOL 2: GO-BACK-N (GBN)
# ==============================================================================

class GoBackNProtocol(BaseARQProtocol):
    """
    Go-Back-N ARQ Protocol with Cumulative ACKs.
    Sequence space constraint: M >= N + 1.
    """
    def __init__(self, window_size=4, seq_modulus=16, timeout_ticks=25, verbose=False):
        super().__init__(window_size=window_size, seq_modulus=seq_modulus, timeout_ticks=timeout_ticks, verbose=verbose)
        assert self.seq_modulus >= self.window_size + 1, (
            "Go-Back-N sequence space violation: modulus M (%d) must be >= window N + 1 (%d)" % (
                self.seq_modulus, self.window_size + 1
            )
        )

        # Sender State
        self.base = 0
        self.next_seq = 0
        self.sender_buffer = {}  # seq_num -> payload
        self.timer_expire_tick = None
        self.pending_queue = []

        # Receiver State
        self.receiver_expected = 0
        self.last_ack_sent = None

    def window_span(self):
        return (self.next_seq - self.base) % self.seq_modulus

    def can_send(self):
        return self.window_span() < self.window_size

    def queue_payload(self, payload):
        self.pending_queue.append(payload)

    def step(self, current_tick, channel):
        self.elapsed_time = current_tick

        # 1. Sender: Fill window from pending queue
        while self.can_send() and self.pending_queue:
            payload = self.pending_queue.pop(0)
            seq = self.next_seq
            self.sender_buffer[seq] = payload
            frame = ARQFrame(FRAME_TYPE_DATA, seq, payload=payload, send_tick=current_tick)
            self.frames_sent += 1

            if self.base == self.next_seq:
                self.timer_expire_tick = current_tick + self.timeout_ticks

            self.log_event(current_tick, "SENDER", "Transmit Frame #%d (Win: [%d..%d])" % (
                seq, self.base, (self.base + self.window_size - 1) % self.seq_modulus
            ))
            ok, status = channel.transmit_to_receiver(frame, current_tick)
            if not ok:
                self.log_event(current_tick, "CHANNEL", "Frame #%d dropped (channel loss)" % seq)

            self.next_seq = (self.next_seq + 1) % self.seq_modulus

        # 2. Channel -> Receiver: Deliver arriving frames
        arrived = channel.deliver_to_receiver(current_tick)
        for item in arrived:
            frame = item['frame']
            corrupted = item['corrupted']

            if corrupted:
                self.log_event(current_tick, "RECEIVER", "Frame #%d discarded due to bit corruption!" % frame.seq_num)
                continue

            if frame.seq_num == self.receiver_expected:
                self.delivered_data.extend(frame.payload)
                self.delivered_chunks.append(frame.payload)
                self.log_event(current_tick, "RECEIVER", "In-order Frame #%d accepted. Cumulative ACK #%d sent." % (
                    frame.seq_num, frame.seq_num
                ))
                ack = ARQFrame(FRAME_TYPE_ACK, 0, ack_num=frame.seq_num, send_tick=current_tick)
                self.acks_sent += 1
                self.last_ack_sent = frame.seq_num
                channel.transmit_to_sender(ack, current_tick)
                self.receiver_expected = (self.receiver_expected + 1) % self.seq_modulus
            else:
                self.out_of_order_discards += 1
                self.log_event(current_tick, "RECEIVER", "Out-of-order Frame #%d discarded! (Expected #%d)" % (
                    frame.seq_num, self.receiver_expected
                ))
                if self.last_ack_sent is not None:
                    # Duplicate cumulative ACK
                    ack = ARQFrame(FRAME_TYPE_ACK, 0, ack_num=self.last_ack_sent, send_tick=current_tick)
                    self.acks_sent += 1
                    channel.transmit_to_sender(ack, current_tick)

        # 3. Channel -> Sender: Deliver cumulative ACKs
        arrived_acks = channel.deliver_to_sender(current_tick)
        for ack in arrived_acks:
            ack_val = ack.ack_num
            # Check if ack_val is within unacknowledged window [base .. next_seq - 1]
            dist = (ack_val - self.base) % self.seq_modulus
            span = self.window_span()
            if dist < span:
                # Cumulative ACK: acknowledges all frames from base up to ack_val
                new_base = (ack_val + 1) % self.seq_modulus
                curr = self.base
                while curr != new_base:
                    if curr in self.sender_buffer:
                        del self.sender_buffer[curr]
                    curr = (curr + 1) % self.seq_modulus

                self.base = new_base
                self.log_event(current_tick, "SENDER", "Cumulative ACK #%d received. Window base advanced to #%d" % (
                    ack_val, self.base
                ))
                if self.base == self.next_seq:
                    self.timer_expire_tick = None
                else:
                    self.timer_expire_tick = current_tick + self.timeout_ticks

        # 4. Sender: Check Timeout and Go-Back-N Retransmission
        if self.timer_expire_tick is not None and current_tick >= self.timer_expire_tick:
            self.timeouts += 1
            self.log_event(current_tick, "SENDER", "TIMEOUT at base #%d! Go-Back-N retransmitting entire window..." % self.base)
            self.timer_expire_tick = current_tick + self.timeout_ticks

            # Retransmit ALL unacknowledged frames in window
            curr = self.base
            while curr != self.next_seq:
                if curr in self.sender_buffer:
                    payload = self.sender_buffer[curr]
                    self.frames_sent += 1
                    self.frames_retransmitted += 1
                    frame = ARQFrame(FRAME_TYPE_DATA, curr, payload=payload, send_tick=current_tick)
                    self.log_event(current_tick, "SENDER", "  [GBN-RESEND] Frame #%d" % curr)
                    channel.transmit_to_receiver(frame, current_tick)
                curr = (curr + 1) % self.seq_modulus

    def is_finished(self):
        return len(self.pending_queue) == 0 and len(self.sender_buffer) == 0 and self.base == self.next_seq


# ==============================================================================
# 6. PROTOCOL 3: SELECTIVE REPEAT (SR)
# ==============================================================================

class SelectiveRepeatProtocol(BaseARQProtocol):
    """
    Selective Repeat ARQ Protocol with Individual ACKs & Receiver Buffering.
    Sequence space constraint: M >= 2 * N.
    """
    def __init__(self, window_size=4, seq_modulus=16, timeout_ticks=25, verbose=False):
        super().__init__(window_size=window_size, seq_modulus=seq_modulus, timeout_ticks=timeout_ticks, verbose=verbose)
        assert self.seq_modulus >= 2 * self.window_size, (
            "Selective Repeat sequence space violation: modulus M (%d) must be >= 2 * window N (%d)" % (
                self.seq_modulus, 2 * self.window_size
            )
        )

        # Sender State
        self.send_base = 0
        self.next_seq = 0
        self.sender_buffer = {}  # seq_num -> {'payload': bytes, 'acked': bool, 'expire_tick': int}
        self.pending_queue = []

        # Receiver State
        self.recv_base = 0
        self.recv_buffer = {}    # seq_num -> bytes

    def window_span(self):
        return (self.next_seq - self.send_base) % self.seq_modulus

    def can_send(self):
        return self.window_span() < self.window_size

    def queue_payload(self, payload):
        self.pending_queue.append(payload)

    def step(self, current_tick, channel):
        self.elapsed_time = current_tick

        # 1. Sender: Fill window from pending queue
        while self.can_send() and self.pending_queue:
            payload = self.pending_queue.pop(0)
            seq = self.next_seq
            self.sender_buffer[seq] = {
                'payload': payload,
                'acked': False,
                'expire_tick': current_tick + self.timeout_ticks
            }
            frame = ARQFrame(FRAME_TYPE_DATA, seq, payload=payload, send_tick=current_tick)
            self.frames_sent += 1

            self.log_event(current_tick, "SENDER", "Transmit Frame #%d (Win: [%d..%d])" % (
                seq, self.send_base, (self.send_base + self.window_size - 1) % self.seq_modulus
            ))
            ok, status = channel.transmit_to_receiver(frame, current_tick)
            if not ok:
                self.log_event(current_tick, "CHANNEL", "Frame #%d dropped (channel loss)" % seq)

            self.next_seq = (self.next_seq + 1) % self.seq_modulus

        # 2. Channel -> Receiver: Deliver arriving frames & handle out-of-order buffering
        arrived = channel.deliver_to_receiver(current_tick)
        for item in arrived:
            frame = item['frame']
            corrupted = item['corrupted']

            if corrupted:
                self.log_event(current_tick, "RECEIVER", "Frame #%d discarded due to bit corruption!" % frame.seq_num)
                continue

            seq = frame.seq_num
            # Check if seq is inside receiver window [recv_base .. recv_base + N - 1]
            dist_ahead = (seq - self.recv_base) % self.seq_modulus
            dist_behind = (self.recv_base - seq) % self.seq_modulus

            if dist_ahead < self.window_size:
                # Inside receiver window: send individual ACK
                ack = ARQFrame(FRAME_TYPE_ACK, 0, ack_num=seq, send_tick=current_tick)
                self.acks_sent += 1
                channel.transmit_to_sender(ack, current_tick)

                if seq not in self.recv_buffer:
                    self.recv_buffer[seq] = frame.payload
                    if seq == self.recv_base:
                        # In-order: deliver contiguous buffered frames to application layer
                        while self.recv_base in self.recv_buffer:
                            deliv = self.recv_buffer.pop(self.recv_base)
                            self.delivered_data.extend(deliv)
                            self.delivered_chunks.append(deliv)
                            self.log_event(current_tick, "RECEIVER", "In-order Frame #%d delivered to app." % self.recv_base)
                            self.recv_base = (self.recv_base + 1) % self.seq_modulus
                    else:
                        self.out_of_order_buffered += 1
                        self.log_event(current_tick, "RECEIVER", "Out-of-order Frame #%d buffered in window." % seq)
                else:
                    self.duplicates_detected += 1
                    self.log_event(current_tick, "RECEIVER", "Duplicate Frame #%d re-ACKed." % seq)

            elif 1 <= dist_behind <= self.window_size:
                # Frame from previous window: already delivered, but re-ACK to help sender advance
                self.duplicates_detected += 1
                self.log_event(current_tick, "RECEIVER", "Previously delivered Frame #%d re-ACKed." % seq)
                ack = ARQFrame(FRAME_TYPE_ACK, 0, ack_num=seq, send_tick=current_tick)
                self.acks_sent += 1
                channel.transmit_to_sender(ack, current_tick)

            else:
                self.log_event(current_tick, "RECEIVER", "Frame #%d outside both windows. Discarded." % seq)

        # 3. Channel -> Sender: Deliver individual ACKs
        arrived_acks = channel.deliver_to_sender(current_tick)
        for ack in arrived_acks:
            ack_val = ack.ack_num
            dist = (ack_val - self.send_base) % self.seq_modulus
            if dist < self.window_size and ack_val in self.sender_buffer:
                self.sender_buffer[ack_val]['acked'] = True
                self.log_event(current_tick, "SENDER", "Selective ACK #%d received." % ack_val)

                # Slide window forward if send_base has been ACKed
                while self.send_base in self.sender_buffer and self.sender_buffer[self.send_base]['acked']:
                    del self.sender_buffer[self.send_base]
                    self.send_base = (self.send_base + 1) % self.seq_modulus
                    self.log_event(current_tick, "SENDER", "Window slid forward; new send_base is #%d" % self.send_base)

        # 4. Sender: Check independent per-packet timeouts
        for seq, entry in list(self.sender_buffer.items()):
            if not entry['acked'] and current_tick >= entry['expire_tick']:
                self.timeouts += 1
                self.frames_sent += 1
                self.frames_retransmitted += 1
                entry['expire_tick'] = current_tick + self.timeout_ticks
                self.log_event(current_tick, "SENDER", "[SELECTIVE-TIMEOUT] Resending ONLY Frame #%d" % seq)
                frame = ARQFrame(FRAME_TYPE_DATA, seq, payload=entry['payload'], send_tick=current_tick)
                channel.transmit_to_receiver(frame, current_tick)

    def is_finished(self):
        return len(self.pending_queue) == 0 and len(self.sender_buffer) == 0 and self.send_base == self.next_seq


# ==============================================================================
# 7. HIGH-LEVEL SIMULATION HARNESS
# ==============================================================================

class ARQSimulation:
    """Orchestrates an end-to-end discrete event ARQ simulation with a virtual clock."""
    def __init__(self, protocol, channel, max_ticks=50000):
        self.protocol = protocol
        self.channel = channel
        self.max_ticks = max_ticks

    def run_transfer(self, chunks):
        """Streams a list of binary chunks through the protocol state machine."""
        for chunk in chunks:
            self.protocol.queue_payload(chunk)

        current_tick = 0
        while not self.protocol.is_finished() and current_tick < self.max_ticks:
            self.protocol.step(current_tick, self.channel)
            current_tick += 1

        # Deliver any residual packets in-flight
        residual_steps = self.channel.prop_delay + 2
        for _ in range(residual_steps):
            self.protocol.step(current_tick, self.channel)
            current_tick += 1

        return self.protocol.get_metrics(), self.protocol.trace_log
