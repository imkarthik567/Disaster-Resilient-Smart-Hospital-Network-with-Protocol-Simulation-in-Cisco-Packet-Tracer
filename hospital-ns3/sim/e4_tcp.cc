/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * ==============================================================================
 * e4_tcp.cc - Experiment 4: TCP Congestion Control Dynamics & Bulk PACS Transfer
 * Disaster-Resilient Smart Hospital Network (NS-3 Discrete-Event Phase)
 * Course: CSE2004 Computer Networks - SCOPE, VIT Vellore
 * Authors: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
 * ==============================================================================
 * Transfers a 50 MB Medical PACS Imaging Study from Remote Clinic to Server:
 *   - Evaluates: TcpNewReno, TcpCubic, TcpBbr, TcpVegas, TcpWestwoodPlus
 *   - Error Rates (RateErrorModel): 0.0%, 0.1%, 0.5%, 1.0%
 *   - Competing Traffic: With and without 500 kbps Guest Cross-Traffic
 *   - Traces: Real-time Congestion Window (cwnd) logged via trace source
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
#include <iomanip>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("HospitalE4TcpSimulation");

static std::ofstream g_cwndStream;
static uint32_t g_retransmissions = 0;

void CwndChangeCallback(uint32_t oldCwnd, uint32_t newCwnd)
{
  double t = Simulator::Now().GetSeconds();
  if (g_cwndStream.is_open())
    {
      g_cwndStream << std::fixed << std::setprecision(6) << t << " " << newCwnd << "\n";
    }
}

void RtoExpiredCallback(Time oldRto, Time newRto)
{
  g_retransmissions++;
}

void ConnectTcpTraces()
{
  Config::ConnectWithoutContext("/NodeList/*/$ns3::TcpL4Protocol/SocketList/*/CongestionWindow",
                               MakeCallback(&CwndChangeCallback));
  Config::ConnectWithoutContext("/NodeList/*/$ns3::TcpL4Protocol/SocketList/*/RTO",
                               MakeCallback(&RtoExpiredCallback));
}

int main(int argc, char *argv[])
{
  uint32_t seed = 1;
  uint32_t run = 1;
  double simTime = 220.0;                // Max seconds allowed for 50 MB transfer over 2 Mbps
  double errorRate = 0.0;                // 0.0, 0.001 (0.1%), 0.005 (0.5%), 0.01 (1.0%)
  bool competingGuest = false;           // Enable 500 kbps guest cross traffic
  std::string guestRate = "500kbps";
  std::string tcpVariant = "TcpCubic";   // TcpNewReno, TcpCubic, TcpBbr, TcpVegas, TcpWestwoodPlus
  uint32_t imagingSizeMb = 50;           // 50 MB medical study
  std::string cwndTrace = "results/e4_tcp/traces/cwnd.dat";
  std::string csvSummary = "results/e4_tcp/e4_summary.csv";
  std::string expId = "E4-RUN";

  CommandLine cmd(__FILE__);
  cmd.AddValue("seed", "RNG seed", seed);
  cmd.AddValue("run", "RNG run index", run);
  cmd.AddValue("simTime", "Maximum simulation execution duration in seconds", simTime);
  cmd.AddValue("errorRate", "Packet loss rate on WAN link (0.0 to 0.05)", errorRate);
  cmd.AddValue("competingGuest", "Enable competing guest background traffic", competingGuest);
  cmd.AddValue("guestRate", "Rate of competing guest traffic", guestRate);
  cmd.AddValue("tcpVariant", "TCP congestion algorithm (TcpNewReno, TcpCubic, TcpBbr, TcpVegas)", tcpVariant);
  cmd.AddValue("imagingSize", "PACS imaging transfer size in MB (default 50)", imagingSizeMb);
  cmd.AddValue("cwndTrace", "Output file for congestion window trace", cwndTrace);
  cmd.AddValue("csvSummary", "Output summary CSV path", csvSummary);
  cmd.AddValue("expId", "Experiment ID identifier", expId);
  cmd.Parse(argc, argv);

  RngSeedManager::SetSeed(seed);
  RngSeedManager::SetRun(run);

  // Configure Selected TCP Variant
  TypeId tcpTypeId = TypeId::LookupByName("ns3::" + tcpVariant);
  Config::SetDefault("ns3::TcpL4Protocol::SocketType", TypeIdValue(tcpTypeId));
  Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(1460));

  // ---------------------------------------------------------------------------
  // 1. Topology Setup
  // ---------------------------------------------------------------------------
  Ptr<Node> nodeR1 = CreateObject<Node>();
  Ptr<Node> nodeR2 = CreateObject<Node>();
  Ptr<Node> nodeServer = CreateObject<Node>();       // Destination PACS Server
  Ptr<Node> nodeClinicImaging = CreateObject<Node>();// Source Clinic Workstation
  Ptr<Node> nodeClinicGuest = CreateObject<Node>();  // Competing Guest Node

  Names::Add("Core-R1", nodeR1);
  Names::Add("Core-R2", nodeR2);
  Names::Add("Records-Server", nodeServer);
  Names::Add("Clinic-Imaging", nodeClinicImaging);
  Names::Add("Clinic-Guest", nodeClinicGuest);

  // 2.0 Mbps, 10ms Primary WAN Link
  PointToPointHelper p2pWan;
  p2pWan.SetDeviceAttribute("DataRate", StringValue("2Mbps"));
  p2pWan.SetChannelAttribute("Delay", StringValue("10ms"));
  p2pWan.SetQueue("ns3::DropTailQueue", "MaxSize", StringValue("100p"));

  // 100 Mbps Campus Access Links
  PointToPointHelper p2pLan;
  p2pLan.SetDeviceAttribute("DataRate", StringValue("100Mbps"));
  p2pLan.SetChannelAttribute("Delay", StringValue("1ms"));

  NetDeviceContainer wanDevs = p2pWan.Install(nodeR1, nodeR2);
  NetDeviceContainer serverDevs = p2pLan.Install(nodeServer, nodeR1);
  NetDeviceContainer imagingDevs = p2pLan.Install(nodeClinicImaging, nodeR2);
  NetDeviceContainer guestDevs = p2pLan.Install(nodeClinicGuest, nodeR2);

  // Apply Packet Error Model (RateErrorModel) on Primary WAN
  if (errorRate > 0.0)
    {
      Ptr<RateErrorModel> emR1 = CreateObject<RateErrorModel>();
      emR1->SetAttribute("ErrorRate", DoubleValue(errorRate));
      emR1->SetAttribute("ErrorUnit", StringValue("ERROR_UNIT_PACKET"));
      wanDevs.Get(0)->SetAttribute("ReceiveErrorModel", PointerValue(emR1));

      Ptr<RateErrorModel> emR2 = CreateObject<RateErrorModel>();
      emR2->SetAttribute("ErrorRate", DoubleValue(errorRate));
      emR2->SetAttribute("ErrorUnit", StringValue("ERROR_UNIT_PACKET"));
      wanDevs.Get(1)->SetAttribute("ReceiveErrorModel", PointerValue(emR2));
    }

  // Internet Stack
  InternetStackHelper internet;
  internet.Install(nodeR1);
  internet.Install(nodeR2);
  internet.Install(nodeServer);
  internet.Install(nodeClinicImaging);
  internet.Install(nodeClinicGuest);

  // IP Addressing (VLSM Alignment)
  Ipv4AddressHelper ipv4;
  ipv4.SetBase("172.16.8.80", "255.255.255.252"); // WAN
  ipv4.Assign(wanDevs);

  ipv4.SetBase("172.16.7.0", "255.255.255.192", "0.0.0.10"); // Server
  Ipv4InterfaceContainer ifServer = ipv4.Assign(serverDevs);
  Ipv4Address serverIp = ifServer.GetAddress(0);

  ipv4.SetBase("172.16.8.32", "255.255.255.224", "0.0.0.45"); // Clinic Imaging
  ipv4.Assign(imagingDevs);

  ipv4.SetBase("172.16.6.128", "255.255.255.128", "0.0.0.135"); // Clinic Guest
  ipv4.Assign(guestDevs);

  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  // ---------------------------------------------------------------------------
  // 2. Traffic Configuration: 50 MB PACS Imaging Transfer + Competing Guest
  // ---------------------------------------------------------------------------
  uint64_t totalBytes = static_cast<uint64_t>(imagingSizeMb) * 1024 * 1024; // 52,428,800 bytes
  uint16_t pacsPort = 5002;

  PacketSinkHelper pacsSink("ns3::TcpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), pacsPort));
  ApplicationContainer sinkApp = pacsSink.Install(nodeServer);
  sinkApp.Start(Seconds(0.5));
  sinkApp.Stop(Seconds(simTime));

  BulkSendHelper pacsClient("ns3::TcpSocketFactory", InetSocketAddress(serverIp, pacsPort));
  pacsClient.SetAttribute("MaxBytes", UintegerValue(totalBytes));
  pacsClient.SetAttribute("SendSize", UintegerValue(1460));
  ApplicationContainer clientApp = pacsClient.Install(nodeClinicImaging);
  clientApp.Start(Seconds(1.0));
  clientApp.Stop(Seconds(simTime));

  // Competing Guest Traffic
  if (competingGuest)
    {
      uint16_t guestPort = 5005;
      PacketSinkHelper guestSink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), guestPort));
      ApplicationContainer guestSinkApp = guestSink.Install(nodeServer);
      guestSinkApp.Start(Seconds(0.5));
      guestSinkApp.Stop(Seconds(simTime));

      OnOffHelper guestApp("ns3::UdpSocketFactory", Address(InetSocketAddress(serverIp, guestPort)));
      guestApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
      guestApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
      guestApp.SetAttribute("DataRate", DataRateValue(DataRate(guestRate)));
      guestApp.SetAttribute("PacketSize", UintegerValue(1024));
      ApplicationContainer guestClientApp = guestApp.Install(nodeClinicGuest);
      guestClientApp.Start(Seconds(2.0));
      guestClientApp.Stop(Seconds(simTime));
    }

  // ---------------------------------------------------------------------------
  // 3. Connect Trace Sinks & Log CWND
  // ---------------------------------------------------------------------------
  // Create trace directory
  std::string dirPath = cwndTrace.substr(0, cwndTrace.find_last_of("/\\"));
  if (!dirPath.empty())
    {
      // Directory will be handled by runner or created
    }
  g_cwndStream.open(cwndTrace);
  if (g_cwndStream.is_open())
    {
      g_cwndStream << "# time_s cwnd_bytes\n";
    }

  Simulator::Schedule(Seconds(1.0001), &ConnectTcpTraces);

  // FlowMonitor Setup
  FlowMonitorHelper flowmon;
  Ptr<FlowMonitor> monitor = flowmon.InstallAll();

  // Run Simulation
  Simulator::Stop(Seconds(simTime));
  Simulator::Run();

  if (g_cwndStream.is_open())
    {
      g_cwndStream.close();
    }

  // ---------------------------------------------------------------------------
  // 4. Extract Performance Metrics
  // ---------------------------------------------------------------------------
  monitor->CheckForLostPackets();
  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmon.GetClassifier());
  std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

  double completionTimeS = 0.0;
  double throughputKbps = 0.0;
  uint32_t txPackets = 0;
  uint32_t rxPackets = 0;
  uint32_t lostPackets = 0;

  for (auto const &flow : stats)
    {
      Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(flow.first);
      if (t.destinationPort == pacsPort)
        {
          double tFirst = flow.second.timeFirstTxPacket.GetSeconds();
          double tLast = flow.second.timeLastRxPacket.GetSeconds();
          completionTimeS = tLast - tFirst;
          throughputKbps = completionTimeS > 0 ? (flow.second.rxBytes * 8.0) / (completionTimeS * 1000.0) : 0.0;
          txPackets = flow.second.txPackets;
          rxPackets = flow.second.rxPackets;
          lostPackets = flow.second.lostPackets;
          break;
        }
    }

  // Append Summary CSV Record
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
          csvOut << "exp_id,seed,run,tcp_variant,error_rate_pct,competing_guest,completion_time_s,throughput_kbps,retransmissions,tx_packets,rx_packets,lost_packets\n";
        }
      csvOut << expId << ","
             << seed << ","
             << run << ","
             << tcpVariant << ","
             << std::fixed << std::setprecision(2) << (errorRate * 100.0) << ","
             << (competingGuest ? "1" : "0") << ","
             << std::fixed << std::setprecision(2) << completionTimeS << ","
             << std::fixed << std::setprecision(2) << throughputKbps << ","
             << (lostPackets + g_retransmissions) << ","
             << txPackets << ","
             << rxPackets << ","
             << lostPackets << "\n";
      csvOut.close();
    }

  std::cout << "[E4 RUN COMPLETED] Variant=" << tcpVariant
            << " | Loss=" << (errorRate * 100.0) << "%"
            << " | Guest=" << (competingGuest ? "Yes" : "No")
            << " | Time=" << completionTimeS << "s"
            << " | Throughput=" << throughputKbps << " kbps"
            << " | Retx=" << (lostPackets + g_retransmissions)
            << " | CWND Trace=" << cwndTrace << std::endl;

  Simulator::Destroy();
  return 0;
}
