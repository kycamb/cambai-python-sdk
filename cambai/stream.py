import typing
import shutil
import subprocess
import asyncio


def stream(audio_stream: typing.Iterator[bytes]) -> bytes:
    if shutil.which("gst-play-1.0") is None:
        message = (
            "Audio streaming requires `gst-play-1.0`, but it was not found on your system."
            "On macOS, type `brew install gstreamer` to install it."
            "On Ubuntu, type `sudo apt install gstreamer1.0-plugins-base-apps` to install it."
        )
        raise ValueError(message)

    gst_play_command = ["gst-play-1.0", "--no-interactive", "fd://0"]
    gst_play_process = subprocess.Popen(
        gst_play_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    audio = b""
    for chunk in audio_stream:
        if chunk is not None:
            gst_play_process.stdin.write(chunk)
            gst_play_process.stdin.flush()
            audio += chunk
    if gst_play_process.stdin:
        gst_play_process.stdin.close()
    gst_play_process.wait()
    return audio


def capture(sample_rate=16000) -> typing.Iterator[bytes]:
    if shutil.which("gst-launch-1.0") is None:
        message = (
            "Audio capture requires `gst-launch-1.0`, but it was not found on your system."
            "On macOS, type `brew install gstreamer` to install it."
            "On Ubuntu, type `sudo apt install gstreamer1.0-tools` to install it."
        )
        raise ValueError(message)

    gst_launch_command = [
        "gst-launch-1.0",
        "autoaudiosrc", "!",
        "audioconvert", "!", "audioresample", "!",
        f"audio/x-raw,format=S16LE,rate={sample_rate}", "!",
        "fdsink", "fd=1"
    ]
    
    process = subprocess.Popen(
        gst_launch_command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        universal_newlines=False  # Read bytes, not text
    )
    
    try:
        while True:
            chunk = process.stdout.read(16384) # Read approx. half a second at a time
            if not chunk:
                break  # EOS
            yield chunk  # Yield the chunk of audio data
    finally:
        process.stdout.close()
        process.wait()


async def stream_async(audio_stream: typing.AsyncIterator[bytes]) -> bytes:
    if shutil.which("gst-play-1.0") is None:
        message = (
            "Audio streaming requires `gst-play-1.0`, but it was not found on your system. "
            "On macOS, type `brew install gstreamer` to install it. "
            "On Ubuntu, type `sudo apt install gstreamer1.0-plugins-base-apps` to install it."
        )
        raise ValueError(message)

    gst_play_command = ["gst-play-1.0", "--no-interactive", "fd://0"]
    
    process = await asyncio.create_subprocess_exec(
        *gst_play_command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )

    audio = b""
    try:
        async for chunk in audio_stream:
            if chunk is not None:
                process.stdin.write(chunk)
                await process.stdin.drain()
                audio += chunk
    finally:
        if process.stdin:
            process.stdin.close()
        await process.wait()
    
    return audio


async def capture_async(sample_rate: int = 16000) -> typing.AsyncIterator[bytes]:
    if shutil.which("gst-launch-1.0") is None:
        message = (
            "Audio capture requires `gst-launch-1.0`, but it was not found on your system. "
            "On macOS, type `brew install gstreamer` to install it. "
            "On Ubuntu, type `sudo apt install gstreamer1.0-tools` to install it."
        )
        raise ValueError(message)

    gst_launch_command = [
        "gst-launch-1.0",
        "autoaudiosrc", "!",
        "audioconvert", "!", "audioresample", "!",
        f"audio/x-raw,format=S16LE,rate={sample_rate}", "!",
        "fdsink", "fd=1"
    ]
    
    process = await asyncio.create_subprocess_exec(
        *gst_launch_command,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    
    try:
        while True:
            chunk = await process.stdout.readexactly(16384)
            if not chunk:
                break  # EOS
            yield chunk
    except asyncio.IncompleteReadError as e:
        # Handle EOS
        if e.partial:
            yield e.partial
    finally:
        process.stdout.close()
        await process.wait()
