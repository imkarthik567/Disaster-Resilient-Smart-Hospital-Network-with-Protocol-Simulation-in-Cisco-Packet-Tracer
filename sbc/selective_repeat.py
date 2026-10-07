#!/usr/bin/env python3
"""
================================================================================
Selective Repeat (SR) Sliding Window Protocol & GBN Benchmark
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
Target Platform: Cisco Packet Tracer SBC-PT (Python 3) / Standalone Terminal
================================================================================
"""

import sys
from go_back_n import GoBackNSimulator

class SelectiveRepeatSimulator:
    def __init__(self, total_frames=12, window_size=4, loss_frames=None):
        self.total_frames = total_frames
        self.window_size = window_size
        self.loss_frames = set(loss_frames if loss_frames else [3, 7])
        
        # State
        self.send_base = 0
        self.recv_base = 0
        self.acked = [False] * total_frames
        self.recv_buffer = {}  # {frame_id: data}
        self.total_transmissions = 0
        self.total_retransmissions = 0

    def simulate(self):
        print("=" * 75)
        print("  SELECTIVE REPEAT (SR) PROTOCOL - PATIENT EHR LOG TRANSFER")
        print("=" * 75)
        print(f"  Configuration:")
        print(f"    Total Patient Telemetry Frames: {self.total_frames}")
        print(f"    Sender & Receiver Window Size:  {self.window_size}")
        print(f"    Simulated Lost Frames:          {sorted(list(self.loss_frames))}")
        print(f"    Protocol Type:                  Individual ACK + Selective Frame Retransmission")
        print("=" * 75)

        round_num = 1
        
        while self.send_base < self.total_frames:
            print(f"\n--- [TRANSMISSION ROUND {round_num}] Sender Win: [{self.send_base} .. {min(self.send_base + self.window_size - 1, self.total_frames - 1)}] | Recv Win: [{self.recv_base} .. {min(self.recv_base + self.window_size - 1, self.total_frames - 1)}] ---")
            
            # Send all un-ACKed frames within the sender window
            window_end = min(self.send_base + self.window_size, self.total_frames)
            transmitted_in_round = []

            for frame_id in range(self.send_base, window_end):
                if not self.acked[frame_id]:
                    self.total_transmissions += 1
                    is_lost = (frame_id in self.loss_frames)
                    transmitted_in_round.append((frame_id, is_lost))
                    status_str = "[DROPPED BY CHANNEL]" if is_lost else "[SENT]"
                    print(f"  --> SENDER: Transmitting Frame #{frame_id:<2} {status_str}")

            # Process arrivals at receiver
            for frame_id, is_lost in transmitted_in_round:
                if is_lost:
                    print(f"  [!] CHANNEL: Frame #{frame_id} dropped! (Timer running on Sender for #{frame_id})")
                    self.loss_frames.remove(frame_id)  # Next retransmission will succeed
                    self.total_retransmissions += 1
                else:
                    print(f"  <-- RECEIVER: Frame #{frame_id} arrived successfully. Returning ACK #{frame_id}")
                    self.acked[frame_id] = True
                    self.recv_buffer[frame_id] = f"Data_{frame_id}"
                    
                    # If this is the lowest expected frame, deliver and advance receiver window
                    if frame_id == self.recv_base:
                        while self.recv_base in self.recv_buffer:
                            print(f"      [APP LAYER] In-order Frame #{self.recv_base} delivered to Hospital EHR Database.")
                            self.recv_base += 1

            # Advance sender window based on consecutive ACKs from send_base
            while self.send_base < self.total_frames and self.acked[self.send_base]:
                self.send_base += 1

            # If unacknowledged frames remain, simulate individual timer expiry
            unacked_in_win = [f for f in range(self.send_base, window_end) if not self.acked[f]]
            if unacked_in_win:
                print(f"  [TIMER EXPIRED] Timeout occurred ONLY for Frame #{unacked_in_win[0]}!")
                print(f"  [SELECTIVE ACTION] Retransmitting ONLY Frame #{unacked_in_win[0]} (No other frames resent!)")

            round_num += 1

        print("\n" + "=" * 75)
        print("  SELECTIVE REPEAT PERFORMANCE & BENCHMARK SUMMARY")
        print("=" * 75)
        payload_frames = self.total_frames
        total_sent = self.total_transmissions
        efficiency = (payload_frames / total_sent) * 100
        
        print(f"  Unique Medical Frames Delivered:   {payload_frames}")
        print(f"  Total Frames Transmitted on Wire: {total_sent}")
        print(f"  Retransmissions Incurred:         {self.total_retransmissions}")
        print(f"  Protocol Efficiency:              {efficiency:.2f}%")
        print(f"  Retransmission Overhead:          {100 - efficiency:.2f}%")
        print(f"  Advantage: Zero redundant frames retransmitted!")
        print("=" * 75)

        return {
            "protocol": "Selective Repeat",
            "frames": payload_frames,
            "total_sent": total_sent,
            "retransmissions": self.total_retransmissions,
            "efficiency": efficiency
        }

def run_comparative_benchmark():
    print("\n\n" + "#" * 75)
    print("  HEAD-TO-HEAD COMPARATIVE BENCHMARK: GO-BACK-N vs. SELECTIVE REPEAT")
    print("#" * 75)

    test_frames = 12
    test_losses = [3, 7]
    win_size = 4

    # Run GBN
    gbn = GoBackNSimulator(total_frames=test_frames, window_size=win_size, loss_frames=list(test_losses))
    res_gbn = gbn.simulate()

    # Run SR
    sr = SelectiveRepeatSimulator(total_frames=test_frames, window_size=win_size, loss_frames=list(test_losses))
    res_sr = sr.simulate()

    # Comparative Table
    print("\n" + "=" * 75)
    print("  QUANTITATIVE PROTOCOL COMPARISON TABLE")
    print("=" * 75)
    print(f"  {'Metric':<35} {'Go-Back-N':<18} {'Selective Repeat':<18}")
    print("  " + "-" * 71)
    print(f"  {'Payload Frames Required':<35} {res_gbn['frames']:<18} {res_sr['frames']:<18}")
    print(f"  {'Total Transmissions on Wire':<35} {res_gbn['total_sent']:<18} {res_sr['total_sent']:<18}")
    print(f"  {'Wasted Retransmissions':<35} {res_gbn['retransmissions']:<18} {res_sr['retransmissions']:<18}")
    print(f"  {'Protocol Efficiency':<35} {res_gbn['efficiency']:.2f}%{'':<11} {res_sr['efficiency']:.2f}%")
    print(f"  {'Receiver Buffer Requirement':<35} {'1 Frame (0 KB)':<18} {f'{win_size} Frames (Buffered)':<18}")
    print(f"  {'Timer Complexity':<35} {'Single Timer':<18} {'Timer per Frame':<18}")
    print("=" * 75)
    print("  CONCLUSION FOR HOSPITAL NETWORK DESIGN:")
    print("  For high-bandwidth medical imaging (MRI/CT PACS), Selective Repeat yields")
    print(f"  {(res_sr['efficiency'] - res_gbn['efficiency']):.2f}% higher network efficiency, eliminating WAN serial link congestion.")
    print("=" * 75)

if __name__ == "__main__":
    run_comparative_benchmark()
