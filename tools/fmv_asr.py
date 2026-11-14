"""Transcribe FMV audio (work/fmv/<name>.wav) to <name>.asr.tsv: start, end, Japanese text. VAD off (lines went missing with it on).
usage: python -X utf8 tools/fmv_asr.py work/fmv/WATA01.wav [...]"""
import sys, wave
import numpy as np
from faster_whisper import WhisperModel

m = WhisperModel('large-v3', device='cpu', compute_type='int8')
for wav in sys.argv[1:]:
    with wave.open(wav) as w:  # 16 kHz mono s16 from ffmpeg; installed PyAV is too old for faster_whisper's decoder
        pcm = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    segs, _ = m.transcribe(pcm, language='ja', vad_filter=False, beam_size=5, word_timestamps=True,
                           condition_on_previous_text=False,  # one hallucination otherwise repeats to the end
                           initial_prompt='ワタル、龍神丸、サクヤ、アラゴト、ヒミコ、創界山、もんじゃ村、救世主')
    with open(wav[:-4] + '.asr.tsv', 'w', encoding='utf-8') as f:
        for s in segs:  # no_speech/logprob: music-only stretches come back as made-up credits
            f.write(f'{s.start:.2f}\t{s.end:.2f}\t{s.text.strip()}\t{s.no_speech_prob:.2f}\t{s.avg_logprob:.2f}\n')
            print(wav, f'{s.start:6.2f} {s.end:6.2f} {s.no_speech_prob:.2f} {s.text.strip()}')
