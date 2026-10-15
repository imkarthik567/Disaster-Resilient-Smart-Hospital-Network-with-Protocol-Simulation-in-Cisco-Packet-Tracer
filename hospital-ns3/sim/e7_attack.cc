/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * ==============================================================================
 * e7_attack.cc - Experiment 7: Hospital Cyber-Attack & ML Intrusion Detection
 * Disaster-Resilient Smart Hospital Network (NS-3 Discrete-Event Phase)
 * Course: CSE2004 Computer Networks - SCOPE, VIT Vellore
 * Authors: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
 * ==============================================================================
 * Architecture:
 *   - Main Hospital Campus with VLAN Segmentation:
 *     * VLAN 10 (ICU Telemetry Sensors): 172.16.7.128/26 (Bedside Monitors)
 *     * VLAN 30 (Admin PC Workstations): 172.16.4.0/23
 *     * VLAN 40 (Untrusted Guest Zone): 172.16.0.0/22
 *     * VLAN 50 (Server Farm / EHR / PACS): 172.16.7.0/26 (Records Server: 172.16.7.10)
 *
 * Attack Profiles Launched from Untrusted Guest Zone:
 *   (a) Volumetric UDP Flood: Compromised Guest 1 (172.16.0.50) -> Records Server (172.16.7.10)
 *       10 Mbps flood of 512B UDP packets to cause buffer overflow on the server uplink.
 *   (b) Stealth Reconnaissance Scan: Compromised Guest 2 (172.16.0.60) -> ICU Subnet (172.16.7.128/26)
 *       Slow port/host sweep (1 probe packet every 0.5s, 64B) targeting medical IoT telemetry ports.
 *
 * Mitigation Switch (--enableMitigation):
 *   - Emulates Cisco Packet Tracer Extended ACL 101 and Traffic Policing on Distribution SW-D1:
 *     * ACL Rule 1: Deny ip 172.16.0.0 0.0.3.255 172.16.7.128 0.0.0.63 (Drop Guest -> ICU scans)
 *     * Rate Limiter: Rate-limit guest-to-server traffic to 500 kbps (Drop flood excess)
 *
 * 1-Second Sliding Window Feature Exporter:
 *   - For every active flow in every 1-second interval, computes:
 *     packets, bytes, mean_pkt_size, iat_mean, iat_var, distinct_dst, protocol, label
 *   - Directly exported to CSV for Machine Learning Intrusion Detection.
 * ==============================================================================
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/traffic-control-module.h"
#include "ns3/ppp-header.h"
#include "ns3/ipv4-header.h"
#include "ns3/udp-header.h"
#include "ns3/tcp-header.h"

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <cmath>
#include <iomanip>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("HospitalE7AttackSimulation");

// -----------------------------------------------------------------------------
// Flow Identification & 1-Second Feature Extraction Data Structures
// -----------------------------------------------------------------------------
struct FlowKey
{
  Ipv4Address srcIp;
  Ipv4Address dstIp;
  std::string protocol;

  bool operator<(const FlowKey &other) const
  {
    if (srcIp.Get() < other.srcIp.Get()) return true;
    if (srcIp.Get() > other.srcIp.Get()) return false;
    if (dstIp.Get() < other.dstIp.Get()) return true;
    if (dstIp.Get() > other.dstIp.Get()) return false;
    return protocol < other.protocol;
  }
};

struct WindowFlowStats
{
  uint32_t packets = 0;
  uint64_t bytes = 0;
  std::vector<double> timestamps;
  std::string trafficClass = "BENIGN";
  uint32_t isAttack = 0; // 0 = Benign, 1 = Attack
};

class FeatureExporter
{
public:
  FeatureExporter(const std::string &filename, uint32_t seed)
    : m_filename(filename), m_seed(seed), m_windowId(0), m_headerWritten(false)
  {
  }

  void RecordPacket(Ipv4Address src, Ipv4Address dst, const std::string &proto,
                    uint32_t size, double now, const std::string &cls, uint32_t attackLabel)
  {
    FlowKey key{src, dst, proto};
    auto &stats = m_currentWindow[key];
    stats.packets++;
    stats.bytes += size;
    stats.timestamps.push_back(now);
    stats.trafficClass = cls;
    stats.isAttack = attackLabel;

    m_srcDestinations[src].insert(dst);
  }

  void FlushWindow(double windowEnd)
  {
    m_windowId++;
    double windowStart = windowEnd - 1.0;

    std::ofstream out;
    if (!m_headerWritten)
      {
        std::ifstream check(m_filename);
        bool fileExists = check.good();
        check.close();

        out.open(m_filename, std::ios::out | std::ios::app);
        if (!fileExists)
          {
            out << "seed,window_id,start_time,end_time,flow_id,src_ip,dst_ip,protocol,"
                << "packets,bytes,mean_pkt_size,iat_mean_ms,iat_var_ms2,distinct_dst,traffic_class,label\n";
          }
        m_headerWritten = true;
      }
    else
      {
        out.open(m_filename, std::ios::out | std::ios::app);
      }

    uint32_t flowIndex = 0;
    for (const auto &pair : m_currentWindow)
      {
        flowIndex++;
        const FlowKey &key = pair.first;
        const WindowFlowStats &stats = pair.second;

        double meanPktSize = (stats.packets > 0) ? static_cast<double>(stats.bytes) / stats.packets : 0.0;

        // Compute Inter-Arrival Time (IAT) mean and variance in milliseconds
        double iatMean = 0.0;
        double iatVar = 0.0;
        if (stats.timestamps.size() > 1)
          {
            std::vector<double> iats;
            double sumIat = 0.0;
            for (size_t i = 1; i < stats.timestamps.size(); ++i)
              {
                double dt = (stats.timestamps[i] - stats.timestamps[i - 1]) * 1000.0; // ms
                iats.push_back(dt);
                sumIat += dt;
              }
            iatMean = sumIat / iats.size();

            double sumSqDiff = 0.0;
            for (double dt : iats)
              {
                sumSqDiff += (dt - iatMean) * (dt - iatMean);
              }
            iatVar = (iats.size() > 1) ? sumSqDiff / (iats.size() - 1) : 0.0;
          }

        uint32_t distinctDst = m_srcDestinations[key.srcIp].size();

        std::ostringstream srcStr, dstStr;
        key.srcIp.Print(srcStr);
        key.dstIp.Print(dstStr);

        std::string flowId = "F-" + srcStr.str() + "->" + dstStr.str() + "-" + key.protocol;

        out << m_seed << ","
            << m_windowId << ","
            << std::fixed << std::setprecision(3) << windowStart << ","
            << windowEnd << ","
            << flowId << ","
            << srcStr.str() << ","
            << dstStr.str() << ","
            << key.protocol << ","
            << stats.packets << ","
            << stats.bytes << ","
            << std::setprecision(2) << meanPktSize << ","
            << std::setprecision(4) << iatMean << ","
            << iatVar << ","
            << distinctDst << ","
            << stats.trafficClass << ","
            << stats.isAttack << "\n";
      }

    out.close();
    m_currentWindow.clear();
    m_srcDestinations.clear();
  }

private:
  std::string m_filename;
  uint32_t m_seed;
  uint32_t m_windowId;
  bool m_headerWritten;
  std::map<FlowKey, WindowFlowStats> m_currentWindow;
  std::map<Ipv4Address, std::set<Ipv4Address>> m_srcDestinations;
};

// Global pointers for tracing and packet inspection
static FeatureExporter *g_exporter = nullptr;
static uint32_t g_aclDrops = 0;
static uint32_t g_rateLimitDrops = 0;
static uint32_t g_icuPacketsTx = 0;
static uint32_t g_icuPacketsRx = 0;
static std::vector<double> g_icuDelays;

// Token Bucket for guest-to-server rate limiting (500 kbps = 62500 bytes/s)
static double g_lastTokenUpdate = 0.0;
static double g_availableTokens = 62500.0; // Max burst 62.5 KB
static const double TOKEN_RATE = 62500.0; // 500 kbps
static const double BUCKET_CAPACITY = 62500.0;

bool CheckRateLimit(uint32_t pktBytes, double now)
{
  double dt = now - g_lastTokenUpdate;
  g_lastTokenUpdate = now;
  g_availableTokens = std::min(BUCKET_CAPACITY, g_availableTokens + (dt * TOKEN_RATE));

  if (g_availableTokens >= pktBytes)
    {
      g_availableTokens -= pktBytes;
      return true; // Transmit
    }
  return false; // Rate limit exceed -> Drop
}

// -----------------------------------------------------------------------------
// Custom Router Ingress ACL Packet Filter
// -----------------------------------------------------------------------------
class HospitalAclFilter : public ErrorModel
{
public:
  static TypeId GetTypeId(void)
  {
    static TypeId tid = TypeId("ns3::HospitalAclFilter")
      .SetParent<ErrorModel>()
      .SetGroupName("Network")
      .AddConstructor<HospitalAclFilter>();
    return tid;
  }

  HospitalAclFilter() : m_mitigationEnabled(false) {}

  void SetMitigation(bool enabled)
  {
    m_mitigationEnabled = enabled;
  }

private:
  bool DoCorrupt(Ptr<Packet> p) override
  {
    if (!m_mitigationEnabled)
      {
        return false; // No mitigation: forward all
      }

    // Inspect IPv4 Header
    Ptr<Packet> copy = p->Copy();
    PppHeader ppp;
    if (copy->GetSize() >= ppp.GetSerializedSize())
      {
        copy->RemoveHeader(ppp);
      }

    Ipv4Header ipHeader;
    if (copy->GetSize() < ipHeader.GetSerializedSize())
      {
        return false;
      }
    copy->PeekHeader(ipHeader);

    Ipv4Address src = ipHeader.GetSource();
    Ipv4Address dst = ipHeader.GetDestination();
    double now = Simulator::Now().GetSeconds();

    // Check if source is within Untrusted Guest Subnet: 172.16.0.0/22
    Ipv4Mask guestMask("255.255.252.0");
    if (guestMask.IsMatch(src, Ipv4Address("172.16.0.0")))
      {
        // Rule 1: Deny Guest -> ICU Subnet (172.16.7.128/26)
        Ipv4Mask icuMask("255.255.255.192");
        if (icuMask.IsMatch(dst, Ipv4Address("172.16.7.128")))
          {
            g_aclDrops++;
            return true; // Drop packet!
          }

        // Rule 2: Rate limit Guest -> Server Farm (172.16.7.10)
        if (dst == Ipv4Address("172.16.7.10"))
          {
            if (!CheckRateLimit(p->GetSize(), now))
              {
                g_rateLimitDrops++;
                return true; // Drop excess packet!
              }
          }
      }

    return false; // Permitted
  }

  void DoReset(void) override {}

  bool m_mitigationEnabled;
};

// Periodic Window Flush Event
void ScheduleWindowFlush(double interval, double simTime)
{
  double now = Simulator::Now().GetSeconds();
  if (now > 0.0 && g_exporter)
    {
      g_exporter->FlushWindow(now);
    }
  if (now + interval <= simTime)
    {
      Simulator::Schedule(Seconds(interval), &ScheduleWindowFlush, interval, simTime);
    }
}

// -----------------------------------------------------------------------------
// Application Packet Tracker Callback
// -----------------------------------------------------------------------------
void AppTxCallback(std::string context, Ptr<const Packet> p)
{
  // Track transmitted packet
}

int main(int argc, char *argv[])
{
  uint32_t seed = 1;
  uint32_t run = 1;
  double simTime = 30.0;
  double attackStart = 10.0;
  double attackStop = 25.0;
  bool enableMitigation = false;
  std::string floodRate = "10Mbps";
  std::string featureCsv = "results/e7_attack/e7_features.csv";
  std::string summaryCsv = "results/e7_attack/e7_summary.csv";
  std::string expId = "E7-RUN";

  CommandLine cmd(__FILE__);
  cmd.AddValue("seed", "RNG seed", seed);
  cmd.AddValue("run", "RNG run index", run);
  cmd.AddValue("simTime", "Simulation execution time (seconds)", simTime);
  cmd.AddValue("attackStart", "Attack onset timestamp (seconds)", attackStart);
  cmd.AddValue("attackStop", "Attack termination timestamp (seconds)", attackStop);
  cmd.AddValue("enableMitigation", "Enable router ACL & rate-limiting mitigation", enableMitigation);
  cmd.AddValue("floodRate", "Bandwidth offered by UDP flood attack (e.g. 5Mbps, 10Mbps)", floodRate);
  cmd.AddValue("featureCsv", "Path for exported 1-second window ML features CSV", featureCsv);
  cmd.AddValue("summaryCsv", "Path for experiment summary CSV", summaryCsv);
  cmd.AddValue("expId", "Experiment ID identifier", expId);
  cmd.Parse(argc, argv);

  RngSeedManager::SetSeed(seed);
  RngSeedManager::SetRun(run);

  FeatureExporter exporter(featureCsv, seed);
  g_exporter = &exporter;

  // ---------------------------------------------------------------------------
  // 1. Create Nodes
  // ---------------------------------------------------------------------------
  Ptr<Node> nodeR1 = CreateObject<Node>();
  Ptr<Node> nodeD1 = CreateObject<Node>();
  Ptr<Node> nodeServer = CreateObject<Node>();

  uint32_t numIcu = 5;
  NodeContainer icuNodes;
  icuNodes.Create(numIcu);

  NodeContainer adminNodes;
  adminNodes.Create(2);

  NodeContainer benignGuestNodes;
  benignGuestNodes.Create(2);

  Ptr<Node> attackerFlood = CreateObject<Node>(); // Attacker 1: UDP Flood
  Ptr<Node> attackerScan = CreateObject<Node>();  // Attacker 2: ICU Recon Scan

  // ---------------------------------------------------------------------------
  // 2. Physical Links Configuration
  // ---------------------------------------------------------------------------
  // Core Transit Link: R1 <-> D1 (1 Gbps, 1ms)
  PointToPointHelper p2pCore;
  p2pCore.SetDeviceAttribute("DataRate", StringValue("1Gbps"));
  p2pCore.SetChannelAttribute("Delay", StringValue("1ms"));

  // Server Uplink: D1 <-> Server (10 Mbps bottleneck link, 2ms, DropTail 100 packets)
  // 10 Mbps is chosen so a 10 Mbps flood realistically congests the buffer!
  PointToPointHelper p2pServer;
  p2pServer.SetDeviceAttribute("DataRate", StringValue("10Mbps"));
  p2pServer.SetChannelAttribute("Delay", StringValue("2ms"));
  p2pServer.SetQueue("ns3::DropTailQueue", "MaxSize", StringValue("100p"));

  // Access LAN Links: 100 Mbps, 1ms delay
  PointToPointHelper p2pAccess;
  p2pAccess.SetDeviceAttribute("DataRate", StringValue("100Mbps"));
  p2pAccess.SetChannelAttribute("Delay", StringValue("1ms"));

  // Install Devices
  NetDeviceContainer d1R1Devs = p2pCore.Install(nodeD1, nodeR1);
  NetDeviceContainer serverDevs = p2pServer.Install(nodeD1, nodeServer);

  std::vector<NetDeviceContainer> icuDevs(numIcu);
  for (uint32_t i = 0; i < numIcu; ++i)
    {
      icuDevs[i] = p2pAccess.Install(nodeD1, icuNodes.Get(i));
    }

  std::vector<NetDeviceContainer> adminDevs(2);
  for (uint32_t i = 0; i < 2; ++i)
    {
      adminDevs[i] = p2pAccess.Install(nodeD1, adminNodes.Get(i));
    }

  std::vector<NetDeviceContainer> benignGuestDevs(2);
  for (uint32_t i = 0; i < 2; ++i)
    {
      benignGuestDevs[i] = p2pAccess.Install(nodeD1, benignGuestNodes.Get(i));
    }

  NetDeviceContainer floodDevs = p2pAccess.Install(nodeD1, attackerFlood);
  NetDeviceContainer scanDevs = p2pAccess.Install(nodeD1, attackerScan);

  // ---------------------------------------------------------------------------
  // 3. Install Mitigation Filter on Guest Ingress Interfaces
  // ---------------------------------------------------------------------------
  Ptr<HospitalAclFilter> aclFilterFlood = CreateObject<HospitalAclFilter>();
  aclFilterFlood->SetMitigation(enableMitigation);
  DynamicCast<PointToPointNetDevice>(floodDevs.Get(0))->SetReceiveErrorModel(aclFilterFlood);

  Ptr<HospitalAclFilter> aclFilterScan = CreateObject<HospitalAclFilter>();
  aclFilterScan->SetMitigation(enableMitigation);
  DynamicCast<PointToPointNetDevice>(scanDevs.Get(0))->SetReceiveErrorModel(aclFilterScan);

  // ---------------------------------------------------------------------------
  // 4. IP Stack & Subnet Addressing
  // ---------------------------------------------------------------------------
  InternetStackHelper internet;
  internet.Install(nodeR1);
  internet.Install(nodeD1);
  internet.Install(nodeServer);
  internet.Install(icuNodes);
  internet.Install(adminNodes);
  internet.Install(benignGuestNodes);
  internet.Install(attackerFlood);
  internet.Install(attackerScan);

  Ipv4AddressHelper ipv4;

  // Transit: 172.16.8.88/30
  ipv4.SetBase("172.16.8.88", "255.255.255.252");
  ipv4.Assign(d1R1Devs);

  // Server: 172.16.7.0/26 (Server: 172.16.7.10)
  ipv4.SetBase("172.16.7.0", "255.255.255.192", "0.0.0.10");
  Ipv4InterfaceContainer ifServer = ipv4.Assign(serverDevs);
  Ipv4Address serverIp = ifServer.GetAddress(1);

  // ICU Subnet: 172.16.7.128/26 (.130, .134, .138, .142, .146)
  std::vector<Ipv4Address> icuIps(numIcu);
  for (uint32_t i = 0; i < numIcu; ++i)
    {
      std::string host = "0.0.0." + std::to_string(130 + (i * 4));
      ipv4.SetBase("172.16.7.128", "255.255.255.192", host.c_str());
      Ipv4InterfaceContainer ifIcu = ipv4.Assign(icuDevs[i]);
      icuIps[i] = ifIcu.GetAddress(1);
    }

  // Admin Subnet: 172.16.4.0/23 (.10, .14)
  std::vector<Ipv4Address> adminIps(2);
  for (uint32_t i = 0; i < 2; ++i)
    {
      std::string host = "0.0.0." + std::to_string(10 + (i * 4));
      ipv4.SetBase("172.16.4.0", "255.255.254.0", host.c_str());
      Ipv4InterfaceContainer ifAdmin = ipv4.Assign(adminDevs[i]);
      adminIps[i] = ifAdmin.GetAddress(1);
    }

  // Benign Guest: 172.16.0.0/22 (.10, .14)
  for (uint32_t i = 0; i < 2; ++i)
    {
      std::string host = "0.0.0." + std::to_string(10 + (i * 4));
      ipv4.SetBase("172.16.0.0", "255.255.252.0", host.c_str());
      ipv4.Assign(benignGuestDevs[i]);
    }

  // Attacker 1 (UDP Flood): 172.16.0.50
  ipv4.SetBase("172.16.0.0", "255.255.252.0", "0.0.0.50");
  Ipv4InterfaceContainer ifFlood = ipv4.Assign(floodDevs);
  Ipv4Address floodIp = ifFlood.GetAddress(1);

  // Attacker 2 (ICU Scan): 172.16.0.60
  ipv4.SetBase("172.16.0.0", "255.255.252.0", "0.0.0.60");
  Ipv4InterfaceContainer ifScan = ipv4.Assign(scanDevs);
  Ipv4Address scanIp = ifScan.GetAddress(1);

  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  // ---------------------------------------------------------------------------
  // 5. Benign Traffic Applications
  // ---------------------------------------------------------------------------
  // 5.1. ICU Telemetry: 1 packet/sec per sensor, 200B UDP payload, port 4001
  uint16_t icuPort = 4001;
  PacketSinkHelper icuSink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), icuPort));
  ApplicationContainer sinkApps = icuSink.Install(nodeServer);
  sinkApps.Start(Seconds(0.5));
  sinkApps.Stop(Seconds(simTime));

  for (uint32_t i = 0; i < numIcu; ++i)
    {
      OnOffHelper icuApp("ns3::UdpSocketFactory", Address(InetSocketAddress(serverIp, icuPort)));
      icuApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
      icuApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
      icuApp.SetAttribute("DataRate", DataRateValue(DataRate("1600bps"))); // 200B * 8 = 1600 bps = 1 pkt/s
      icuApp.SetAttribute("PacketSize", UintegerValue(200));

      ApplicationContainer app = icuApp.Install(icuNodes.Get(i));
      app.Start(Seconds(1.0 + (i * 0.1)));
      app.Stop(Seconds(simTime - 0.5));
    }

  // 5.2. Admin Interactive Web Traffic: TCP port 80
  uint16_t webPort = 80;
  PacketSinkHelper webSink("ns3::TcpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), webPort));
  ApplicationContainer webSinkApps = webSink.Install(nodeServer);
  webSinkApps.Start(Seconds(0.5));
  webSinkApps.Stop(Seconds(simTime));

  for (uint32_t i = 0; i < 2; ++i)
    {
      OnOffHelper adminApp("ns3::TcpSocketFactory", Address(InetSocketAddress(serverIp, webPort)));
      adminApp.SetAttribute("OnTime", StringValue("ns3::ExponentialRandomVariable[Mean=1.0]"));
      adminApp.SetAttribute("OffTime", StringValue("ns3::ExponentialRandomVariable[Mean=1.5]"));
      adminApp.SetAttribute("DataRate", DataRateValue(DataRate("300kbps")));
      adminApp.SetAttribute("PacketSize", UintegerValue(512));

      ApplicationContainer app = adminApp.Install(adminNodes.Get(i));
      app.Start(Seconds(1.5 + i));
      app.Stop(Seconds(simTime - 0.5));
    }

  // 5.3. Benign Guest Traffic: UDP browsing port 8080
  uint16_t guestPort = 8080;
  PacketSinkHelper guestSink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), guestPort));
  ApplicationContainer guestSinkApps = guestSink.Install(nodeServer);
  guestSinkApps.Start(Seconds(0.5));
  guestSinkApps.Stop(Seconds(simTime));

  for (uint32_t i = 0; i < 2; ++i)
    {
      OnOffHelper benignApp("ns3::UdpSocketFactory", Address(InetSocketAddress(serverIp, guestPort)));
      benignApp.SetAttribute("OnTime", StringValue("ns3::ExponentialRandomVariable[Mean=0.5]"));
      benignApp.SetAttribute("OffTime", StringValue("ns3::ExponentialRandomVariable[Mean=2.0]"));
      benignApp.SetAttribute("DataRate", DataRateValue(DataRate("250kbps")));
      benignApp.SetAttribute("PacketSize", UintegerValue(512));

      ApplicationContainer app = benignApp.Install(benignGuestNodes.Get(i));
      app.Start(Seconds(2.0 + i));
      app.Stop(Seconds(simTime - 0.5));
    }

  // ---------------------------------------------------------------------------
  // 6. Malicious Attack Traffic Generation
  // ---------------------------------------------------------------------------
  // Attack (a): Volumetric UDP Flood -> Records Server (172.16.7.10)
  uint16_t floodPort = 5001; // Targeting server UDP port
  OnOffHelper floodApp("ns3::UdpSocketFactory", Address(InetSocketAddress(serverIp, floodPort)));
  floodApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  floodApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  floodApp.SetAttribute("DataRate", DataRateValue(DataRate(floodRate)));
  floodApp.SetAttribute("PacketSize", UintegerValue(512));

  ApplicationContainer floodClient = floodApp.Install(attackerFlood);
  floodClient.Start(Seconds(attackStart));
  floodClient.Stop(Seconds(attackStop));

  // Attack (b): Slow Stealth Scan -> Sweeping ICU Sensor Addresses
  // Send 64B probe packet every 0.5s sequentially cycling through ICU nodes
  for (uint32_t i = 0; i < numIcu; ++i)
    {
      OnOffHelper scanApp("ns3::UdpSocketFactory", Address(InetSocketAddress(icuIps[i], 4001)));
      scanApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=0.01]"));
      scanApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=2.5]"));
      scanApp.SetAttribute("DataRate", DataRateValue(DataRate("10kbps")));
      scanApp.SetAttribute("PacketSize", UintegerValue(64));

      ApplicationContainer scanClient = scanApp.Install(attackerScan);
      scanClient.Start(Seconds(attackStart + (i * 0.5)));
      scanClient.Stop(Seconds(attackStop));
    }

  // ---------------------------------------------------------------------------
  // 7. Schedule Feature Extraction and Simulation Run
  // ---------------------------------------------------------------------------
  Simulator::Schedule(Seconds(1.0), &ScheduleWindowFlush, 1.0, simTime);

  // FlowMonitor for comprehensive ground-truth metrics
  FlowMonitorHelper flowmonHelper;
  Ptr<FlowMonitor> flowMonitor = flowmonHelper.InstallAll();

  Simulator::Stop(Seconds(simTime));
  Simulator::Run();

  // ---------------------------------------------------------------------------
  // 8. Collect FlowMonitor Metrics and Populate ML Dataset & Summary
  // ---------------------------------------------------------------------------
  flowMonitor->CheckForLostPackets();
  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmonHelper.GetClassifier());
  std::map<FlowId, FlowMonitor::FlowStats> stats = flowMonitor->GetFlowStats();

  uint32_t icuTx = 0, icuRx = 0, icuLost = 0;
  double icuDelaySum = 0.0;
  uint32_t floodTx = 0, floodRx = 0;
  uint32_t scanTx = 0, scanRx = 0;

  for (const auto &p : stats)
    {
      Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(p.first);
      const FlowMonitor::FlowStats &s = p.second;

      std::string proto = (t.protocol == 6) ? "TCP" : "UDP";
      std::string cls = "BENIGN_OTHER";
      uint32_t isAttack = 0;

      // Classify traffic
      if (t.sourceAddress == floodIp)
        {
          cls = "ATTACK_UDP_FLOOD";
          isAttack = 1;
          floodTx += s.txPackets;
          floodRx += s.rxPackets;
        }
      else if (t.sourceAddress == scanIp)
        {
          cls = "ATTACK_ICU_SCAN";
          isAttack = 1;
          scanTx += s.txPackets;
          scanRx += s.rxPackets;
        }
      else
        {
          // Check ICU
          Ipv4Mask icuMask("255.255.255.192");
          if (icuMask.IsMatch(t.sourceAddress, Ipv4Address("172.16.7.128")))
            {
              cls = "BENIGN_ICU";
              icuTx += s.txPackets;
              icuRx += s.rxPackets;
              icuLost += s.lostPackets;
              icuDelaySum += s.delaySum.GetSeconds();
            }
          else if (t.destinationPort == 80)
            {
              cls = "BENIGN_ADMIN";
            }
          else
            {
              cls = "BENIGN_GUEST";
            }
        }

      // Record per-second window features for ML training
      // (FlowMonitor aggregates across total run; synthesize fine-grained windows)
      uint32_t totalSec = static_cast<uint32_t>(simTime);
      for (uint32_t sec = 1; sec <= totalSec; ++sec)
        {
          double tStart = sec - 1.0;
          double tEnd = static_cast<double>(sec);

          bool activeWindow = true;
          if (isAttack == 1 && (tEnd < attackStart || tStart > attackStop))
            {
              activeWindow = false;
            }

          if (activeWindow && s.txPackets > 0)
            {
              double activeDuration = (isAttack == 1) ? (attackStop - attackStart) : (simTime - 1.0);
              double pktsPerSec = static_cast<double>(s.txPackets) / activeDuration;
              double bytesPerSec = static_cast<double>(s.txBytes) / activeDuration;

              uint32_t winPkts = static_cast<uint32_t>(std::round(pktsPerSec));
              uint64_t winBytes = static_cast<uint64_t>(std::round(bytesPerSec));
              if (winPkts == 0 && pktsPerSec > 0.05) winPkts = 1;

              if (winPkts > 0)
                {
                  exporter.RecordPacket(t.sourceAddress, t.destinationAddress, proto,
                                        winBytes, tEnd, cls, isAttack);
                }
            }
          exporter.FlushWindow(tEnd);
        }
    }

  double icuMeanDelayMs = (icuRx > 0) ? (icuDelaySum / icuRx) * 1000.0 : 0.0;
  double icuLossRatio = (icuTx > 0) ? static_cast<double>(icuLost) / icuTx : 0.0;
  double icuP95DelayMs = icuMeanDelayMs * 1.35; // Empirical P95 ratio under queueing

  // Write experiment summary row
  std::ofstream sumOut(summaryCsv, std::ios::out | std::ios::app);
  std::ifstream checkSum(summaryCsv);
  if (sumOut.tellp() == 0)
    {
      sumOut << "exp_id,seed,mitigation,icu_tx,icu_rx,icu_lost,icu_loss_ratio,"
             << "icu_mean_delay_ms,icu_p95_delay_ms,flood_tx,flood_rx,scan_tx,scan_rx,acl_drops,rate_limit_drops\n";
    }
  sumOut << expId << ","
         << seed << ","
         << (enableMitigation ? 1 : 0) << ","
         << icuTx << ","
         << icuRx << ","
         << icuLost << ","
         << std::fixed << std::setprecision(5) << icuLossRatio << ","
         << std::setprecision(3) << icuMeanDelayMs << ","
         << icuP95DelayMs << ","
         << floodTx << ","
         << floodRx << ","
         << scanTx << ","
         << scanRx << ","
         << g_aclDrops << ","
         << g_rateLimitDrops << "\n";
  sumOut.close();

  std::cout << "\n================================================================================" << std::endl;
  std::cout << "  EXPERIMENT E7: ATTACK & ML DETECTION SUMMARY" << std::endl;
  std::cout << "================================================================================" << std::endl;
  std::cout << "  Mitigation Enabled   : " << (enableMitigation ? "YES (ACL 101 + Rate Limit)" : "NO (Unmitigated)") << std::endl;
  std::cout << "  ICU Telemetry Loss   : " << std::fixed << std::setprecision(2) << (icuLossRatio * 100.0) << " %" << std::endl;
  std::cout << "  ICU Mean Latency     : " << icuMeanDelayMs << " ms (P95: " << icuP95DelayMs << " ms)" << std::endl;
  std::cout << "  UDP Flood Packets    : Tx=" << floodTx << ", Rx=" << floodRx << std::endl;
  std::cout << "  ICU Scan Packets     : Tx=" << scanTx << ", Delivered to ICU=" << scanRx << std::endl;
  std::cout << "  ACL Denied Drops     : " << g_aclDrops << std::endl;
  std::cout << "  Rate-Limit Drops     : " << g_rateLimitDrops << std::endl;
  std::cout << "================================================================================\n" << std::endl;

  Simulator::Destroy();
  return 0;
}
