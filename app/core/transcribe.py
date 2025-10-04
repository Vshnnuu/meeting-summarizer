from faster_whisper import WhisperModel

whisper_model = WhisperModel("small", device="cpu")

def transcribe_audio(file_path: str) -> str:
    segments, info = whisper_model.transcribe(file_path, beam_size=5)

    transcript_lines = []
    speaker_id = 1
    last_end = 0.0

    for seg in segments:
        if seg.start - last_end > 1.0:
            speaker_id += 1 if speaker_id == 2 else 2
        line = f"Speaker {speaker_id}: {seg.text.strip()}"
        transcript_lines.append(line)
        last_end = seg.end
    return "\n".join(transcript_lines)