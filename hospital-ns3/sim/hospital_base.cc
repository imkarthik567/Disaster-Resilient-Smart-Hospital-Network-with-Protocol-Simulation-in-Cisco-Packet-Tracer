/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * ==============================================================================
 * hospital_base.cc - Universal Baseline Discrete-Event Scenario for Hospital Network
 * Disaster-Resilient Smart Hospital Network (NS-3 Academic Extension)
 * Course: CSE2004 Computer Networks - SCOPE, VIT Vellore
 * Authors: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
 * ==============================================================================
 *
 * NOTE ON VLAN MODELING IN NS-3:
 * In Cisco Packet Tracer, traffic segmentation is configured using 802.1Q VLAN
 * tags (VLAN 10=ICU, 20=Surgery, 30=Admin, 40=Guest, 50=Servers, 60=Voice).
 * In NS-3, 802.1Q encapsulation adds simulation overhead without altering L3
 * routing semantics. Therefore, each hospital zone is represented as a dedicated
 * point-to-point / CSMA subnet matching the classless VLSM plan (172.16.0.0/16).
 *
 * TOPOLOGY OVERVIEW:
 *   [Main Hospital Campus]
 *     - ICU Sensor Nodes (3-10 nodes, 172.16.7.128/26)
 *     - Surgery Workstations (2 nodes, 172.16.7.64/26)
 *     - Admin Workstations (2 nodes, 172.16.4.0/23)
 *     - PACS Imaging Workstations (2 nodes, 172.16.7.64/26)
 *     - Clinical Voice Phones (2 nodes, 172.16.6.0/25)
 *     - Guest Wi-Fi Clients (Configurable, 172.16.0.0/22)
 *     - Central Server Farm / EHR Sink (172.16.7.0/26)
 *     - Aggregated via Distribution Node (SW-D1) -> Core Router R1 (172.16.8.88/30)
 *
 *   [Remote Clinic Campus]
 *     - Clinic Triage / Monitors (172.16.8.32/27)
 *     - Clinic Admin Workstations (172.16.8.0/27)
 *     - Clinic Voice VoIP (172.16.7.224/27)
 *     - Clinic Guest Wi-Fi (172.16.6.128/25)
 *     - Aggregated via Distribution Node (SW-D3) -> Core Router R2 (172.16.8.96/30)
 *
 *   [Core WAN Backbone]
 *     - Primary WAN Link: 2 Mbps, 10 ms delay (172.16.8.80/30)
 *     - Backup Standby WAN: 1 Mbps, 20 ms delay (172.16.8.84/30)
 *
 *   [Optional Internet Edge]
 *     - R1 <-> EDGE-ISP (172.16.8.100/30)
 * ==============================================================================
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/traffic-control-module.h"

#if __has_include("ns3/netanim-module.h")
#include "ns3/netanim-module.h"
#define HAS_NETANIM 1
#else
#define HAS_NETANIM 0
#endif

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <iomanip>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("HospitalBaseSimulation");

// Structure for printing formatted topology inventory table
struct TopologyEntry
{
  uint32_t nodeId;
  std::string nodeName;
  std::string role;
  std::string ipAddress;
  std::string subnetMask;
  std::string zoneVlan;
};

static std::vector<TopologyEntry> g_topologyTable;

void AddTopologyEntry(uint32_t id, const std::string &name, const std::string &role,
                      const std::string &ip, const std::string &mask, const std::string &vlan)
{
  g_topologyTable.push_back({id, name, role, ip, mask, vlan});
}

void AddTopologyEntryIp(uint32_t id, const std::string &name, const std::string &role,
                        Ipv4Address ip, const std::string &mask, const std::string &vlan)
{
  std::ostringstream oss;
  ip.Print(oss);
  g_topologyTable.push_back({id, name, role, oss.str(), mask, vlan});
}

void PrintTopologyTable()
{
  std::cout << "\n====================================================================================================" << std::endl;
  std::cout << "                 DISASTER-RESILIENT SMART HOSPITAL NETWORK - TOPOLOGY INVENTORY" << std::endl;
  std::cout << "====================================================================================================" << std::endl;
  std::cout << std::left
            << std::setw(8)  << "Node ID"
            << std::setw(20) << "Node Name"
            << std::setw(24) << "Role / Equipment"
            << std::setw(18) << "IPv4 Address"
            << std::setw(18) << "Subnet Mask"
            << std::setw(16) << "Zone / VLAN"
            << std::endl;
  std::cout << "----------------------------------------------------------------------------------------------------" << std::endl;

  for (const auto &entry : g_topologyTable)
    {
      std::cout << std::left
                << std::setw(8)  << entry.nodeId
                << std::setw(20) << entry.nodeName
                << std::setw(24) << entry.role
                << std::setw(18) << entry.ipAddress
                << std::setw(18) << entry.subnetMask
                << std::setw(16) << entry.zoneVlan
                << std::endl;
    }
  std::cout << "====================================================================================================\n" << std::endl;
}

int main(int argc, char *argv[])
{
  // ---------------------------------------------------------------------------
  // 1. Command-Line Parameters (Strictly Configurable as Required)
  // ---------------------------------------------------------------------------
  uint32_t seed = 1;
  uint32_t run = 1;
  double simTime = 30.0;
  std::string guestLoad = "500kbps";
  uint32_t imagingSizeMb = 50;           // PACS imaging transfer size (MB)
  uint32_t packetSize = 200;             // ICU telemetry packet payload size (bytes)
  std::string queueType = "DropTail";    // DropTail, Red, Prio
  std::string tcpVariant = "TcpCubic";   // TcpNewReno, TcpCubic, TcpBbr
  double failAt = 12.0;                  // Time to cut primary WAN (negative disables failure)
  std::string routing = "global";        // global, static
  uint32_t numIcu = 5;                   // ICU sensor count (configurable 3 to 10)
  uint32_t numGuest = 3;                 // Guest client count
  bool enableEdge = true;                // Optional Internet edge ISP node
  bool enableAscii = false;              // Optional ASCII packet trace
  std::string animFile = "hospital_anim.xml";
  std::string xmlTrace = "flowmon.xml";
  std::string csvSummary = "summary.csv";
  std::string expId = "BASE-RUN";

  CommandLine cmd(__FILE__);
  cmd.AddValue("seed", "RNG seed for simulation repeatability", seed);
  cmd.AddValue("run", "RNG run index", run);
  cmd.AddValue("simTime", "Total simulation execution time in seconds", simTime);
  cmd.AddValue("guestLoad", "Offered bandwidth load for guest traffic (e.g. 500kbps, 1Mbps)", guestLoad);
  cmd.AddValue("imagingSize", "PACS imaging bulk transfer size in Megabytes (default 50)", imagingSizeMb);
  cmd.AddValue("packetSize", "ICU sensor packet payload size in bytes (default 200)", packetSize);
  cmd.AddValue("queue", "Queue discipline: DropTail, Red, Prio", queueType);
  cmd.AddValue("tcpVariant", "TCP congestion algorithm: TcpNewReno, TcpCubic, TcpBbr", tcpVariant);
  cmd.AddValue("failAt", "Primary WAN failure time in seconds (-1 disables)", failAt);
  cmd.AddValue("routing", "Routing protocol engine: global (OSPF-like), static", routing);
  cmd.AddValue("numIcu", "Number of bedside ICU telemetry sensors (3-10)", numIcu);
  cmd.AddValue("numGuest", "Number of guest Wi-Fi endpoints", numGuest);
  cmd.AddValue("enableEdge", "Enable simulated Internet Edge ISP router", enableEdge);
  cmd.AddValue("enableAscii", "Enable ASCII packet traces", enableAscii);
  cmd.AddValue("animFile", "NetAnim XML export filename", animFile);
  cmd.AddValue("xmlTrace", "FlowMonitor XML output filename", xmlTrace);
  cmd.AddValue("csvSummary", "Single-line summary CSV output filename", csvSummary);
  cmd.AddValue("expId", "Experiment ID tag", expId);
  cmd.Parse(argc, argv);

  // Bounds enforcement
  if (numIcu < 3) numIcu = 3;
  if (numIcu > 10) numIcu = 10;

  // ---------------------------------------------------------------------------
  // 2. Random Number Generator Seeding & TCP Configuration
  // ---------------------------------------------------------------------------
  RngSeedManager::SetSeed(seed);
  RngSeedManager::SetRun(run);

  TypeId tcpTypeId = TypeId::LookupByName("ns3::" + tcpVariant);
  Config::SetDefault("ns3::TcpL4Protocol::SocketType", TypeIdValue(tcpTypeId));

  // ---------------------------------------------------------------------------
  // 3. Node Allocation & Topology Hierarchy Creation
  // ---------------------------------------------------------------------------
  // Core Routers: R1 (Main), R2 (Clinic)
  Ptr<Node> nodeR1 = CreateObject<Node>();
  Ptr<Node> nodeR2 = CreateObject<Node>();
  Names::Add("Core-R1", nodeR1);
  Names::Add("Core-R2", nodeR2);

  // Distribution Switches (L3 aggregation nodes): SW-D1 (Main), SW-D3 (Clinic)
  Ptr<Node> nodeD1 = CreateObject<Node>();
  Ptr<Node> nodeD3 = CreateObject<Node>();
  Names::Add("Dist-SW-D1", nodeD1);
  Names::Add("Dist-SW-D3", nodeD3);

  // Central Server Farm Node (Records, EHR, PACS, Telemetry Sink)
  Ptr<Node> nodeServer = CreateObject<Node>();
  Names::Add("Records-Server", nodeServer);

  // Main Campus Floor Zones
  NodeContainer icuNodes;
  icuNodes.Create(numIcu);
  for (uint32_t i = 0; i < numIcu; ++i)
    {
      Names::Add("ICU-Sensor-" + std::to_string(i + 1), icuNodes.Get(i));
    }

  NodeContainer surgeryNodes;
  surgeryNodes.Create(2); // Surgery OT Stations
  Names::Add("Surgery-Station-1", surgeryNodes.Get(0));
  Names::Add("Surgery-Station-2", surgeryNodes.Get(1));

  NodeContainer adminNodes;
  adminNodes.Create(2); // Admin Workstations
  Names::Add("Admin-PC-1", adminNodes.Get(0));
  Names::Add("Admin-PC-2", adminNodes.Get(1));

  NodeContainer imagingNodes;
  imagingNodes.Create(2); // PACS Workstations
  Names::Add("PACS-Station-1", imagingNodes.Get(0));
  Names::Add("PACS-Station-2", imagingNodes.Get(1));

  NodeContainer voiceNodes;
  voiceNodes.Create(2); // VoIP IP Phones
  Names::Add("VoIP-Phone-1", voiceNodes.Get(0));
  Names::Add("VoIP-Phone-2", voiceNodes.Get(1));

  NodeContainer guestNodes;
  guestNodes.Create(numGuest); // Guest Wi-Fi Clients
  for (uint32_t i = 0; i < numGuest; ++i)
    {
      Names::Add("Guest-Client-" + std::to_string(i + 1), guestNodes.Get(i));
    }

  // Remote Clinic Nodes
  Ptr<Node> clinicTriage = CreateObject<Node>();
  Ptr<Node> clinicAdmin = CreateObject<Node>();
  Ptr<Node> clinicVoice = CreateObject<Node>();
  Ptr<Node> clinicImaging = CreateObject<Node>();
  Ptr<Node> clinicGuest = CreateObject<Node>();
  Names::Add("Clinic-Triage", clinicTriage);
  Names::Add("Clinic-Admin", clinicAdmin);
  Names::Add("Clinic-Voice", clinicVoice);
  Names::Add("Clinic-Imaging", clinicImaging);
  Names::Add("Clinic-Guest", clinicGuest);

  // Optional Internet Edge Node
  Ptr<Node> nodeIsp = nullptr;
  if (enableEdge)
    {
      nodeIsp = CreateObject<Node>();
      Names::Add("EDGE-ISP", nodeIsp);
    }

  // ---------------------------------------------------------------------------
  // 4. Point-to-Point Link Helpers & Channel Attributes
  // ---------------------------------------------------------------------------
  // Primary WAN: 2 Mbps, 10ms delay (OSPF Area 0 Primary Serial Path)
  PointToPointHelper p2pPrimaryWan;
  p2pPrimaryWan.SetDeviceAttribute("DataRate", StringValue("2Mbps"));
  p2pPrimaryWan.SetChannelAttribute("Delay", StringValue("10ms"));
  p2pPrimaryWan.SetQueue("ns3::DropTailQueue", "MaxSize", StringValue("100p"));

  // Backup WAN: 1 Mbps, 20ms delay (Standby Disaster Recovery Path)
  PointToPointHelper p2pBackupWan;
  p2pBackupWan.SetDeviceAttribute("DataRate", StringValue("1Mbps"));
  p2pBackupWan.SetChannelAttribute("Delay", StringValue("20ms"));
  p2pBackupWan.SetQueue("ns3::DropTailQueue", "MaxSize", StringValue("100p"));

  // Campus Core Transit Links: 1 Gbps GigabitEthernet, 1ms delay
  PointToPointHelper p2pCoreTransit;
  p2pCoreTransit.SetDeviceAttribute("DataRate", StringValue("1000Mbps"));
  p2pCoreTransit.SetChannelAttribute("Delay", StringValue("1ms"));

  // Campus Access LAN Links: 100 Mbps FastEthernet, 1ms delay
  PointToPointHelper p2pLan;
  p2pLan.SetDeviceAttribute("DataRate", StringValue("100Mbps"));
  p2pLan.SetChannelAttribute("Delay", StringValue("1ms"));

  // ---------------------------------------------------------------------------
  // 5. Install NetDevices on All Physical Links
  // ---------------------------------------------------------------------------
  // R1 <-> R2 WAN Links
  NetDeviceContainer primaryWanDevs = p2pPrimaryWan.Install(nodeR1, nodeR2);
  NetDeviceContainer backupWanDevs = p2pBackupWan.Install(nodeR1, nodeR2);

  // Distribution to Core Transits
  NetDeviceContainer transitD1R1 = p2pCoreTransit.Install(nodeD1, nodeR1);
  NetDeviceContainer transitD3R2 = p2pCoreTransit.Install(nodeD3, nodeR2);

  // Main Hospital Access Links (All converge into Distribution Node SW-D1)
  NetDeviceContainer serverDevs = p2pLan.Install(nodeServer, nodeD1);

  std::vector<NetDeviceContainer> icuDevs(numIcu);
  for (uint32_t i = 0; i < numIcu; ++i)
    {
      icuDevs[i] = p2pLan.Install(icuNodes.Get(i), nodeD1);
    }

  std::vector<NetDeviceContainer> surgeryDevs(2);
  for (uint32_t i = 0; i < 2; ++i)
    {
      surgeryDevs[i] = p2pLan.Install(surgeryNodes.Get(i), nodeD1);
    }

  std::vector<NetDeviceContainer> adminDevs(2);
  for (uint32_t i = 0; i < 2; ++i)
    {
      adminDevs[i] = p2pLan.Install(adminNodes.Get(i), nodeD1);
    }

  std::vector<NetDeviceContainer> imagingDevs(2);
  for (uint32_t i = 0; i < 2; ++i)
    {
      imagingDevs[i] = p2pLan.Install(imagingNodes.Get(i), nodeD1);
    }

  std::vector<NetDeviceContainer> voiceDevs(2);
  for (uint32_t i = 0; i < 2; ++i)
    {
      voiceDevs[i] = p2pLan.Install(voiceNodes.Get(i), nodeD1);
    }

  std::vector<NetDeviceContainer> guestDevs(numGuest);
  for (uint32_t i = 0; i < numGuest; ++i)
    {
      guestDevs[i] = p2pLan.Install(guestNodes.Get(i), nodeD1);
    }

  // Remote Clinic Access Links (All converge into Distribution Node SW-D3)
  NetDeviceContainer clinicTriageDevs = p2pLan.Install(clinicTriage, nodeD3);
  NetDeviceContainer clinicAdminDevs = p2pLan.Install(clinicAdmin, nodeD3);
  NetDeviceContainer clinicVoiceDevs = p2pLan.Install(clinicVoice, nodeD3);
  NetDeviceContainer clinicImagingDevs = p2pLan.Install(clinicImaging, nodeD3);
  NetDeviceContainer clinicGuestDevs = p2pLan.Install(clinicGuest, nodeD3);

  // Optional Internet Edge ISP link
  NetDeviceContainer ispDevs;
  if (enableEdge && nodeIsp != nullptr)
    {
      ispDevs = p2pLan.Install(nodeR1, nodeIsp);
    }

  // ---------------------------------------------------------------------------
  // 6. Install Internet Stack
  // ---------------------------------------------------------------------------
  InternetStackHelper internet;
  internet.Install(nodeR1);
  internet.Install(nodeR2);
  internet.Install(nodeD1);
  internet.Install(nodeD3);
  internet.Install(nodeServer);
  internet.Install(icuNodes);
  internet.Install(surgeryNodes);
  internet.Install(adminNodes);
  internet.Install(imagingNodes);
  internet.Install(voiceNodes);
  internet.Install(guestNodes);
  internet.Install(clinicTriage);
  internet.Install(clinicAdmin);
  internet.Install(clinicVoice);
  internet.Install(clinicImaging);
  internet.Install(clinicGuest);
  if (enableEdge && nodeIsp != nullptr)
    {
      internet.Install(nodeIsp);
    }

  // ---------------------------------------------------------------------------
  // 7. Configure Traffic Control / Queue Disciplines (QoS)
  // ---------------------------------------------------------------------------
  if (queueType == "Prio")
    {
      TrafficControlHelper tch;
      tch.SetRootQueueDisc("ns3::PrioQueueDisc", "Priomap",
                           StringValue("1 2 2 2 1 2 0 0 1 1 1 1 1 1 1 1"));
      tch.Install(primaryWanDevs);
      tch.Install(backupWanDevs);
    }
  else if (queueType == "Red")
    {
      TrafficControlHelper tch;
      tch.SetRootQueueDisc("ns3::RedQueueDisc");
      tch.Install(primaryWanDevs);
      tch.Install(backupWanDevs);
    }
  // DropTail uses default PointToPointNetDevice queue

  // ---------------------------------------------------------------------------
  // 8. IP Addressing Plan Assignment (Directly Mirroring VLSM 172.16.0.0/16)
  // ---------------------------------------------------------------------------
  Ipv4AddressHelper ipv4;

  // Primary WAN Link: 172.16.8.80/30 (R1 Se0/0/0: .81, R2 Se0/0/0: .82)
  ipv4.SetBase("172.16.8.80", "255.255.255.252");
  Ipv4InterfaceContainer ifPrimaryWan = ipv4.Assign(primaryWanDevs);
  AddTopologyEntry(nodeR1->GetId(), "Core-R1", "Core Router", "172.16.8.81", "255.255.255.252", "Primary WAN");
  AddTopologyEntry(nodeR2->GetId(), "Core-R2", "Core Router", "172.16.8.82", "255.255.255.252", "Primary WAN");

  // Backup WAN Link: 172.16.8.84/30 (R1 Se0/0/1: .85, R2 Se0/0/1: .86)
  ipv4.SetBase("172.16.8.84", "255.255.255.252");
  Ipv4InterfaceContainer ifBackupWan = ipv4.Assign(backupWanDevs);
  AddTopologyEntry(nodeR1->GetId(), "Core-R1", "Core Router", "172.16.8.85", "255.255.255.252", "Backup WAN");
  AddTopologyEntry(nodeR2->GetId(), "Core-R2", "Core Router", "172.16.8.86", "255.255.255.252", "Backup WAN");

  // Core Transit Links:
  // R1 <-> SW-D1: 172.16.8.88/30 (R1: .89, D1: .90)
  ipv4.SetBase("172.16.8.88", "255.255.255.252");
  Ipv4InterfaceContainer ifTransitD1R1 = ipv4.Assign(transitD1R1);
  AddTopologyEntry(nodeD1->GetId(), "Dist-SW-D1", "Distribution", "172.16.8.90", "255.255.255.252", "Transit Core");

  // R2 <-> SW-D3: 172.16.8.96/30 (R2: .97, D3: .98)
  ipv4.SetBase("172.16.8.96", "255.255.255.252");
  Ipv4InterfaceContainer ifTransitD3R2 = ipv4.Assign(transitD3R2);
  AddTopologyEntry(nodeD3->GetId(), "Dist-SW-D3", "Distribution", "172.16.8.98", "255.255.255.252", "Transit Clinic");

  // Central Server Farm: 172.16.7.0/26 (Records Server: 172.16.7.10)
  ipv4.SetBase("172.16.7.0", "255.255.255.192", "0.0.0.10");
  Ipv4InterfaceContainer ifServer = ipv4.Assign(serverDevs);
  Ipv4Address serverIp = ifServer.GetAddress(0);
  AddTopologyEntryIp(nodeServer->GetId(), "Records-Server", "Server Farm", serverIp, "255.255.255.192", "VLAN 50 Servers");

  // ICU Telemetry Subnet: 172.16.7.128/26 (Hosts: .130 upwards)
  std::vector<Ipv4Address> icuIps(numIcu);
  for (uint32_t i = 0; i < numIcu; ++i)
    {
      std::string hostStart = "0.0.0." + std::to_string(130 + (i * 4));
      ipv4.SetBase("172.16.7.128", "255.255.255.192", hostStart.c_str());
      Ipv4InterfaceContainer ifIcu = ipv4.Assign(icuDevs[i]);
      icuIps[i] = ifIcu.GetAddress(0);
      AddTopologyEntryIp(icuNodes.Get(i)->GetId(), "ICU-Sensor-" + std::to_string(i + 1), "ICU Bedside IoT",
                         icuIps[i], "255.255.255.192", "VLAN 10 ICU");
    }

  // Surgery Workstations: 172.16.7.64/26
  for (uint32_t i = 0; i < 2; ++i)
    {
      std::string hostStart = "0.0.0." + std::to_string(70 + (i * 4));
      ipv4.SetBase("172.16.7.64", "255.255.255.192", hostStart.c_str());
      Ipv4InterfaceContainer ifSurg = ipv4.Assign(surgeryDevs[i]);
      AddTopologyEntryIp(surgeryNodes.Get(i)->GetId(), "Surgery-Station-" + std::to_string(i + 1), "OT Surgical Node",
                         ifSurg.GetAddress(0), "255.255.255.192", "VLAN 20 Surgery");
    }

  // Admin Workstations: 172.16.4.0/23
  for (uint32_t i = 0; i < 2; ++i)
    {
      std::string hostStart = "0.0.0." + std::to_string(10 + (i * 4));
      ipv4.SetBase("172.16.4.0", "255.255.254.0", hostStart.c_str());
      Ipv4InterfaceContainer ifAdm = ipv4.Assign(adminDevs[i]);
      AddTopologyEntryIp(adminNodes.Get(i)->GetId(), "Admin-PC-" + std::to_string(i + 1), "Hospital Admin",
                         ifAdm.GetAddress(0), "255.255.254.0", "VLAN 30 Admin");
    }

  // PACS Imaging Workstations: 172.16.7.64/26
  std::vector<Ipv4Address> imagingIps(2);
  for (uint32_t i = 0; i < 2; ++i)
    {
      std::string hostStart = "0.0.0." + std::to_string(80 + (i * 4));
      ipv4.SetBase("172.16.7.64", "255.255.255.192", hostStart.c_str());
      Ipv4InterfaceContainer ifImg = ipv4.Assign(imagingDevs[i]);
      imagingIps[i] = ifImg.GetAddress(0);
      AddTopologyEntryIp(imagingNodes.Get(i)->GetId(), "PACS-Station-" + std::to_string(i + 1), "Radiology PACS",
                         imagingIps[i], "255.255.255.192", "VLAN 20 Imaging");
    }

  // Clinical Voice VoIP: 172.16.6.0/25
  for (uint32_t i = 0; i < 2; ++i)
    {
      std::string hostStart = "0.0.0." + std::to_string(10 + (i * 4));
      ipv4.SetBase("172.16.6.0", "255.255.255.128", hostStart.c_str());
      Ipv4InterfaceContainer ifVoi = ipv4.Assign(voiceDevs[i]);
      AddTopologyEntryIp(voiceNodes.Get(i)->GetId(), "VoIP-Phone-" + std::to_string(i + 1), "Clinical Voice",
                         ifVoi.GetAddress(0), "255.255.255.128", "VLAN 60 Voice");
    }

  // Guest Wi-Fi Clients: 172.16.0.0/22
  for (uint32_t i = 0; i < numGuest; ++i)
    {
      std::string hostStart = "0.0.0." + std::to_string(10 + (i * 4));
      ipv4.SetBase("172.16.0.0", "255.255.252.0", hostStart.c_str());
      Ipv4InterfaceContainer ifGst = ipv4.Assign(guestDevs[i]);
      AddTopologyEntryIp(guestNodes.Get(i)->GetId(), "Guest-Client-" + std::to_string(i + 1), "Guest Untrusted",
                         ifGst.GetAddress(0), "255.255.252.0", "VLAN 40 Guest");
    }

  // Remote Clinic Subnets:
  // Clinic Triage: 172.16.8.32/27
  ipv4.SetBase("172.16.8.32", "255.255.255.224", "0.0.0.35");
  Ipv4InterfaceContainer ifClinicTriage = ipv4.Assign(clinicTriageDevs);
  Ipv4Address clinicTriageIp = ifClinicTriage.GetAddress(0);
  AddTopologyEntryIp(clinicTriage->GetId(), "Clinic-Triage", "Remote Patient Mon", clinicTriageIp, "255.255.255.224", "Clinic VLAN 10");

  // Clinic Admin: 172.16.8.0/27
  ipv4.SetBase("172.16.8.0", "255.255.255.224", "0.0.0.5");
  Ipv4InterfaceContainer ifClinicAdmin = ipv4.Assign(clinicAdminDevs);
  AddTopologyEntryIp(clinicAdmin->GetId(), "Clinic-Admin", "Remote Reception", ifClinicAdmin.GetAddress(0), "255.255.255.224", "Clinic VLAN 30");

  // Clinic Voice: 172.16.7.224/27
  ipv4.SetBase("172.16.7.224", "255.255.255.224", "0.0.0.228");
  Ipv4InterfaceContainer ifClinicVoice = ipv4.Assign(clinicVoiceDevs);
  AddTopologyEntryIp(clinicVoice->GetId(), "Clinic-Voice", "Remote VoIP", ifClinicVoice.GetAddress(0), "255.255.255.224", "Clinic VLAN 60");

  // Clinic Imaging: 172.16.8.32/27 (.45)
  ipv4.SetBase("172.16.8.32", "255.255.255.224", "0.0.0.45");
  Ipv4InterfaceContainer ifClinicImaging = ipv4.Assign(clinicImagingDevs);
  Ipv4Address clinicImagingIp = ifClinicImaging.GetAddress(0);
  AddTopologyEntryIp(clinicImaging->GetId(), "Clinic-Imaging", "Remote X-Ray", clinicImagingIp, "255.255.255.224", "Clinic VLAN 10");

  // Clinic Guest: 172.16.6.128/25
  ipv4.SetBase("172.16.6.128", "255.255.255.128", "0.0.0.135");
  Ipv4InterfaceContainer ifClinicGuest = ipv4.Assign(clinicGuestDevs);
  AddTopologyEntryIp(clinicGuest->GetId(), "Clinic-Guest", "Remote Guest Wi-Fi", ifClinicGuest.GetAddress(0), "255.255.255.128", "Clinic VLAN 40");

  // Optional Internet Edge ISP Subnet: 172.16.8.100/30 (R1: .101, ISP: .102)
  if (enableEdge && nodeIsp != nullptr)
    {
      ipv4.SetBase("172.16.8.100", "255.255.255.252");
      Ipv4InterfaceContainer ifIsp = ipv4.Assign(ispDevs);
      AddTopologyEntryIp(nodeIsp->GetId(), "EDGE-ISP", "Internet Gateway", ifIsp.GetAddress(1), "255.255.255.252", "Internet Edge");
    }

  // Print Formatted Topology Inventory
  PrintTopologyTable();

  // ---------------------------------------------------------------------------
  // 9. Routing Configuration (Dijkstra Global Routing vs Static)
  // ---------------------------------------------------------------------------
  if (routing == "global")
    {
      Ipv4GlobalRoutingHelper::PopulateRoutingTables();
    }
  else
    {
      // Static routing fallback
      Ipv4StaticRoutingHelper staticRouting;
      Ptr<Ipv4StaticRouting> r1Static = staticRouting.GetStaticRouting(nodeR1->GetObject<Ipv4>());
      r1Static->AddNetworkRouteTo(Ipv4Address("172.16.8.0"), Ipv4Mask("255.255.255.0"), Ipv4Address("172.16.8.82"), 1);
    }

  // ---------------------------------------------------------------------------
  // 10. Multi-Zone Healthcare Application Traffic Generation
  // ---------------------------------------------------------------------------
  ApplicationContainer serverApps;

  // 10.1. ICU Telemetry Stream (UDP 1 packet/sec, 200 bytes, ToS = 0xB8 / DSCP EF)
  uint16_t icuPort = 5001;
  PacketSinkHelper icuSink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), icuPort));
  serverApps.Add(icuSink.Install(nodeServer));

  for (uint32_t i = 0; i < numIcu; ++i)
    {
      OnOffHelper icuApp("ns3::UdpSocketFactory", Address(InetSocketAddress(serverIp, icuPort)));
      icuApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
      icuApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
      // 1 packet of 200 bytes per second = 1600 bps
      icuApp.SetAttribute("DataRate", DataRateValue(DataRate(std::to_string(packetSize * 8) + "bps")));
      icuApp.SetAttribute("PacketSize", UintegerValue(packetSize));
      // Set High Priority ToS (DSCP EF: 46 << 2 = 184 = 0xB8)
      icuApp.SetAttribute("Tos", UintegerValue(0xB8));

      ApplicationContainer app = icuApp.Install(icuNodes.Get(i));
      app.Start(Seconds(1.0 + (i * 0.1)));
      app.Stop(Seconds(simTime - 0.5));
    }

  // 10.2. PACS Medical Imaging Bulk Transfers (TCP BulkSend, 50 MB default)
  uint16_t pacsPort = 5002;
  PacketSinkHelper pacsSink("ns3::TcpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), pacsPort));
  serverApps.Add(pacsSink.Install(nodeServer));

  uint64_t maxImagingBytes = static_cast<uint64_t>(imagingSizeMb) * 1024 * 1024;
  BulkSendHelper pacsApp("ns3::TcpSocketFactory", InetSocketAddress(serverIp, pacsPort));
  pacsApp.SetAttribute("MaxBytes", UintegerValue(maxImagingBytes));
  pacsApp.SetAttribute("SendSize", UintegerValue(1460));

  // Local Main Hospital Imaging Workstation 1 -> Server
  ApplicationContainer pacs1 = pacsApp.Install(imagingNodes.Get(0));
  pacs1.Start(Seconds(2.0));
  pacs1.Stop(Seconds(simTime - 0.5));

  // Remote Clinic Imaging Workstation -> Server (Across Primary WAN)
  ApplicationContainer pacsClinic = pacsApp.Install(clinicImaging);
  pacsClinic.Start(Seconds(2.5));
  pacsClinic.Stop(Seconds(simTime - 0.5));

  // 10.3. Administrative Interactive Traffic (TCP OnOff request-like)
  uint16_t adminPort = 5003;
  PacketSinkHelper adminSink("ns3::TcpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), adminPort));
  serverApps.Add(adminSink.Install(nodeServer));

  OnOffHelper adminApp("ns3::TcpSocketFactory", Address(InetSocketAddress(serverIp, adminPort)));
  adminApp.SetAttribute("OnTime", StringValue("ns3::ExponentialRandomVariable[Mean=1.0]"));
  adminApp.SetAttribute("OffTime", StringValue("ns3::ExponentialRandomVariable[Mean=2.0]"));
  adminApp.SetAttribute("DataRate", DataRateValue(DataRate("500Kbps")));
  adminApp.SetAttribute("PacketSize", UintegerValue(1024));

  ApplicationContainer adm1 = adminApp.Install(adminNodes.Get(0));
  adm1.Start(Seconds(3.0));
  adm1.Stop(Seconds(simTime - 0.5));

  // 10.4. Clinical Voice VoIP (UDP 160-byte packets every 20ms = 64 kbps G.711)
  uint16_t voicePort = 5004;
  PacketSinkHelper voiceSink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), voicePort));
  serverApps.Add(voiceSink.Install(nodeServer));

  OnOffHelper voiceApp("ns3::UdpSocketFactory", Address(InetSocketAddress(serverIp, voicePort)));
  voiceApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  voiceApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  voiceApp.SetAttribute("DataRate", DataRateValue(DataRate("64Kbps")));
  voiceApp.SetAttribute("PacketSize", UintegerValue(160));
  voiceApp.SetAttribute("Tos", UintegerValue(0xB8)); // DSCP EF for Voice

  ApplicationContainer voi1 = voiceApp.Install(voiceNodes.Get(0));
  voi1.Start(Seconds(1.5));
  voi1.Stop(Seconds(simTime - 0.5));

  // 10.5. Guest Wi-Fi Best-Effort Cross Traffic (Configurable load)
  uint16_t guestPort = 5005;
  PacketSinkHelper guestSink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), guestPort));
  serverApps.Add(guestSink.Install(nodeServer));

  OnOffHelper guestApp("ns3::UdpSocketFactory", Address(InetSocketAddress(serverIp, guestPort)));
  guestApp.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
  guestApp.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  guestApp.SetAttribute("DataRate", DataRateValue(DataRate(guestLoad)));
  guestApp.SetAttribute("PacketSize", UintegerValue(1024));
  guestApp.SetAttribute("Tos", UintegerValue(0x00)); // Best Effort

  ApplicationContainer gst1 = guestApp.Install(guestNodes.Get(0));
  gst1.Start(Seconds(4.0));
  gst1.Stop(Seconds(simTime - 0.5));

  // Start All Server Sinks
  serverApps.Start(Seconds(0.5));
  serverApps.Stop(Seconds(simTime));

  // ---------------------------------------------------------------------------
  // 11. Disaster Failover Scheduling (Primary WAN Link Disruption)
  // ---------------------------------------------------------------------------
  if (failAt > 0.0 && failAt < simTime)
    {
      NS_LOG_INFO("Scheduling Primary WAN failure event at t=" << failAt << " seconds...");
      Simulator::Schedule(Seconds(failAt), &PointToPointNetDevice::SetReceiveErrorModel,
                          DynamicCast<PointToPointNetDevice>(primaryWanDevs.Get(0)),
                          CreateObject<RateErrorModel>());
      if (routing == "global")
        {
          Simulator::Schedule(Seconds(failAt), &Ipv4GlobalRoutingHelper::RecomputeRoutingTables);
        }
    }

  // ---------------------------------------------------------------------------
  // 12. Packet Capture Traces & NetAnim
  // ---------------------------------------------------------------------------
  if (enableAscii)
    {
      AsciiTraceHelper ascii;
      p2pPrimaryWan.EnableAsciiAll(ascii.CreateFileStream("hospital_primary_wan.tr"));
      p2pBackupWan.EnableAsciiAll(ascii.CreateFileStream("hospital_backup_wan.tr"));
    }

#if HAS_NETANIM
  AnimationInterface anim(animFile);
  anim.SetConstantPosition(nodeR1, 200.0, 300.0);
  anim.SetConstantPosition(nodeR2, 500.0, 300.0);
  anim.SetConstantPosition(nodeD1, 200.0, 400.0);
  anim.SetConstantPosition(nodeD3, 500.0, 400.0);
  anim.SetConstantPosition(nodeServer, 100.0, 500.0);
  anim.UpdateNodeDescription(nodeR1, "Core-R1");
  anim.UpdateNodeDescription(nodeR2, "Core-R2");
  anim.UpdateNodeDescription(nodeServer, "Records-Server");
  anim.UpdateNodeColor(nodeServer, 255, 0, 0); // Red
#endif

  // ---------------------------------------------------------------------------
  // 13. FlowMonitor Performance Measurement Engine
  // ---------------------------------------------------------------------------
  FlowMonitorHelper flowmon;
  Ptr<FlowMonitor> monitor = flowmon.InstallAll();

  // Run Simulation
  Simulator::Stop(Seconds(simTime));
  Simulator::Run();

  // Gather Flow Statistics
  monitor->CheckForLostPackets();
  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmon.GetClassifier());
  std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

  uint64_t totalTxBytes = 0;
  uint64_t totalRxBytes = 0;
  uint32_t totalTxPackets = 0;
  uint32_t totalRxPackets = 0;
  uint32_t totalLostPackets = 0;
  double sumDelayMs = 0.0;
  uint32_t activeFlowCount = 0;

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
          activeFlowCount++;
        }
    }

  double avgDelayMs = activeFlowCount > 0 ? (sumDelayMs / activeFlowCount) : 0.0;
  double deliveryRatioPct = totalTxPackets > 0 ? (100.0 * totalRxPackets / totalTxPackets) : 0.0;
  double overallThroughputKbps = (totalRxBytes * 8.0) / (simTime * 1000.0);

  // Export FlowMonitor XML
  monitor->SerializeToXmlFile(xmlTrace, true, true);

  // Write One-Line Standardized CSV Summary
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
          csvOut << "exp_id,seed,run,sim_time,fail_at,routing,queue,tcp_variant,guest_load,num_icu,tx_pkts,rx_pkts,lost_pkts,pdr_pct,mean_delay_ms,throughput_kbps\n";
        }
      csvOut << expId << ","
             << seed << ","
             << run << ","
             << simTime << ","
             << failAt << ","
             << routing << ","
             << queueType << ","
             << tcpVariant << ","
             << guestLoad << ","
             << numIcu << ","
             << totalTxPackets << ","
             << totalRxPackets << ","
             << totalLostPackets << ","
             << std::fixed << std::setprecision(2) << deliveryRatioPct << ","
             << std::fixed << std::setprecision(2) << avgDelayMs << ","
             << std::fixed << std::setprecision(2) << overallThroughputKbps << "\n";
      csvOut.close();
    }

  // Print Terminal Run Summary
  std::cout << "====================================================================================================" << std::endl;
  std::cout << "  NS-3 HOSPITAL BASELINE SIMULATION COMPLETED (" << expId << ")" << std::endl;
  std::cout << "====================================================================================================" << std::endl;
  std::cout << "  Seed / Run               : " << seed << " / " << run << std::endl;
  std::cout << "  Simulation Time          : " << simTime << " seconds" << std::endl;
  std::cout << "  Primary WAN Failure At   : " << (failAt > 0.0 ? std::to_string(failAt) + "s" : "Disabled") << std::endl;
  std::cout << "  Queue Type / TCP Variant : " << queueType << " / " << tcpVariant << std::endl;
  std::cout << "  Guest Competing Load     : " << guestLoad << std::endl;
  std::cout << "  Active ICU Sensors       : " << numIcu << " bedside units" << std::endl;
  std::cout << "  Total Packets Tx / Rx    : " << totalTxPackets << " / " << totalRxPackets << std::endl;
  std::cout << "  Total Packets Lost       : " << totalLostPackets << std::endl;
  std::cout << "  Packet Delivery Ratio    : " << std::fixed << std::setprecision(2) << deliveryRatioPct << " %" << std::endl;
  std::cout << "  Mean End-to-End Latency  : " << std::fixed << std::setprecision(2) << avgDelayMs << " ms" << std::endl;
  std::cout << "  Overall Aggregated Rate  : " << std::fixed << std::setprecision(2) << overallThroughputKbps << " kbps" << std::endl;
  std::cout << "  FlowMonitor XML Export   : " << xmlTrace << std::endl;
  std::cout << "  Summary CSV Record       : " << csvSummary << std::endl;
  std::cout << "====================================================================================================" << std::endl;

  Simulator::Destroy();
  return 0;
}
