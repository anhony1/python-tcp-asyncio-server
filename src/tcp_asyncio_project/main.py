from server import Server

import asyncio as asy


def main():

    server = Server(8888, "0.0.0.0")

    server.whats_ip()
    server.whats_port()

    asy.run(server.start_server())

    print("Hello World!")

if __name__ == "__main__":
    main()