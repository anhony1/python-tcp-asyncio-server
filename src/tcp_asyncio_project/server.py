import asyncio as asy
import random
from datetime import datetime

class Server:
    
    def __init__(self, port, ip,):
        self.port = port
        self.ip = ip
        self.tasks = set()
        # client_id, 
        self.clients = dict()

    # functions that start with the async def are coroutine functions

    async def handle_message(self, reader, writer):
        
        print("Handling Message :) ")

        data = await reader.read(1024)
        message = data.decode()
        addr = writer.get_extra_info('peername')

        print(f"Received {message!r} from {addr!r}")

        print(f"Send: {message!r}")
        writer.write(data)
        await writer.drain()

        print("Close the connection")
        writer.close()
        await writer.wait_closed()

    async def handle_specific_message(self, reader, writer):

        print("handling specific message")

        data = await reader.read(100)
        addr = writer.get_extra_info('peername')
        
        print("Message Received")

        message = self.decode_message(data)

        print("Message Decoded")
        
        print(f"Received {message!r} from {addr!r}")

        print(f"Send: {message!r}")
        writer.write(data)
        await writer.drain()

        print("Close the connection")
        writer.close()
        await writer.wait_closed()

    async def handle_client_constantly(self, reader, writer):
        """Handle individual client connections."""
        addr = writer.get_extra_info('peername')
        print(f"New connection from {addr}")
        
        try:
            while True:
                # Wait for data from the client
                data = await reader.read(1024)
                
                if not data:
                    # Connection closed by client
                    break
                    
                message = data.decode()
                print(f"Received {message!r} from {addr}")

                result = 0
                for i in range(20000000):  # Adjust this number to make it slower/faster
                    result += i * i

                # Echo the message back to client (optional)
                response = f"Server received: {message}"
                writer.write(response.encode())
                await writer.drain()
                
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            print(f"Closing connection with {addr}")
            writer.close()
            await writer.wait_closed()

    async def handle_client_multitasking(self, reader, writer):
        
        """Handle individual client connections."""
        addr = writer.get_extra_info('peername')
        client_id = f"{addr[0]:{addr[1]}}"
        
        self.clients[client_id] = writer

        print(f"New connection from {addr}")
        
        try:
            while True:
                # Wait for data from the client
                data = await reader.read(1024)
                
                if not data:
                    # Connection closed by client
                    break
        
                message = data.decode()
            
                # create a new task to use a coroutine that processes messages
                # the create_task() function to run coroutines concurrently as asyncio tasks
                task = asy.create_task(self.process_message(message, client_id, random.randint(1,10)))
    
                self.tasks.add(task)
                # To prevent keeping references to finished tasks forever,
                # make each task remove its own reference from the set after
                # completion:
                task.add_done_callback(self.tasks.discard)
        
                print(f"Received {message!r} from {addr}")
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            print(f"Closing connection with {addr}")
            self.clients.pop(client_id, None)
            writer.close()
            await writer.wait_closed()

    async def process_message(self, message, client_id, sleep_time):
        print("Processing Message")
        try:
    
            # Echo the message back to client (optional)
            if client_id in self.clients:
                writer = self.clients[client_id]
                response = f"Server received: {message}"
                writer.write(response.encode())
                await writer.drain()
            # broadcast message to ALL clients
            
            self.broadcast_message(message, client_id)

        except Exception as e:
            print("Error processing message from client {}: Exception: {}".format(client_id, e))


    async def broadcast_message(self, message, client_id):
        print("Broadcasting Message")
        
        response = "{} sent message: {}".format(client_id, message)

        for client, writer in self.clients:
            print("Broadcasting Message to: {}", client)
            writer.write(response.encode())
            await writer.drain()

    async def monitor_tasks(self):
        """Monitor and report on active tasks."""
        # Get the current timestamp
        now = datetime.now()
    
        while True:
            await asy.sleep(5)  # Check every 5 seconds
            active_tasks = [task for task in self.tasks if not task.done()]
            print("{} Active Tasks: {}".format(now.strftime("%Y-%m-%d %H:%M:%S"), len(active_tasks)))
            for task in active_tasks:
                print(f"- {task.get_name()}")

    async def start_server(self):
        print("Starting Server")
        
        # server = await asy.start_server(self.handle_message, self.ip, self.port)

        server = await asy.start_server(self.handle_client_multitasking, self.ip, self.port)

        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        print(f'Serving on {addrs}')

        # Montior task is designed to run forever which is why we don't have a add_done_callback function
        monitor_task = asy.create_task(self.monitor_tasks())
        
        # with this, I can track tasks fucking anywhere! 
        self.tasks.add(monitor_task)

        async with server:
            await server.serve_forever()


    async def stop_server(self):
        print("Stopping Server")

    '''
    Protocol Format:
    [4 bytes: total message length]
    [1 byte: message type]
    [1 byte: action type]
    [variable bytes: payload]
    '''
    
    def encode_message(self, message_type, action_type, payload):
        # Convert payload to bytes
        payload_bytes = payload.encode('utf-8')
        
        # Calculate total length (4-byte length + 1-byte type + 1-byte type + payload)
        total_length = 4 + 1 + 1 + len(payload_bytes)
        
        # Construct message
        message = (
            total_length.to_bytes(4, byteorder='big') +  # Total length
            message_type.to_bytes(1, byteorder='big') +  # Message type
            action_type.to_bytes(1, byteorder='big') + # Action Type
            payload_bytes  # Payload
        )
        
        return message


    def decode_message(self, data):
        
        print("Data: {}".format(data))
        
        # Extract total length
        total_length = int.from_bytes(data[:4], byteorder='big')
        
        # Extract message type
        message_type = int.from_bytes(data[4:5], byteorder='big')
        
        # Extract action type
        action_type = int.from_bytes(data[5:6], byteorder='big')

        # Extract payload
        payload = data[6:].decode('utf-8')
        
        return {
            'length': total_length,
            'message_type': message_type,
            'action_type': action_type,
            'payload': payload
        }

    def whats_ip(self):
        print("IP address is {}".format(self.ip))

    def whats_port(self):
        print("Port is: {}".format(self.port))
    
