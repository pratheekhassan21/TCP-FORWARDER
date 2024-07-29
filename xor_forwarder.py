import socket
import select
from logzero import logger

# python forwarder.py localhost:1337 github.com:443

# python xor_forwarder.py localhost:1337 localhost:4242
# python xor_forwarder.py localhost:4242 ipinfo.io:80

# curl -v http://localhost.com:1337 -H "Host: ipinfo.io"

class Forwarder:

    def __init__(self, src_host, src_port, dst_host, dst_port):
        # create tcp socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((src_ip, int(src_port)))

        # listen for incoming connections
        self.sock.listen(5)

        self.target = (dst_host, int(dst_port))
    
    # FIXME: replace with secure encryption/decryption
    def xor(self, input, key_byte=42):
        result = b""
        for b in input:
            result += bytes([b ^ key_byte])
        return result

    def exchange_loop(self, client, remote):
        while True:
            # wait until client or remote is available for read
            r, w, e = select.select([client, remote], [], [])

            # if there is data from client, forward to remote host
            if client in r:
                data = client.recv(4096)
                logger.debug(f" CLIENT > REMOTE : {len(data)} bytes")
                # decrypt data and forward to remote
                if remote.send(self.xor(data)) <= 0:
                    return

            # if there is data from remote host, forward to client
            if remote in r:
                data = remote.recv(4096)
                logger.debug(f" CLIENT < REMOTE : {len(data)} bytes")
                # encrypt data and forward to client
                if client.send(self.xor(data)) <= 0:
                    return

    def run(self):
        while True:
            # wait for incoming client connections
            client, addr = self.sock.accept()
            logger.info(f"[NEW] CLIENT({addr[0]}) forward REMOTE({self.target[0]})")

            # create a new socket to connect to remote host
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # connect to remote host
            remote.connect(self.target)

            # start exchange loop to forward data between client and remote
            self.exchange_loop(client, remote)
            

            # close client and remote sockets
            client.close()
            logger.info(f"[CLOSE] CLIENT({addr[0]})")
        remote.close()
        logger.info(f"[CLOSE] REMOTE({self.target[0]})")

if __name__ == '__main__':
    import sys
    src_ip, src_port = sys.argv[1].split(':')
    dst_ip, dst_port = sys.argv[2].split(':')
    logger.info(f'TCP forward {src_ip}:{src_port} > {dst_ip}:{dst_port}')

    proxy = Forwarder(src_ip, src_port, dst_ip, dst_port)
    proxy.run()