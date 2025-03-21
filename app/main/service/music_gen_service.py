import logging
import time
from math import ceil
from typing import Tuple
from pydub import AudioSegment, effects
import io
import replicate
import requests
from app.main.model.arrangement_status import ArrangementStatus

logger = logging.getLogger("music_generator")


class MusicGenerator:
    def __init__(self, status_update_handler):
        self._status_update_handler = status_update_handler
        self._status = ArrangementStatus.PENDING

    def _handle_update(self, status: ArrangementStatus):
        if callable(self._status_update_handler):
            self._status_update_handler(status)

    def create(self, drums_bytes: bytes, bpm: float, tags: str) -> Tuple[bytes, int]:
        with open("test_drums.wav", "wb") as f:
            f.write(drums_bytes)
        try:
            music_url = self.__generate_music(bpm, tags)
            plain_music_url = self.__remove_drums(music_url)
            plain_music_bytes = self.__get_audio(plain_music_url)

            drums = AudioSegment.from_file(io.BytesIO(drums_bytes), format="wav")
            music = AudioSegment.from_file(io.BytesIO(plain_music_bytes), format="wav")

            music = music.set_frame_rate(drums.frame_rate)
            music = music.set_channels(drums.channels)
            music = music.set_sample_width(drums.sample_width)

            bar_duration_ms = (60 / bpm) * 4 * 1000

            target_duration_ms = 30 * 1000

            drums = effects.normalize(self.__process_drums_duration(drums, target_duration_ms))
            processed_music = effects.normalize(self.__process_melody_duration(music, drums, bar_duration_ms))

            mixed = effects.normalize(drums.overlay(processed_music))

            buffer = io.BytesIO()
            mixed.export(buffer, format="wav")
            return buffer.getvalue(), 200

        except Exception:
            return bytes(), 500

    @staticmethod
    def __process_drums_duration(drums: AudioSegment, target_duration: int) -> AudioSegment:
        current_duration = len(drums)
        if current_duration < target_duration:
            repeat_count = ceil(target_duration / current_duration)
            looped = drums * repeat_count
            return looped[:target_duration]
        return drums

    @staticmethod
    def __process_melody_duration(music: AudioSegment, drums: AudioSegment, bar_duration: float) -> AudioSegment:
        drums_duration = len(drums)
        music_duration = len(music)

        music_bars = round(music_duration / bar_duration)
        segment_duration = 2 * bar_duration if music_bars == 3 else 4 * bar_duration

        repeat_times = ceil(drums_duration / segment_duration)
        segment = music[:segment_duration]
        processed = (segment * repeat_times)[:drums_duration]

        return processed

    def __generate_music(self, bpm: float, tags: str) -> str:
        try:
            prediction = replicate.predictions.create(
                version="f8140d0457c2b39ad8728a80736fea9a67a0ec0cd37b35f40b68cce507db2366",
                input={
                    "bpm": bpm,
                    "seed": -1,
                    "top_k": 250,
                    "top_p": 0,
                    "prompt": tags,
                    "variations": 1,
                    "temperature": 1,
                    "max_duration": ceil(60 / bpm * 4 * 4) + 2,
                    "model_version": "medium",
                    "output_format": "wav",
                    "classifier_free_guidance": 3
                }
            )

            time.sleep(2)

            start_time = time.time()
            while prediction.status not in ["succeeded", "failed", "canceled"]:
                if time.time() - start_time > 300:
                    raise TimeoutError("Generation timed out after 5 minutes")

                if self._status == ArrangementStatus.PENDING and prediction.status == "processing":
                    self._status = ArrangementStatus.PROCESSING
                    self._handle_update(ArrangementStatus.PROCESSING)

                time.sleep(10)
                prediction.reload()

            if prediction.status == "succeeded":
                audio_url = prediction.output['variation_01']
                return audio_url
            elif prediction.status in ("failed", "canceled"):
                self._handle_update(ArrangementStatus.FAILED)
            else:
                raise Exception(f"Generation failed: {prediction.error}")

        except Exception as e:
            logging.info(str(e))

    def __remove_drums(self, url: str) -> str:
        try:
            prediction = replicate.predictions.create(
                version="5a7041cc9b82e5a558fea6b3d7b12dea89625e89da33f0447bd727c2d0ab9e77",
                input={
                    "jobs": 0,
                    "stem": "other",
                    "audio": url,
                    "model": "htdemucs",
                    "split": True,
                    "shifts": 1,
                    "overlap": 0.25,
                    "clip_mode": "rescale",
                    "mp3_preset": 2,
                    "wav_format": "int24",
                    "mp3_bitrate": 320,
                    "output_format": "wav"
                }
            )
            start_time = time.time()
            while prediction.status not in ["succeeded", "failed", "canceled"]:
                if time.time() - start_time > 300:
                    raise TimeoutError("Generation timed out after 5 minutes")

                time.sleep(5)
                prediction.reload()

            if prediction.status == "succeeded":
                audio_url = prediction.output["other"]
                return audio_url
            elif prediction.status in ("failed", "canceled"):
                self._handle_update(ArrangementStatus.FAILED)
            else:
                raise Exception(f"Generation failed: {prediction.error}")

        except Exception as e:
            logger.error(str(e))

    @staticmethod
    def __get_audio(url: str) -> bytes:
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                return response.content
            except requests.exceptions.RequestException as e:
                logger.error(f"Download attempt {attempt + 1} failed: {str(e)}")
                time.sleep(5)

        raise Exception("Failed to download after 3 attempts")
