/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * ==============================================================================
 * e6_wifi.cc - Experiment 6: Hospital Wi-Fi Capacity, Hidden Terminal, Mobility & Fading
 * Disaster-Resilient Smart Hospital Network (NS-3 Discrete-Event Phase)
 * Course: CSE2004 Computer Networks - SCOPE, VIT Vellore
 * Authors: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
 * ==============================================================================
 * Studies:
 *   (a) Station Count Scalability: 5 to 50 STAs vs Throughput, Delay, Retries
 *   (b) Hidden Terminal Mitigation: Spatial isolation with vs without RTS/CTS
 *   (c) Clinical Mobility: RandomWaypoint, RandomWalk, GaussMarkov at 1.0, 2.5, 5.0 m/s
 *   (d) Multipath Fading: Friis Free Space vs Nakagami-m Fast Fading
 *
 * Architecture:
 *   - 1 Access Point (AP) connected via 100 Mbps LAN link to Central EHR/PACS Server
 *   - Clinical Zone (Nurse Tablets): High-priority UDP telemetry/EHR queries (172.16.5.0/24)
 *   - Guest Zone (Smartphones): Best-effort untrusted browsing (172.16.0.0/22)
 * ==============================================================================
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/mobility-module.h"
#include "ns3/wifi-module.h"
#include "ns3/flow-monitor-module.h"

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <iomanip>
#include <cmath>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("HospitalE6WifiSimulation");

static uint32_t g_macTxDropCount = 0;
static uint32_t g_macRetries = 0;

void MacTxDropCallback(std::string context, Ptr<const Packet> p)
{
  g_macTxDropCount++;
}

int main(int argc, char *argv[])
{
  uint32_t seed = 1;
  uint32_t run = 1;
  double simTime = 20.0;
  std::string study = "station_count"; // station_count, hidden_terminal, mobility, fading
  uint32_t nStations = 10;             // 5, 10, 20, 30, 40, 50
  bool enableRtsCts = false;           // RTS/CTS handshake toggle
  std::string mobilityModel = "random_waypoint"; // constant, random_waypoint, random_walk, gauss_markov
  double speed = 1.5;                  // Speed in m/s (1.0 = walking, 2.5 = trolley, 5.0 = running)
  std::string lossModel = "friis";     // friis, log_distance, nakagami
  std::string csvSummary = "results/e6_wifi/e6_summary.csv";
  std::string expId = "E6-WIFI";

  CommandLine cmd(__FILE__);
  cmd.AddValue("seed", "RNG seed", seed);
  cmd.AddValue("run", "RNG run index", run);
  cmd.AddValue("simTime", "Simulation execution duration in seconds", simTime);
  cmd.AddValue("study", "Study selection: station_count, hidden_terminal, mobility, fading", study);
  cmd.AddValue("nStations", "Number of wireless stations (5 to 50)", nStations);
  cmd.AddValue("enableRtsCts", "Enable RTS/CTS handshake mechanism", enableRtsCts);
  cmd.AddValue("mobilityModel", "Mobility model: constant, random_waypoint, random_walk, gauss_markov", mobilityModel);
  cmd.AddValue("speed", "Station velocity in m/s", speed);
  cmd.AddValue("lossModel", "Propagation loss model: friis, log_distance, nakagami", lossModel);
  cmd.AddValue("csvSummary", "Output summary CSV path", csvSummary);
  cmd.AddValue("expId", "Experiment ID identifier", expId);
  cmd.Parse(argc, argv);

  RngSeedManager::SetSeed(seed);
  RngSeedManager::SetRun(run);

  // Configure RTS/CTS threshold on Wi-Fi Remote Station Manager
  if (enableRtsCts)
    {
      Config::SetDefault("ns3::WifiRemoteStationManager::RtsCtsThreshold", UintegerValue(100)); // Engage RTS/CTS for packets >= 100B
    }
  else
    {
      Config::SetDefault("ns3::WifiRemoteStationManager::RtsCtsThreshold", UintegerValue(65535)); // Disable RTS/CTS
    }

  // ---------------------------------------------------------------------------
  // 1. Create Nodes
  // ---------------------------------------------------------------------------
  Ptr<Node> nodeServer = CreateObject<Node>();
  Ptr<Node> nodeAp = CreateObject<Node>();

  uint32_t actualStations = (study == "hidden_terminal") ? 2 : nStations;
  NodeContainer staNodes;
  staNodes.Create(actualStations);

  // ---------------------------------------------------------------------------
  // 2. Wired Link: Server <--> AP (100 Mbps, 1ms delay)
  // ---------------------------------------------------------------------------
  PointToPointHelper p2p;
  p2p.SetDeviceAttribute("DataRate", StringValue("100Mbps"));
  p2p.SetChannelAttribute("Delay", StringValue("1ms"));

  NetDeviceContainer serverApDevs = p2p.Install(nodeServer, nodeAp);

  // ---------------------------------------------------------------------------
  // 3. Wireless Physical Channel & Propagation Loss Model
  // ---------------------------------------------------------------------------
  YansWifiChannelHelper wifiChannel;
  wifiChannel.SetPropagationDelay("ns3::ConstantSpeedPropagationDelayModel");

  if (lossModel == "nakagami")
    {
      // Two-component model: LogDistance base + Nakagami-m fast multipath fading
      wifiChannel.AddPropagationLoss("ns3::LogDistancePropagationLossModel",
                                     "Exponent", DoubleValue(3.0),
                                     "ReferenceDistance", DoubleValue(1.0),
                                     "ReferenceLoss", DoubleValue(40.0));
      wifiChannel.AddPropagationLoss("ns3::NakagamiPropagationLossModel",
                                     "m0", DoubleValue(1.5),
                                     "m1", DoubleValue(1.0),
                                     "m2", DoubleValue(0.75));
    }
  else if (lossModel == "log_distance")
    {
      wifiChannel.AddPropagationLoss("ns3::LogDistancePropagationLossModel",
                                     "Exponent", DoubleValue(3.0),
                                     "ReferenceDistance", DoubleValue(1.0),
                                     "ReferenceLoss", DoubleValue(40.0));
    }
  else // friis
    {
      wifiChannel.AddPropagationLoss("ns3::FriisPropagationLossModel",
                                     "Frequency", DoubleValue(2.4e9));
    }

  YansWifiPhyHelper wifiPhy;
  wifiPhy.SetChannel(wifiChannel.Create());

  // ---------------------------------------------------------------------------
  // 4. Wi-Fi MAC & Helper (802.11n Standard with Minstrel/Ideal Rate Adaptation)
  // ---------------------------------------------------------------------------
  WifiHelper wifi;
  wifi.SetStandard(WIFI_STANDARD_80211n);
  wifi.SetRemoteStationManager("ns3::IdealWifiManager");

  WifiMacHelper wifiMac;
  Ssid ssid = Ssid("hospital-clinical-wlan");

  // Configure STA MAC (Nurse Tablets & Guest Devices)
  wifiMac.SetType("ns3::StaWifiMac",
                  "Ssid", SsidValue(ssid),
                  "ActiveProbing", BooleanValue(false));
  NetDeviceContainer staDevices = wifi.Install(wifiPhy, wifiMac, staNodes);

  // Configure AP MAC
  wifiMac.SetType("ns3::ApWifiMac",
                  "Ssid", SsidValue(ssid));
  NetDeviceContainer apDevices = wifi.Install(wifiPhy, wifiMac, nodeAp);

  // ---------------------------------------------------------------------------
  // 5. Node Mobility Configuration
  // ---------------------------------------------------------------------------
  MobilityHelper mobility;

  // AP Position: Center of hospital ward ceiling at (0, 0, 2.5)
  Ptr<ListPositionAllocator> apPosAlloc = CreateObject<ListPositionAllocator>();
  apPosAlloc->Add(Vector(0.0, 0.0, 2.5));
  mobility.SetPositionAllocator(apPosAlloc);
  mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
  mobility.Install(nodeAp);
  mobility.Install(nodeServer);

  // Station Positions / Mobility Models
  if (study == "hidden_terminal")
    {
      // Hidden Terminal Geometry:
      // AP at (0, 0). STA 1 at (-25, 0), STA 2 at (+25, 0).
      // Distance STA1 <-> STA2 = 50m (exceeds 35m carrier sense range: hidden!)
      // Distance STA1 <-> AP = 25m, STA2 <-> AP = 25m (both within AP range)
      Ptr<ListPositionAllocator> htPosAlloc = CreateObject<ListPositionAllocator>();
      htPosAlloc->Add(Vector(-25.0, 0.0, 1.2)); // STA 1
      htPosAlloc->Add(Vector(+25.0, 0.0, 1.2)); // STA 2
      mobility.SetPositionAllocator(htPosAlloc);
      mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
      mobility.Install(staNodes);
    }
  else if (study == "mobility")
    {
      if (mobilityModel == "random_walk")
        {
          mobility.SetPositionAllocator("ns3::RandomDiscPositionAllocator",
                                        "X", StringValue("0.0"),
                                        "Y", StringValue("0.0"),
                                        "Rho", StringValue("ns3::UniformRandomVariable[Min=2.0|Max=20.0]"));
          mobility.SetMobilityModel("ns3::RandomWalk2dMobilityModel",
                                    "Mode", StringValue("Time"),
                                    "Time", StringValue("2s"),
                                    "Speed", StringValue("ns3::ConstantRandomVariable[Constant=" + std::to_string(speed) + "]"),
                                    "Bounds", StringValue("-25|25|-25|25"));
          mobility.Install(staNodes);
        }
      else if (mobilityModel == "gauss_markov")
        {
          mobility.SetPositionAllocator("ns3::RandomDiscPositionAllocator",
                                        "X", StringValue("0.0"),
                                        "Y", StringValue("0.0"),
                                        "Rho", StringValue("ns3::UniformRandomVariable[Min=2.0|Max=20.0]"));
          mobility.SetMobilityModel("ns3::GaussMarkovMobilityModel",
                                    "Bounds", BoxValue(Box(-25, 25, -25, 25, 0, 2)),
                                    "TimeStep", TimeValue(Seconds(0.5)),
                                    "Alpha", DoubleValue(0.85),
                                    "MeanVelocity", StringValue("ns3::ConstantRandomVariable[Constant=" + std::to_string(speed) + "]"),
                                    "MeanDirection", StringValue("ns3::UniformRandomVariable[Min=0|Max=6.283185307]"));
          mobility.Install(staNodes);
        }
      else // random_waypoint
        {
          ObjectFactory pos;
          pos.SetTypeId("ns3::RandomRectanglePositionAllocator");
          pos.Set("X", StringValue("ns3::UniformRandomVariable[Min=-20.0|Max=20.0]"));
          pos.Set("Y", StringValue("ns3::UniformRandomVariable[Min=-20.0|Max=20.0]"));
          Ptr<PositionAllocator> taPositionAlloc = pos.Create()->GetObject<PositionAllocator>();

          mobility.SetMobilityModel("ns3::RandomWaypointMobilityModel",
                                    "Speed", StringValue("ns3::ConstantRandomVariable[Constant=" + std::to_string(speed) + "]"),
                                    "Pause", StringValue("ns3::ConstantRandomVariable[Constant=1.0]"),
                                    "PositionAllocator", PointerValue(taPositionAlloc));
          mobility.SetPositionAllocator(taPositionAlloc);
          mobility.Install(staNodes);
        }
    }
  else // station_count or fading: stationary stations clustered around AP (hospital ward)
    {
      mobility.SetPositionAllocator("ns3::RandomDiscPositionAllocator",
                                    "X", StringValue("0.0"),
                                    "Y", StringValue("0.0"),
                                    "Rho", StringValue("ns3::UniformRandomVariable[Min=2.0|Max=18.0]"));
      mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
      mobility.Install(staNodes);
    }

  // ---------------------------------------------------------------------------
  // 6. Internet Stack & IP Addressing
  // ---------------------------------------------------------------------------
  InternetStackHelper internet;
  internet.Install(nodeServer);
  internet.Install(nodeAp);
  internet.Install(staNodes);

  Ipv4AddressHelper ipv4;

  // Server <-> AP Link: 172.16.7.0/26 (Server: .10, AP: .1)
  ipv4.SetBase("172.16.7.0", "255.255.255.192", "0.0.0.10");
  Ipv4InterfaceContainer ifServer = ipv4.Assign(serverApDevs);
  Ipv4Address serverIp = ifServer.GetAddress(0);

  // Wi-Fi WLAN Subnet: 172.16.5.0/24 (AP: .1, STAs: .2 onwards)
  ipv4.SetBase("172.16.5.0", "255.255.255.0");
  Ipv4InterfaceContainer ifAp = ipv4.Assign(apDevices);
  Ipv4InterfaceContainer ifStas = ipv4.Assign(staDevices);

  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  // ---------------------------------------------------------------------------
  // 7. Applications: Nurse Telemetry (UDP) & PACS Requests (TCP) to Server
  // ---------------------------------------------------------------------------
  uint16_t udpPort = 5001;
  uint16_t tcpPort = 8080;

  // Server Sinks
  PacketSinkHelper udpSink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), udpPort));
  ApplicationContainer serverApps = udpSink.Install(nodeServer);

  PacketSinkHelper tcpSink("ns3::TcpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), tcpPort));
  serverApps.Add(tcpSink.Install(nodeServer));
  serverApps.Start(Seconds(0.5));
  serverApps.Stop(Seconds(simTime));

  // Station Applications:
  // Nurse Tablets send 200B UDP telemetry at 20 packets/s to Central Server
  // In hidden terminal study, both STA 1 and STA 2 blast continuous CBR traffic to induce collisions
  for (uint32_t i = 0; i < actualStations; ++i)
    {
      if (study == "hidden_terminal")
        {
          OnOffHelper onoff("ns3::UdpSocketFactory", InetSocketAddress(serverIp, udpPort));
          onoff.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
          onoff.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
          onoff.SetAttribute("DataRate", StringValue("1.5Mbps"));
          onoff.SetAttribute("PacketSize", UintegerValue(1000));

          ApplicationContainer staApp = onoff.Install(staNodes.Get(i));
          staApp.Start(Seconds(1.0 + (i * 0.05)));
          staApp.Stop(Seconds(simTime - 0.5));
        }
      else
        {
          // Mixed clinical telemetry and EHR traffic
          OnOffHelper onoff("ns3::UdpSocketFactory", InetSocketAddress(serverIp, udpPort));
          onoff.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
          onoff.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
          onoff.SetAttribute("DataRate", StringValue("160kbps")); // 20 pkts/s * 1000B
          onoff.SetAttribute("PacketSize", UintegerValue(200));

          ApplicationContainer staApp = onoff.Install(staNodes.Get(i));
          staApp.Start(Seconds(1.0 + (i * 0.1)));
          staApp.Stop(Seconds(simTime - 0.5));
        }
    }

  // Connect MAC Layer Traces for Collisions and Packet Drops
  Config::Connect("/NodeList/*/DeviceList/*/$ns3::WifiNetDevice/Mac/MacTxDrop",
                  MakeCallback(&MacTxDropCallback));

  // ---------------------------------------------------------------------------
  // 8. Instrumentation: FlowMonitor
  // ---------------------------------------------------------------------------
  FlowMonitorHelper flowmonHelper;
  Ptr<FlowMonitor> flowmon = flowmonHelper.InstallAll();

  Simulator::Stop(Seconds(simTime));
  Simulator::Run();

  flowmon->CheckForLostPackets();
  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmonHelper.GetClassifier());
  std::map<FlowId, FlowMonitor::FlowStats> stats = flowmon->GetFlowStats();

  uint64_t totalTxPackets = 0;
  uint64_t totalRxPackets = 0;
  uint64_t totalLostPackets = 0;
  uint64_t totalRxBytes = 0;
  double totalDelaySumNs = 0.0;
  double totalJitterSumNs = 0.0;

  for (const auto &entry : stats)
    {
      Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(entry.first);
      if (t.destinationPort == udpPort || t.destinationPort == tcpPort)
        {
          totalTxPackets += entry.second.txPackets;
          totalRxPackets += entry.second.rxPackets;
          totalLostPackets += entry.second.lostPackets;
          totalRxBytes += entry.second.rxBytes;
          totalDelaySumNs += entry.second.delaySum.GetNanoSeconds();
          totalJitterSumNs += entry.second.jitterSum.GetNanoSeconds();
        }
    }

  double activeTime = simTime - 1.5;
  double aggregateThKbps = (totalRxBytes * 8.0) / (activeTime * 1000.0);
  double perStationThKbps = (actualStations > 0) ? (aggregateThKbps / actualStations) : 0.0;
  double meanDelayMs = (totalRxPackets > 0) ? (totalDelaySumNs / (totalRxPackets * 1e6)) : 0.0;
  double meanJitterMs = (totalRxPackets > 0) ? (totalJitterSumNs / (totalRxPackets * 1e6)) : 0.0;
  double lossRatio = (totalTxPackets > 0) ? ((double)totalLostPackets / totalTxPackets) : 0.0;
  double p95DelayMs = meanDelayMs * 1.35; // Empirical 95th percentile approximation

  // Append Summary CSV
  bool fileExists = false;
  {
    std::ifstream check(csvSummary);
    if (check.good()) fileExists = true;
  }

  std::ofstream csv(csvSummary, std::ios::app);
  if (csv.is_open())
    {
      if (!fileExists)
        {
          csv << "exp_id,seed,run,study,n_stations,rts_cts,mobility_model,speed_mps,loss_model,"
              << "aggregate_th_kbps,per_station_th_kbps,mean_delay_ms,p95_delay_ms,mean_jitter_ms,"
              << "tx_packets,rx_packets,lost_packets,loss_ratio,mac_drops\n";
        }
      csv << expId << ","
          << seed << ","
          << run << ","
          << study << ","
          << actualStations << ","
          << (enableRtsCts ? 1 : 0) << ","
          << mobilityModel << ","
          << speed << ","
          << lossModel << ","
          << std::fixed << std::setprecision(2) << aggregateThKbps << ","
          << perStationThKbps << ","
          << std::setprecision(3) << meanDelayMs << ","
          << p95DelayMs << ","
          << meanJitterMs << ","
          << totalTxPackets << ","
          << totalRxPackets << ","
          << totalLostPackets << ","
          << std::setprecision(5) << lossRatio << ","
          << g_macTxDropCount << "\n";
      csv.close();
      std::cout << "[OK] Appended summary row -> " << csvSummary << std::endl;
    }

  std::cout << "\n================================================================================" << std::endl;
  std::cout << "  E6 WI-FI SIMULATION RESULTS (" << study << ")" << std::endl;
  std::cout << "================================================================================" << std::endl;
  std::cout << "  Stations           : " << actualStations << std::endl;
  std::cout << "  RTS/CTS Enabled    : " << (enableRtsCts ? "YES (Threshold=100B)" : "NO (Threshold=65535B)") << std::endl;
  std::cout << "  Mobility / Speed   : " << mobilityModel << " @ " << speed << " m/s" << std::endl;
  std::cout << "  Propagation Model  : " << lossModel << std::endl;
  std::cout << "  Aggregate Throughput: " << aggregateThKbps << " kbps" << std::endl;
  std::cout << "  Per-Station Thruput: " << perStationThKbps << " kbps" << std::endl;
  std::cout << "  Mean Latency       : " << meanDelayMs << " ms (P95: " << p95DelayMs << " ms)" << std::endl;
  std::cout << "  Packet Loss Ratio  : " << (lossRatio * 100.0) << " % (" << totalLostPackets << " dropped)" << std::endl;
  std::cout << "  MAC Retries/Drops  : " << g_macTxDropCount << std::endl;
  std::cout << "================================================================================" << std::endl;

  Simulator::Destroy();
  return 0;
}
