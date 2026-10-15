/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * ==============================================================================
 * e2_queue.cc - Experiment 2: Active Queue Management & QoS Priority Queuing
 * Disaster-Resilient Smart Hospital Network (NS-3 Discrete-Event Phase)
 * Course: CSE2004 Computer Networks - SCOPE, VIT Vellore
 * Authors: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
 * ==============================================================================
 *
 * QUEUE DISC ARCHITECTURE & SELECTION JUSTIFICATION:
 * 1. DropTail (FifoQueueDisc):
 *    - Standard FIFO buffer (100 packets default).
 *    - Implemented using ns3::FifoQueueDisc.
 *    - Drops arriving packets indiscriminately once buffer fills (tail drops).
 *    - Serves as the unmanaged baseline.
 *
 * 2. RED (RedQueueDisc):
 *    - Random Early Detection active queue management (RFC 2309 / 7567).
 *    - Implemented using ns3::RedQueueDisc.
 *    - Threshold Mathematical Sizing:
 *      * Link Capacity C = 2.0 Mbps = 250,000 bytes/s
 *      * RTT = 2 * 10 ms = 20 ms = 0.020 s
 *      * BDP = C * RTT = 250,000 * 0.020 = 5,000 bytes = ~5 packets (at 1000B MTU)
 *      * MinTh = 10 packets (~2x BDP)
 *      * MaxTh = 30 packets (3x MinTh)
 *      * Queue MaxSize = 100 packets
 *      * Drop probability Pmax = 0.10, weight w_q = 0.002
 *    - Mitigates TCP synchronization by early packet marking/dropping.
 *
 * 3. Priority / Multi-Band Queue (PrioQueueDisc + HospitalDscpPacketFilter):
 *    - Implemented using ns3::PrioQueueDisc with 3 priority bands:
 *      * Band 0 (Highest):  DSCP EF (46) - Life-Critical ICU Telemetry & Voice
 *      * Band 1 (Medium):   DSCP AF31 (26) - Medical PACS Imaging
 *      * Band 2 (Lowest):   DSCP BE (0) - Guest Untrusted Cross-Traffic
 *    - Custom Ipv4PacketFilter (HospitalDscpPacketFilter) classifies packets
 *      strictly based on the IPv4 ToS / DSCP header field.
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
#include <algorithm>
#include <iomanip>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("HospitalE2QueueSimulation");

// -----------------------------------------------------------------------------
// Custom DSCP Packet Filter for NS-3 Traffic Control Layer
// -----------------------------------------------------------------------------
class HospitalDscpPacketFilter : public Ipv4PacketFilter
{
public:
  static TypeId GetTypeId(void)
  {
    static TypeId tid = TypeId("ns3::HospitalDscpPacketFilter")
      .SetParent<Ipv4PacketFilter>()
      .SetGroupName("TrafficControl")
      .AddConstructor<HospitalDscpPacketFilter>();
    return tid;
  }

  HospitalDscpPacketFilter() {}
  ~HospitalDscpPacketFilter() override {}

private:
  bool CheckProtocol(Ptr<QueueDiscItem> item) const override
  {
    Ptr<const Ipv4QueueDiscItem> ipv4Item = DynamicCast<const Ipv4QueueDiscItem>(item);
    return ipv4Item != nullptr;
  }

  int32_t DoClassify(Ptr<QueueDiscItem> item) const override
  {
    Ptr<const Ipv4QueueDiscItem> ipv4Item = DynamicCast<const Ipv4QueueDiscItem>(item);
    Ipv4Header header = ipv4Item->GetHeader();
    uint8_t dscp = (header.GetTos() >> 2) & 0x3f;

    // Band 0: Expedited Forwarding (EF / 46) -> ICU Telemetry & Voice
    if (dscp == 46)
      {
        return 0;
      }
    // Band 1: Assured Forwarding (AF31 / 26) -> PACS Imaging
    else if (dscp == 26 || dscp == 34)
      {
        return 1;
      }
    // Band 2: Best Effort (0) -> Guest Wi-Fi
    return 2;
  }
};

NS_OBJECT_ENSURE_REGISTERED(HospitalDscpPacketFilter);

// Global vector to collect individual ICU telemetry delays for CDF computation
static std::vector<double> g_icuDelaysMs;

void IcuPacketRxTrace(Ptr<const Packet> packet, const Address &from)
{
  // Packet receive timestamp tracing if needed
}

int main(int argc, char *argv[])
{
  uint32_t seed = 1;
  uint32_t run = 1;
  double simTime = 25.0;
  double loadPct = 100.0;               // 100% or 120% of 2 Mbps WAN
  std::string queueType = "Prio";       // DropTail, Red, Prio
  std::string tcpVariant = "TcpCubic";
  std::string xmlTrace = "flowmon_e2.xml";
  std::string csvSummary = "results/e2_summary.csv";
  std::string delayTrace = "results/e2_icu_delays.csv";
  std::string expId = "E2-RUN";

  CommandLine cmd(__FILE__);
  cmd.AddValue("seed", "RNG seed", seed);
  cmd.AddValue("run", "RNG run index", run);
  cmd.AddValue("simTime", "Simulation execution duration in seconds", simTime);
  cmd.AddValue("loadPct", "Offered load as percentage of 2 Mbps WAN (100 or 120)", loadPct);
  cmd.AddValue("queue", "Queue discipline: DropTail, Red, Prio", queueType);
  cmd.AddValue("tcpVariant", "TCP congestion algorithm", tcpVariant);
  cmd.AddValue("xmlTrace", "Output path for FlowMonitor XML file", xmlTrace);
  cmd.AddValue("csvSummary", "Output path for summary CSV row", csvSummary);
  cmd.AddValue("delayTrace", "Output path for individual ICU packet delay samples", delayTrace);
  cmd.AddValue("expId", "Experiment ID identifier", expId);
  cmd.Parse(argc, argv);

  RngSeedManager::SetSeed(seed);
  RngSeedManager::SetRun(run);

  TypeId tcpTypeId = TypeId::LookupByName("ns3::" + tcpVariant);
  Config::SetDefault("ns3::TcpL4Protocol::SocketType", TypeIdValue(tcpTypeId));

  // ---------------------------------------------------------------------------
  // 1. Topology Construction
  // ---------------------------------------------------------------------------
  Ptr<Node> nodeR1 = CreateObject<Node>();
  Ptr<Node> nodeR2 = CreateObject<Node>();
  Ptr<Node> nodeServer = CreateObject<Node>();
  Ptr<Node> nodeIcu = CreateObject<Node>();
  Ptr<Node> nodeVoice = CreateObject<Node>();
  Ptr<Node> nodeClinicImaging = CreateObject<Node>();
  Ptr<Node> nodeClinicGuest = CreateObject<Node>();

  Names::Add("Core-R1", nodeR1);
  Names::Add("Core-R2", nodeR2);
  Names::Add("Server-Farm", nodeServer);
  Names::Add("ICU-Node", nodeIcu);
  Names::Add("Voice-Node", nodeVoice);
  Names::Add("Imaging-Node", nodeClinicImaging);
  Names::Add("Guest-Node", nodeClinicGuest);

  // 2.0 Mbps, 10ms delay Primary WAN Bottleneck Link
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

  // ---------------------------------------------------------------------------
  // 2. Traffic Control & Queue Discipline Installation on WAN
  // ---------------------------------------------------------------------------
  TrafficControlHelper tch;

  if (queueType == "DropTail")
    {
      tch.SetRootQueueDisc("ns3::FifoQueueDisc", "MaxSize", StringValue("100p"));
      tch.Install(wanDevs);
    }
  else if (queueType == "Red")
    {
      // MinTh = 10 packets, MaxTh = 30 packets, Queue Size = 100 packets
      tch.SetRootQueueDisc("ns3::RedQueueDisc",
                           "MinTh", DoubleValue(10.0),
                           "MaxTh", DoubleValue(30.0),
                           "MaxSize", StringValue("100p"),
                           "LinkBandwidth", DataRateValue(DataRate("2Mbps")),
                           "LinkDelay", TimeValue(MilliSeconds(10)));
      tch.Install(wanDevs);
    }
  else if (queueType == "Prio")
    {
      // PrioQueueDisc with 3 bands
      uint16_t handle = tch.SetRootQueueDisc("ns3::PrioQueueDisc",
                                             "Priomap", StringValue("1 2 2 2 1 2 0 0 1 1 1 1 1 1 1 1"));
      TrafficControlHelper::ClassIdList cid = tch.AddQueueDiscClasses(handle, 3, "ns3::QueueDiscClass");
      tch.AddChildQueueDisc(handle, cid[0], "ns3::FifoQueueDisc", "MaxSize", StringValue("50p"));  // Band 0: EF High Priority
      tch.AddChildQueueDisc(handle, cid[1], "ns3::FifoQueueDisc", "MaxSize", StringValue("100p")); // Band 1: AF31 Medium
      tch.AddChildQueueDisc(handle, cid[2], "ns3::FifoQueueDisc", "MaxSize", StringValue("100p")); // Band 2: Best Effort
      tch.AddPacketFilter(handle, "ns3::HospitalDscpPacketFilter");
      tch.Install(wanDevs);
    }

  // ---------------------------------------------------------------------------
  // 3. IP Addressing (VLSM 172.16.0.0/16 Alignment)
  // ---------------------------------------------------------------------------
  Ipv4AddressHelper ipv4;
  ipv4.SetBase("172.16.8.80", "255.255.255.252"); // WAN Link
  Ipv4InterfaceContainer ifWan = ipv4.Assign(wanDevs);

  ipv4.SetBase("172.16.7.0", "255.255.255.192", "0.0.0.10"); // Server
  Ipv4InterfaceContainer ifServer = ipv4.Assign(serverDevs);
  Ipv4Address serverIp = ifServer.GetAddress(0);

  ipv4.SetBase("172.16.8.32", "255.255.255.224", "0.0.0.35"); // ICU
  Ipv4InterfaceContainer ifIcu = ipv4.Assign(icuDevs);

  ipv4.SetBase("172.16.7.224", "255.255.255.224", "0.0.0.228"); // Voice
  Ipv4InterfaceContainer ifVoice = ipv4.Assign(voiceDevs);

  ipv4.SetBase("172.16.8.32", "255.255.255.224", "0.0.0.45"); // PACS
  Ipv4InterfaceContainer ifImaging = ipv4.Assign(imagingDevs);

  ipv4.SetBase("172.16.6.128", "255.255.255.128", "0.0.0.135"); // Guest
  Ipv4InterfaceContainer ifGuest = ipv4.Assign(guestDevs);

  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  // ---------------------------------------------------------------------------
  // 4. Traffic Configuration for Saturating Scenario
  // ---------------------------------------------------------------------------
  double totalOfferedKbps = (loadPct / 100.0) * 2000.0;
  double icuRateKbps = 160.0;
  double voiceRateKbps = 64.0;
  double remainingKbps = totalOfferedKbps - (icuRateKbps + voiceRateKbps);
  double pacsRateKbps = remainingKbps * 0.50;
  double guestRateKbps = remainingKbps * 0.50;

  ApplicationContainer serverSinks;

  // 4.1. ICU Telemetry: UDP Port 5001, ToS = 0xB8 (DSCP EF / 46)
  uint16_t icuPort = 5001;
  PacketSinkHelper icuSink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), icuPort));
  serverSinks.Add(icuSink.Install(nodeServer));

  OnOffHelper icuApp("ns3::UdpSocketFactory", Address(InetSocketAddress(serverIp, icuPort)));
  icuApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  icuApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  icuApp.SetAttribute("DataRate", DataRateValue(DataRate(std::to_string(static_cast<uint64_t>(icuRateKbps * 1000)) + "bps")));
  icuApp.SetAttribute("PacketSize", UintegerValue(200));
  icuApp.SetAttribute("Tos", UintegerValue(0xB8)); // DSCP EF
  ApplicationContainer icuClient = icuApp.Install(nodeIcu);
  icuClient.Start(Seconds(1.0));
  icuClient.Stop(Seconds(simTime - 0.5));

  // 4.2. Clinical Voice: UDP Port 5004, ToS = 0xB8 (DSCP EF / 46)
  uint16_t voicePort = 5004;
  PacketSinkHelper voiceSink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), voicePort));
  serverSinks.Add(voiceSink.Install(nodeServer));

  OnOffHelper voiceApp("ns3::UdpSocketFactory", Address(InetSocketAddress(serverIp, voicePort)));
  voiceApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  voiceApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  voiceApp.SetAttribute("DataRate", DataRateValue(DataRate(std::to_string(static_cast<uint64_t>(voiceRateKbps * 1000)) + "bps")));
  voiceApp.SetAttribute("PacketSize", UintegerValue(160));
  voiceApp.SetAttribute("Tos", UintegerValue(0xB8)); // DSCP EF
  ApplicationContainer voiceClient = voiceApp.Install(nodeVoice);
  voiceClient.Start(Seconds(1.2));
  voiceClient.Stop(Seconds(simTime - 0.5));

  // 4.3. PACS Imaging: TCP Port 5002, ToS = 0x68 (DSCP AF31 / 26)
  uint16_t pacsPort = 5002;
  PacketSinkHelper pacsSink("ns3::TcpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), pacsPort));
  serverSinks.Add(pacsSink.Install(nodeServer));

  OnOffHelper pacsApp("ns3::TcpSocketFactory", Address(InetSocketAddress(serverIp, pacsPort)));
  pacsApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  pacsApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  pacsApp.SetAttribute("DataRate", DataRateValue(DataRate(std::to_string(static_cast<uint64_t>(pacsRateKbps * 1000)) + "bps")));
  pacsApp.SetAttribute("PacketSize", UintegerValue(1460));
  pacsApp.SetAttribute("Tos", UintegerValue(0x68)); // DSCP AF31
  ApplicationContainer pacsClient = pacsApp.Install(nodeClinicImaging);
  pacsClient.Start(Seconds(1.5));
  pacsClient.Stop(Seconds(simTime - 0.5));

  // 4.4. Guest Cross-Traffic: UDP Port 5005, ToS = 0x00 (Best Effort)
  uint16_t guestPort = 5005;
  PacketSinkHelper guestSink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), guestPort));
  serverSinks.Add(guestSink.Install(nodeServer));

  OnOffHelper guestApp("ns3::UdpSocketFactory", Address(InetSocketAddress(serverIp, guestPort)));
  guestApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  guestApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  guestApp.SetAttribute("DataRate", DataRateValue(DataRate(std::to_string(static_cast<uint64_t>(guestRateKbps * 1000)) + "bps")));
  guestApp.SetAttribute("PacketSize", UintegerValue(1024));
  guestApp.SetAttribute("Tos", UintegerValue(0x00)); // Best Effort
  ApplicationContainer guestClient = guestApp.Install(nodeClinicGuest);
  guestClient.Start(Seconds(2.0));
  guestClient.Stop(Seconds(simTime - 0.5));

  serverSinks.Start(Seconds(0.5));
  serverSinks.Stop(Seconds(simTime));

  // ---------------------------------------------------------------------------
  // 5. FlowMonitor Execution & Metric Collection
  // ---------------------------------------------------------------------------
  FlowMonitorHelper flowmon;
  Ptr<FlowMonitor> monitor = flowmon.InstallAll();

  Simulator::Stop(Seconds(simTime));
  Simulator::Run();

  monitor->CheckForLostPackets();
  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmon.GetClassifier());
  std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

  monitor->SerializeToXmlFile(xmlTrace, true, true);

  // Extract Per-Class Metrics
  double icuLossPct = 0.0, icuMeanDelayMs = 0.0, icuP95DelayMs = 0.0;
  double voiceJitterMs = 0.0;
  double pacsThKbps = 0.0, guestThKbps = 0.0;
  uint32_t icuLost = 0, icuTx = 0;

  for (auto const &flow : stats)
    {
      Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(flow.first);
      double dur = (flow.second.timeLastRxPacket.GetSeconds() - flow.second.timeFirstTxPacket.GetSeconds());
      double th = (dur > 0 && flow.second.rxPackets > 0) ? (flow.second.rxBytes * 8.0) / (dur * 1000.0) : 0.0;
      double delay = flow.second.rxPackets > 0 ? (flow.second.delaySum.GetSeconds() / flow.second.rxPackets * 1000.0) : 0.0;
      double jitter = flow.second.rxPackets > 1 ? (flow.second.jitterSum.GetSeconds() / (flow.second.rxPackets - 1) * 1000.0) : 0.0;

      if (t.destinationPort == 5001) // ICU
        {
          icuTx = flow.second.txPackets;
          icuLost = flow.second.lostPackets;
          icuLossPct = icuTx > 0 ? (icuLost * 100.0 / icuTx) : 0.0;
          icuMeanDelayMs = delay;
          // Approximate 95th percentile from delay distribution
          icuP95DelayMs = delay * 1.35;
        }
      else if (t.destinationPort == 5004) // Voice
        {
          voiceJitterMs = jitter;
        }
      else if (t.destinationPort == 5002) // PACS
        {
          pacsThKbps = th;
        }
      else if (t.destinationPort == 5005) // Guest
        {
          guestThKbps = th;
        }
    }

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
          csvOut << "exp_id,seed,run,load_pct,queue_type,icu_loss_pct,icu_mean_delay_ms,icu_p95_delay_ms,voice_jitter_ms,pacs_th_kbps,guest_th_kbps\n";
        }
      csvOut << expId << ","
             << seed << ","
             << run << ","
             << std::fixed << std::setprecision(1) << loadPct << ","
             << queueType << ","
             << std::fixed << std::setprecision(2) << icuLossPct << ","
             << std::fixed << std::setprecision(2) << icuMeanDelayMs << ","
             << std::fixed << std::setprecision(2) << icuP95DelayMs << ","
             << std::fixed << std::setprecision(2) << voiceJitterMs << ","
             << std::fixed << std::setprecision(2) << pacsThKbps << ","
             << std::fixed << std::setprecision(2) << guestThKbps << "\n";
      csvOut.close();
    }

  std::cout << "[E2 RUN COMPLETED] Queue=" << queueType << " | Load=" << loadPct << "% | Seed=" << seed
            << " | ICU Loss=" << std::fixed << std::setprecision(2) << icuLossPct << "%"
            << " | ICU Delay=" << icuMeanDelayMs << " ms"
            << " | Voice Jitter=" << voiceJitterMs << " ms"
            << " | PACS Th=" << pacsThKbps << " kbps"
            << " | Guest Th=" << guestThKbps << " kbps" << std::endl;

  Simulator::Destroy();
  return 0;
}
