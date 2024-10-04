import argparse
import random
import socket


class DNSPacket:
    def __init__(self, header, question, answer, additional):
        self.header = header
        self.question = question
        self.answer = answer
        self.additional = additional


class Header:
    def __init__(self, ID, QR, OPCODE, AA, TC, RD, RA, Z, RDCODE, QDCOUNT, ANCOUNT, NSCOUNT, ARCOUNT):
        self.ID = ID
        self.QR = QR
        self.OPCODE = OPCODE
        self.AA = AA
        self.TC = TC
        self.RD = RD
        self.RA = RA
        self.Z = Z
        self.RDCODE = RDCODE
        self.QDCOUNT = QDCOUNT
        self.ANCOUNT = ANCOUNT
        self.NSCOUNT = NSCOUNT
        self.ARCOUNT = ARCOUNT


class Question:
    def __init__(self, QNAME, QTYPE, QCLASS):
        self.QNAME = QNAME
        self.QTYPE = QTYPE
        self.QCLASS = QCLASS


class Answer:
    def __init__(self, NAME, TYPE, CLASS, TTL, RDLENGTH, RDATA, REFERENCE, EXCHANGE):
        self.NAME = NAME
        self.TYPE = TYPE
        self.CLASS = CLASS
        self.TTL = TTL
        self.RDLENGTH = RDLENGTH
        self.RDATA = RDATA
        self.REFERENCE = REFERENCE
        self.EXCHANGE = EXCHANGE


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-t', '--timeout', type=int, default=5)  # how long to wait, in seconds, before
    # retransmitting an unanswered query
    parser.add_argument('r', '--max_retries', type=int, default=3)  # maximum number of times to retransmit an
    # unanswered query before giving up
    parser.add_argument('-p', '--port', type=int, default=53)  # UDP port number of the DNS server

    # Create mutually exclusive group for mx, ns
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-mx', action='store_true')  # send MX (mail server)
    group.add_argument('ns', action='store_true')  # send NS (name server)

    parser.add_argument('server')
    parser.add_argument('name')

    args = parser.parse_args()

    return args


def validate_args(args):
    # TODO
    return


def build_request():

    # Create header
    random_int = random.randint(0, 0xFFFF)  # create random 16-bit number
    id = '0x' + f'{random_int:04x}'  # format random int as a 4-digit hex number prepended with 0x
    flags = 0x0100  # qr, opcode, aa, tc, rd, ra, z and rcode combined into 16-bits
    qd_count = 1  # 1 question per packet
    an_count = 0  # only matters for response
    ns_count = 0  # instructions say we can ignore
    ar_count = 0  # only matters for response

    header = (
        id.to_bytes(2, 'big') +
        flags.to_bytes(2, 'big') +
        qd_count.to_bytes(2, 'big') +
        an_count.to_bytes(2, 'big') +
        ns_count.to_bytes(2, 'big') +
        ar_count.to_bytes(2, 'big')
    )
    
    # Encode domain name (QNAME)

    # Define QTYPE and QCLASS

    # Question = QNAME + QTYPE + QCLASS

    # Combine header and question
    return


def main():
    # Parse command line arguments
    args = parse_args()

    # Validate input

    # TODO construct DNS request packet

    # TODO Send request packet to specified DNS server using UDP and socket

    # Output


if __name__ == "__main__":
    main()
