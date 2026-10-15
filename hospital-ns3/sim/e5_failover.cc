/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * ==============================================================================
 * e5_failover.cc - Experiment 5: WAN Link Failure, Dynamic Failover & Restoration
 * Disaster-Resilient Smart Hospital Network (NS-3 Discrete-Event Phase)
 * Course: CSE2004 Computer Networks - SCOPE, VIT Vellore
 * Authors: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
 * ==============================================================================
 * Topologies:
 *   - Main Hospital (Core R1) <--> Remote Clinic (Core R2)
 *   - Primary WAN: 2.0 Mbps, 10 ms delay, subnet 172.16.8.80/30 (Cost 1)
 *   - Backup WAN : 1.0 Mbps, 20 ms delay, subnet 172.16.8.84/30 (Cost 10)
 *
 * Routing Modes (--routing):
 *   1. "static"       : Pre-configured floating backup route with carrier-sense (< 5 ms)
 *   2. "ospf_tuned"   : Modelled OSPFv2 (3s Dead Interval + 5ms SPF + 1ms FIB = ~3.006s)
 *   3. "ospf_default" : Modelled OSPFv2 (40s Dead Interval + 5ms SPF + 1ms FIB = ~40.006s)
 *   4. "rip"          : RFC 2453 RIPv2 Distance-Vector with triggered updates
 *
 * Traffic:
 *   - Continuous ICU-to-Clinic UDP Probe: 10 pkts/s (100 ms interval), 200 bytes
 *   - Bulk DICOM Imaging TCP Flow: Clinic to Main Server (PACS Archive)
 *   - Clinical Background Telemetry & Voice
 * ==============================================================================
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/traffic-control-module.h"
#include "ns3/rip-helper.h"

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <iomanip>
#include <cmath>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("HospitalE5FailoverSimulation");

// =============================================================================
// Continuous ICU Probe Application (10 packets/s UDP with high-res timestamp)
// =============================================================================
class IcuProbeSender : public Application
{
public:
  IcuProbeSender() : m_socket(nullptr), m_running(false), m_seq(0), m_interval(MilliSeconds(100)), m_pktSize(200) {}
  ~IcuProbeSender() override { m_socket = nullptr; }

  void Setup(Address destAddr, uint16_t destPort, Time interval, uint32_t pktSize = 200)
  {
    m_destAddr = destAddr;
    m_destPort = destPort;
    m_interval = interval;
    m_pktSize = pktSize;
  }

  uint32_t GetTotalSent() const { return m_seq; }

private:
  void StartApplication() override
  {
    m_running = true;
    m_socket = Socket::CreateSocket(GetNode(), UdpSocketFactory::GetTypeId());
    m_socket->Connect(InetSocketAddress(Ipv4Address::ConvertFrom(m_destAddr), m_destPort));
    m_sendEvent = Simulator::Schedule(Seconds(0.0), &IcuProbeSender::SendProbePacket, this);
  }

  void StopApplication() override
  {
    m_running = false;
    if (m_sendEvent.IsPending())
      {
        Simulator::Cancel(m_sendEvent);
      }
    if (m_socket)
      {
        m_socket->Close();
      }
  }

  void SendProbePacket()
  {
    if (!m_running) return;

    uint8_t buffer[512];
    double txTime = Simulator::Now().GetSeconds();
    std::memcpy(buffer, &m_seq, sizeof(m_seq));
    std::memcpy(buffer + sizeof(m_seq), &txTime, sizeof(txTime));

    Ptr<Packet> packet = Create<Packet>(buffer, m_pktSize);
    m_socket->Send(packet);
    m_seq++;

    m_sendEvent = Simulator::Schedule(m_interval, &IcuProbeSender::SendProbePacket, this);
  }

  Ptr<Socket> m_socket;
  Address m_destAddr;
  uint16_t m_destPort;
  bool m_running;
  uint32_t m_seq;
  Time m_interval;
  uint32_t m_pktSize;
  EventId m_sendEvent;
};

class IcuProbeReceiver : public Application
{
public:
  IcuProbeReceiver() : m_socket(nullptr), m_rxCount(0), m_expectedSeq(0),
                       m_firstLostSeq(0), m_lastLostSeq(0),
                       m_firstLostTime(-1.0), m_lastLostTime(-1.0),
                       m_lastRxTimeBeforeOutage(-1.0), m_firstRxTimeAfterRecovery(-1.0),
                       m_lostCount(0), m_inOutage(false) {}
  ~IcuProbeReceiver() override { m_socket = nullptr; }

  void Setup(uint16_t port)
  {
    m_port = port;
  }

  uint32_t GetRxCount() const { return m_rxCount; }
  uint32_t GetLostCount() const { return m_lostCount; }
  double GetFirstLostTime() const { return m_firstLostTime; }
  double GetLastLostTime() const { return m_lastLostTime; }
  double GetOutageDuration() const
  {
    if (m_lastRxTimeBeforeOutage > 0.0 && m_firstRxTimeAfterRecovery > m_lastRxTimeBeforeOutage)
      {
        return m_firstRxTimeAfterRecovery - m_lastRxTimeBeforeOutage;
      }
    if (m_firstLostTime > 0.0 && m_lastLostTime >= m_firstLostTime)
      {
        return (m_lastLostTime - m_firstLostTime) + 0.1;
      }
    return 0.0;
  }

private:
  void StartApplication() override
  {
    m_socket = Socket::CreateSocket(GetNode(), UdpSocketFactory::GetTypeId());
    InetSocketAddress local = InetSocketAddress(Ipv4Address::GetAny(), m_port);
    m_socket->Bind(local);
    m_socket->SetRecvCallback(MakeCallback(&IcuProbeReceiver::HandleRead, this));
  }

  void StopApplication() override
  {
    if (m_socket)
      {
        m_socket->Close();
      }
  }

  void HandleRead(Ptr<Socket> socket)
  {
    Ptr<Packet> packet;
    Address from;
    while ((packet = socket->RecvFrom(from)))
      {
        double rxTime = Simulator::Now().GetSeconds();
        uint8_t buffer[512];
        packet->CopyData(buffer, std::min((uint32_t)sizeof(buffer), packet->GetSize()));

        uint32_t seq;
        double txTime;
        std::memcpy(&seq, buffer, sizeof(seq));
        std::memcpy(&txTime, buffer + sizeof(seq), sizeof(txTime));

        m_rxCount++;

        // Detect Sequence Gap (Loss / Outage)
        if (seq > m_expectedSeq)
          {
            uint32_t gap = seq - m_expectedSeq;
            m_lostCount += gap;

            if (!m_inOutage)
              {
                m_inOutage = true;
                m_firstLostSeq = m_expectedSeq;
                // Estimated time for first lost packet:
                m_firstLostTime = txTime - (gap * 0.1);
                m_lastRxTimeBeforeOutage = (m_rxTimestamps.empty()) ? (m_firstLostTime - 0.1) : m_rxTimestamps.back();
              }
            m_lastLostSeq = seq - 1;
            m_lastLostTime = txTime - 0.1;
            m_firstRxTimeAfterRecovery = rxTime;
          }
        else if (m_inOutage && seq == m_expectedSeq)
          {
            m_inOutage = false;
            m_firstRxTimeAfterRecovery = rxTime;
          }

        m_rxTimestamps.push_back(rxTime);
        m_expectedSeq = seq + 1;
      }
  }

  uint16_t m_port;
  Ptr<Socket> m_socket;
  uint32_t m_rxCount;
  uint32_t m_expectedSeq;
  uint32_t m_firstLostSeq;
  uint32_t m_lastLostSeq;
  double m_firstLostTime;
  double m_lastLostTime;
  double m_lastRxTimeBeforeOutage;
  double m_firstRxTimeAfterRecovery;
  uint32_t m_lostCount;
  bool m_inOutage;
  std::vector<double> m_rxTimestamps;
};

// =============================================================================
// Periodic Throughput Time Series Sampler
// =============================================================================
struct TimeSeriesRecord
{
  double timeSec;
  double primaryRxKbps;
  double backupRxKbps;
  double icuProbeKbps;
  double imagingTcpKbps;
};

static std::vector<TimeSeriesRecord> g_timeSeries;
static uint64_t g_lastPrimaryBytes = 0;
static uint64_t g_lastBackupBytes = 0;
static uint64_t g_lastIcuProbeBytes = 0;
static uint64_t g_lastImagingTcpBytes = 0;

static Ptr<PacketSink> g_sinkPrimaryWan;
static Ptr<PacketSink> g_sinkBackupWan;
static Ptr<PacketSink> g_sinkImagingTcp;
static Ptr<IcuProbeReceiver> g_icuProbeApp;

void SampleThroughput(double intervalSec)
{
  double now = Simulator::Now().GetSeconds();

  uint64_t curPrimary = (g_sinkPrimaryWan) ? g_sinkPrimaryWan->GetTotalRx() : 0;
  uint64_t curBackup = (g_sinkBackupWan) ? g_sinkBackupWan->GetTotalRx() : 0;
  uint64_t curImaging = (g_sinkImagingTcp) ? g_sinkImagingTcp->GetTotalRx() : 0;
  uint64_t curIcuPkts = (g_icuProbeApp) ? g_icuProbeApp->GetRxCount() : 0;
  uint64_t curIcuBytes = curIcuPkts * 200;

  double primaryKbps = ((curPrimary - g_lastPrimaryBytes) * 8.0) / (intervalSec * 1000.0);
  double backupKbps = ((curBackup - g_lastBackupBytes) * 8.0) / (intervalSec * 1000.0);
  double imagingKbps = ((curImaging - g_lastImagingTcpBytes) * 8.0) / (intervalSec * 1000.0);
  double icuKbps = ((curIcuBytes - g_lastIcuProbeBytes) * 8.0) / (intervalSec * 1000.0);

  g_lastPrimaryBytes = curPrimary;
  g_lastBackupBytes = curBackup;
  g_lastImagingTcpBytes = curImaging;
  g_lastIcuProbeBytes = curIcuBytes;

  g_timeSeries.push_back({now, primaryKbps, backupKbps, icuKbps, imagingKbps});

  Simulator::Schedule(Seconds(intervalSec), &SampleThroughput, intervalSec);
}

// =============================================================================
// Link Failure & Restoration Event Callbacks
// =============================================================================
void TriggerOspfRecompute(const std::string &phase)
{
  std::cout << "[" << std::fixed << std::setprecision(3) << Simulator::Now().GetSeconds()
            << "s] [OSPF-MODEL] " << phase << ": SPF (Dijkstra) calculation completed. FIB updated." << std::endl;
  Ipv4GlobalRoutingHelper::RecomputeRoutingTables();
}

void SchedulePrimaryFailure(Ptr<Node> r1, Ptr<Node> r2, uint32_t r1Iface, uint32_t r2Iface,
                            const std::string &routingMode, double deadInterval,
                            double spfDelay, double fibDelay)
{
  std::cout << "\n================================================================================" << std::endl;
  std::cout << "[" << std::fixed << std::setprecision(3) << Simulator::Now().GetSeconds()
            << "s] [DISASTER EVENT] Primary WAN R1-R2 Fiber Cut Injected!" << std::endl;
  std::cout << "================================================================================" << std::endl;

  // Bring physical/IPv4 interface down
  r1->GetObject<Ipv4>()->SetDown(r1Iface);
  r2->GetObject<Ipv4>()->SetDown(r2Iface);

  if (routingMode == "ospf_tuned" || routingMode == "ospf_default" || routingMode == "global")
    {
      double totalDetection = deadInterval + spfDelay + fibDelay;
      std::cout << "[" << Simulator::Now().GetSeconds()
                << "s] [OSPF-MODEL] Dead timer armed (" << deadInterval << "s). Outage will span: "
                << totalDetection << "s (Dead=" << deadInterval << "s + SPF=" << spfDelay * 1000 << "ms + FIB=" << fibDelay * 1000 << "ms)" << std::endl;
      Simulator::Schedule(Seconds(totalDetection), &TriggerOspfRecompute, "Dead-Interval Expired");
    }
  else if (routingMode == "static")
    {
      std::cout << "[" << Simulator::Now().GetSeconds()
                << "s] [STATIC-ROUTING] Hardware Carrier-Sense link-down detected (<5ms). Floating backup route engaged." << std::endl;
    }
  else if (routingMode == "rip")
    {
      std::cout << "[" << Simulator::Now().GetSeconds()
                << "s] [RIPv2] Interface down signaled. Triggered update scheduled across backup link." << std::endl;
    }
}

void SchedulePrimaryRestoration(Ptr<Node> r1, Ptr<Node> r2, uint32_t r1Iface, uint32_t r2Iface,
                                const std::string &routingMode, double helloInterval,
                                double spfDelay, double fibDelay)
{
  std::cout << "\n================================================================================" << std::endl;
  std::cout << "[" << std::fixed << std::setprecision(3) << Simulator::Now().GetSeconds()
            << "s] [RESTORATION EVENT] Primary WAN Fiber Repaired. Interface Coming UP!" << std::endl;
  std::cout << "================================================================================" << std::endl;

  r1->GetObject<Ipv4>()->SetUp(r1Iface);
  r2->GetObject<Ipv4>()->SetUp(r2Iface);

  if (routingMode == "ospf_tuned" || routingMode == "ospf_default" || routingMode == "global")
    {
      double restorationDelay = helloInterval + spfDelay + fibDelay;
      std::cout << "[" << Simulator::Now().GetSeconds()
                << "s] [OSPF-MODEL] Hello adjacency armed (" << helloInterval << "s). Restoration convergence scheduled." << std::endl;
      Simulator::Schedule(Seconds(restorationDelay), &TriggerOspfRecompute, "Adjacency Re-established");
    }
  else if (routingMode == "static")
    {
      std::cout << "[" << Simulator::Now().GetSeconds()
                << "s] [STATIC-ROUTING] Primary interface restored. Primary metric 1 re-preferred." << std::endl;
    }
  else if (routingMode == "rip")
    {
      std::cout << "[" << Simulator::Now().GetSeconds()
                << "s] [RIPv2] Primary interface up. Periodic update will restore primary path metric." << std::endl;
    }
}

// =============================================================================
// MAIN SIMULATION ENTRY POINT
// =============================================================================
int main(int argc, char *argv[])
{
  uint32_t seed = 1;
  uint32_t run = 1;
  double simTime = 60.0;
  double failAt = 15.0;
  double restoreAt = 45.0;
  std::string routingMode = "ospf_tuned"; // static, ospf_tuned, ospf_default, rip
  double deadInterval = 3.0;              // 3.0s (tuned) or 40.0s (default Cisco)
  double helloInterval = 1.0;             // 1.0s (tuned) or 10.0s (default Cisco)
  double spfDelay = 0.005;                // 5 ms Dijkstra computation
  double fibDelay = 0.001;                // 1 ms FIB installation
  std::string csvSummary = "results/e5_failover/e5_summary.csv";
  std::string timeseriesTrace = "results/e5_failover/traces/timeseries.csv";
  std::string expId = "E5-RUN";

  CommandLine cmd(__FILE__);
  cmd.AddValue("seed", "RNG seed", seed);
  cmd.AddValue("run", "RNG run index", run);
  cmd.AddValue("simTime", "Simulation execution duration in seconds", simTime);
  cmd.AddValue("failAt", "Timestamp for Primary WAN link failure (seconds)", failAt);
  cmd.AddValue("restoreAt", "Timestamp for Primary WAN link restoration (seconds, 0 to disable)", restoreAt);
  cmd.AddValue("routing", "Routing mode: static, ospf_tuned, ospf_default, rip", routingMode);
  cmd.AddValue("deadInterval", "OSPF Dead Interval failure detection delay in seconds", deadInterval);
  cmd.AddValue("helloInterval", "OSPF Hello Interval adjacency timer in seconds", helloInterval);
  cmd.AddValue("spfDelay", "Dijkstra SPF calculation delay in seconds", spfDelay);
  cmd.AddValue("fibDelay", "FIB hardware route installation delay in seconds", fibDelay);
  cmd.AddValue("csvSummary", "Output summary CSV path", csvSummary);
  cmd.AddValue("timeseriesTrace", "Output throughput timeseries CSV path", timeseriesTrace);
  cmd.AddValue("expId", "Experiment ID identifier", expId);
  cmd.Parse(argc, argv);

  // Auto-tune OSPF parameters based on mode selection if defaults are used
  if (routingMode == "ospf_default")
    {
      if (deadInterval == 3.0) deadInterval = 40.0;
      if (helloInterval == 1.0) helloInterval = 10.0;
    }

  RngSeedManager::SetSeed(seed);
  RngSeedManager::SetRun(run);

  // Theoretical Outage Calculation
  double theoreticalOutage = 0.0;
  if (routingMode == "static")
    {
      theoreticalOutage = 0.002; // ~2ms carrier sense
    }
  else if (routingMode == "ospf_tuned" || routingMode == "ospf_default")
    {
      theoreticalOutage = deadInterval + spfDelay + fibDelay;
    }
  else if (routingMode == "rip")
    {
      theoreticalOutage = 1.0 + 0.010; // MinTriggeredCooldown (1s) + propagation
    }

  std::cout << "================================================================================" << std::endl;
  std::cout << "  EXPERIMENT E5: HOSPITAL WAN FAILOVER, DYNAMIC RECONVERGENCE & RESTORATION" << std::endl;
  std::cout << "================================================================================" << std::endl;
  std::cout << "  Routing Mode       : " << routingMode << std::endl;
  std::cout << "  Failure Timestamp  : " << failAt << " s" << std::endl;
  std::cout << "  Restore Timestamp  : " << restoreAt << " s" << std::endl;
  std::cout << "  OSPF Dead Timer    : " << deadInterval << " s" << std::endl;
  std::cout << "  OSPF Hello Timer   : " << helloInterval << " s" << std::endl;
  std::cout << "  Theoretical Outage : " << theoreticalOutage << " s" << std::endl;
  std::cout << "================================================================================" << std::endl;

  // ---------------------------------------------------------------------------
  // 1. Topology Creation
  // ---------------------------------------------------------------------------
  // Core Routers: R1 (Main Hospital), R2 (Remote Clinic)
  Ptr<Node> nodeR1 = CreateObject<Node>();
  Ptr<Node> nodeR2 = CreateObject<Node>();

  // Distribution Switches
  Ptr<Node> nodeD1 = CreateObject<Node>(); // Main Site Distribution
  Ptr<Node> nodeD3 = CreateObject<Node>(); // Clinic Site Distribution

  // Main Hospital Endpoints
  Ptr<Node> nodeIcu = CreateObject<Node>();       // ICU Bedside Monitor (172.16.7.130)
  Ptr<Node> nodeServer = CreateObject<Node>();    // Central PACS Server (172.16.7.10)

  // Remote Clinic Endpoints
  Ptr<Node> nodeClinicServer = CreateObject<Node>();  // Clinic Records Server (172.16.8.35)
  Ptr<Node> nodeClinicImaging = CreateObject<Node>(); // Clinic X-Ray / PACS Station (172.16.8.45)

  NodeContainer allNodes = NodeContainer(nodeR1, nodeR2, nodeIcu, nodeServer, nodeClinicServer, nodeClinicImaging);

  // ---------------------------------------------------------------------------
  // 2. Point-to-Point Links Setup
  // ---------------------------------------------------------------------------
  PointToPointHelper p2pPrimary;
  p2pPrimary.SetDeviceAttribute("DataRate", StringValue("2Mbps"));
  p2pPrimary.SetChannelAttribute("Delay", StringValue("10ms"));

  PointToPointHelper p2pBackup;
  p2pBackup.SetDeviceAttribute("DataRate", StringValue("1Mbps"));
  p2pBackup.SetChannelAttribute("Delay", StringValue("20ms"));

  PointToPointHelper p2pLan;
  p2pLan.SetDeviceAttribute("DataRate", StringValue("100Mbps"));
  p2pLan.SetChannelAttribute("Delay", StringValue("1ms"));

  // WAN Interfaces
  NetDeviceContainer devsPrimaryWan = p2pPrimary.Install(nodeR1, nodeR2);
  NetDeviceContainer devsBackupWan  = p2pBackup.Install(nodeR1, nodeR2);

  // Campus Access LAN Interfaces
  NetDeviceContainer devsR1Icu    = p2pLan.Install(nodeIcu, nodeR1);
  NetDeviceContainer devsR1Server = p2pLan.Install(nodeServer, nodeR1);

  NetDeviceContainer devsR2ClinicServer  = p2pLan.Install(nodeClinicServer, nodeR2);
  NetDeviceContainer devsR2ClinicImaging = p2pLan.Install(nodeClinicImaging, nodeR2);

  // ---------------------------------------------------------------------------
  // 3. Routing Stack Installation
  // ---------------------------------------------------------------------------
  InternetStackHelper internet;
  Ipv4StaticRoutingHelper staticHelper;
  RipHelper ripHelper;

  if (routingMode == "rip")
    {
      Ipv4ListRoutingHelper list;
      list.Add(ripHelper, 10);
      internet.SetRoutingHelper(list);
      internet.Install(allNodes);
    }
  else if (routingMode == "static")
    {
      Ipv4ListRoutingHelper list;
      list.Add(staticHelper, 10);
      internet.SetRoutingHelper(list);
      internet.Install(allNodes);
    }
  else // ospf_tuned, ospf_default, global
    {
      Ipv4GlobalRoutingHelper globalHelper;
      internet.Install(allNodes);
    }

  // ---------------------------------------------------------------------------
  // 4. IP Addressing (Strictly conforming to Hospital VLSM Plan)
  // ---------------------------------------------------------------------------
  Ipv4AddressHelper ipv4;

  // Primary WAN: 172.16.8.80/30 (R1: .81, R2: .82)
  ipv4.SetBase("172.16.8.80", "255.255.255.252");
  Ipv4InterfaceContainer ifPrimaryWan = ipv4.Assign(devsPrimaryWan);

  // Backup WAN: 172.16.8.84/30 (R1: .85, R2: .86)
  ipv4.SetBase("172.16.8.84", "255.255.255.252");
  Ipv4InterfaceContainer ifBackupWan = ipv4.Assign(devsBackupWan);

  // Main ICU Subnet: 172.16.7.128/26 (Host: .130, R1: .129)
  ipv4.SetBase("172.16.7.128", "255.255.255.192", "0.0.0.1");
  Ipv4InterfaceContainer ifR1Icu = ipv4.Assign(devsR1Icu);
  Ipv4Address icuIp = ifR1Icu.GetAddress(0);

  // Main Server Subnet: 172.16.7.0/26 (Host: .10, R1: .1)
  ipv4.SetBase("172.16.7.0", "255.255.255.192", "0.0.0.1");
  Ipv4InterfaceContainer ifR1Server = ipv4.Assign(devsR1Server);
  Ipv4Address serverIp = ifR1Server.GetAddress(0);

  // Clinic Records Server: 172.16.8.32/27 (Host: .35, R2: .33)
  ipv4.SetBase("172.16.8.32", "255.255.255.224", "0.0.0.1");
  Ipv4InterfaceContainer ifR2ClinicServer = ipv4.Assign(devsR2ClinicServer);
  Ipv4Address clinicServerIp = ifR2ClinicServer.GetAddress(0);

  // Clinic Imaging Station: 172.16.8.0/27 (Host: .10, R2: .1)
  ipv4.SetBase("172.16.8.0", "255.255.255.224", "0.0.0.1");
  Ipv4InterfaceContainer ifR2ClinicImaging = ipv4.Assign(devsR2ClinicImaging);
  Ipv4Address clinicImagingIp = ifR2ClinicImaging.GetAddress(0);

  uint32_t r1PrimaryIface = ifPrimaryWan.Get(0).second;
  uint32_t r2PrimaryIface = ifPrimaryWan.Get(1).second;
  uint32_t r1BackupIface  = ifBackupWan.Get(0).second;
  uint32_t r2BackupIface  = ifBackupWan.Get(1).second;

  // Configure Routing Metrics / Paths
  if (routingMode == "static")
    {
      // R1 Static Routes to Clinic Subnets:
      Ptr<Ipv4StaticRouting> staticR1 = staticHelper.GetStaticRouting(nodeR1->GetObject<Ipv4>());
      staticR1->AddNetworkRouteTo(Ipv4Address("172.16.8.32"), Ipv4Mask("255.255.255.224"),
                                  ifPrimaryWan.GetAddress(1), r1PrimaryIface, 1);
      staticR1->AddNetworkRouteTo(Ipv4Address("172.16.8.32"), Ipv4Mask("255.255.255.224"),
                                  ifBackupWan.GetAddress(1), r1BackupIface, 10);
      staticR1->AddNetworkRouteTo(Ipv4Address("172.16.8.0"), Ipv4Mask("255.255.255.224"),
                                  ifPrimaryWan.GetAddress(1), r1PrimaryIface, 1);
      staticR1->AddNetworkRouteTo(Ipv4Address("172.16.8.0"), Ipv4Mask("255.255.255.224"),
                                  ifBackupWan.GetAddress(1), r1BackupIface, 10);

      // R2 Static Routes to Main Hospital Subnets:
      Ptr<Ipv4StaticRouting> staticR2 = staticHelper.GetStaticRouting(nodeR2->GetObject<Ipv4>());
      staticR2->AddNetworkRouteTo(Ipv4Address("172.16.7.128"), Ipv4Mask("255.255.255.192"),
                                  ifPrimaryWan.GetAddress(0), r2PrimaryIface, 1);
      staticR2->AddNetworkRouteTo(Ipv4Address("172.16.7.128"), Ipv4Mask("255.255.255.192"),
                                  ifBackupWan.GetAddress(0), r2BackupIface, 10);
      staticR2->AddNetworkRouteTo(Ipv4Address("172.16.7.0"), Ipv4Mask("255.255.255.192"),
                                  ifPrimaryWan.GetAddress(0), r2PrimaryIface, 1);
      staticR2->AddNetworkRouteTo(Ipv4Address("172.16.7.0"), Ipv4Mask("255.255.255.192"),
                                  ifBackupWan.GetAddress(0), r2BackupIface, 10);

      // Default Routes on endpoints pointing to their connected router
      Ptr<Ipv4StaticRouting> staticIcu = staticHelper.GetStaticRouting(nodeIcu->GetObject<Ipv4>());
      staticIcu->SetDefaultRoute(ifR1Icu.GetAddress(1), ifR1Icu.Get(0).second);

      Ptr<Ipv4StaticRouting> staticServer = staticHelper.GetStaticRouting(nodeServer->GetObject<Ipv4>());
      staticServer->SetDefaultRoute(ifR1Server.GetAddress(1), ifR1Server.Get(0).second);

      Ptr<Ipv4StaticRouting> staticClinicServer = staticHelper.GetStaticRouting(nodeClinicServer->GetObject<Ipv4>());
      staticClinicServer->SetDefaultRoute(ifR2ClinicServer.GetAddress(1), ifR2ClinicServer.Get(0).second);

      Ptr<Ipv4StaticRouting> staticClinicImaging = staticHelper.GetStaticRouting(nodeClinicImaging->GetObject<Ipv4>());
      staticClinicImaging->SetDefaultRoute(ifR2ClinicImaging.GetAddress(1), ifR2ClinicImaging.Get(0).second);
    }
  else if (routingMode == "rip")
    {
      // Exclude LAN host-facing interfaces from RIP updates
      ripHelper.ExcludeInterface(nodeR1, ifR1Icu.Get(1).second);
      ripHelper.ExcludeInterface(nodeR1, ifR1Server.Get(1).second);
      ripHelper.ExcludeInterface(nodeR2, ifR2ClinicServer.Get(1).second);
      ripHelper.ExcludeInterface(nodeR2, ifR2ClinicImaging.Get(1).second);

      // Set Primary WAN Metric = 1, Backup WAN Metric = 2 (Higher cost)
      ripHelper.SetInterfaceMetric(nodeR1, r1PrimaryIface, 1);
      ripHelper.SetInterfaceMetric(nodeR2, r2PrimaryIface, 1);
      ripHelper.SetInterfaceMetric(nodeR1, r1BackupIface, 2);
      ripHelper.SetInterfaceMetric(nodeR2, r2BackupIface, 2);

      // Set default routes on hosts
      ripHelper.SetDefaultRouter(nodeIcu, ifR1Icu.GetAddress(1), ifR1Icu.Get(0).second);
      ripHelper.SetDefaultRouter(nodeServer, ifR1Server.GetAddress(1), ifR1Server.Get(0).second);
      ripHelper.SetDefaultRouter(nodeClinicServer, ifR2ClinicServer.GetAddress(1), ifR2ClinicServer.Get(0).second);
      ripHelper.SetDefaultRouter(nodeClinicImaging, ifR2ClinicImaging.GetAddress(1), ifR2ClinicImaging.Get(0).second);
    }
  else // ospf_tuned, ospf_default, global
    {
      // Set interface metrics: Primary WAN cost = 1, Backup WAN cost = 10
      nodeR1->GetObject<Ipv4>()->SetMetric(r1PrimaryIface, 1);
      nodeR2->GetObject<Ipv4>()->SetMetric(r2PrimaryIface, 1);
      nodeR1->GetObject<Ipv4>()->SetMetric(r1BackupIface, 10);
      nodeR2->GetObject<Ipv4>()->SetMetric(r2BackupIface, 10);

      Ipv4GlobalRoutingHelper::PopulateRoutingTables();
    }


  // ---------------------------------------------------------------------------
  // 5. Application Setup
  // ---------------------------------------------------------------------------
  uint16_t icuPort = 5001;
  uint16_t tcpImagingPort = 8080;

  // A. Continuous ICU-to-Clinic UDP Probe (10 pkts/s, 200B)
  Ptr<IcuProbeReceiver> probeReceiver = CreateObject<IcuProbeReceiver>();
  probeReceiver->Setup(icuPort);
  nodeClinicServer->AddApplication(probeReceiver);
  probeReceiver->SetStartTime(Seconds(0.5));
  probeReceiver->SetStopTime(Seconds(simTime));
  g_icuProbeApp = probeReceiver;

  Ptr<IcuProbeSender> probeSender = CreateObject<IcuProbeSender>();
  probeSender->Setup(clinicServerIp, icuPort, MilliSeconds(100), 200);
  nodeIcu->AddApplication(probeSender);
  probeSender->SetStartTime(Seconds(1.0));
  probeSender->SetStopTime(Seconds(simTime - 1.0));

  // B. Bulk DICOM PACS Imaging TCP Flow (Clinic -> Main Server)
  PacketSinkHelper tcpSink("ns3::TcpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), tcpImagingPort));
  ApplicationContainer sinkApps = tcpSink.Install(nodeServer);
  sinkApps.Start(Seconds(0.5));
  sinkApps.Stop(Seconds(simTime));
  g_sinkImagingTcp = DynamicCast<PacketSink>(sinkApps.Get(0));

  BulkSendHelper tcpSource("ns3::TcpSocketFactory", InetSocketAddress(serverIp, tcpImagingPort));
  tcpSource.SetAttribute("MaxBytes", UintegerValue(0)); // Continuous bulk transfer
  tcpSource.SetAttribute("SendSize", UintegerValue(1460));
  ApplicationContainer sourceApps = tcpSource.Install(nodeClinicImaging);
  sourceApps.Start(Seconds(2.0));
  sourceApps.Stop(Seconds(simTime - 1.0));

  // WAN Physical Link Throughput Sinks
  PacketSinkHelper wanSinkPrimary("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), 9991));
  PacketSinkHelper wanSinkBackup("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), 9992));

  // ---------------------------------------------------------------------------
  // 6. Schedule Failure & Restoration Events
  // ---------------------------------------------------------------------------
  Simulator::Schedule(Seconds(failAt), &SchedulePrimaryFailure,
                      nodeR1, nodeR2, r1PrimaryIface, r2PrimaryIface,
                      routingMode, deadInterval, spfDelay, fibDelay);

  if (restoreAt > failAt && restoreAt < simTime)
    {
      Simulator::Schedule(Seconds(restoreAt), &SchedulePrimaryRestoration,
                          nodeR1, nodeR2, r1PrimaryIface, r2PrimaryIface,
                          routingMode, helloInterval, spfDelay, fibDelay);
    }

  // Schedule Throughput Sampler every 250 ms
  Simulator::Schedule(Seconds(0.5), &SampleThroughput, 0.25);

  // ---------------------------------------------------------------------------
  // 7. Execute Simulation
  // ---------------------------------------------------------------------------
  Simulator::Stop(Seconds(simTime));
  Simulator::Run();

  // ---------------------------------------------------------------------------
  // 8. Metric Compilation & Trace Output
  // ---------------------------------------------------------------------------
  uint32_t totalSent = probeSender->GetTotalSent();
  uint32_t totalRx = probeReceiver->GetRxCount();
  uint32_t lostPkts = probeReceiver->GetLostCount();
  double measuredOutage = probeReceiver->GetOutageDuration();
  double firstLost = probeReceiver->GetFirstLostTime();
  double lastLost = probeReceiver->GetLastLostTime();

  // Calculate Throughput Before and After Failover from time series
  double primaryThBefore = 0.0;
  double backupThAfter = 0.0;
  double imagingThBefore = 0.0;
  double imagingThAfter = 0.0;
  uint32_t countBefore = 0;
  uint32_t countAfter = 0;

  for (const auto &rec : g_timeSeries)
    {
      if (rec.timeSec > 5.0 && rec.timeSec < failAt - 1.0)
        {
          primaryThBefore += rec.primaryRxKbps;
          imagingThBefore += rec.imagingTcpKbps;
          countBefore++;
        }
      else if (rec.timeSec > (failAt + measuredOutage + 2.0) &&
               (restoreAt <= 0 || rec.timeSec < restoreAt - 1.0))
        {
          backupThAfter += rec.backupRxKbps;
          imagingThAfter += rec.imagingTcpKbps;
          countAfter++;
        }
    }

  if (countBefore > 0)
    {
      primaryThBefore /= countBefore;
      imagingThBefore /= countBefore;
    }
  if (countAfter > 0)
    {
      backupThAfter /= countAfter;
      imagingThAfter /= countAfter;
    }

  // Write Time Series Trace File
  std::ofstream tsFile(timeseriesTrace);
  if (tsFile.is_open())
    {
      tsFile << "time_sec,primary_rx_kbps,backup_rx_kbps,icu_probe_kbps,imaging_tcp_kbps\n";
      for (const auto &rec : g_timeSeries)
        {
          tsFile << std::fixed << std::setprecision(3)
                 << rec.timeSec << ","
                 << rec.primaryRxKbps << ","
                 << rec.backupRxKbps << ","
                 << rec.icuProbeKbps << ","
                 << rec.imagingTcpKbps << "\n";
        }
      tsFile.close();
      std::cout << "[OK] Saved Timeseries Trace -> " << timeseriesTrace << std::endl;
    }

  // Write Summary CSV Row
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
          csv << "exp_id,seed,run,routing_mode,fail_at,restore_at,dead_interval,theoretical_outage,measured_outage,"
              << "first_lost_time,last_lost_time,lost_packets,total_probe_tx,total_probe_rx,"
              << "primary_th_before_kbps,backup_th_after_kbps,imaging_th_before_kbps,imaging_th_after_kbps\n";
        }
      csv << expId << ","
          << seed << ","
          << run << ","
          << routingMode << ","
          << failAt << ","
          << restoreAt << ","
          << deadInterval << ","
          << std::fixed << std::setprecision(4) << theoreticalOutage << ","
          << measuredOutage << ","
          << firstLost << ","
          << lastLost << ","
          << lostPkts << ","
          << totalSent << ","
          << totalRx << ","
          << std::setprecision(2) << primaryThBefore << ","
          << backupThAfter << ","
          << imagingThBefore << ","
          << imagingThAfter << "\n";
      csv.close();
      std::cout << "[OK] Summary row appended -> " << csvSummary << std::endl;
    }

  std::cout << "\n================================================================================" << std::endl;
  std::cout << "  E5 SIMULATION RESULTS SUMMARY" << std::endl;
  std::cout << "================================================================================" << std::endl;
  std::cout << "  Routing Protocol    : " << routingMode << std::endl;
  std::cout << "  Probe Packets TX/RX : " << totalSent << " / " << totalRx << " (" << lostPkts << " lost)" << std::endl;
  std::cout << "  First Loss Timestamp: " << firstLost << " s" << std::endl;
  std::cout << "  Last Loss Timestamp : " << lastLost << " s" << std::endl;
  std::cout << "  Theoretical Outage  : " << theoreticalOutage << " s" << std::endl;
  std::cout << "  Measured Outage     : " << measuredOutage << " s" << std::endl;
  std::cout << "  Imaging TCP Thruput : Before Failover = " << imagingThBefore << " kbps | On Backup = " << imagingThAfter << " kbps" << std::endl;
  std::cout << "================================================================================" << std::endl;

  Simulator::Destroy();
  return 0;
}
