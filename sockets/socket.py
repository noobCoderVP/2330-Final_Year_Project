import asyncio
import websockets

# Set to store all connected clients
connected_clients = set()

async def handle_client(websocket, path):
    # Add client to the set of connected clients
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            # Broadcast the received message to all connected clients
            await asyncio.gather(*[client.send(message) for client in connected_clients])
    except websockets.exceptions.ConnectionClosedError:
        pass
    finally:
        # Remove client from the set of connected clients when they disconnect
        connected_clients.remove(websocket)

async def main():
    # Start the WebSocket server
    async with websockets.serve(handle_client, "localhost", 8765):
        print("WebSocket server started!")
        await asyncio.Future()  # Run forever

# Run the main coroutine
asyncio.run(main())