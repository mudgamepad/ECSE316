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
    # TODO
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
