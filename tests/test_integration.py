"""Real device integration tests.

Run with: COMELIT_HOST=192.168.1.XX COMELIT_TOKEN=<token> pytest tests/test_integration.py -v
Set COMELIT_PASSWORD to auto-extract token via HTTP backup.

Video tests require:
  1. The intercom screen to be awake (tap it — WiFi drops when idle).
  2. The HA comelit_man integration to be STOPPED or DISABLED. The device
     only accepts one CTPP session at a time; if HA is running with the
     integration active, it holds CTPP and the video tests will fail with
     ConnectionResetError during call initiation. Disable in HA → Settings
     → Devices & Services → Comelit Man, run the tests, then re-enable.

Gate flags:
  COMELIT_TEST_VIDEO=1   — run video pipeline tests (starts a real call)
  COMELIT_TEST_DOOR=1    — run door-open tests (actually triggers the relay)
  COMELIT_TEST_PUSH=1    — run 30-second push listener test
"""

import asyncio
import os
import struct

import pytest

COMELIT_HOST = os.environ.get("COMELIT_HOST")
COMELIT_TOKEN = os.environ.get("COMELIT_TOKEN")
COMELIT_PASSWORD = os.environ.get("COMELIT_PASSWORD", "comelit")

pytestmark = pytest.mark.skipif(not COMELIT_HOST, reason="COMELIT_HOST not set (real device required)")


@pytest.mark.asyncio
async def test_extract_token():
    """Extract token from device backup.

    Useful for initial setup when no token is known yet. If COMELIT_TOKEN
    is already set this test is skipped — the token is proven valid by the
    other tests that use it directly.
    """
    if COMELIT_TOKEN:
        pytest.skip("COMELIT_TOKEN already set — extraction not needed")
    pytest.importorskip("aiohttp")
    from custom_components.comelit_man.token import extract_token

    token = await extract_token(COMELIT_HOST, password=COMELIT_PASSWORD)
    assert len(token) == 32
    assert all(c in "0123456789abcdef" for c in token)
    print(f"Extracted token: {token}")


@pytest.mark.asyncio
async def test_connect_and_authenticate():
    """Connect and authenticate with the device."""
    if not COMELIT_TOKEN:
        pytest.skip("COMELIT_TOKEN not set")

    from custom_components.comelit_man.client import IconaBridgeClient
    from custom_components.comelit_man.auth import authenticate

    client = IconaBridgeClient(COMELIT_HOST)
    await client.connect()
    try:
        await authenticate(client, COMELIT_TOKEN)
        assert client.connected
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_get_config():
    """Fetch device configuration."""
    if not COMELIT_TOKEN:
        pytest.skip("COMELIT_TOKEN not set")

    from custom_components.comelit_man.client import IconaBridgeClient
    from custom_components.comelit_man.auth import authenticate
    from custom_components.comelit_man.config_reader import get_device_config

    client = IconaBridgeClient(COMELIT_HOST)
    await client.connect()
    try:
        await authenticate(client, COMELIT_TOKEN)
        config = await get_device_config(client)
        print(f"Apt address: {config.apt_address}")
        print(f"Doors: {[d.name for d in config.doors]}")
        print(f"Cameras: {[c.name for c in config.cameras]}")
        assert config.apt_address
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_open_door():
    """Open the first door (CAREFUL: this actually opens a door!)."""
    if not COMELIT_TOKEN:
        pytest.skip("COMELIT_TOKEN not set")
    if not os.environ.get("COMELIT_TEST_DOOR"):
        pytest.skip("Set COMELIT_TEST_DOOR=1 to actually open a door")

    from custom_components.comelit_man.client import IconaBridgeClient
    from custom_components.comelit_man.auth import authenticate
    from custom_components.comelit_man.config_reader import get_device_config
    from custom_components.comelit_man.door import open_door
    from custom_components.comelit_man.protocol import ICONA_BRIDGE_PORT

    client = IconaBridgeClient(COMELIT_HOST)
    await client.connect()
    try:
        await authenticate(client, COMELIT_TOKEN)
        config = await get_device_config(client)
        assert config.doors, "No doors found in config"
        door = config.doors[0]
        print(f"Opening door: {door.name}")
        await open_door(COMELIT_HOST, ICONA_BRIDGE_PORT, COMELIT_TOKEN, client, config, door)
        print(f"Device ACKed relay open — {door.name} triggered")
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_push_listener():
    """Listen for push notifications for 30 seconds."""
    if not COMELIT_TOKEN:
        pytest.skip("COMELIT_TOKEN not set")
    if not os.environ.get("COMELIT_TEST_PUSH"):
        pytest.skip("Set COMELIT_TEST_PUSH=1 to listen for push events")

    from custom_components.comelit_man.client import IconaBridgeClient
    from custom_components.comelit_man.auth import authenticate
    from custom_components.comelit_man.config_reader import get_device_config
    from custom_components.comelit_man.push import register_push

    events = []

    client = IconaBridgeClient(COMELIT_HOST)
    await client.connect()
    try:
        await authenticate(client, COMELIT_TOKEN)
        config = await get_device_config(client)
        await register_push(client, config, lambda e: events.append(e))
        print("Listening for push events for 30 seconds... ring the doorbell!")
        await asyncio.sleep(30)
        print(f"Received {len(events)} events: {events}")
    finally:
        await client.disconnect()


# ---------------------------------------------------------------------------
# CTPP setup helper — mirrors coordinator._open_ctpp_channels
# ---------------------------------------------------------------------------


async def _setup_ctpp(client, config) -> int:
    """Open CTPP+CSPB channels and run the init handshake.

    The device requires this registration before it will accept a video call
    initiation. In normal HA operation the coordinator does this at setup via
    the VIP listener; integration tests must replicate it before calling
    VideoCallSession.start().

    Returns the init_ts used in the handshake (needed for subsequent ACKs).
    """
    import time
    from custom_components.comelit_man.channels import ChannelType
    from custom_components.comelit_man.ctpp import ctpp_init_sequence

    our_addr = f"{config.apt_address}{config.apt_subaddress}"
    ctpp = await client.open_channel("CTPP", ChannelType.UAUT, extra_data=our_addr)
    await client.open_channel("CSPB", ChannelType.UAUT)
    ts = int(time.time()) & 0xFFFFFFFF
    await ctpp_init_sequence(
        client,
        ctpp,
        config.apt_address,
        config.apt_subaddress,
        our_addr,
        ts,
    )
    return ts


# ---------------------------------------------------------------------------
# RTSP client helpers (used by video integration tests)
# ---------------------------------------------------------------------------


async def _read_rtsp_response(reader: asyncio.StreamReader) -> bytes:
    """Read one complete RTSP response (headers + body) from the stream."""
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = await asyncio.wait_for(reader.read(4096), timeout=15.0)
        if not chunk:
            break
        data += chunk
    # Read body if Content-Length is present
    for line in data.split(b"\r\n"):
        if line.lower().startswith(b"content-length:"):
            body_len = int(line.split(b":", 1)[1].strip())
            header_end = data.index(b"\r\n\r\n") + 4
            remaining = body_len - (len(data) - header_end)
            while remaining > 0:
                chunk = await asyncio.wait_for(reader.read(remaining), timeout=15.0)
                if not chunk:
                    break
                data += chunk
                remaining -= len(chunk)
            break
    return data


async def _read_interleaved_frame(reader: asyncio.StreamReader) -> tuple[int, bytes]:
    """Read one interleaved RTSP/RTP frame: $ channel(1) len(2) data(len).

    Skips bytes until the $ magic is found (handles partial RTSP response
    trailing data that may precede the first RTP frame).
    """
    while True:
        b = await asyncio.wait_for(reader.read(1), timeout=10.0)
        if b == b"$":
            break
        if not b:
            raise EOFError("Stream closed before interleaved frame")
    channel = struct.unpack("B", await asyncio.wait_for(reader.readexactly(1), timeout=5.0))[0]
    length = struct.unpack("!H", await asyncio.wait_for(reader.readexactly(2), timeout=5.0))[0]
    payload = await asyncio.wait_for(reader.readexactly(length), timeout=5.0)
    return channel, payload


async def _rtsp_play(
    url: str,
    port: int,
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Connect a minimal RTSP client and negotiate through to PLAY.

    Returns (reader, writer) with the stream positioned just after the
    PLAY 200 OK response — subsequent reads will be interleaved RTP frames.
    Caller is responsible for closing the writer.
    """
    reader, writer = await asyncio.wait_for(asyncio.open_connection("127.0.0.1", port), timeout=5.0)
    base_url = f"rtsp://127.0.0.1:{port}/intercom"

    # OPTIONS
    writer.write(f"OPTIONS {base_url} RTSP/1.0\r\nCSeq: 1\r\n\r\n".encode())
    await writer.drain()
    resp = await _read_rtsp_response(reader)
    assert b"200 OK" in resp, f"OPTIONS failed: {resp[:200]}"

    # DESCRIBE
    writer.write(f"DESCRIBE {base_url} RTSP/1.0\r\nCSeq: 2\r\nAccept: application/sdp\r\n\r\n".encode())
    await writer.drain()
    resp = await _read_rtsp_response(reader)
    assert b"200 OK" in resp, f"DESCRIBE failed: {resp[:200]}"

    # SETUP video track (interleaved TCP)
    writer.write(
        f"SETUP {base_url}/track0 RTSP/1.0\r\n"
        f"CSeq: 3\r\n"
        f"Transport: RTP/AVP/TCP;unicast;interleaved=0-1\r\n\r\n".encode()
    )
    await writer.drain()
    resp = await _read_rtsp_response(reader)
    assert b"200 OK" in resp, f"SETUP failed: {resp[:200]}"
    # Extract session ID from response
    session_id = "87654321"
    for line in resp.split(b"\r\n"):
        if line.lower().startswith(b"session:"):
            session_id = line.split(b":", 1)[1].strip().split(b";")[0].decode()
            break

    # PLAY
    writer.write(f"PLAY {base_url} RTSP/1.0\r\nCSeq: 4\r\nSession: {session_id}\r\n\r\n".encode())
    await writer.drain()
    resp = await _read_rtsp_response(reader)
    assert b"200 OK" in resp, f"PLAY failed: {resp[:200]}"

    return reader, writer


# ---------------------------------------------------------------------------
# Video integration tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_video_call():
    """Start a real video call and verify RTP packets flow from the device.

    Does not involve the RTSP server — tests the raw pipeline:
    TCP signaling → UDP RTP receiver → first NAL received.
    Wake the intercom screen before running.
    """
    if not COMELIT_TOKEN:
        pytest.skip("COMELIT_TOKEN not set")
    if not os.environ.get("COMELIT_TEST_VIDEO"):
        pytest.skip("Set COMELIT_TEST_VIDEO=1 to run video tests")

    from custom_components.comelit_man.client import IconaBridgeClient
    from custom_components.comelit_man.auth import authenticate
    from custom_components.comelit_man.config_reader import get_device_config
    from custom_components.comelit_man.video_call import VideoCallSession

    client = IconaBridgeClient(COMELIT_HOST)
    await client.connect()
    session = None
    try:
        await authenticate(client, COMELIT_TOKEN)
        config = await get_device_config(client)
        await _setup_ctpp(client, config)

        session = VideoCallSession(client, config, auto_timeout=False)
        # start() internally waits for the first video NAL before returning
        receiver = await session.start()

        assert session.active, "Session not active after start()"
        total_pkts = receiver.udp_media_packet_count + receiver.tcp_media_packet_count
        assert total_pkts > 0, "No RTP packets received"
        print(f"\nVideo flowing — UDP={receiver.udp_media_packet_count} TCP={receiver.tcp_media_packet_count} pkts")
    finally:
        if session:
            await session.stop()
        await client.disconnect()


@pytest.mark.asyncio
async def test_rtsp_server_streams_video():
    """Start a real video call, pipe it through LocalRtspServer, connect a
    minimal TCP RTSP client, and verify interleaved RTP frames arrive.

    Covers the full stack: device → UDP RTP → rtp_receiver → rtsp_server
    queues → TCP interleaved → client socket.
    Wake the intercom screen before running.
    """
    if not COMELIT_TOKEN:
        pytest.skip("COMELIT_TOKEN not set")
    if not os.environ.get("COMELIT_TEST_VIDEO"):
        pytest.skip("Set COMELIT_TEST_VIDEO=1 to run video tests")

    from custom_components.comelit_man.client import IconaBridgeClient
    from custom_components.comelit_man.auth import authenticate
    from custom_components.comelit_man.config_reader import get_device_config
    from custom_components.comelit_man.video_call import VideoCallSession
    from custom_components.comelit_man.rtsp_server import LocalRtspServer

    client = IconaBridgeClient(COMELIT_HOST)
    await client.connect()
    rtsp_server = LocalRtspServer()
    session = None
    rtsp_writer = None
    try:
        await authenticate(client, COMELIT_TOKEN)
        config = await get_device_config(client)
        await _setup_ctpp(client, config)

        url = await rtsp_server.start()
        port = rtsp_server._rtsp_port
        print(f"\nRTSP server at {url}")

        # VideoCallSession attaches receiver queues to the RTSP server internally
        session = VideoCallSession(client, config, auto_timeout=False, rtsp_server=rtsp_server)
        await session.start()
        # Unblock PLAY handlers now that video is flowing
        rtsp_server.mark_ready()

        # Connect minimal RTSP client and negotiate to PLAY
        rtsp_reader, rtsp_writer = await _rtsp_play(url, port)

        # Read 10 interleaved RTP frames on video channel (0) — ignore RTCP (1)
        video_frames: list[bytes] = []
        while len(video_frames) < 10:
            channel, payload = await _read_interleaved_frame(rtsp_reader)
            if channel == 0:
                video_frames.append(payload)

        print(f"Received {len(video_frames)} video RTP frames")

        # Validate RTP structure on the first video frame
        rtp = video_frames[0]
        assert len(rtp) >= 12, "RTP packet too short"
        version = (rtp[0] >> 6) & 0x3
        assert version == 2, f"RTP version expected 2, got {version}"
        pt = rtp[1] & 0x7F
        # PT 96 is H.264 dynamic (per SDP); passthrough loop may use same PT
        assert pt in (96, 97), f"Unexpected RTP payload type {pt}"

        # Send TEARDOWN
        base_url = f"rtsp://127.0.0.1:{port}/intercom"
        rtsp_writer.write(f"TEARDOWN {base_url} RTSP/1.0\r\nCSeq: 5\r\nSession: 87654321\r\n\r\n".encode())
        await rtsp_writer.drain()

    finally:
        if rtsp_writer:
            rtsp_writer.close()
        if session:
            await session.stop()
        await rtsp_server.stop()
        await client.disconnect()


@pytest.mark.asyncio
async def test_video_then_door_open():
    """Start video, open a door mid-stream, verify video keeps flowing.

    This exercises the highest-risk code path: async_open_door_on_ctpp
    sends a 0x1840/0x000D on the live video CTPP channel without
    interrupting the video session.
    Wake the intercom screen before running.
    """
    if not COMELIT_TOKEN:
        pytest.skip("COMELIT_TOKEN not set")
    if not os.environ.get("COMELIT_TEST_VIDEO"):
        pytest.skip("Set COMELIT_TEST_VIDEO=1 to run video tests")
    if not os.environ.get("COMELIT_TEST_DOOR"):
        pytest.skip("Set COMELIT_TEST_DOOR=1 to actually open a door")

    from custom_components.comelit_man.client import IconaBridgeClient
    from custom_components.comelit_man.auth import authenticate
    from custom_components.comelit_man.config_reader import get_device_config
    from custom_components.comelit_man.video_call import VideoCallSession
    from custom_components.comelit_man.rtsp_server import LocalRtspServer

    client = IconaBridgeClient(COMELIT_HOST)
    await client.connect()
    rtsp_server = LocalRtspServer()
    session = None
    rtsp_writer = None
    try:
        await authenticate(client, COMELIT_TOKEN)
        config = await get_device_config(client)
        assert config.doors, "No doors in config — cannot test door open"
        await _setup_ctpp(client, config)

        url = await rtsp_server.start()
        port = rtsp_server._rtsp_port

        session = VideoCallSession(client, config, auto_timeout=False, rtsp_server=rtsp_server)
        await session.start()
        rtsp_server.mark_ready()

        rtsp_reader, rtsp_writer = await _rtsp_play(url, port)

        # Confirm video is flowing before the door open
        pre_frames: list[bytes] = []
        while len(pre_frames) < 5:
            channel, payload = await _read_interleaved_frame(rtsp_reader)
            if channel == 0:
                pre_frames.append(payload)
        print(f"\n{len(pre_frames)} video frames before door open")

        # Open the door on the active CTPP channel
        door = config.doors[0]
        our_addr = f"{config.apt_address}{config.apt_subaddress}"
        entrance_addr = config.caller_address or our_addr
        print(f"Opening door '{door.name}' (output_index={door.output_index}) on CTPP")
        await session.async_open_door_on_ctpp(our_addr, entrance_addr, door.output_index)
        print(f"Device ACKed relay open — {door.name} triggered")
        print("Checking video continues...")

        # Confirm video keeps flowing after the door open
        post_frames: list[bytes] = []
        while len(post_frames) < 5:
            channel, payload = await _read_interleaved_frame(rtsp_reader)
            if channel == 0:
                post_frames.append(payload)
        print(f"{len(post_frames)} video frames after door open — stream intact")

        assert len(post_frames) == 5, "Video stopped after door open"

        rtsp_writer.write(
            f"TEARDOWN rtsp://127.0.0.1:{port}/intercom RTSP/1.0\r\nCSeq: 5\r\nSession: 87654321\r\n\r\n".encode()
        )
        await rtsp_writer.drain()

    finally:
        if rtsp_writer:
            rtsp_writer.close()
        if session:
            await session.stop()
        await rtsp_server.stop()
        await client.disconnect()
