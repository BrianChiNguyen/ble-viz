# ble_server.py
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from bleak import BleakClient, BleakScanner
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/ui", StaticFiles(directory="static", html=True), name="static")

client: BleakClient = None
CHAR_UUID = "00001526-1212-efde-1523-785feabcd123"
collected_data = [[] for _ in range(4)]
streaming = False

@app.get("/scan")
async def scan_devices():
    print("🔍 Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=5.0)
    result = [{"name": d.name or "Unknown", "address": d.address} for d in devices]
    print(f"✅ Found {len(result)} devices")
    return JSONResponse(content=result)

@app.post("/connect")
async def connect_device(request: Request):
    global client
    body = await request.json()
    address = body.get("address")
    if not address:
        return JSONResponse({"error": "No address provided"}, status_code=400)

    client = BleakClient(address)
    try:
        await client.connect()
        print(f"✅ Connected to {address}")
        return JSONResponse({"status": "connected", "address": address})
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return JSONResponse({"status": "failed", "error": str(e)}, status_code=500)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global client, streaming, collected_data
    await websocket.accept()

    if not client or not client.is_connected:
        await websocket.send_json({"error": "Device not connected"})
        await websocket.close()
        return

    collected_data = [[] for _ in range(4)]
    streaming = True
    print("✅ WebSocket connected, starting notifications")

    async def handler(sender, data: bytearray):
        if not streaming:
            return
        samples = [[] for _ in range(4)]
        for i in range(0, len(data), 2):
            raw = data[i] | (data[i + 1] << 8)
            voltage = raw / 3000.0
            ch = (i // 2) % 4
            val = voltage + ch * 1.5
            samples[ch].append(val)
            collected_data[ch].append(val)
        await websocket.send_json({"samples": samples})

    await client.start_notify(CHAR_UUID, handler)

    try:
        while True:
            # keep the WS open until client.close() from browser
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        streaming = False
        print("⏹️ Stop notifications and disconnecting BLE client")
        await client.stop_notify(CHAR_UUID)
        await client.disconnect()

@app.get("/download")
def download_csv():
    min_len = min(len(ch) for ch in collected_data)
    if min_len == 0:
        return JSONResponse({"error": "No data collected"}, status_code=400)

    data = {
        "Sample": list(range(1, min_len + 1)),
        "Channel0": collected_data[0][:min_len],
        "Channel1": collected_data[1][:min_len],
        "Channel2": collected_data[2][:min_len],
        "Channel3": collected_data[3][:min_len],
    }
    df = pd.DataFrame(data)
    csv = df.to_csv(index=False)
    return JSONResponse(content={"csv": csv})

print("✅ ble_server.py loaded successfully")
