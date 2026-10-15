/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * ==============================================================================
 * e1_tcp_udp.cc - Experiment 1: TCP vs UDP Capacity & Congestion Dynamics
 * Disaster-Resilient Smart Hospital Network (NS-3 Discrete-Event Phase)
 * Course: CSE2004 Computer Networks - SCOPE, VIT Vellore
 * Authors: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
 * ==============================================================================
 * Evaluates WAN bottleneck behavior across offered loads from 10% to 120%
 * of the 2 Mbps Primary WAN link:
 *   - UDP Life-Critical Telemetry (ICU sensors, 160 kbps, DSCP EF)
 *   - UDP Clinical Voice (VoIP, 64 kbps, DSCP EF)
 *   - TCP Medical PACS Imaging (Bulk transfers, TcpCubic/TcpNewReno)
 *   - UDP/TCP Guest Best-Effort Load (Competing cross-traffic)
 * ==============================================================================
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/traffic-control-module.h"

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <cmath>
#include <iomanip>
#include <algorithm>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("HospitalE1TcpUdpSimulation");

int main(int argc, char *argv[])
{
  uint32_t seed = 1;
  uint32_t run = 1;
  double simTime = 25.0;
  double loadPct = 50.0;                 // Offered load as % of 2 Mbps WAN (10 to 120)
  std::string tcpVariant = "TcpCubic";   // TcpNewReno, TcpCubic, TcpBbr
  std::string queueType = "DropTail";    // DropTail, Prio, Red
  uint32_t queueSizePkts = 100;          // Queue size in packets
  std::string xmlTrace = "flowmon_e1.xml";
  std::string csvSummary = "results/e1_summary.csv";
  std::string expId = "E1-RUN";

  CommandLine cmd(__FILE__);
  cmd.AddValue("seed", "RNG seed", seed);
  cmd.AddValue("run", "RNG run index", run);
  cmd.AddValue("simTime", "Simulation execution duration in seconds", simTime);
  cmd.AddValue("loadPct", "Offered load as percentage of 2 Mbps WAN (10 to 120)", loadPct);
  cmd.AddValue("tcpVariant", "TCP congestion algorithm (TcpNewReno, TcpCubic, TcpBbr)", tcpVariant);
  cmd.AddValue("queueType", "Queue discipline (DropTail, Prio, Red)", queueType);
  cmd.AddValue("queueSize", "Bottleneck queue buffer size in packets", queueSizePkts);
  cmd.AddValue("xmlTrace", "Output path for FlowMonitor XML file", xmlTrace);
  cmd.AddValue("csvSummary", "Output path for summary CSV row", csvSummary);
  cmd.AddValue("expId", "Experiment ID identifier", expId);
  cmd.Parse(argc, argv);

  // RNG Seeding
  RngSeedManager::SetSeed(seed);
  RngSeedManager::SetRun(run);

  // TCP Protocol Setup
  TypeId tcpTypeId = TypeId::LookupByName("ns3::" + tcpVariant);
  Config::SetDefault("ns3::TcpL4Protocol::SocketType", TypeIdValue(tcpTypeId));

  // ---------------------------------------------------------------------------
  // 1. Network Topology (Main Hospital Core <-> Remote Clinic Core)
  // ---------------------------------------------------------------------------
  Ptr<Node> nodeR1 = CreateObject<Node>();
  Ptr<Node> nodeR2 = CreateObject<Node>();
  Names::Add("Core-R1", nodeR1);
  Names::Add("Core-R2", nodeR2);

  Ptr<Node> nodeServer = CreateObject<Node>();       // Server Farm / Collector
  Ptr<Node> nodeIcu = CreateObject<Node>();          // ICU Bedside Telemetry
  Ptr<Node> nodeVoice = CreateObject<Node>();        // Clinical VoIP Phone
  Ptr<Node> nodeClinicImaging = CreateObject<Node>();// Clinic PACS Station
  Ptr<Node> nodeClinicGuest = CreateObject<Node>();  // Clinic Guest Client

  Names::Add("Records-Server", nodeServer);
  Names::Add("ICU-Telemetry", nodeIcu);
  Names::Add("Clinical-Voice", nodeVoice);
  Names::Add("Clinic-Imaging", nodeClinicImaging);
  Names::Add("Clinic-Guest", nodeClinicGuest);

  // Primary WAN Link: 2.0 Mbps, 10ms delay (The Bottleneck)
  PointToPointHelper p2pWan;
  p2pWan.SetDeviceAttribute("DataRate", StringValue("2Mbps"));
  p2pWan.SetChannelAttribute("Delay", StringValue("10ms"));
  p2pWan.SetQueue("ns3::DropTailQueue", "MaxSize", StringValue(std::to_string(queueSizePkts) + "p"));

  // High-Speed Campus LAN Access Links: 100 Mbps, 1ms delay
  PointToPointHelper p2pLan;
  p2pLan.SetDeviceAttribute("DataRate", StringValue("100Mbps"));
  p2pLan.SetChannelAttribute("Delay", StringValue("1ms"));

  // Install Devices
  NetDeviceContainer wanDevs = p2pWan.Install(nodeR1, nodeR2);
  NetDeviceContainer serverDevs = p2pLan.Install(nodeServer, nodeR1);
  NetDeviceContainer icuDevs = p2pLan.Install(nodeIcu, nodeR2);
  NetDeviceContainer voiceDevs = p2pLan.Install(nodeVoice, nodeR2);
  NetDeviceContainer imagingDevs = p2pLan.Install(nodeClinicImaging, nodeR2);
  NetDeviceContainer guestDevs = p2pLan.Install(nodeClinicGuest, nodeR2);

  // Internet Stack
  InternetStackHelper internet;
  internet.Install(nodeR1);
  internet.Install(nodeR2);
  internet.Install(nodeServer);
  internet.Install(nodeIcu);
  internet.Install(nodeVoice);
  internet.Install(nodeClinicImaging);
  internet.Install(nodeClinicGuest);

  // Optional Queue Discipline Setup
  if (queueType == "Prio")
    {
      TrafficControlHelper tch;
      tch.SetRootQueueDisc("ns3::PrioQueueDisc", "Priomap",
                           StringValue("1 2 2 2 1 2 0 0 1 1 1 1 1 1 1 1"));
      tch.Install(wanDevs);
    }
  else if (queueType == "Red")
    {
      TrafficControlHelper tch;
      tch.SetRootQueueDisc("ns3::RedQueueDisc");
      tch.Install(wanDevs);
    }

  // ---------------------------------------------------------------------------
  // 2. IP Addressing Plan (VLSM 172.16.0.0/16 Alignment)
  // ---------------------------------------------------------------------------
  Ipv4AddressHelper ipv4;

  // WAN Link: 172.16.8.80/30 (R1: .81, R2: .82)
  ipv4.SetBase("172.16.8.80", "255.255.255.252");
  Ipv4InterfaceContainer ifWan = ipv4.Assign(wanDevs);

  // Server Farm: 172.16.7.0/26 (Server: .10)
  ipv4.SetBase("172.16.7.0", "255.255.255.192", "0.0.0.10");
  Ipv4InterfaceContainer ifServer = ipv4.Assign(serverDevs);
  Ipv4Address serverIp = ifServer.GetAddress(0);

  // ICU Telemetry: 172.16.8.32/27 (Remote Clinic Clinical Subnet)
  ipv4.SetBase("172.16.8.32", "255.255.255.224", "0.0.0.35");
  Ipv4InterfaceContainer ifIcu = ipv4.Assign(icuDevs);

  // Voice VoIP: 172.16.7.224/27
  ipv4.SetBase("172.16.7.224", "255.255.255.224", "0.0.0.228");
  Ipv4InterfaceContainer ifVoice = ipv4.Assign(voiceDevs);

  // Imaging PACS: 172.16.8.32/27 (.45)
  ipv4.SetBase("172.16.8.32", "255.255.255.224", "0.0.0.45");
  Ipv4InterfaceContainer ifImaging = ipv4.Assign(imagingDevs);

  // Guest Wi-Fi: 172.16.6.128/25 (.135)
  ipv4.SetBase("172.16.6.128", "255.255.255.128", "0.0.0.135");
  Ipv4InterfaceContainer ifGuest = ipv4.Assign(guestDevs);

  // Compute Dijkstra Shortest-Path Forwarding Tables
  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  // ---------------------------------------------------------------------------
  // 3. Traffic Distribution Across Load Sweep (10% to 120% of 2 Mbps WAN)
  // ---------------------------------------------------------------------------
  // WAN capacity = 2000 kbps
  double totalOfferedKbps = (loadPct / 100.0) * 2000.0;

  // Fixed baseline priority clinical loads:
  double icuRateKbps = 160.0;   // 160 kbps (100 Hz, 200B)
  double voiceRateKbps = 64.0;  // 64 kbps (G.711 VoIP)

  // Remaining offered rate distributed between TCP Imaging and UDP Guest
  double remainingKbps = totalOfferedKbps - (icuRateKbps + voiceRateKbps);
  if (remainingKbps < 50.0) remainingKbps = 50.0;

  double pacsRateKbps = remainingKbps * 0.50;  // 50% of variable load to PACS TCP
  double guestRateKbps = remainingKbps * 0.50; // 50% of variable load to Guest UDP

  // Applications Container
  ApplicationContainer serverSinks;

  // 3.1. Flow 1: Life-Critical ICU Telemetry (UDP, Port 5001, ToS = 0xB8 / DSCP EF)
  uint16_t icuPort = 5001;
  PacketSinkHelper icuSink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), icuPort));
  serverSinks.Add(icuSink.Install(nodeServer));

  OnOffHelper icuApp("ns3::UdpSocketFactory", Address(InetSocketAddress(serverIp, icuPort)));
  icuApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  icuApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  icuApp.SetAttribute("DataRate", DataRateValue(DataRate(std::to_string(static_cast<uint64_t>(icuRateKbps * 1000)) + "bps")));
  icuApp.SetAttribute("PacketSize", UintegerValue(200));
  icuApp.SetAttribute("Tos", UintegerValue(0xB8)); // DSCP EF
  ApplicationContainer icuClientApp = icuApp.Install(nodeIcu);
  icuClientApp.Start(Seconds(1.0));
  icuClientApp.Stop(Seconds(simTime - 0.5));

  // 3.2. Flow 2: Clinical Voice VoIP (UDP, Port 5004, ToS = 0xB8 / DSCP EF)
  uint16_t voicePort = 5004;
  PacketSinkHelper voiceSink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), voicePort));
  serverSinks.Add(voiceSink.Install(nodeServer));

  OnOffHelper voiceApp("ns3::UdpSocketFactory", Address(InetSocketAddress(serverIp, voicePort)));
  voiceApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  voiceApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  voiceApp.SetAttribute("DataRate", DataRateValue(DataRate(std::to_string(static_cast<uint64_t>(voiceRateKbps * 1000)) + "bps")));
  voiceApp.SetAttribute("PacketSize", UintegerValue(160));
  voiceApp.SetAttribute("Tos", UintegerValue(0xB8));
  ApplicationContainer voiceClientApp = voiceApp.Install(nodeVoice);
  voiceClientApp.Start(Seconds(1.2));
  voiceClientApp.Stop(Seconds(simTime - 0.5));

  // 3.3. Flow 3: Medical PACS Imaging (TCP, Port 5002, ToS = 0x68 / DSCP AF31)
  uint16_t pacsPort = 5002;
  PacketSinkHelper pacsSink("ns3::TcpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), pacsPort));
  serverSinks.Add(pacsSink.Install(nodeServer));

  OnOffHelper pacsApp("ns3::TcpSocketFactory", Address(InetSocketAddress(serverIp, pacsPort)));
  pacsApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  pacsApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  pacsApp.SetAttribute("DataRate", DataRateValue(DataRate(std::to_string(static_cast<uint64_t>(pacsRateKbps * 1000)) + "bps")));
  pacsApp.SetAttribute("PacketSize", UintegerValue(1460));
  pacsApp.SetAttribute("Tos", UintegerValue(0x68)); // DSCP AF31
  ApplicationContainer pacsClientApp = pacsApp.Install(nodeClinicImaging);
  pacsClientApp.Start(Seconds(1.5));
  pacsClientApp.Stop(Seconds(simTime - 0.5));

  // 3.4. Flow 4: Guest Wi-Fi Competing Cross-Traffic (UDP, Port 5005, Best Effort)
  uint16_t guestPort = 5005;
  PacketSinkHelper guestSink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), guestPort));
  serverSinks.Add(guestSink.Install(nodeServer));

  OnOffHelper guestApp("ns3::UdpSocketFactory", Address(InetSocketAddress(serverIp, guestPort)));
  guestApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  guestApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  guestApp.SetAttribute("DataRate", DataRateValue(DataRate(std::to_string(static_cast<uint64_t>(guestRateKbps * 1000)) + "bps")));
  guestApp.SetAttribute("PacketSize", UintegerValue(1024));
  guestApp.SetAttribute("Tos", UintegerValue(0x00)); // Best Effort
  ApplicationContainer guestClientApp = guestApp.Install(nodeClinicGuest);
  guestClientApp.Start(Seconds(2.0));
  guestClientApp.Stop(Seconds(simTime - 0.5));

  serverSinks.Start(Seconds(0.5));
  serverSinks.Stop(Seconds(simTime));

  // ---------------------------------------------------------------------------
  // 4. FlowMonitor Execution & Metric Extraction
  // ---------------------------------------------------------------------------
  FlowMonitorHelper flowmon;
  Ptr<FlowMonitor> monitor = flowmon.InstallAll();

  Simulator::Stop(Seconds(simTime));
  Simulator::Run();

  monitor->CheckForLostPackets();
  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmon.GetClassifier());
  std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

  // Export FlowMonitor XML
  monitor->SerializeToXmlFile(xmlTrace, true, true);

  // Compute Overall and Per-Flow Metrics
  uint32_t totalTx = 0, totalRx = 0, totalLost = 0;
  std::vector<double> flowThroughputs;

  for (auto const &flow : stats)
    {
      totalTx += flow.second.txPackets;
      totalRx += flow.second.rxPackets;
      totalLost += flow.second.lostPackets;

      double dur = (flow.second.timeLastRxPacket.GetSeconds() - flow.second.timeFirstTxPacket.GetSeconds());
      if (dur > 0 && flow.second.rxPackets > 0)
        {
          double th = (flow.second.rxBytes * 8.0) / (dur * 1000.0);
          flowThroughputs.push_back(th);
        }
    }

  // Calculate Jain's Fairness Index across all active WAN flows
  double sumTh = 0.0, sumThSq = 0.0;
  for (double th : flowThroughputs)
    {
      sumTh += th;
      sumThSq += (th * th);
    }
  double jainFairness = 1.0;
  if (!flowThroughputs.empty() && sumThSq > 0.0)
    {
      jainFairness = (sumTh * sumTh) / (flowThroughputs.size() * sumThSq);
    }

  double pdr = totalTx > 0 ? (totalRx * 100.0 / totalTx) : 0.0;

  // Append summary CSV row
  bool fileExists = false;
  std::ifstream checkFile(csvSummary);
  if (checkFile.is_open())
    {
      checkFile.seekg(0, std::ios::end);
      if (checkFile.tellg() > 0) fileExists = true;
      checkFile.close();
    }

  std::ofstream csvOut(csvSummary, std::ios::app);
  if (csvOut.is_open())
    {
      if (!fileExists)
        {
          csvOut << "exp_id,seed,run,sim_time,load_pct,total_offered_kbps,pacs_rate_kbps,guest_rate_kbps,queue_type,tcp_variant,total_tx,total_rx,total_lost,pdr_pct,jain_fairness\n";
        }
      csvOut << expId << ","
             << seed << ","
             << run << ","
             << simTime << ","
             << std::fixed << std::setprecision(1) << loadPct << ","
             << std::fixed << std::setprecision(1) << totalOfferedKbps << ","
             << std::fixed << std::setprecision(1) << pacsRateKbps << ","
             << std::fixed << std::setprecision(1) << guestRateKbps << ","
             << queueType << ","
             << tcpVariant << ","
             << totalTx << ","
             << totalRx << ","
             << totalLost << ","
             << std::fixed << std::setprecision(2) << pdr << ","
             << std::fixed << std::setprecision(4) << jainFairness << "\n";
      csvOut.close();
    }

  std::cout << "[E1 RUN COMPLETED] Load=" << loadPct << "% | Seed=" << seed
            << " | Tx=" << totalTx << " | Rx=" << totalRx
            << " | Lost=" << totalLost << " | PDR=" << std::fixed << std::setprecision(2) << pdr << "%"
            << " | JainFairness=" << std::fixed << std::setprecision(3) << jainFairness << std::endl;

  Simulator::Destroy();
  return 0;
}
