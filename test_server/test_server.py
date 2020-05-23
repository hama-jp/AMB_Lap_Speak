#!/usr/bin/env python

import socket
from time import sleep
from argparse import ArgumentParser

INPUT_FILE = "amb.out"
ADDR = '127.0.0.1'
PORT = 12001


def get_args():
    parser = ArgumentParser()
    parser.add_argument("INPUT_FILE", help="amb.out HEX file location", default=INPUT_FILE, nargs='?')
    parser.add_argument("-l", "--listen-address", help="IP address to bind on",  default=ADDR, dest='ADDR')
    parser.add_argument("-p", "--listen-port", help="PORT to bind on",  default=PORT, dest='PORT', type=int)
    parser.add_argument("-i", "--interval", help="interval to send data", default=0.5, dest='INTERVAL', type=int)
    args = parser.parse_args()
    return args


def create_sock(ADDR, PORT):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((ADDR, PORT))
    s.listen(1)
    print("Listening, waiting for connection")
    conn, addr = s.accept()
    print("Accepted connection")
    return conn, s


def send_net(ADDR, PORT, INPUT_FILE, INTERVAL=0.5):
    conn, s = create_sock(ADDR, PORT)
    with open(INPUT_FILE, "r") as fd:
        while True:
            data = "{}".format(fd.readline()).rstrip()
            data_bytes = bytes.fromhex(data)
            try:
                if data_bytes is not None:
                    conn.send(data_bytes)
                    print("sending: {}".format(data))
                    print("sending bytes: {}".format(data_bytes))
                    sleep(INTERVAL)
            except (ConnectionResetError, BrokenPipeError) as error:
                print("socket connection error: {}".format(error))
                conn.close()
                s.close()
                break
            except (KeyboardInterrupt, TypeError) as error:
                print("closing socket, connection: {}".format(error))
                conn.close()
                s.close()
                break

    conn.close()
    s.close()


def main():
    args = get_args()
    while True:
        print("Starting server")
        send_net(args.ADDR, args.PORT, args.INPUT_FILE, args.INTERVAL)
        sleep(0.5)


if __name__ == "__main__":
    main()
