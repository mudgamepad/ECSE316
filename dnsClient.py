import argparse
import random
import socket
import time
import sys


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-t', '--timeout', type=int, default=5)  # how long to wait, in seconds, before
    # retransmitting an unanswered query
    parser.add_argument('-r', '--max_retries', type=int, default=3)  # maximum number of times to retransmit an
    # unanswered query before giving up
    parser.add_argument('-p', '--port', type=int, default=53)  # UDP port number of the DNS server

    # Create mutually exclusive group for mx, ns
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-mx', action='store_true')  # send MX (mail server)
    group.add_argument('-ns', action='store_true')  # send NS (name server)

    parser.add_argument('server', help="Provide IPv4 address of the DNS server, in a.b.c.d. format")
    parser.add_argument('name', help="Provide  the domain name to query for")

    args = parser.parse_args()

    return args


def validate_args(args):
    error = ""
    is_error = False

    # Validate timeout
    if args.timeout < 0:
        is_error = True
        error += f"ERROR    Timeout must be non-negative\n"

    # Validate max_retries
    if args.max_retries < 0:
        is_error = True
        error += f"ERROR    Max-retries must be non-negative\n"

    # Validate port number (port)
    if not (0 <= args.port <= 65535):
        is_error = True
        error += f"ERROR    Invalid port number. Must be in range [0, 65535]\n"

    # Validate ip address (server)
    ip = args.server.lstrip('@')  # remove leading '@' if there is one
    ip_segments = ip.split('.')

    # ip address must have 4 numbers delineated by periods, each number in range [0, 255]
    if len(ip_segments != 4):
        is_error = True
        error += f"ERROR    Invalid server IP address format. Must be in 'a.b.c.d' format\n"

    if is_error:
        print(error)
        sys.exit(1)


def build_request(args):

    # Build header
    request_id = random.randint(0, 0xFFFF)  # create random 16-bit number
    flags = 0x0100  # qr, opcode, aa, tc, rd, ra, z and rcode combined into 16-bits
    qd_count = 1  # 1 question per packet
    an_count = 0  # only matters for response
    ns_count = 0  # instructions say we can ignore
    ar_count = 0  # only matters for response

    header = (
        request_id.to_bytes(2, 'big') +  # to_bytes converts int to byte representation
        flags.to_bytes(2, 'big') +
        qd_count.to_bytes(2, 'big') +
        an_count.to_bytes(2, 'big') +
        ns_count.to_bytes(2, 'big') +
        ar_count.to_bytes(2, 'big')
    )

    # Build question

    # Encode q_name
    labels = args.name.split('.')  # split domain name into labels
    q_name = b''.join(len(label).to_bytes(1, 'big') + label.encode() for label in labels)  # encode converts string
    # into byte representation
    q_name += b'\x00'  # delimit end of q_name

    # Change query type field depending on mx/ns field
    if args.mx:
        q_type = 0x000f  # type-MX query (mail server)
        request_type = "MX"
    elif args.ns:
        q_type = 0x0002  # type-NS query (name server)
        request_type = "NS"
    else:
        q_type = 0x0001  # type-A query (host address)
        request_type = "A"

    q_class = 0x0001  # represents an Internet address

    # Combine parts of question
    question = q_name + q_type.to_bytes(2, 'big') + q_class.to_bytes(2, 'big')

    # Combine header and question
    packet = header + question

    return packet, request_type


def send_request(args, packet, request_type):
    # Initial printout
    print(f"DnsClient sending request for {args.name}")
    print(f"Server: {args.server}")
    print(f"Request type: {request_type}")

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # AF_INET specifies IPV4 address family, SOCK_DGRAM
    # specifies UDP socket rather than TCP
    sock.settimeout(args.timeout)

    num_retries = 0  # keep track of retries
    start_time = time.time()  # timer

    while num_retries <= args.max_retries:
        try:
            # Strip @ from ip
            ip = args.server.lstrip('@')

            # Send DNS query
            sock.sendto(packet, (ip, args.port))

            response = sock.recvfrom(512)

            print(f"Response received after {time.time() - start_time} seconds ({num_retries} retries)")

            sock.close()

            return response

        # Try to send the packet again if no response within socket timeout
        except socket.timeout:
            num_retries += 1

        # General error handling
        except Exception as e:
            print(f"ERROR   {e}")
            sys.exit(1)

    # No success before max retries
    print(f"ERROR   Maximum number of retries {args.max_retries} exceeded")
    sock.close()
    sys.exit(1)


def parse_response(response):

    # Extract number of response records from header
    header = response[:12]
    qd_count = int.from_bytes(header[4:6], 'big')
    an_count = int.from_bytes(header[6:8], 'big')  # number of resource records in Answer section
    ns_count = int.from_bytes(header[8:10], 'big')  # number of name server resource records in Authority section
    ar_count = int.from_bytes(header[10:12], 'big')  # number of resource records in Additional records section

    # No records found
    if an_count == 0 and ar_count == 0:
        print(f"NOT FOUND")
        sys.exit(1)

    index = 12  # header is 12 bytes long

    # Skip over Question section
    for _ in range(qd_count):
        # Skip QNAME
        while response[index] != 0:  # 0 indicates the end of QNAME
            index += 1

        # Skip zero-length octet(1) + QTYPE(2) + QCLASS(2) = 5
        index += 5

    # Read Answer section
    if an_count > 0:
        print(f"***Answer Section ({an_count} records)***")

        for i in range(an_count):
            index = parse_record(response, index)

    # Skip over Authority section
    for _ in range(ns_count):
        # Skip NAME
        while response[index] != 0:
            index += 1

        # Skip zero-length octet(1) + TYPE(2) + CLASS(2) + TTL(4) = 9
        index += 9

        # Get RDLENGTH
        rd_length = int.from_bytes(response[index:index+2], 'big')

        # Skip RDLENGTH(2), RDATA(1 * RDLENGTH)
        index += 2 + rd_length

    # Read Additional section
    if ar_count > 0:
        print(f"***Additional Section ({ar_count} records)***")

        for i in range(ar_count):
            index = parse_record(response, index)


def parse_record(response, index):
    name_index = index

    # NAME, TYPE, CLASS, TTL, RDLENGTH, RDATA

    while response[index] != 0:
        index += 1

    name = int.from_bytes(response[name_index:index], 'big')  # check for correct index

    # TODO Check for name compression

    dns_type = int.from_bytes(response[index:index+2])
    index += 2

    dns_class = int.from_bytes(response[index:index+2], 'big')
    index += 2

    ttl = int.from_bytes(response[index:index+4], 'big')
    index += 4

    rdlength = int.from_bytes(response[index:index+2], 'big')
    index += 2

    # TODO Handle rdata depending on record type (dns_type)

    return index


def main():
    # Parse command line arguments
    args = parse_args()

    # Validate input
    validate_args(args)

    # Construct request packet
    packet, request_type = build_request(args)

    # Send request packet using sockets
    response = send_request(args, packet, request_type)

    # Parse response
    parse_response(response)


if __name__ == "__main__":
    main()
