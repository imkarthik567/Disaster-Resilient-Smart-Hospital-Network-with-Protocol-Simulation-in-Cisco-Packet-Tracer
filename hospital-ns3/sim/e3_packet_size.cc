/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * ==============================================================================
 * e3_packet_size.cc - Experiment 3: Packet Size, Protocol Efficiency & Queue Divergence
 * Disaster-Resilient Smart Hospital Network (NS-3 Discrete-Event Phase)
 * Course: CSE2004 Computer Networks - SCOPE, VIT Vellore
 * Authors: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
 * ==============================================================================
 * Sweeps packet payload sizes: 64, 128, 256, 512, 1024, 1460 bytes
 * Across 3 fixed WAN offered load regimes:
 *   1. Light Load: 30% of 2 Mbps WAN (600 kbps)
 *   2. Near Saturation: 90% of 2 Mbps WAN (1800 kbps)
 *   3. Overloaded: 120% of 2 Mbps WAN (2400 kbps)
 *
 * Evaluates:
 *   - Transmission delay vs. Queuing delay divergence
 *   - Goodput vs. Raw Throughput
 *   - Protocol Header Overhead: OH = Headers / (Payload + Headers)
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

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("HospitalE3PacketSizeSimulation");

int main(int argc, char *argv[])
{
  uint32_t seed = 1;
  uint32_t run = 1;
  double simTime = 20.0;
  uint32_t packetSize = 256;             // 64, 128, 256, 512, 1024, 1460 bytes
  std::string loadMode = "near_sat";     // light (30%), near_sat (90%), overloaded (120%)
  std::string tcpVariant = "TcpCubic";
  std::string xmlTrace = "flowmon_e3.xml";
  std::string csvSummary = "results/e3_packet_size/e3_summary.csv";
  std::string expId = "E3-RUN";

  CommandLine cmd(__FILE__);
  cmd.AddValue("seed", "RNG seed", seed);
  cmd.AddValue("run", "RNG run index", run);
  cmd.AddValue("simTime", "Simulation execution duration in seconds", simTime);
  cmd.AddValue("packetSize", "Packet payload size in bytes (64, 128, 256, 512, 1024, 1460)", packetSize);
  cmd.AddValue("loadMode", "Offered load regime: light (30%), near_sat (90%), overloaded (120%)", loadMode);
  cmd.AddValue("tcpVariant", "TCP congestion algorithm", tcpVariant);
  cmd.AddValue("xmlTrace", "Output path for FlowMonitor XML file", xmlTrace);
  cmd.AddValue("csvSummary", "Output path for summary CSV row", csvSummary);
  cmd.AddValue("expId", "Experiment ID identifier", expId);
  cmd.Parse(argc, argv);

  RngSeedManager::SetSeed(seed);
  RngSeedManager::SetRun(run);

  // Configure TCP Segment Size matching packetSize
  TypeId tcpTypeId = TypeId::LookupByName("ns3::" + tcpVariant);
  Config::SetDefault("ns3::TcpL4Protocol::SocketType", TypeIdValue(tcpTypeId));
  Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(packetSize));

  // Determine Offered Load in kbps
  double loadFactor = 0.90; // default near_sat
  if (loadMode == "light")
    {
      loadFactor = 0.30; // 600 kbps
    }
  else if (loadMode == "overloaded")
    {
      loadFactor = 1.20; // 2400 kbps
    }
  double totalOfferedKbps = loadFactor * 2000.0;

  // ---------------------------------------------------------------------------
  // 1. Topology Construction
  // ---------------------------------------------------------------------------
  Ptr<Node> nodeR1 = CreateObject<Node>();
  Ptr<Node> nodeR2 = CreateObject<Node>();
  Ptr<Node> nodeServer = CreateObject<Node>();
  Ptr<Node> nodeUdpTelemetry = CreateObject<Node>();
  Ptr<Node> nodeTcpImaging = CreateObject<Node>();

  Names::Add("Core-R1", nodeR1);
  Names::Add("Core-R2", nodeR2);
  Names::Add("Records-Server", nodeServer);
  Names::Add("Telemetry-Source", nodeUdpTelemetry);
  Names::Add("Imaging-Source", nodeTcpImaging);

  // 2.0 Mbps, 10ms Primary WAN Link
  PointToPointHelper p2pWan;
  p2pWan.SetDeviceAttribute("DataRate", StringValue("2Mbps"));
  p2pWan.SetChannelAttribute("Delay", StringValue("10ms"));
  p2pWan.SetQueue("ns3::DropTailQueue", "MaxSize", StringValue("100p"));

  // 100 Mbps LAN links
  PointToPointHelper p2pLan;
  p2pLan.SetDeviceAttribute("DataRate", StringValue("100Mbps"));
  p2pLan.SetChannelAttribute("Delay", StringValue("1ms"));

  NetDeviceContainer wanDevs = p2pWan.Install(nodeR1, nodeR2);
  NetDeviceContainer serverDevs = p2pLan.Install(nodeServer, nodeR1);
  NetDeviceContainer udpDevs = p2pLan.Install(nodeUdpTelemetry, nodeR2);
  NetDeviceContainer tcpDevs = p2pLan.Install(nodeTcpImaging, nodeR2);

  // Internet Stack
  InternetStackHelper internet;
  internet.Install(nodeR1);
  internet.Install(nodeR2);
  internet.Install(nodeServer);
  internet.Install(nodeUdpTelemetry);
  internet.Install(nodeTcpImaging);

  // IP Addressing
  Ipv4AddressHelper ipv4;
  ipv4.SetBase("172.16.8.80", "255.255.255.252"); // WAN
  ipv4.Assign(wanDevs);

  ipv4.SetBase("172.16.7.0", "255.255.255.192", "0.0.0.10"); // Server
  Ipv4InterfaceContainer ifServer = ipv4.Assign(serverDevs);
  Ipv4Address serverIp = ifServer.GetAddress(0);

  ipv4.SetBase("172.16.8.32", "255.255.255.224", "0.0.0.35"); // UDP Telemetry
  ipv4.Assign(udpDevs);

  ipv4.SetBase("172.16.8.32", "255.255.255.224", "0.0.0.45"); // TCP Imaging
  ipv4.Assign(tcpDevs);

  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  // ---------------------------------------------------------------------------
  // 2. Traffic Flow Setup (UDP Telemetry + TCP Imaging)
  // ---------------------------------------------------------------------------
  double udpRateKbps = totalOfferedKbps * 0.40; // 40% of offered load to UDP
  double tcpRateKbps = totalOfferedKbps * 0.60; // 60% of offered load to TCP

  ApplicationContainer serverSinks;

  // 2.1. UDP Telemetry Sink & Client
  uint16_t udpPort = 5001;
  PacketSinkHelper udpSink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), udpPort));
  serverSinks.Add(udpSink.Install(nodeServer));

  OnOffHelper udpApp("ns3::UdpSocketFactory", Address(InetSocketAddress(serverIp, udpPort)));
  udpApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  udpApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  udpApp.SetAttribute("DataRate", DataRateValue(DataRate(std::to_string(static_cast<uint64_t>(udpRateKbps * 1000)) + "bps")));
  udpApp.SetAttribute("PacketSize", UintegerValue(packetSize));
  udpApp.SetAttribute("Tos", UintegerValue(0xB8)); // DSCP EF
  ApplicationContainer udpClientApp = udpApp.Install(nodeUdpTelemetry);
  udpClientApp.Start(Seconds(1.0));
  udpClientApp.Stop(Seconds(simTime - 0.5));

  // 2.2. TCP Imaging Sink & Client
  uint16_t tcpPort = 5002;
  PacketSinkHelper tcpSink("ns3::TcpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), tcpPort));
  serverSinks.Add(tcpSink.Install(nodeServer));

  OnOffHelper tcpApp("ns3::TcpSocketFactory", Address(InetSocketAddress(serverIp, tcpPort)));
  tcpApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  tcpApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  tcpApp.SetAttribute("DataRate", DataRateValue(DataRate(std::to_string(static_cast<uint64_t>(tcpRateKbps * 1000)) + "bps")));
  tcpApp.SetAttribute("PacketSize", UintegerValue(packetSize));
  tcpApp.SetAttribute("Tos", UintegerValue(0x68)); // DSCP AF31
  ApplicationContainer tcpClientApp = tcpApp.Install(nodeTcpImaging);
  tcpClientApp.Start(Seconds(1.5));
  tcpClientApp.Stop(Seconds(simTime - 0.5));

  serverSinks.Start(Seconds(0.5));
  serverSinks.Stop(Seconds(simTime));

  // ---------------------------------------------------------------------------
  // 3. FlowMonitor Performance Measurement Engine
  // ---------------------------------------------------------------------------
  FlowMonitorHelper flowmon;
  Ptr<FlowMonitor> monitor = flowmon.InstallAll();

  Simulator::Stop(Seconds(simTime));
  Simulator::Run();

  monitor->CheckForLostPackets();
  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmon.GetClassifier());
  std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

  monitor->SerializeToXmlFile(xmlTrace, true, true);

  // ---------------------------------------------------------------------------
  // 4. Extract Per-Protocol Metrics & Theoretical Headers
  // ---------------------------------------------------------------------------
  // Exact Header Sizes over Point-to-Point Link:
  // L2 PPP Header = 2 bytes (or 4 with framing)
  // L3 IPv4 Header = 20 bytes
  // L4 UDP Header = 8 bytes -> Total UDP Overhead = 30 bytes
  // L4 TCP Header = 20 bytes -> Total TCP Overhead = 42 bytes
  const double UDP_HEADERS = 30.0;
  const double TCP_HEADERS = 42.0;

  double udpTh = 0.0, udpGoodput = 0.0, udpDelay = 0.0, udpLoss = 0.0;
  double tcpTh = 0.0, tcpGoodput = 0.0, tcpDelay = 0.0, tcpLoss = 0.0;

  for (auto const &flow : stats)
    {
      Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(flow.first);
      double dur = (flow.second.timeLastRxPacket.GetSeconds() - flow.second.timeFirstTxPacket.GetSeconds());
      double rxBytes = flow.second.rxBytes;
      uint32_t rxPkts = flow.second.rxPackets;
      uint32_t txPkts = flow.second.txPackets;
      uint32_t lostPkts = flow.second.lostPackets;

      double th = (dur > 0 && rxPkts > 0) ? (rxBytes * 8.0) / (dur * 1000.0) : 0.0;
      double delay = rxPkts > 0 ? (flow.second.delaySum.GetSeconds() / rxPkts * 1000.0) : 0.0;
      double loss = txPkts > 0 ? (lostPkts * 100.0 / txPkts) : 0.0;

      if (t.destinationPort == 5001) // UDP Telemetry
        {
          udpTh = th;
          // Goodput: payload only
          double payloadBytes = rxPkts * packetSize;
          udpGoodput = (dur > 0 && rxPkts > 0) ? (payloadBytes * 8.0) / (dur * 1000.0) : 0.0;
          udpDelay = delay;
          udpLoss = loss;
        }
      else if (t.destinationPort == 5002) // TCP Imaging
        {
          tcpTh = th;
          double payloadBytes = rxPkts * packetSize;
          tcpGoodput = (dur > 0 && rxPkts > 0) ? (payloadBytes * 8.0) / (dur * 1000.0) : 0.0;
          tcpDelay = delay;
          tcpLoss = loss;
        }
    }

  // Theoretical Calculations
  double udpEfficiencyTheory = static_cast<double>(packetSize) / (packetSize + UDP_HEADERS);
  double tcpEfficiencyTheory = static_cast<double>(packetSize) / (packetSize + TCP_HEADERS);
  double udpOverheadTheory = UDP_HEADERS / (packetSize + UDP_HEADERS);
  double tcpOverheadTheory = TCP_HEADERS / (packetSize + TCP_HEADERS);

  // Transmission delay on 2 Mbps link: (size + headers) * 8 / 2,000,000 * 1000 ms
  double udpTxDelayTheoryMs = ((packetSize + UDP_HEADERS) * 8.0) / 2000.0;
  double tcpTxDelayTheoryMs = ((packetSize + TCP_HEADERS) * 8.0) / 2000.0;

  // Total theoretical unloaded delay = 10ms propagation + tx delay
  double udpTotalDelayTheoryMs = 10.0 + udpTxDelayTheoryMs;
  double tcpTotalDelayTheoryMs = 10.0 + tcpTxDelayTheoryMs;

  // Append to Summary CSV
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
          csvOut << "exp_id,seed,run,packet_size,load_mode,load_pct,total_offered_kbps,"
                 << "udp_th_kbps,udp_goodput_kbps,udp_delay_ms,udp_loss_pct,udp_overhead_theory,udp_delay_theory_ms,"
                 << "tcp_th_kbps,tcp_goodput_kbps,tcp_delay_ms,tcp_loss_pct,tcp_overhead_theory,tcp_delay_theory_ms\n";
        }
      csvOut << expId << ","
             << seed << ","
             << run << ","
             << packetSize << ","
             << loadMode << ","
             << std::fixed << std::setprecision(1) << (loadFactor * 100.0) << ","
             << std::fixed << std::setprecision(1) << totalOfferedKbps << ","
             << std::fixed << std::setprecision(2) << udpTh << ","
             << std::fixed << std::setprecision(2) << udpGoodput << ","
             << std::fixed << std::setprecision(2) << udpDelay << ","
             << std::fixed << std::setprecision(2) << udpLoss << ","
             << std::fixed << std::setprecision(4) << udpOverheadTheory << ","
             << std::fixed << std::setprecision(2) << udpTotalDelayTheoryMs << ","
             << std::fixed << std::setprecision(2) << tcpTh << ","
             << std::fixed << std::setprecision(2) << tcpGoodput << ","
             << std::fixed << std::setprecision(2) << tcpDelay << ","
             << std::fixed << std::setprecision(2) << tcpLoss << ","
             << std::fixed << std::setprecision(4) << tcpOverheadTheory << ","
             << std::fixed << std::setprecision(2) << tcpTotalDelayTheoryMs << "\n";
      csvOut.close();
    }

  std::cout << "[E3 RUN COMPLETED] Size=" << packetSize << "B | Load=" << loadMode
            << " | UDP Delay=" << udpDelay << "ms (Theory=" << udpTotalDelayTheoryMs << "ms)"
            << " | UDP Th=" << udpTh << " kbps | Goodput=" << udpGoodput << " kbps"
            << " | Overhead=" << std::fixed << std::setprecision(1) << (udpOverheadTheory * 100.0) << "%"
            << std::endl;

  Simulator::Destroy();
  return 0;
}
