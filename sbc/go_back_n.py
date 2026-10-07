#!/usr/bin/env python3
"""
================================================================================
Go-Back-N (GBN) Sliding Window Flow Control Protocol Simulation
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
Target Platform: Cisco Packet Tracer SBC-PT (Python 3) / Standalone Terminal
================================================================================
"""

import sys
import time
import random

class GoBackNSimulator:
    def __init__(self, total_frames=12, window_size=4, loss_frames=None, timeout_val=1.5):
        self.total_frames = total_frames
        self.window_size = window_size
        self.loss_frames = set(loss_frames if loss_frames else [3, 7])
        self.timeout_val = timeout_val
        
        # State
        self.base = 0
        self.next_seq_num = 0
        self.expected_frame = 0
        self.total_transmissions = 0
        self.total_retransmissions = 0
        self.events_log = []

    def simulate(self):
        print("=" * 75)
        print("  GO-BACK-N (GBN) SLIDING WINDOW PROTOCOL - PATIENT EHR LOG TRANSFER")
        print("=" * 75)
        print(f"  Configuration:")
        print(f"    Total Patient Telemetry Frames: {self.total_frames}")
        print(f"    Sender Window Size (N):         {self.window_size}")
        print(f"    Simulated Lost Frames:          {sorted(list(self.loss_frames))}")
        print(f"    Protocol Type:                  Cumulative ACK + Go-Back-N on Timeout")
        print("=" * 75)

        round_num = 1
        
        while self.base < self.total_frames:
            print(f"\n--- [TRANSMISSION ROUND {round_num}] Window: [{self.base} .. {min(self.base + self.window_size - 1, self.total_frames - 1)}] ---")
            
            # Send all available frames in current window
            sent_in_burst = []
            while self.next_seq_num < self.base + self.window_size and self.next_seq_num < self.total_frames:
                frame_id = self.next_seq_num
                self.total_transmissions += 1
                if self.total_transmissions > self.total_frames:
                    self.total_retransmissions += 1
                    
                is_lost = (frame_id in self.loss_frames)
                sent_in_burst.append((frame_id, is_lost))
                
                status_str = "[DROPPED BY NOISE]" if is_lost else "[SENT]"
                print(f"  --> SENDER: Transmitting Frame #{frame_id:<2} {status_str}")
                self.next_seq_num += 1

            # Receiver processes frames arriving from the burst
            timeout_occurred = False
            first_dropped_frame = None

            for frame_id, is_lost in sent_in_burst:
                if is_lost:
                    print(f"  [!] CHANNEL: Frame #{frame_id} lost due to link saturation!")
                    # Consume the loss so subsequent retransmissions succeed
                    self.loss_frames.remove(frame_id)
                    timeout_occurred = True
                    first_dropped_frame = frame_id
                    break
                else:
                    if frame_id == self.expected_frame:
                        print(f"  <-- RECEIVER: In-order Frame #{frame_id} received. Sending ACK #{frame_id + 1}")
                        self.expected_frame += 1
                        self.base = self.expected_frame
                    else:
                        print(f"  <-- RECEIVER: Out-of-order Frame #{frame_id} discarded! Resending Duplicate ACK #{self.expected_frame}")

            if timeout_occurred:
                print(f"\n  [TIMER EXPIRED] Sender timer expired waiting for ACK of Frame #{self.base}!")
                print(f"  [ACTION: GO-BACK-N] Sliding window reverts from #{self.next_seq_num - 1} back to #{self.base}!")
                print(f"  [RETRANSMISSION] Retransmitting all unacknowledged frames in window starting at Frame #{self.base}...")
                self.next_seq_num = self.base

            round_num += 1

        print("\n" + "=" * 75)
        print("  GO-BACK-N PERFORMANCE & BENCHMARK SUMMARY")
        print("=" * 75)
        payload_frames = self.total_frames
        total_sent = self.total_transmissions
        efficiency = (payload_frames / total_sent) * 100
        
        print(f"  Unique Medical Frames Delivered:   {payload_frames}")
        print(f"  Total Frames Transmitted on Wire: {total_sent}")
        print(f"  Retransmissions Incurred:         {self.total_retransmissions}")
        print(f"  Protocol Efficiency:              {efficiency:.2f}%")
        print(f"  Retransmission Overhead:          {100 - efficiency:.2f}%")
        print(f"  Diagnostic: In Go-Back-N, lost frame #{first_dropped_frame or 'N/A'} caused retransmission")
        print(f"              of ALL subsequent frames in the window, even if they arrived intact!")
        print("=" * 75)

        return {
            "protocol": "Go-Back-N",
            "frames": payload_frames,
            "total_sent": total_sent,
            "retransmissions": self.total_retransmissions,
            "efficiency": efficiency
        }

if __name__ == "__main__":
    sim = GoBackNSimulator(total_frames=12, window_size=4, loss_frames=[3, 7])
    sim.simulate()
