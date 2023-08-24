import asyncio
import websockets

async def websocket_client():
    # Update for ws or wss and snapcast
    uri = "ws://your_websocket_uri"
    async with websockets.connect(uri) as websocket:
        while True:
            response = await websocket.recv()
            # Parse response for stream updates
            print(f"< {response}")

# Python 3.7+
if __name__ == "__main__":
    asyncio.run(websocket_client())
