"""
Chordelia Playback Module

Provides audio playback functionality for musical sequences using sine wave synthesis.
Integrates with the rhythm and notes modules to play sequences with precise timing.

This module requires sounddevice and numpy for audio output:
    pip install sounddevice numpy
"""

import math
import threading
import time
from typing import List, Tuple, Union, Optional, Any
from dataclasses import dataclass
from enum import Enum

MISSING_DEPS = ""
AUDIO_AVAILABLE = False
try:
    import sounddevice as sd
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError as e:
    AUDIO_AVAILABLE = False
    MISSING_DEPS = str(e)

from chordelia.notes import Note
from chordelia.rhythm import Duration, Tempo, TimeSignature, COMMON_TIME


class Waveform(Enum):
    """Types of waveforms for synthesis."""
    SINE = "sine"
    SQUARE = "square"
    SAWTOOTH = "sawtooth"
    TRIANGLE = "triangle"


@dataclass
class PlaybackNote:
    """
    Represents a note to be played with timing information.
    
    Args:
        start_time: When to start playing (Duration or milliseconds)
        note: The Note to play (must have octave for frequency)
        duration: How long to play (Duration or milliseconds)
        velocity: Volume (0.0 to 1.0)
    """
    start_time: Union[Duration, float]
    note: Note
    duration: Union[Duration, float]
    velocity: float = 0.7
    
    def __post_init__(self):
        if self.velocity < 0.0 or self.velocity > 1.0:
            raise ValueError("Velocity must be between 0.0 and 1.0")
        
        if self.note.octave is None:
            raise ValueError("Note must have octave information for playback")


class AudioBackend:
    """
    Audio backend for playing sine waves using sounddevice.
    
    Handles low-level audio output, mixing, and real-time playback.
    """
    
    def __init__(self, sample_rate: int = 44100, buffer_size: int = 1024):
        if not AUDIO_AVAILABLE:
            raise ImportError(f"Audio dependencies not available: {MISSING_DEPS}")
        
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self._active_notes = {}  # note_id -> (frequency, amplitude, phase, envelope_pos)
        self._next_note_id = 0
        self._stream = None
        self._lock = threading.Lock()
        
        # Anti-crackling measures
        self._dc_filter_x = 0.0  # DC removal filter state
        self._dc_filter_y = 0.0
        self._dc_filter_alpha = 0.995  # High-pass filter coefficient
        self._lowpass_prev = 0.0  # Low-pass filter for smoothing
        
    def start(self):
        """Start the audio stream."""
        if self._stream is not None:
            return
            
        self._stream = sd.OutputStream(
            channels=1,
            samplerate=self.sample_rate,
            blocksize=self.buffer_size,
            callback=self._audio_callback,
            dtype=np.float32,
            latency='low'  # Request low latency
        )
        self._stream.start()
        
    def stop(self):
        """Stop the audio stream."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
            
        with self._lock:
            self._active_notes.clear()
    
    def play_note(self, frequency: float, duration: float, velocity: float = 0.7, 
                  waveform: Waveform = Waveform.SINE) -> int:
        """
        Start playing a note.
        
        Args:
            frequency: Frequency in Hz
            duration: Duration in seconds
            velocity: Volume (0.0 to 1.0)
            waveform: Type of waveform to generate
            
        Returns:
            Note ID for stopping the note early
        """
        with self._lock:
            note_id = self._next_note_id
            self._next_note_id += 1
            
            # Calculate envelope parameters (simple ADSR) - prevent clicks
            attack_time = max(0.005, min(0.02, duration * 0.05))  # 5-20ms attack
            decay_time = max(0.01, min(0.1, duration * 0.15))     # 10-100ms decay  
            release_time = max(0.01, min(0.05, duration * 0.2))   # 10-50ms release
            
            self._active_notes[note_id] = {
                'frequency': frequency,
                'amplitude': velocity,
                'phase': 0.0,
                'waveform': waveform,
                'start_time': time.time(),
                'duration': duration,
                'attack_time': attack_time,
                'decay_time': decay_time,
                'release_time': release_time,
                'sustain_level': 0.7
            }
            
            return note_id
    
    def stop_note(self, note_id: int):
        """Stop a playing note."""
        with self._lock:
            if note_id in self._active_notes:
                # Mark for release phase
                note = self._active_notes[note_id]
                current_time = time.time()
                note['release_start'] = current_time
    
    def _audio_callback(self, outdata: Any, frames: int, time_info: Any, status: Any):
        """Audio callback function for real-time audio generation."""
        outdata.fill(0)
        current_time = time.time()
        
        with self._lock:
            notes_to_remove = []
            
            # Scale amplitude based on number of active notes to prevent clipping
            num_active_notes = len(self._active_notes)
            volume_scale = 1.0 / max(1, num_active_notes * 0.7) if num_active_notes > 1 else 1.0
            
            for note_id, note in self._active_notes.items():
                elapsed = current_time - note['start_time']
                
                # Check if note should be finished
                if elapsed >= note['duration'] and 'release_start' not in note:
                    note['release_start'] = current_time
                
                # Calculate envelope
                amplitude = self._calculate_envelope(note, elapsed, current_time)
                
                if amplitude <= 0.001:  # Note finished
                    notes_to_remove.append(note_id)
                    continue
                
                # Generate waveform
                frequency = note['frequency']
                phase = note['phase']
                waveform = note['waveform']
                
                # Generate samples with volume scaling
                t = np.arange(frames) / self.sample_rate
                scaled_amplitude = amplitude * volume_scale
                if waveform == Waveform.SINE:
                    samples = scaled_amplitude * np.sin(2 * np.pi * frequency * t + phase)
                elif waveform == Waveform.SQUARE:
                    samples = scaled_amplitude * np.sign(np.sin(2 * np.pi * frequency * t + phase))
                elif waveform == Waveform.SAWTOOTH:
                    samples = scaled_amplitude * (2 * (frequency * t + phase / (2 * np.pi)) % 1 - 1)
                elif waveform == Waveform.TRIANGLE:
                    saw = 2 * (frequency * t + phase / (2 * np.pi)) % 1 - 1
                    samples = scaled_amplitude * (2 * np.abs(saw) - 1)
                else:
                    samples = scaled_amplitude * np.sin(2 * np.pi * frequency * t + phase)
                
                # Update phase for next callback
                note['phase'] = (phase + 2 * np.pi * frequency * frames / self.sample_rate) % (2 * np.pi)
                
                # Mix into output
                outdata[:, 0] += samples
            
            # Remove finished notes
            for note_id in notes_to_remove:
                del self._active_notes[note_id]
            
            # Apply soft clipping and DC removal
            self._apply_audio_processing(outdata[:, 0])
    
    def _apply_audio_processing(self, audio_buffer: "np.ndarray"):
        """Apply anti-crackling audio processing."""
        # 1. DC removal (high-pass filter)
        for i in range(len(audio_buffer)):
            # Simple first-order high-pass filter
            self._dc_filter_y = self._dc_filter_alpha * (self._dc_filter_y + audio_buffer[i] - self._dc_filter_x)
            self._dc_filter_x = audio_buffer[i]
            audio_buffer[i] = self._dc_filter_y
        
        # 2. Simple low-pass filter for smoothing (removes harsh high frequencies)
        lowpass_alpha = 0.7  # Cutoff around 8kHz at 44.1kHz sample rate
        for i in range(len(audio_buffer)):
            self._lowpass_prev = lowpass_alpha * self._lowpass_prev + (1 - lowpass_alpha) * audio_buffer[i]
            audio_buffer[i] = self._lowpass_prev
        
        # 3. Soft clipping using tanh function
        # This provides smooth saturation instead of hard clipping
        audio_buffer[:] = np.tanh(audio_buffer * 0.8) * 0.95
        
        # 4. Additional safety net - hard limit at ±0.98
        np.clip(audio_buffer, -0.98, 0.98, out=audio_buffer)
    
    def _calculate_envelope(self, note: dict, elapsed: float, current_time: float) -> float:
        """Calculate ADSR envelope amplitude."""
        attack_time = note['attack_time']
        decay_time = note['decay_time'] 
        sustain_level = note['sustain_level']
        release_time = note['release_time']
        amplitude = note['amplitude']
        
        # Check if in release phase
        if 'release_start' in note:
            release_elapsed = current_time - note['release_start']
            if release_elapsed >= release_time:
                return 0.0
            # Smooth exponential release curve
            release_factor = 1.0 - (release_elapsed / release_time)
            return amplitude * sustain_level * (release_factor * release_factor)
        
        # ADSR phases with smoother curves
        if elapsed < attack_time:
            # Attack phase - smooth curve using sine
            attack_progress = elapsed / attack_time
            smooth_attack = 0.5 * (1.0 - math.cos(math.pi * attack_progress))
            return amplitude * smooth_attack
        elif elapsed < attack_time + decay_time:
            # Decay phase - exponential curve
            decay_progress = (elapsed - attack_time) / decay_time
            smooth_decay = 1.0 - (decay_progress * decay_progress * (1.0 - sustain_level))
            return amplitude * smooth_decay
        else:
            # Sustain phase
            return amplitude * sustain_level


class Playback:
    """
    Main playback class for playing musical sequences.
    
    Handles timing, note scheduling, and integration with Chordelia's
    rhythm and note systems.
    """
    
    def __init__(self, tempo: Tempo, time_signature: TimeSignature = COMMON_TIME,
                 sample_rate: int = 44100, buffer_size: int = 1024,
                 default_waveform: Waveform = Waveform.SINE):
        """
        Initialize playback system.
        
        Args:
            tempo: Tempo for playback timing
            time_signature: Time signature for duration calculations
            sample_rate: Audio sample rate
            buffer_size: Audio buffer size
            default_waveform: Default waveform for all notes
        """
        self.tempo = tempo
        self.time_signature = time_signature
        self.default_waveform = default_waveform
        self._backend = AudioBackend(sample_rate, buffer_size) 
        self._playing = False
        self._start_time = None
        
    def play_sequence(self, notes: List[PlaybackNote], blocking: bool = True):
        """
        Play a sequence of notes with precise timing.
        
        Args:
            notes: List of PlaybackNote objects to play
            blocking: If True, wait for sequence to complete
        """
        if not AUDIO_AVAILABLE:
            raise ImportError(f"Audio dependencies not available: {MISSING_DEPS}")
            
        if self._playing:
            raise RuntimeError("Already playing a sequence")
        
        self._playing = True
        self._start_time = time.time()
        
        try:
            self._backend.start()
            
            # Schedule notes
            scheduled_notes = []
            for note in notes:
                start_ms = self._convert_to_milliseconds(note.start_time)
                duration_ms = self._convert_to_milliseconds(note.duration)
                
                scheduled_notes.append({
                    'note': note,
                    'start_time': start_ms / 1000.0,  # Convert to seconds
                    'duration': duration_ms / 1000.0,
                    'scheduled': False
                })
            
            # Sort by start time
            scheduled_notes.sort(key=lambda x: x['start_time'])
            
            if blocking:
                self._play_sequence_blocking(scheduled_notes)
            else:
                threading.Thread(target=self._play_sequence_blocking, 
                               args=(scheduled_notes,), daemon=True).start()
                
        except Exception as e:
            self._playing = False
            self._backend.stop()
            raise e
    
    def _play_sequence_blocking(self, scheduled_notes: List[dict]):
        """Play sequence in blocking mode with precise timing."""
        try:
            start_time = time.time()
            active_note_ids = []
            
            while scheduled_notes or active_note_ids:
                current_time = time.time() - start_time
                
                # Start notes that should begin now
                for note_data in scheduled_notes[:]:  # Copy list to avoid modification issues
                    if not note_data['scheduled'] and current_time >= note_data['start_time']:
                        playback_note = note_data['note']
                        frequency = playback_note.note.frequency
                        duration = note_data['duration']
                        velocity = playback_note.velocity
                        
                        note_id = self._backend.play_note(frequency, duration, velocity, self.default_waveform)
                        active_note_ids.append((note_id, current_time + duration))
                        note_data['scheduled'] = True
                        
                # Remove finished notes
                active_note_ids = [(nid, end_time) for nid, end_time in active_note_ids 
                                 if current_time < end_time]
                
                # Remove scheduled notes
                scheduled_notes = [n for n in scheduled_notes if not n['scheduled']]
                
                # Small sleep to avoid busy waiting
                time.sleep(0.001)
                
        finally:
            self._playing = False
            # Give a moment for notes to finish naturally
            time.sleep(0.2)
            self._backend.stop()
    
    def stop(self):
        """Stop playback immediately."""
        self._playing = False
        self._backend.stop()
    
    def _convert_to_milliseconds(self, time_value: Union[Duration, float]) -> float:
        """Convert Duration or milliseconds to milliseconds."""
        if isinstance(time_value, Duration):
            return time_value.to_milliseconds(self.tempo.bpm, self.time_signature)
        else:
            # Float values are already in milliseconds, pass through unchanged
            return float(time_value)

    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup."""
        self.stop()


# Convenience functions for common playback scenarios

def play_scale(scale, tempo: Tempo = Tempo(120), note_duration: Duration = None, 
               octave: int = 4) -> None:
    """
    Play a scale with equal note durations.
    
    Args:
        scale: Scale object to play
        tempo: Playback tempo
        note_duration: Duration of each note (default: quarter note)
        octave: Octave to play the scale in (only used if scale notes don't have octave info)
    """
    from chordelia.rhythm import quarter_note
    
    if note_duration is None:
        note_duration = quarter_note()
    
    notes = []
    current_time = Duration(0)

    if scale.root.octave is None:
        scale = scale.with_octave(octave)
    
    for note in scale.notes:
        notes.append(PlaybackNote(
            start_time=current_time,
            note=note,
            duration=note_duration,
            velocity=0.6
        ))
        
        current_time = current_time + note_duration
    
    with Playback(tempo) as player:
        player.play_sequence(notes)


def play_chord(chord, tempo: Tempo = Tempo(120), duration: Duration = None,
               octave: int = 4) -> None:
    """
    Play a chord with all notes starting simultaneously.
    
    Args:
        chord: Chord object to play
        tempo: Playback tempo  
        duration: Duration to hold the chord (default: whole note)
        octave: Base octave for the chord
    """
    from chordelia.rhythm import whole_note
    
    if duration is None:
        duration = whole_note()
    
    notes = []
    
    for i, chord_note in enumerate(chord.notes):
        # Distribute chord notes across octaves for better voice leading
        note_octave = octave + (i // 7)  # Move up octave every 7 notes
        note = chord_note.with_octave(note_octave)
        
        notes.append(PlaybackNote(
            start_time=Duration(0),  # All start at the same time
            note=note,
            duration=duration,
            velocity=0.5  # Slightly quieter for chord playback
        ))
    
    with Playback(tempo) as player:
        player.play_sequence(notes)


class ContinuousChordPlayer:
    """
    Continuous chord player that can update chord notes in real-time.
    
    Maintains a continuous audio stream and allows updating the current chord
    without interrupting playback. Provides smooth transitions between chords.
    """
    
    def __init__(self, sample_rate: int = 44100, buffer_size: int = 1024, 
                 base_octave: int = 4):
        """
        Initialize continuous chord player.
        
        Args:
            sample_rate: Audio sample rate
            buffer_size: Audio buffer size
            base_octave: Base octave for chord notes
        """
        if not AUDIO_AVAILABLE:
            raise ImportError(f"Audio dependencies not available: {MISSING_DEPS}")
            
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.base_octave = base_octave
        
        # Audio processing parameters
        self._waveform = Waveform.SINE
        self._filter_cutoff = 8000.0  # Default cutoff frequency in Hz
        self._filter_enabled = True
        
        # Thread-safe chord state (using RLock for reentrant access)
        self._chord_lock = threading.RLock()
        self._current_chord = None
        self._current_frequencies = []
        self._target_frequencies = []
        
        # Audio generation state
        self._phase_accumulators = {}  # Track phase for each frequency to maintain continuity
        self._sample_count = 0  # Track total samples generated for time calculation
        
        # Low-pass filter state (simple first-order filter)
        self._filter_prev = 0.0
        self._filter_alpha = self._calculate_filter_alpha(self._filter_cutoff)
        
        # Playback control
        self._stream = None
        self._is_playing = False
        self._should_stop = threading.Event()
        
    def _note_to_frequency(self, note: Note) -> float:
        """Convert a Note to its frequency in Hz."""
        if note.octave is None:
            # Default to base octave if not specified
            note = note.with_octave(self.base_octave)
            
        # A4 = 440 Hz, each semitone is 2^(1/12) ratio
        a4_midi = 69  # MIDI note number for A4
        note_midi = (note.octave + 1) * 12 + note.pitch_class
        
        return 440.0 * (2.0 ** ((note_midi - a4_midi) / 12.0))
    
    def _calculate_filter_alpha(self, cutoff_freq: float) -> float:
        """Calculate alpha coefficient for low-pass filter."""
        if cutoff_freq >= self.sample_rate / 2:
            return 1.0  # No filtering
        # RC = 1 / (2 * pi * cutoff_freq)
        # alpha = dt / (RC + dt) where dt = 1 / sample_rate
        dt = 1.0 / self.sample_rate
        rc = 1.0 / (2.0 * np.pi * cutoff_freq)
        return dt / (rc + dt)
    
    def _generate_waveform(self, frequency: float, t: "np.ndarray", phase: float) -> "np.ndarray":
        """Generate waveform samples based on current waveform type."""
        phase_signal = 2 * np.pi * frequency * t + phase
        
        if self._waveform == Waveform.SINE:
            return np.sin(phase_signal)
        elif self._waveform == Waveform.SQUARE:
            return np.sign(np.sin(phase_signal))
        elif self._waveform == Waveform.SAWTOOTH:
            return 2 * (frequency * t + phase / (2 * np.pi)) % 1 - 1
        elif self._waveform == Waveform.TRIANGLE:
            saw = 2 * (frequency * t + phase / (2 * np.pi)) % 1 - 1
            return 2 * np.abs(saw) - 1
        else:
            return np.sin(phase_signal)  # Default to sine
    
    def _apply_lowpass_filter(self, samples: "np.ndarray") -> "np.ndarray":
        """Apply simple first-order low-pass filter."""
        if not self._filter_enabled or self._filter_cutoff >= self.sample_rate / 2:
            return samples
        
        # Use local variable to avoid race conditions during parameter changes
        filter_state = self._filter_prev
        alpha = self._filter_alpha
        
        filtered = np.zeros_like(samples)
        for i in range(len(samples)):
            filter_state = alpha * samples[i] + (1 - alpha) * filter_state
            filtered[i] = filter_state
        
        # Update persistent state only once at the end
        self._filter_prev = filter_state
        return filtered
    
    def _apply_lowpass_filter_lockfree(self, samples: "np.ndarray", filter_enabled: bool, filter_cutoff: float, filter_alpha: float) -> "np.ndarray":
        """Apply simple first-order low-pass filter without locks."""
        if not filter_enabled or filter_cutoff >= self.sample_rate / 2:
            return samples
        
        # Use local variable to avoid race conditions during parameter changes
        filter_state = self._filter_prev
        
        filtered = np.zeros_like(samples)
        for i in range(len(samples)):
            filter_state = filter_alpha * samples[i] + (1 - filter_alpha) * filter_state
            filtered[i] = filter_state
        
        # Update persistent state only once at the end
        self._filter_prev = filter_state
        return filtered
    
    def _generate_chord_samples_lockfree(self, num_samples: int, current_frequencies: list, target_frequencies: list, waveform) -> "np.ndarray":
        """Generate audio samples for the current chord without locks."""
        if not current_frequencies and not target_frequencies:
            return np.zeros(num_samples, dtype=np.float32)
        
        # Always use target frequencies if they exist (including empty list for silence)
        frequencies = target_frequencies
        
        # Update current frequencies to target (immediate transition)
        self._current_frequencies = frequencies
        
        if not frequencies:
            return np.zeros(num_samples, dtype=np.float32)
        
        # Generate time array for this buffer
        t_start = self._sample_count / self.sample_rate
        t = np.linspace(t_start, t_start + (num_samples - 1) / self.sample_rate, num_samples)
        self._sample_count += num_samples
        
        # Generate and sum waveforms for each frequency
        samples = np.zeros(num_samples, dtype=np.float32)
        
        for freq in frequencies:
            if freq > 0:  # Skip invalid frequencies
                # Get or initialize phase accumulator for this frequency
                phase_key = f"{freq:.2f}"
                if phase_key not in self._phase_accumulators:
                    self._phase_accumulators[phase_key] = 0.0
                
                phase_start = self._phase_accumulators[phase_key]
                
                # Generate waveform samples
                waveform_samples = self._generate_waveform_lockfree(freq, t, phase_start, waveform)
                
                # Calculate amplitude with volume scaling
                amplitude = (0.3 / len(frequencies)) * 1.5  # Match original AudioBackend volume
                
                # Apply simple envelope to reduce clicks
                envelope = np.ones(num_samples)
                if len(frequencies) > 1:  # Only apply envelope for chord changes
                    attack_samples = min(int(0.005 * self.sample_rate), num_samples // 4)  # 5ms or 1/4 buffer
                    if attack_samples > 0:
                        envelope[:attack_samples] *= np.linspace(0, 1, attack_samples)  # Short attack
                        envelope[-attack_samples:] *= np.linspace(1, 0, attack_samples)  # Short release
                
                samples += amplitude * waveform_samples * envelope
                
                # Update phase accumulator (calculate final phase properly)
                phase_increment = 2 * np.pi * freq * num_samples / self.sample_rate
                self._phase_accumulators[phase_key] = (phase_start + phase_increment) % (2 * np.pi)
        
        return samples
    
    def _generate_waveform_lockfree(self, frequency: float, t: "np.ndarray", phase: float, waveform) -> "np.ndarray":
        """Generate waveform samples based on waveform type without locks."""
        phase_signal = 2 * np.pi * frequency * t + phase
        
        if waveform == Waveform.SINE:
            return np.sin(phase_signal)
        elif waveform == Waveform.SQUARE:
            return np.sign(np.sin(phase_signal))
        elif waveform == Waveform.SAWTOOTH:
            return 2 * (frequency * t + phase / (2 * np.pi)) % 1 - 1
        elif waveform == Waveform.TRIANGLE:
            saw = 2 * (frequency * t + phase / (2 * np.pi)) % 1 - 1
            return 2 * np.abs(saw) - 1
        else:
            return np.sin(phase_signal)  # Default to sine
    
    def _generate_chord_samples(self, num_samples: int) -> "np.ndarray":
        """Generate audio samples for the current chord."""
        if not self._current_frequencies and not self._target_frequencies:
            return np.zeros(num_samples, dtype=np.float32)
        
        # Update current frequencies immediately (no slow fade)
        if self._target_frequencies != self._current_frequencies:
            self._current_frequencies = self._target_frequencies.copy()
        
        # Generate samples for current chord at full volume
        samples = np.zeros(num_samples, dtype=np.float32)
        
        if self._current_frequencies:
            # Match original AudioBackend clipping prevention: 1.0 / (num_notes * 0.7)
            num_notes = len(self._current_frequencies)
            volume_scale = 1.0 / max(1, num_notes * 0.7) if num_notes > 1 else 1.0
            amplitude = 0.5 * volume_scale  # Match original velocity, full volume immediately
            
            for freq in self._current_frequencies:
                if freq > 0:  # Avoid silence
                    phase_key = f"freq_{freq}"
                    if phase_key not in self._phase_accumulators:
                        self._phase_accumulators[phase_key] = 0.0
                    
                    # Generate waveform based on current waveform type
                    t = np.arange(num_samples, dtype=np.float32) / self.sample_rate
                    phase_start = self._phase_accumulators[phase_key]
                    
                    # Generate waveform samples
                    waveform_samples = self._generate_waveform(freq, t, phase_start)
                    
                    # Apply very short envelope just to avoid clicks (5ms attack/release)
                    envelope = np.ones_like(t)
                    attack_samples = min(int(0.005 * self.sample_rate), num_samples // 4)  # 5ms or 1/4 buffer
                    if attack_samples > 0:
                        envelope[:attack_samples] *= np.linspace(0, 1, attack_samples)  # Short attack
                        envelope[-attack_samples:] *= np.linspace(1, 0, attack_samples)  # Short release
                    
                    samples += amplitude * waveform_samples * envelope
                    
                    # Update phase accumulator (calculate final phase properly)
                    phase_increment = 2 * np.pi * freq * num_samples / self.sample_rate
                    self._phase_accumulators[phase_key] = (phase_start + phase_increment) % (2 * np.pi)
        
        return samples
    
    def _audio_callback(self, outdata: "np.ndarray", frames: int, time, status):
        """Audio callback function for sounddevice."""
        if status:
            print(f"Audio callback status: {status}")
        
        try:
            # Create atomic snapshot of audio parameters to avoid blocking
            # This prevents deadlocks by not using locks in the audio callback
            current_frequencies = self._current_frequencies.copy() if self._current_frequencies else []
            target_frequencies = self._target_frequencies.copy() if self._target_frequencies else []
            waveform = self._waveform
            filter_cutoff = self._filter_cutoff
            filter_alpha = self._filter_alpha
            filter_enabled = self._filter_enabled
            
            # Generate samples with snapshot parameters
            samples = self._generate_chord_samples_lockfree(frames, current_frequencies, target_frequencies, waveform)
            
            # Apply filter with snapshot parameters
            samples = self._apply_lowpass_filter_lockfree(samples, filter_enabled, filter_cutoff, filter_alpha)
            
            # Apply soft clipping and limiting (like original AudioBackend)
            # Soft clipping using tanh function for smooth saturation
            samples = np.tanh(samples * 0.8) * 0.95
            # Hard limit as safety net
            samples = np.clip(samples, -0.98, 0.98)
            
            # Ensure proper shape for stereo output
            if hasattr(outdata, 'shape') and len(outdata.shape) > 1 and outdata.shape[1] == 2:  # Stereo
                outdata[:, 0] = samples
                outdata[:, 1] = samples
            elif hasattr(outdata, 'shape') and len(outdata.shape) == 1:  # Mono
                outdata[:] = samples
            else:
                # Fallback: try to handle as 1D array
                try:
                    outdata[:] = samples
                except:
                    print(f"Audio callback: unexpected outdata shape/type: {type(outdata)}")
                    outdata.fill(0)
                
        except Exception as e:
            print(f"Audio callback error: {e}")
            outdata.fill(0)  # Output silence on error
    
    def update_chord(self, chord):
        """
        Update the current chord for playback.
        
        Args:
            chord: Chord object to play, or None for silence
        """
        with self._chord_lock:
            # Store current chord for octave changes
            self._current_chord = chord
            
            if chord is None:
                self._target_frequencies = []
            else:
                # Convert chord notes to frequencies
                frequencies = []
                for i, note in enumerate(chord.notes):
                    # Distribute notes across octaves for better voicing
                    octave = self.base_octave + (i // 4)  # Move up every 4 notes
                    if note.octave is None:
                        note = note.with_octave(octave)
                    frequencies.append(self._note_to_frequency(note))
                
                self._target_frequencies = frequencies
            
            # No fade transition needed - chord changes are immediate
    
    def set_waveform(self, waveform: Waveform):
        """Set the waveform type for chord playback."""
        with self._chord_lock:
            self._waveform = waveform
    
    def set_filter_cutoff(self, cutoff_freq: float):
        """Set the low-pass filter cutoff frequency."""
        with self._chord_lock:
            self._filter_cutoff = cutoff_freq
            self._filter_alpha = self._calculate_filter_alpha(cutoff_freq)
            # Reset filter state to avoid artifacts
            self._filter_prev = 0.0
    
    def set_base_octave(self, octave: int):
        """Set the base octave for chord notes."""
        with self._chord_lock:
            self.base_octave = octave
            # Re-calculate frequencies for current chord if playing
            if hasattr(self, '_current_chord') and self._current_chord:
                # Trigger frequency recalculation by updating the chord
                chord = self._current_chord
                self._current_chord = None  # Force update
                self.update_chord(chord)
    
    def start(self):
        """Start continuous playback."""
        if self._is_playing:
            return
        
        try:
            self._stream = sd.OutputStream(
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                channels=2,  # Stereo
                dtype=np.float32,
                callback=self._audio_callback
            )
            self._stream.start()
            self._is_playing = True
            print("Continuous chord player started")
            
        except Exception as e:
            print(f"Failed to start continuous chord player: {e}")
            raise
    
    def stop(self):
        """Stop continuous playback."""
        if not self._is_playing:
            return
        
        self._should_stop.set()
        
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        
        self._is_playing = False
        print("Continuous chord player stopped")
    
    def is_playing(self) -> bool:
        """Check if playback is active."""
        return self._is_playing
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def play_melody(melody_notes: List[Tuple[Note, Duration]], tempo: Tempo = Tempo(120)) -> None:
    """
    Play a melody from a list of (note, duration) tuples.
    
    Args:
        melody_notes: List of (Note, Duration) tuples
        tempo: Playback tempo
    """
    notes = []
    current_time = Duration(0)
    
    for note, duration in melody_notes:
        if note.octave is None:
            raise ValueError("All notes must have octave information for playback")
            
        notes.append(PlaybackNote(
            start_time=current_time,
            note=note,
            duration=duration,
            velocity=0.7
        ))
        
        current_time = current_time + duration
    
    with Playback(tempo) as player:
        player.play_sequence(notes)
