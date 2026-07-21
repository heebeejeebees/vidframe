# video_processor.py
import cv2
import time
import base64
from datetime import timedelta
from typing import Dict, Any, Callable, Generator, Optional, Tuple, List


class VideoClarityProcessor:
    def __init__(self, time_start: str = "00:00", time_end: str = "00:00"):
        """
        time_start/time_end in 'MM:SS' format.
        If time_end == '00:00', process until end of video.
        """
        self.time_start = time_start
        self.time_end = time_end

    def process(
        self,
        location: str,
        include_bitmap: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """
        Process clarity of each frame using Laplacian variance.
        Optionally includes per-frame JPEG bitmaps as base64 (disabled by default
        because it's heavy).
        """
        start = time.time()

        video = cv2.VideoCapture(location)
        if not video.isOpened():
            raise ValueError(f"Could not open video at location: {location}")

        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(video.get(cv2.CAP_PROP_FPS))
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

        processed_frames: List[Dict[str, Any]] = []

        start_fno, end_fno = resolve_frame_bounds(
            total_frames, fps, self.time_start, self.time_end
        )
        frames_to_process = max(0, end_fno - start_fno)

        if progress_callback is not None and frames_to_process == 0:
            progress_callback(0, 0)

        for done_count, (fno, timestamp) in enumerate(
            calculate_frame_range(total_frames, fps, self.time_start, self.time_end),
            start=1,
        ):
            video.set(cv2.CAP_PROP_POS_FRAMES, fno)
            ok, image = video.read()
            if not ok or image is None:
                # skip unreadable frame
                if progress_callback is not None:
                    progress_callback(done_count, frames_to_process)
                continue

            # calculate clarity (the higher, the clearer)
            clarity = cv2.Laplacian(image, cv2.CV_64F).var()

            frame_data: Dict[str, Any] = {
                "index": fno,
                "laplacian_variance": float(clarity),
                "timestamp": timestamp,
            }

            if include_bitmap:
                # Encode frame as JPEG and base64 for JSON-safe transport
                _, buffer = cv2.imencode(".jpg", image)
                frame_data["bitmap_jpeg_base64"] = base64.b64encode(buffer).decode(
                    "ascii"
                )

            processed_frames.append(frame_data)

            if progress_callback is not None:
                progress_callback(done_count, frames_to_process)

        video.release()

        return {
            "frames": total_frames,
            "fps": fps,
            "width": width,
            "height": height,
            "duration_seconds": round(time.time() - start, 2),
            "data": processed_frames,
        }


def calculate_frame_range(
    total_frames: int, fps: float, time_start: str, time_end: str
) -> Generator[Tuple[int, str], None, None]:
    """
    Yields (frame_number, 'MM:SS') between time_start and time_end.
    If time_end == '00:00', process until total_frames.
    """
    if not fps > 0:
        raise ValueError("FPS must be a positive number.")

    start_fno, end_fno = resolve_frame_bounds(
        total_frames=total_frames,
        fps=fps,
        time_start=time_start,
        time_end=time_end,
    )

    for fno in range(start_fno, min(end_fno, total_frames)):
        current_seconds = fno / fps
        minutes = int(current_seconds // 60)
        seconds = int(current_seconds % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"
        yield fno, timestamp


def resolve_frame_bounds(
    total_frames: int, fps: float, time_start: str, time_end: str
) -> Tuple[int, int]:
    """
    Resolve frame boundaries from MM:SS timestamps.
    Returns (start_fno, end_fno) where end is exclusive.
    """
    try:
        s = time.strptime(time_start, "%M:%S")
        e = time.strptime(time_end, "%M:%S")
    except (ValueError, TypeError):
        raise ValueError("Invalid timestamp format. Please use 'MM:SS'.")

    start_seconds = timedelta(minutes=s.tm_min, seconds=s.tm_sec).total_seconds()
    start_fno = int(round(start_seconds * fps))

    end_seconds = timedelta(minutes=e.tm_min, seconds=e.tm_sec).total_seconds()
    end_fno = total_frames if end_seconds == 0 else int(round(end_seconds * fps))

    if start_fno < 0:
        start_fno = 0
    if end_fno < start_fno:
        raise ValueError("time_end must be greater than or equal to time_start.")

    return start_fno, min(end_fno, total_frames)


def extract_frame_jpeg(location: str, frame_number: int, jpeg_quality: int = 92) -> bytes:
    """
    Extract a single frame and return JPEG bytes.
    """
    if frame_number < 0:
        raise ValueError("frame_number must be non-negative.")

    video = cv2.VideoCapture(location)
    if not video.isOpened():
        raise ValueError(f"Could not open video at location: {location}")

    try:
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_number >= total_frames:
            raise ValueError(
                f"frame_number {frame_number} is out of range for video with {total_frames} frames."
            )

        video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ok, image = video.read()
        if not ok or image is None:
            raise ValueError(f"Could not read frame {frame_number}.")

        ok_encode, encoded = cv2.imencode(
            ".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
        )
        if not ok_encode:
            raise ValueError(f"Could not encode frame {frame_number} as JPEG.")

        return encoded.tobytes()
    finally:
        video.release()
