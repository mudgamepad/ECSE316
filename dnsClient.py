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

    # Create mutually exclusive group for mx and ns (only one should be true at a time)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-mx', action='store_true')  # send MX (mail server)
    group.add_argument('-ns', action='store_true')  # send NS (name server)

    parser.add_argument('server', type=str)  # IPv4 address of the DNS server
    parser.add_argument('name', type=str)  # domain name to query for

    return parser.parse_args()


def validate_args(args):
    error = ""  # keep track of total error message
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

    # ip address must be in a.b.c.d format
    if len(ip_segments) != 4:
        is_error = True
        error += f"ERROR    Invalid server IP address format. Must be in 'a.b.c.d' format\n"

    # only print if an error was encountered
    if is_error:
        print(error)
        sys.exit(1)


# From input arguments, construct packet
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
    q_name = b''.join(len(label).to_bytes(1, 'big') + label.encode() for label in labels)  # create byte string by
    # encoding each label into byte representation
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

    return packet


# Send packet using UDP socket to IP with PORT
def send_request(args, packet):
    # Initial printout
    print(f"DNS client sending request for {args.name}")

    # Strip @ from ip
    ip = args.server.lstrip('@')
    print(f"Server: {ip}")

    # Set request type depending on flag
    if args.mx:
        request_type = "MX"
    elif args.ns:
        request_type = "NS"
    else:
        request_type = "A"

    print(f"Request type: {request_type}")

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # AF_INET specifies IPV4 address family, SOCK_DGRAM
    # specifies UDP socket rather than TCP
    sock.settimeout(args.timeout)

    num_retries = 0  # keep track of retries
    start_time = time.time()  # timer

    # If no response within socket timeout, try again up to max_retries attempts
    while num_retries <= args.max_retries:
        try:

            # Send DNS query to IP, PORT
            sock.sendto(packet, (ip, args.port))

            response, _ = sock.recvfrom(512)  # attempt to get a response packet

            print(f"Response received after {time.time() - start_time} seconds ({num_retries} retries)")

            sock.close()  # Close socket once response received

            return response

        # Update number of attempts after failed attempt
        except socket.timeout:
            num_retries += 1

        # General error handling for unexpected response
        except Exception as e:
            print(f"ERROR   Unexpected response: {e}")
            sys.exit(1)

    # No success before max retries
    print(f"ERROR   Maximum number of retries {args.max_retries} exceeded")
    sock.close()  # close socket if no response
    sys.exit(1)


# Parse all records in Answer and Additional sections
def parse_response(response):

    # Parse header
    header = response[:12]

    # Get AA (authoritative if True)
    flags = int.from_bytes(header[2:4], 'big')
    aa = (flags & 0x04) >> 2  # 0x04 = 0000 0100, then shift right by 2 to get bit

    # Extract counts from different sections
    qd_count = int.from_bytes(header[4:6], 'big')  # number of entries in Question section
    an_count = int.from_bytes(header[6:8], 'big')  # number of resource records in Answer section
    ns_count = int.from_bytes(header[8:10], 'big')  # number of name server resource records in Authority section
    ar_count = int.from_bytes(header[10:12], 'big')  # number of resource records in Additional records section

    # If no Answer or Additional records, exit
    if an_count == 0 and ar_count == 0:
        print(f"NOT FOUND")
        sys.exit(1)

    index = 12  # index keeps track of current byte in response packet (skipped 12 -> header is 12 bytes)

    # Skip over Question section
    for _ in range(qd_count):
        # Skip QNAME
        while response[index] != 0:  # 0 indicates the end of QNAME
            index += 1

        # Skip zero-length octet(1) + QTYPE(2) + QCLASS(2) = 5 bytes
        index += 5

    # Parse Answer section if there is at least one record
    if an_count > 0:
        print(f"***Answer Section ({an_count} {'record' if an_count == 1 else 'records'})***")  # print record if 1
        # record, records if more than 1 record

        # Parse all records in Answer section
        for _ in range(an_count):
            index = parse_record(response, index, aa)

    # Skip over Authority section
    for _ in range(ns_count):
        # Skip NAME
        while response[index] != 0:
            index += 1  # NAME is 1 byte long

        # Skip NAME + TYPE(2) + CLASS(2) + TTL(4) = 9 bytes
        index += 9

        # Get RDLENGTH
        rd_length = int.from_bytes(response[index:index+2], 'big')  # Skip 2 bytes from RDLENGTH

        # Skip RDLENGTH(2), RDATA(1 * RDLENGTH)
        index += 2 + rd_length

    # Parse Additional section if there is at least one record
    if ar_count > 0:
        print(f"***Additional Section ({ar_count} {'record' if ar_count == 1 else 'records'})***")  # print record if 1
        # record, records if more than 1 record

        # Parse all records in Additional section
        for _ in range(ar_count):
            index = parse_record(response, index, aa)


# Parse given record and printout record contents
def parse_record(response, index, aa):

    # Parse NAME

    # Handle name compression
    if (response[index] & 0xC0) == 0xC0:  # Check if first 2 bits of NAME are 11
        # Name is a pointer
        offset = int.from_bytes(response[index:index+2], 'big') & 0x3FFF  # extract 14-bit offset
        name, _ = parse_name(response, offset)
        index += 2

    #  No name compression
    else:
        name, index = parse_name(response, index)

    # Parse TYPE
    record_type = int.from_bytes(response[index:index+2], 'big')
    index += 2

    # Parse CLASS
    record_class = int.from_bytes(response[index:index+2], 'big')

    # Unexpected CLASS
    if record_class != 0x0001:  # Only handle Internet address
        print(f"ERROR   Unexpected response: Answer CLASS {record_class} cannot be interpreted. Only 0x0001 (IN) "
              f"accepted")
        sys.exit(1)
    index += 2

    # Parse TTL
    ttl = int.from_bytes(response[index:index+4], 'big')
    index += 4

    # Parse RDLENGTH
    rdlength = int.from_bytes(response[index:index+2], 'big')
    index += 2

    # Parse RDATA based on TYPE
    rdata = response[index:index+rdlength]
    index += rdlength

    if aa:
        auth = "auth"
    else:
        auth = "nonauth"

    # Type A
    if record_type == 0x0001:
        ip = ".".join(str(octet) for octet in rdata)
        print(f"IP  {ip}    {ttl}   {auth}")

    # Type NS
    elif record_type == 0x0002:
        ns_name, _ = parse_name(response, index - rdlength)
        print(f"NS  {ns_name}  {ttl}  {auth}")

    # Type CNAME
    elif record_type == 0x0005:
        cname, _ = parse_name(response, index - rdlength)
        print(f"CNAME  {cname}  {ttl}  {auth}")

    # Type MX
    elif record_type == 0x000f:
        exchange, _ = parse_name(response, index - rdlength + 2)  # first 2 bytes are preference
        print(f"MX  {exchange}  {ttl}  {auth}")

    # Unrecognized TYPE
    else:
        print(f"ERROR   Unexpected response: Unrecognized answer TYPE {record_type}. TYPE must be 0x0001 (A), 0x0002 ("
              f"NS), 0x0005 (CNAME) or 0x000f (MX)")
        sys.exit(1)

    return index


# Resolve name compression
def parse_name(response, index):
    labels = []  # store labels

    while True:
        length = response[index]  # retrieve first byte of name

        # Pointer
        if (length & 0xC0) == 0xC0:  # if the first 2 bits = '11' name is a pointer
            offset = int.from_bytes(response[index:index+2], 'big') & 0x3FFF  # retrieve 14 offset bits
            name, _ = parse_name(response, offset)  # get name from response at pointer location
            labels.append(name)
            index += 2  # skip over pointer bytes
            break  # end of compressed name field

        # Non-compressed name

        # End of name
        elif length == 0:   # a byte of 0 indicates end of name
            index += 1  # move past the zero-length octet
            break  # end of non-compressed name field

        # Parse next byte of name
        else:
            index += 1
            label = response[index:index+length].decode()  # convert byte to string
            labels.append(label)
            index += length  # move index past current label

    return ".".join(labels), index


def main():
    # Parse command line arguments
    args = parse_args()

    # Validate input
    validate_args(args)

    # Construct request packet
    packet = build_request(args)

    # Send request packet using sockets
    response = send_request(args, packet)

    # Parse response
    parse_response(response)


if __name__ == "__main__":
    main()
