import argparse


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
    return args


def execute_query(args):
    if args.mx:
        print("MX query")
    elif args.ns:
        print("NS query")
    else:
        print("A query")


def main():
    # Parse command line arguments
    args = parse_args()


if __name__ == "__main__":
    main()


------------------------------------------------------------------------

from random import *

class DnsPacket:
    def _init_(self,header,question,answer,additional):
         self.header = header
         self.question = question
         self.answer = answer
         self.additional = additional
         
class Header:
    def _init_(self,ID,QR,OPCODE,AA,TC,RD,RA,Z,RDCODE,QDCOUNT,ANCOUNT,NSCOUNT,ARCOUNT):
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
    def _init_(self,QNAME,QTYPE,QCLASS):
        self.QNAME = QNAME
        self.QTYPE = QTYPE
        self.QCLASS = QCLASS

class Answer:
    def _init_(self,NAME,TYPE,CLASS,TTL,RDLENGTH,RDATA,REFERENCE,EXCHANGE):
        self.NAME = NAME
        self.TYPE = TYPE
        self.CLASS = CLASS
        self.TTL = TTL
        self.RDLENGTH = RDLENGTH
        self.RDATA = RDATA
        self.REFERENCE = REFERENCE
        self.EXCHANGE = EXCHANGE
        
def find(s,l):
    for i in range(len(l)):
        if l[i] == s:
            return i
    return -1

def getTimeOut(l):
    f = find("-t",l)
    if f == -1:
        return 5
    return l[f + 1]

def maxRetries(l):
    f = find("-r",l)
    if f == -1:
        return 3
    return l[f + 1]

def port(l):
    f = find("-p",l)
    if f == -1:
        return 53
    return l[f + 1]

def flag(l):
    f = find("-mx",l)
    if f == -1:
        f = find("-ns",l)
        if f == -1:
            return "-a"
        return "-ns"
    return "-mx"
