# Central Server Farm Configuration Guide

**Device:** PT Central Server (`SRV-CENTRAL`)  
**Location:** Main Hospital Campus — VLAN 50 (Server Farm)  
**Physical Connection:** SW-D1 FastEthernet0/10  
**Operating Environment:** Cisco Packet Tracer 8.x Server Appliance

---

## 1. Static IP Configuration

In Packet Tracer, click on **Server** -> **Desktop** tab -> **IP Configuration**:

| Parameter | Value | Rationale |
| :--- | :--- | :--- |
| **Interface** | FastEthernet0 | Connected to SW-D1 Fa0/10 |
| **IP Configuration** | Static | Critical server infrastructure |
| **IP Address** | `172.16.4.2` | First usable server address after gateway |
| **Subnet Mask** | `255.255.255.224` | `/27` subnet mask (Server Farm) |
| **Default Gateway** | `172.16.4.1` | SW-D1 SVI VLAN 50 IP address |
| **DNS Server** | `172.16.4.2` | Resolves locally via own DNS service |

---

## 2. DNS Service Configuration

Click on **Server** -> **Services** tab -> **DNS**:
1. Set **DNS Service**: **ON**
2. Add Resource Records:

| Name | Type | IP Address | Description |
| :--- | :---: | :--- | :--- |
| `records.hospital.local` | A Record | `172.16.4.2` | Central Electronic Health Records (EHR) Portal |
| `portal.hospital.local` | A Record | `172.16.4.2` | Hospital Intranet & Clinical Dashboard |
| `telemetry.hospital.local` | A Record | `172.16.4.2` | IoT Sensor Ingestion & Telemetry Collector |
| `pacs.hospital.local` | A Record | `172.16.4.2` | Medical Imaging Archive (MRI/CT Studies) |

Click **Add** for each record.

---

## 3. HTTP / Web Service Configuration

Click on **Server** -> **Services** tab -> **HTTP**:
1. Set **HTTP**: **ON** and **HTTPS**: **ON**
2. Click **(edit)** next to `index.html` and replace with the following clinical dashboard:

```html
<!DOCTYPE html>
<html>
<head>
  <title>Smart Hospital Clinical Records & Telemetry Portal</title>
  <style>
    body { font-family: Segoe UI, Arial, sans-serif; margin: 40px; background-color: #f4f7f9; }
    .card { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    h1 { color: #006699; }
    .badge { background: #28a745; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; }
    th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
    th { background: #006699; color: white; }
  </style>
</head>
<body>
  <div class="card">
    <h1>VIT Smart Hospital - Electronic Health Records (EHR)</h1>
    <p>Status: <span class="badge">NETWORK RESILIENT & ONLINE</span></p>
    <p>Authorized access only. Connected via Core Tier with Multi-Area OSPF & EIGRP Redundancy.</p>
    <h3>Active Clinical Telemetry Feeds:</h3>
    <table>
      <tr><th>Zone</th><th>VLAN</th><th>Telemetry Status</th><th>QoS Class</th></tr>
      <tr><td>ICU Ward 3A</td><td>VLAN 10</td><td>Real-Time Streaming (SBC-PT)</td><td>DSCP EF (46)</td></tr>
      <tr><td>Surgical Suite 1</td><td>VLAN 20</td><td>Active Telemetry</td><td>DSCP EF (46)</td></tr>
      <tr><td>Remote Clinic 1</td><td>VLAN 10 (Remote)</td><td>Synchronized via WAN</td><td>DSCP EF (46)</td></tr>
      <tr><td>PACS Imaging Node</td><td>VLAN 50</td><td>Bulk DICOM Transfer</td><td>DSCP AF31 (26)</td></tr>
    </table>
  </div>
</body>
</html>
```

Click **Save**.

---

## 4. Central DHCP Server Pools

Click on **Server** -> **Services** tab -> **DHCP**:
1. Set **DHCP Service**: **ON**
2. Configure the following pools (click **Add** / **Save** for each):

| Pool Name | Default Gateway | DNS Server | Start IP Address | Subnet Mask | Max Users |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `serverPool` (Default) | `172.16.4.1` | `172.16.4.2` | `172.16.4.10` | `255.255.255.224` | 20 |
| `POOL-ICU` | `172.16.3.129` | `172.16.4.2` | `172.16.3.135` | `255.255.255.192` | 50 |
| `POOL-SURGERY` | `172.16.3.193` | `172.16.4.2` | `172.16.3.200` | `255.255.255.192` | 40 |
| `POOL-ADMIN` | `172.16.2.1` | `172.16.4.2` | `172.16.2.10` | `255.255.255.0` | 200 |
| `POOL-GUEST` | `172.16.0.1` | `172.16.4.2` | `172.16.0.10` | `255.255.254.0` | 450 |
| `POOL-VOICE` | `172.16.3.1` | `172.16.4.2` | `172.16.3.10` | `255.255.255.128` | 100 |

> **Note on DHCP Relay:** To enable DHCP delivery across VLANs, ensure `ip helper-address 172.16.4.2` is configured on the respective SVI interfaces on **SW-D1** and **SW-D2**:
> ```text
> interface Vlan10
>  ip helper-address 172.16.4.2
> interface Vlan20
>  ip helper-address 172.16.4.2
> interface Vlan30
>  ip helper-address 172.16.4.2
> interface Vlan40
>  ip helper-address 172.16.4.2
> interface Vlan60
>  ip helper-address 172.16.4.2
> ```

---

## 5. Client Verification Steps

### Verification A: Dynamic Addressing
On an ICU or Admin PC:
1. Open **Desktop** -> **IP Configuration** -> Select **DHCP**.
2. Verify it receives:
   - IP within its designated subnet
   - Default gateway matching the local SVI
   - DNS server: `172.16.4.2`

### Verification B: DNS Resolution & HTTP Browsing
1. Open **Command Prompt** on PC:
   ```cmd
   nslookup records.hospital.local
   ```
   *Expected Response:*
   ```text
   Server:  records.hospital.local
   Address: 172.16.4.2
   ```
2. Open **Web Browser** on PC -> enter `http://records.hospital.local`.
   *Expected Result:* The Clinical Records portal loads successfully.
