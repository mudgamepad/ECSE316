import argparse
import random
import socket
import time


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
    # TODO
    # Check that timeout >= 0
    return


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

    num_retries = 0  # keep track of retries
    start_time = time.time()  # timer

    while num_retries <= args.max_retries:
        try:
            # Send DNS query
            sock.sendto(packet, (args.server, args.port))

            response = sock.recvfrom(512)

            print(f"Response received after {time.time() - start_time} seconds ({num_retries} retries)")

            return response

        # Try to send the packet again if no response within socket timeout
        except socket.timeout:
            num_retries += 1

        # General error handling
        except Exception as e:
            print(f"ERROR   {e}")

        # Close socket
        finally:
            sock.close()

    # No success before max retries
    print(f"ERROR   Maximum number of retries {args.max_retries} exceeded")


def parse_response(packet):

    # Check if packet contains records in the answer section
    num_answers = 0

    if num_answers > 0:
        print(f"Answer Section ({num_answers} records)")

        # TODO handle A, MX, NS, CNAME records
        # TODO handle unexpected response
    else:
        print(f"NOT FOUND")


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
