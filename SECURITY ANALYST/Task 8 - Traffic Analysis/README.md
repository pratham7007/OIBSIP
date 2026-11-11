# Task 8 — Wireshark traffic analysis

**Status: not performed.** Wireshark was not available and no capture was taken. There is
no `.pcap` file, handshake screenshot, or claim about observed traffic. Capture only
traffic on an interface/network you own or explicitly administer; other people's traffic
can contain sensitive information.

## Safe completion checklist

1. Install Wireshark from [wireshark.org](https://www.wireshark.org/download.html) in your
   own lab and use an interface authorized for capture.
2. Capture for the required duration, then apply the Wireshark display filters `http`,
   `dns`, and `tcp` within the isolated test traffic.
3. To analyze the three-way handshake, identify one connection's SYN, SYN/ACK, and ACK
   packets by stream/sequence, then record only the necessary metadata.
4. Do not collect credentials or unrelated personal content. Use a purpose-built test
   service if demonstrating cleartext HTTP; avoid real accounts and data.
5. Save your actual `.pcap` and annotated screenshots locally. Share only after reviewing
   and removing unrelated or sensitive packets.

### Glossary

- **Packet:** a formatted unit of data transmitted over a network.
- **Protocol:** agreed rules for communicating, such as DNS or TCP.
- **Port:** a transport-layer number used to direct traffic to an application endpoint.
- **Payload:** the data carried by a packet beyond its protocol-control fields.
- **Handshake:** an exchange used to establish or negotiate a connection; TCP begins with
  SYN, SYN/ACK, then ACK.

Unencrypted HTTP can expose content to observers on the path. HTTPS uses TLS to authenticate
the server and protect application data in transit, subject to correct certificate
validation and endpoint security.

See [capture_notes.txt](./capture_notes.txt) for the blank evidence record.
