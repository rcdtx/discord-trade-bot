from scapy.all import *
from scapy.layers.inet import IP, UDP

# Load the original pcap with fragmented packets
print("Loading fragmented packets...")
packets = rdpcap('fragmented_udp.pcap')
print(f"Total packets loaded: {len(packets)}")

# Group fragments by IP ID
fragments = {}
for pkt in packets:
    if IP in pkt:
        ip_id = pkt[IP].id
        if ip_id not in fragments:
            fragments[ip_id] = []
        fragments[ip_id].append(pkt)

# Reassemble fragmented packets
reassembled_packets = []
for ip_id, frag_list in fragments.items():
    # Skip if not fragmented (only one packet)
    if len(frag_list) == 1 and not frag_list[0][IP].flags.MF and frag_list[0][IP].frag == 0:
        reassembled_packets.append(frag_list[0])
        continue
    
    # Sort fragments by offset
    frag_list.sort(key=lambda x: x[IP].frag)
    
    # Check for completeness
    expected_offset = 0
    complete = True
    for frag in frag_list:
        if frag[IP].frag * 8 != expected_offset:
            complete = False
            break
        expected_offset += len(frag[IP].payload)
        if not frag[IP].flags.MF:  # Last fragment
            break
    
    if not complete:
        print(f"Skipping IP ID {hex(ip_id)}: incomplete fragments")
        continue
    
    # Reassemble
    first_frag = frag_list[0]
    full_payload = b''
    for frag in frag_list:
        full_payload += bytes(frag[IP].payload)  # Append payload (skip IP header)
    
    # Create a new packet with the first fragment's headers
    reassembled = IP(src=first_frag[IP].src, dst=first_frag[IP].dst, id=ip_id, proto=17)  # 17 = UDP
    reassembled.payload = first_frag[IP].payload.__class__(full_payload)  # Preserve UDP layer
    reassembled[IP].len = len(reassembled)  # Update IP length
    reassembled[IP].flags = 0  # Clear MF flag
    reassembled[IP].frag = 0  # Clear fragment offset
    
    # Fix UDP length if necessary
    if UDP in reassembled:
        reassembled[UDP].len = len(reassembled[UDP])  # Update UDP length field
    
    reassembled.time = first_frag.time  # Preserve timestamp
    reassembled_packets.append(reassembled)

# Filter for UDP packets (optional)
udp_packets = [pkt for pkt in reassembled_packets if UDP in pkt]

# Write to new pcap
output_file = 'defragmented_udp.pcap'
wrpcap(output_file, udp_packets)
print(f"Saved {len(udp_packets)} defragmented UDP packets to '{output_file}'")

# Optional: Inspect the results
for pkt in udp_packets:
    print(f"Reassembled: Src={pkt[IP].src}:{pkt[UDP].sport}, "
          f"Dst={pkt[IP].dst}:{pkt[UDP].dport}, Len={len(pkt[UDP].payload)} bytes")