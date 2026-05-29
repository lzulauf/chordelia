"""
Simple demonstration of Chordelia's playback functionality.

This shows how the playback module integrates with the rest of Chordelia
to provide musical playback capabilities.
"""

import sys

from chordelia import *


# Avoid UnicodeEncodeError on Windows code pages when examples print symbols.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def demonstrate_playback_integration():
    """Show how playback integrates with existing Chordelia modules."""
    
    print("Chordelia Playback Module Demonstration")
    print("=" * 40)
    
    # Check if playback is available
    try:
        from chordelia import Playback, PlaybackNote, play_scale
        print("✓ Playback module successfully imported!")
        print("  Note: Audio output requires: pip install sounddevice numpy")
    except ImportError as e:
        print(f"✗ Playback module not available: {e}")
        return
    
    print("\n1. Integration with Notes Module:")
    # Create notes with octaves (required for playback)
    notes = [Note("C4"), Note("E4"), Note("G4")]
    print(f"   Created notes: {[str(n) for n in notes]}")
    print(f"   Frequencies: {[f'{n.frequency:.1f}Hz' for n in notes]}")
    
    print("\n2. Integration with Rhythm Module:")
    # Create different durations
    durations = [quarter_note(), dotted(quarter_note()), half_note()]
    tempo = Tempo(120)
    time_sig = COMMON_TIME
    
    print(f"   Tempo: {tempo}")
    print(f"   Time Signature: {time_sig}")
    print("   Duration conversions to milliseconds:")
    for dur in durations:
        ms = dur.to_milliseconds(tempo.bpm, time_sig)
        print(f"     {dur} = {ms:.0f}ms")
    
    print("\n3. Integration with Scales Module:")
    # Create a scale for playback
    scale = Scale("G", ScaleType.MAJOR)
    print(f"   Scale: {scale}")
    print(f"   Notes: {[str(n) for n in scale.notes]}")
    
    print("\n4. Integration with Chords Module:")
    # Create chords for playback
    chords = [Chord.from_string(name) for name in ["G", "Em", "C", "D"]]
    print("   Chord progression:")
    for chord in chords:
        print(f"     {chord.name}: {[str(n) for n in chord.notes]}")
    
    print("\n5. PlaybackNote Creation:")
    # Demonstrate creating PlaybackNote objects
    try:
        from chordelia.audio_playback import PlaybackNote
        
        # Create a simple melody
        melody_data = [
            (Note("G4"), quarter_note()),
            (Note("A4"), quarter_note()),
            (Note("B4"), quarter_note()),
            (Note("C5"), half_note()),
        ]
        
        playback_notes = []
        current_time = Duration(0)
        
        for note, duration in melody_data:
            playback_note = PlaybackNote(
                start_time=current_time,
                note=note,
                duration=duration,
                velocity=0.7
            )
            playback_notes.append(playback_note)
            current_time = current_time + duration
        
        print("   Created PlaybackNote sequence:")
        for pn in playback_notes:
            start_ms = pn.start_time.to_milliseconds(tempo.bpm, time_sig) if isinstance(pn.start_time, Duration) else pn.start_time
            dur_ms = pn.duration.to_milliseconds(tempo.bpm, time_sig) if isinstance(pn.duration, Duration) else pn.duration
            print(f"     {pn.note} at {start_ms:.0f}ms for {dur_ms:.0f}ms (vel: {pn.velocity})")
        
    except Exception as e:
        print(f"   Error creating PlaybackNote: {e}")
    
    print("\n6. Available Playback Functions:")
    try:
        from chordelia.audio_playback import play_scale, play_chord, play_melody
        print("   ✓ play_scale() - Play scales with timing")
        print("   ✓ play_chord() - Play chords simultaneously") 
        print("   ✓ play_melody() - Play note sequences")
        print("   ✓ Playback class - Full control over playback timing")
    except ImportError:
        print("   ✗ Convenience functions not available")
    
    print("\n7. Musical Examples (would play with audio dependencies):")
    print("   - C major scale ascending")
    print("   - Jazz chord progression (Cmaj7-Am7-Dm7-G7)")
    print("   - Mary Had a Little Lamb melody")
    print("   - Arpeggios across multiple octaves")
    print("   - Complex rhythms with triplets and dotted notes")
    
    print("\nComplete Integration Summary:")
    print("✓ Notes: Frequency calculation for sine wave generation")
    print("✓ Rhythm: Precise timing conversion from musical to real time")
    print("✓ Scales: Automated scale playback with proper note selection")
    print("✓ Chords: Simultaneous note playback with voice leading")
    print("✓ Timing: Integration of Duration, Tempo, and TimeSignature")
    print("✓ ADSR: Attack-Decay-Sustain-Release envelope for natural sound")
    print("✓ Threading: Non-blocking playback with precise scheduling")
    print("✓ Context Management: Automatic cleanup of audio resources")
    
    print(f"\nTo enable audio playback, install dependencies:")
    print(f"  pip install sounddevice numpy")
    

if __name__ == "__main__":
    demonstrate_playback_integration()
