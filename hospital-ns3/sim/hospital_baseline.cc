/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * ==============================================================================
 * hospital_baseline.cc - Discrete-Event Simulation of Smart Hospital Network
 * Disaster-Resilient Smart Hospital Network (NS-3 Academic Extension)
 * Course: CSE2004 Computer Networks - SCOPE, VIT Vellore
 * Authors: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
 * ==============================================================================
 * Topology:
 *   [Main Hospital LAN]                               [Remote Clinic LAN]
 *    - ICU Vitals (UDP 100Hz)                          - Clinic Triage (UDP)
 *    - PACS Imaging (TCP Bulk)                         - Clinic Admin (TCP)
 *    - Admin Web (TCP OnOff)       Primary WAN (2M)    - Clinic Voice (UDP)
 *    - Voice VoIP (UDP 20ms)     +-----------------+
 *    - Guest Wi-Fi (Best Effort) | 172.16.8.80/30  |
 *          \                     | Delay: 10ms     |         /
 *           [Core Router R1] ----+                 +---- [Core Router R2]
 *                                | Backup WAN (1M) |
 *                                | 172.16.8.84/30  |
 *                                | Delay: 25ms     |
 *                                +-----------------+
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
#include <iomanip>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("HospitalBaselineSimulation");

int main(int argc, char *argv[])
{
  // Simulation Command-Line Parameters
  uint32_t seed = 1;
  uint32_t run = 1;
  double simTime = 30.0;                 // Total simulation duration (seconds)
  double failureTime = 12.0;             // Primary WAN failure event time (seconds)
  double recoveryTime = 22.0;            // Primary WAN recovery event time (seconds)
  bool enableFailure = true;             // Toggle WAN failure injection
  bool enablePcap = false;               // Toggle PCAP generation
  std::string tcpVariant = "TcpCubic";   // TCP congestion control variant
  std::string xmlTrace = "flowmon.xml";  // FlowMonitor XML export path
  std::string csvSummary = "summary.csv";// One-line CSV summary path
  std::string expId = "EXP-01-BASELINE";

  CommandLine cmd(__FILE__);
  cmd.AddValue("seed", "Random number generator seed", seed);
  cmd.AddValue("run", "Random number generator run number", run);
  cmd.AddValue("simTime", "Total simulation execution time in seconds", simTime);
  cmd.AddValue("failureTime", "Time to inject primary WAN link failure", failureTime);
  cmd.AddValue("recoveryTime", "Time to restore primary WAN link", recoveryTime);
  cmd.AddValue("enableFailure", "Enable link failure event injection", enableFailure);
  cmd.AddValue("enablePcap", "Enable PCAP packet traces on all links", enablePcap);
  cmd.AddValue("tcpVariant", "TCP congestion control variant (TcpNewReno, TcpCubic, TcpBbr)", tcpVariant);
  cmd.AddValue("xmlTrace", "Output path for FlowMonitor XML file", xmlTrace);
  cmd.AddValue("csvSummary", "Output path for one-line CSV summary row", csvSummary);
  cmd.AddValue("expId", "Experiment identifier label", expId);
  cmd.Parse(argc, argv);

  // Seed Pseudo-Random Number Generator for Strict Repeatability
  RngSeedManager::SetSeed(seed);
  RngSeedManager::SetRun(run);

  // Configure TCP Congestion Control Variant
  TypeId tcpTypeId = TypeId::LookupByName("ns3::" + tcpVariant);
  Config::SetDefault("ns3::TcpL4Protocol::SocketType", TypeIdValue(tcpTypeId));

  NS_LOG_INFO("Initializing Disaster-Resilient Hospital Network Simulation...");

  // ---------------------------------------------------------------------------
  // 1. Create Core Routers and Hospital Nodes
  // ---------------------------------------------------------------------------
  NodeContainer coreRouters;
  coreRouters.Create(2); // Node 0: Main R1, Node 1: Remote R2

  NodeContainer mainHospitalNodes;
  mainHospitalNodes.Create(5); 
  // Main: 0=ICU Sensor, 1=PACS Workstation, 2=Admin PC, 3=VoIP Phone, 4=Server Farm

  NodeContainer remoteClinicNodes;
  remoteClinicNodes.Create(4);
  // Remote: 0=Clinic Triage, 1=Clinic Admin, 2=Clinic VoIP, 3=Clinic Guest

  // ---------------------------------------------------------------------------
  // 2. Configure Point-to-Point WAN and Campus LAN Links
  // ---------------------------------------------------------------------------
  // Primary WAN: 2 Mbps, 10ms propagation delay (OSPF Area 0 Primary Path)
  PointToPointHelper p2pPrimaryWan;
  p2pPrimaryWan.SetDeviceAttribute("DataRate", StringValue("2Mbps"));
  p2pPrimaryWan.SetChannelAttribute("Delay", StringValue("10ms"));
  p2pPrimaryWan.SetQueue("ns3::DropTailQueue", "MaxSize", StringValue("100p"));

  // Backup WAN: 1 Mbps, 25ms propagation delay (Standby Disaster Link)
  PointToPointHelper p2pBackupWan;
  p2pBackupWan.SetDeviceAttribute("DataRate", StringValue("1Mbps"));
  p2pBackupWan.SetChannelAttribute("Delay", StringValue("25ms"));
  p2pBackupWan.SetQueue("ns3::DropTailQueue", "MaxSize", StringValue("100p"));

  // Hospital Campus LAN Links: 100 Mbps FastEthernet, 1ms delay
  PointToPointHelper lanHelper;
  lanHelper.SetDeviceAttribute("DataRate", StringValue("100Mbps"));
  lanHelper.SetChannelAttribute("Delay", StringValue("1ms"));

  // Install WAN NetDevices
  NetDeviceContainer primaryWanDevices = p2pPrimaryWan.Install(coreRouters.Get(0), coreRouters.Get(1));
  NetDeviceContainer backupWanDevices = p2pBackupWan.Install(coreRouters.Get(0), coreRouters.Get(1));

  // Install Main Hospital LAN NetDevices
  std::vector<NetDeviceContainer> mainLanDevices(5);
  for (uint32_t i = 0; i < 5; ++i)
    {
      mainLanDevices[i] = lanHelper.Install(mainHospitalNodes.Get(i), coreRouters.Get(0));
    }

  // Install Remote Clinic LAN NetDevices
  std::vector<NetDeviceContainer> remoteLanDevices(4);
  for (uint32_t i = 0; i < 4; ++i)
    {
      remoteLanDevices[i] = lanHelper.Install(remoteClinicNodes.Get(i), coreRouters.Get(1));
    }

  // ---------------------------------------------------------------------------
  // 3. Install Internet Stack & Global Routing
  // ---------------------------------------------------------------------------
  InternetStackHelper stack;
  stack.Install(coreRouters);
  stack.Install(mainHospitalNodes);
  stack.Install(remoteClinicNodes);

  // Assign IP Addresses matching VLSM Plan (172.16.0.0/16)
  Ipv4AddressHelper ipv4;

  // Primary WAN: 172.16.8.80/30
  ipv4.SetBase("172.16.8.80", "255.255.255.252");
  Ipv4InterfaceContainer primaryWanInterfaces = ipv4.Assign(primaryWanDevices);

  // Backup WAN: 172.16.8.84/30
  ipv4.SetBase("172.16.8.84", "255.255.255.252");
  Ipv4InterfaceContainer backupWanInterfaces = ipv4.Assign(backupWanDevices);

  // Main Hospital Subnets:
  // Node 0: ICU Vitals -> 172.16.7.128/26
  ipv4.SetBase("172.16.7.128", "255.255.255.192");
  Ipv4InterfaceContainer icuIfs = ipv4.Assign(mainLanDevices[0]);

  // Node 1: PACS Imaging -> 172.16.7.64/26
  ipv4.SetBase("172.16.7.64", "255.255.255.192");
  Ipv4InterfaceContainer pacsIfs = ipv4.Assign(mainLanDevices[1]);

  // Node 2: Admin Workstations -> 172.16.4.0/23
  ipv4.SetBase("172.16.4.0", "255.255.254.0");
  Ipv4InterfaceContainer adminIfs = ipv4.Assign(mainLanDevices[2]);

  // Node 3: Clinical Voice VoIP -> 172.16.6.0/25
  ipv4.SetBase("172.16.6.0", "255.255.255.128");
  Ipv4InterfaceContainer voiceIfs = ipv4.Assign(mainLanDevices[3]);

  // Node 4: Server Farm (EHR & Telemetry Sink) -> 172.16.7.0/26
  ipv4.SetBase("172.16.7.0", "255.255.255.192");
  Ipv4InterfaceContainer serverIfs = ipv4.Assign(mainLanDevices[4]);

  // Remote Clinic Subnets:
  // Node 0: Clinic Clinical Triage -> 172.16.8.32/27
  ipv4.SetBase("172.16.8.32", "255.255.255.224");
  Ipv4InterfaceContainer triageIfs = ipv4.Assign(remoteLanDevices[0]);

  // Node 1: Clinic Admin Workstations -> 172.16.8.0/27
  ipv4.SetBase("172.16.8.0", "255.255.255.224");
  Ipv4InterfaceContainer clinicAdminIfs = ipv4.Assign(remoteLanDevices[1]);

  // Node 2: Clinic Voice VoIP -> 172.16.7.224/27
  ipv4.SetBase("172.16.7.224", "255.255.255.224");
  Ipv4InterfaceContainer clinicVoiceIfs = ipv4.Assign(remoteLanDevices[2]);

  // Node 3: Clinic Guest Wi-Fi -> 172.16.6.128/25
  ipv4.SetBase("172.16.6.128", "255.255.255.128");
  Ipv4InterfaceContainer clinicGuestIfs = ipv4.Assign(remoteLanDevices[3]);

  // Calculate Routing Tables (Dijkstra Shortest Path First / OSPF-like)
  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  // ---------------------------------------------------------------------------
  // 4. Clinical Traffic Generation (SLA Priority Hierarchy)
  // ---------------------------------------------------------------------------
  Ipv4Address serverIp = serverIfs.GetAddress(0); // Server Farm EHR / Telemetry Collector

  // 4.1. Life-Critical ICU Vitals Stream (UDP, 200 bytes @ 100 Hz = 160 kbps)
  uint16_t icuPort = 5001;
  Address sinkLocalAddress(InetSocketAddress(Ipv4Address::GetAny(), icuPort));
  PacketSinkHelper icuSinkHelper("ns3::UdpSocketFactory", sinkLocalAddress);
  ApplicationContainer icuSinkApp = icuSinkHelper.Install(mainHospitalNodes.Get(4)); // Server
  icuSinkApp.Start(Seconds(1.0));
  icuSinkApp.Stop(Seconds(simTime));

  OnOffHelper icuClient("ns3::UdpSocketFactory", Address(InetSocketAddress(serverIp, icuPort)));
  icuClient.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  icuClient.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  icuClient.SetAttribute("DataRate", DataRateValue(DataRate("160Kbps")));
  icuClient.SetAttribute("PacketSize", UintegerValue(200));
  ApplicationContainer icuApp = icuClient.Install(mainHospitalNodes.Get(0)); // ICU Sensor Node
  icuApp.Start(Seconds(2.0));
  icuApp.Stop(Seconds(simTime - 1.0));

  // 4.2. Medical PACS Imaging Transfer (TCP BulkSend)
  uint16_t pacsPort = 5002;
  PacketSinkHelper pacsSinkHelper("ns3::TcpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), pacsPort));
  ApplicationContainer pacsSinkApp = pacsSinkHelper.Install(mainHospitalNodes.Get(4)); // Server
  pacsSinkApp.Start(Seconds(1.0));
  pacsSinkApp.Stop(Seconds(simTime));

  BulkSendHelper pacsClient("ns3::TcpSocketFactory", InetSocketAddress(serverIp, pacsPort));
  pacsClient.SetAttribute("MaxBytes", UintegerValue(5000000)); // 5 MB transfer
  pacsClient.SetAttribute("SendSize", UintegerValue(1460));
  ApplicationContainer pacsApp = pacsClient.Install(mainHospitalNodes.Get(1)); // PACS Station
  pacsApp.Start(Seconds(3.0));
  pacsApp.Stop(Seconds(simTime - 1.0));

  // 4.3. Remote Clinic Cross-WAN Telemetry Stream (Clinic Triage -> Server)
  uint16_t triagePort = 5003;
  PacketSinkHelper triageSinkHelper("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), triagePort));
  ApplicationContainer triageSinkApp = triageSinkHelper.Install(mainHospitalNodes.Get(4));
  triageSinkApp.Start(Seconds(1.0));
  triageSinkApp.Stop(Seconds(simTime));

  OnOffHelper triageClient("ns3::UdpSocketFactory", Address(InetSocketAddress(serverIp, triagePort)));
  triageClient.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  triageClient.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  triageClient.SetAttribute("DataRate", DataRateValue(DataRate("256Kbps")));
  triageClient.SetAttribute("PacketSize", UintegerValue(256));
  ApplicationContainer triageApp = triageClient.Install(remoteClinicNodes.Get(0));
  triageApp.Start(Seconds(2.5));
  triageApp.Stop(Seconds(simTime - 1.0));

  // ---------------------------------------------------------------------------
  // 5. Disaster Failover Event Scheduling
  // ---------------------------------------------------------------------------
  if (enableFailure)
    {
      // Simulate Primary WAN Fiber Cut at failureTime
      Simulator::Schedule(Seconds(failureTime), &PointToPointNetDevice::SetReceiveErrorModel,
                          DynamicCast<PointToPointNetDevice>(primaryWanDevices.Get(0)),
                          CreateObject<RateErrorModel>());
      Simulator::Schedule(Seconds(failureTime), &Ipv4GlobalRoutingHelper::RecomputeRoutingTables);

      // Simulate WAN Link Recovery at recoveryTime
      Simulator::Schedule(Seconds(recoveryTime), &Ipv4GlobalRoutingHelper::RecomputeRoutingTables);
    }

  if (enablePcap)
    {
      p2pPrimaryWan.EnablePcapAll("hospital-primary-wan");
      p2pBackupWan.EnablePcapAll("hospital-backup-wan");
    }

  // ---------------------------------------------------------------------------
  // 6. FlowMonitor Measurement Engine
  // ---------------------------------------------------------------------------
  FlowMonitorHelper flowmon;
  Ptr<FlowMonitor> monitor = flowmon.InstallAll();

  // Run Simulation
  Simulator::Stop(Seconds(simTime));
  Simulator::Run();

  // Collect Metrics
  monitor->CheckForLostPackets();
  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmon.GetClassifier());
  std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

  uint64_t totalTxBytes = 0;
  uint64_t totalRxBytes = 0;
  uint32_t totalTxPackets = 0;
  uint32_t totalRxPackets = 0;
  uint32_t totalLostPackets = 0;
  double sumDelayMs = 0.0;
  uint32_t activeFlows = 0;

  for (auto const &flow : stats)
    {
      totalTxBytes += flow.second.txBytes;
      totalRxBytes += flow.second.rxBytes;
      totalTxPackets += flow.second.txPackets;
      totalRxPackets += flow.second.rxPackets;
      totalLostPackets += flow.second.lostPackets;

      if (flow.second.rxPackets > 0)
        {
          sumDelayMs += (flow.second.delaySum.GetSeconds() / flow.second.rxPackets) * 1000.0;
          activeFlows++;
        }
    }

  double avgDelayMs = activeFlows > 0 ? (sumDelayMs / activeFlows) : 0.0;
  double deliveryRatio = totalTxPackets > 0 ? (100.0 * totalRxPackets / totalTxPackets) : 0.0;
  double overallThroughputKbps = (totalRxBytes * 8.0) / (simTime * 1000.0);

  // Export FlowMonitor XML
  monitor->SerializeToXmlFile(xmlTrace, true, true);

  // Write One-Line Standardized CSV Row
  std::ofstream csvFile(csvSummary, std::ios::app);
  if (csvFile.is_open())
    {
      // Check if file is newly created to write header
      std::ifstream checkFile(csvSummary);
      checkFile.seekg(0, std::ios::end);
      if (checkFile.tellg() <= 0)
        {
          csvFile << "exp_id,seed,run,sim_time,failure_time,tcp_variant,tx_packets,rx_packets,lost_packets,delivery_ratio_pct,avg_delay_ms,throughput_kbps\n";
        }
      csvFile << expId << ","
              << seed << ","
              << run << ","
              << simTime << ","
              << failureTime << ","
              << tcpVariant << ","
              << totalTxPackets << ","
              << totalRxPackets << ","
              << totalLostPackets << ","
              << std::fixed << std::setprecision(2) << deliveryRatio << ","
              << std::fixed << std::setprecision(2) << avgDelayMs << ","
              << std::fixed << std::setprecision(2) << overallThroughputKbps << "\n";
      csvFile.close();
    }

  std::cout << "================================================================================" << std::endl;
  std::cout << "  NS-3 HOSPITAL SIMULATION RUN COMPLETE (" << expId << ")" << std::endl;
  std::cout << "================================================================================" << std::endl;
  std::cout << "  Seed / Run Number        : " << seed << " / " << run << std::endl;
  std::cout << "  TCP Variant              : " << tcpVariant << std::endl;
  std::cout << "  Packets Transmitted      : " << totalTxPackets << std::endl;
  std::cout << "  Packets Received         : " << totalRxPackets << std::endl;
  std::cout << "  Packets Lost             : " << totalLostPackets << std::endl;
  std::cout << "  Packet Delivery Ratio    : " << std::fixed << std::setprecision(2) << deliveryRatio << " %" << std::endl;
  std::cout << "  Average End-to-End Delay : " << std::fixed << std::setprecision(2) << avgDelayMs << " ms" << std::endl;
  std::cout << "  Aggregated Throughput    : " << std::fixed << std::setprecision(2) << overallThroughputKbps << " kbps" << std::endl;
  std::cout << "  FlowMonitor XML Export   : " << xmlTrace << std::endl;
  std::cout << "  Summary CSV Appended     : " << csvSummary << std::endl;
  std::cout << "================================================================================" << std::endl;

  Simulator::Destroy();
  return 0;
}
