# BGP-Inter-Scenario 2
## Overview
In BGP-Inter-Scenario 2, we implement a routing setup where routers from different autonomous systems (AS) exchange routes using BGP. The primary focus is on configuring AS-Path Prepending and Prefix Filtering as export policies, ensuring that:

- **AS-Path Prepending** influences path selection by making certain routes less preferred.
- **Prefix Filtering** ensures routers only advertise their own prefixes (such as /23 and /24) and do not act as transit routers for external traffic.

This scenario uses the following routers:

- **R1 (AS100)** : Connected to R2 and R3, with specific policies applied for BGP route exports.
- **R2 (AS200)** : Connected to R1 and R3, with appropriate OSPF and BGP configuration.
- **R3 (AS300)** : Connected to R1 and R2, sharing routes between its own network and the other ASes.

## BGP Policies Applied:
1. **Export Policy - AS-Path Prepending**:
- R1 applies AS-Path prepending when advertising routes to R2. This policy makes routes learned via R1 less preferred by adding extra AS numbers to the AS path, making it appear longer.

2. **Export Policy - Prefix Filtering**:
- R1 only exports its own prefixes (/23 and /24) and avoids advertising routes it learns from other routers. This policy prevents R1 from becoming a transit router for traffic between R2 and R3.

## Topology
The topology includes the following interconnections between the routers:

- R1 (AS100) ↔ R2 (AS200) via `10.10.1.0/24`
- R1 (AS100) ↔ R3 (AS300) via `10.10.2.0/24`
- R2 (AS200) ↔ R3 (AS300) via `10.10.3.0/24`

Each router also has its own internal networks:

- R1: `10.11.1.0/24`
- R2: `10.12.1.0/24`
- R3: `10.13.1.0/24`

## Testing
1. AS-Path Prepending: You can verify the AS-path prepending by checking the BGP route advertisements from R1 to R2. R2 will receive the routes with additional AS numbers added by R1.

```bash
R2# show ip bgp neighbors 10.10.1.1 advertised-routes
```

2. Prefix Filtering: On R3, you can confirm that it only receives prefixes directly from R1, without any transit prefixes being passed from R2.

```bash
R3# show ip bgp neighbors 10.10.2.1 advertised-routes
```

3. OSPF: Each router will also have OSPF running within its own AS, ensuring internal communication. You can verify the OSPF configuration and routing table with:

```bash
R1# show ip ospf neighbor
R2# show ip ospf neighbor
R3# show ip ospf neighbor

```

## Licencse
This project is licensed under the Creative Commons Legal Code CC0 1.0 Universal. See the [LICENSE](LICENSE) file for details.

## Project Report (in Indonesian)

For more detailed information on the project setup, configuration, and results, refer to the full report:

[Inter-Domain-Routing.pdf](https://github.com/user-attachments/files/17414904/Inter-Domain-Routing.pdf)
