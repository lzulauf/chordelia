"""
MIDI File Playback Example

This example demonstrates how to use Chordelia's MIDI module to:
1. Load and analyze MIDI files
2. Convert MIDI data to Chordelia's playback format
3. Play MIDI files using different waveforms
4. Extract and play individual tracks

For this example to work, you'll need:
1. A MIDI file (you can download free MIDI files from various sources)
2. The mido library installed: pip install mido
3. The sounddevice and numpy libraries for audio playback

Example MIDI files you can try:
- smells_like_teen_spirit.mid (included in examples directory)
- https://freemidi.org/
- Any .mid file you have on your system
"""

import os
import sys
from pathlib import Path


# Avoid UnicodeEncodeError on Windows code pages when examples print symbols.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Check if MIDI functionality is available
try:
    from chordelia import MidiFile, load_midi_file, play_midi_file
    MIDI_AVAILABLE = True
    print("🎹 MIDI module available!")
except ImportError as e:
    MIDI_AVAILABLE = False
    print(f"❌ MIDI module not available: {e}")
    print("Install dependencies: pip install mido")

# Check if playback is available
try:
    from chordelia import Playback, Waveform
    PLAYBACK_AVAILABLE = True
    print("🎵 Playback module available!")
except ImportError as e:
    PLAYBACK_AVAILABLE = False
    print(f"❌ Playback module not available: {e}")
    print("Install dependencies: pip install sounddevice numpy")


def create_sample_midi():
    """Create a simple MIDI file for testing purposes."""
    try:
        import mido
        
        # Create a new MIDI file
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        # Set tempo to 120 BPM
        track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(120)))
        
        # Add a simple melody: C-D-E-F-G-A-B-C (C major scale)
        notes = [60, 62, 64, 65, 67, 69, 71, 72]  # MIDI note numbers
        
        for i, note in enumerate(notes):
            # Note on
            track.append(mido.Message('note_on', channel=0, note=note, velocity=64, time=0))
            # Note off after 480 ticks (quarter note at 480 ticks per beat)
            track.append(mido.Message('note_off', channel=0, note=note, velocity=64, time=480))
        
        # Save the file
        sample_path = "sample_scale.mid"
        mid.save(sample_path)
        print(f"✅ Created sample MIDI file: {sample_path}")
        return sample_path
        
    except ImportError:
        print("❌ Cannot create sample MIDI - mido not available")
        return None


def analyze_midi_file(filepath: str):
    """Analyze and display information about a MIDI file."""
    if not MIDI_AVAILABLE:
        print("❌ MIDI functionality not available")
        return None
        
    try:
        print(f"\n🔍 ANALYZING MIDI FILE: {filepath}")
        print("=" * 50)
        
        # Load the MIDI file
        midi = MidiFile(filepath)
        
        # Print basic information
        midi.print_info()
        
        return midi
        
    except FileNotFoundError:
        print(f"❌ MIDI file not found: {filepath}")
        return None
    except Exception as e:
        print(f"❌ Error loading MIDI file: {e}")
        return None


def play_midi_with_different_waveforms(filepath: str):
    """Demonstrate playing the same MIDI file with different waveforms."""
    if not (MIDI_AVAILABLE and PLAYBACK_AVAILABLE):
        print("❌ MIDI or playback functionality not available")
        return
        
    try:
        midi = MidiFile(filepath)
        
        # Different waveforms to try
        waveforms = [
            (Waveform.SINE, "🌊 Sine wave (pure, clean tone)"),
            (Waveform.TRIANGLE, "🔺 Triangle wave (soft, mellow)"),
            (Waveform.SAWTOOTH, "🪚 Sawtooth wave (bright, buzzy)"),
            (Waveform.SQUARE, "⬜ Square wave (hollow, retro)"),
        ]
        
        print(f"\n🎵 PLAYING WITH DIFFERENT WAVEFORMS")
        print("=" * 40)
        
        for waveform, description in waveforms:
            print(f"\n{description}")
            input("Press Enter to play, or Ctrl+C to skip...")
            
            try:
                # Convert MIDI to playback notes with the specified waveform
                notes = midi.to_playback_notes(waveform=waveform)
                
                # Play the notes
                with Playback(midi.tempo) as playback:
                    playback.play_sequence(notes, blocking=True)
                    
            except KeyboardInterrupt:
                print("⏭️  Skipped")
                continue
                
    except Exception as e:
        print(f"❌ Error playing MIDI: {e}")


def play_individual_tracks(filepath: str):
    """Demonstrate playing individual tracks from a MIDI file."""
    if not (MIDI_AVAILABLE and PLAYBACK_AVAILABLE):
        print("❌ MIDI or playback functionality not available")
        return
        
    try:
        midi = MidiFile(filepath)
        
        if len(midi.tracks_info) <= 1:
            print("🎵 MIDI file has only one track")
            return
            
        print(f"\n🎼 PLAYING INDIVIDUAL TRACKS")
        print("=" * 35)
        
        for i, track_info in enumerate(midi.tracks_info):
            print(f"\n🎵 Track {i}: {track_info.name}")
            print(f"   Notes: {track_info.note_count}")
            
            if track_info.note_count == 0:
                print("   (No notes to play)")
                continue
                
            response = input("Play this track? (y/n/q): ").lower()
            
            if response == 'q':
                break
            elif response == 'y':
                try:
                    # Get notes for this specific track
                    notes = midi.get_track_notes(i, waveform=Waveform.SINE)
                    
                    if notes:
                        print(f"   Playing {len(notes)} notes...")
                        with Playback(midi.tempo) as playback:
                            playback.play_sequence(notes, blocking=True)
                    else:
                        print("   No playable notes found")
                        
                except KeyboardInterrupt:
                    print("   ⏹️  Stopped")
                    
    except Exception as e:
        print(f"❌ Error playing tracks: {e}")


def main():
    """Main example function."""
    print("🎹 CHORDELIA MIDI PLAYBACK EXAMPLE")
    print("=" * 40)
    non_interactive = (
        not sys.stdin.isatty()
        or not sys.stdout.isatty()
        or os.environ.get("CHORDELIA_NONINTERACTIVE") == "1"
    )

    def safe_input(prompt: str, default: str = "") -> str:
        """Read input safely and return default if stdin is unavailable."""
        try:
            return input(prompt)
        except EOFError:
            return default
    
    if not (MIDI_AVAILABLE and PLAYBACK_AVAILABLE):
        print("❌ Required modules not available")
        print("Please install: pip install mido sounddevice numpy")
        return
    
    # Try to find a MIDI file to use
    midi_file = None
    
    # Option 1: Look for MIDI files in current directory and examples directory
    current_dir = Path(".")
    examples_dir = Path("examples")
    
    midi_files = (list(current_dir.glob("*.mid")) + 
                 list(current_dir.glob("*.midi")) +
                 list(examples_dir.glob("*.mid")) + 
                 list(examples_dir.glob("*.midi")))
    
    if midi_files:
        print(f"🎵 Found MIDI files in current directory:")
        for i, filepath in enumerate(midi_files[:5]):  # Show first 5
            print(f"  {i+1}. {filepath.name}")

        if non_interactive:
            midi_file = str(midi_files[0])
            print("Non-interactive mode detected: using the first MIDI file.")
        else:
            try:
                choice = safe_input("\nSelect a file (1-{}) or press Enter to create sample: ".format(len(midi_files)))
                if choice.strip() and choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(midi_files):
                        midi_file = str(midi_files[idx])
            except ValueError:
                pass
    
    # Option 2: Create a sample MIDI file
    if not midi_file:
        print("\n📝 Creating sample MIDI file...")
        midi_file = create_sample_midi()
    
    if not midi_file:
        print("❌ No MIDI file available for testing")
        return
    
    # Analyze the MIDI file
    midi = analyze_midi_file(midi_file)
    if not midi:
        return

    if non_interactive:
        print("\nNon-interactive mode detected: skipping interactive playback menu.")
        if midi_file == "sample_scale.mid" and os.path.exists(midi_file):
            try:
                os.remove(midi_file)
                print(f"🗑️  Cleaned up sample file: {midi_file}")
            except Exception:
                pass
        return
    
    print("\n🎵 DEMO OPTIONS")
    print("=" * 20)
    print("1. Play with different waveforms")
    print("2. Play individual tracks")
    print("3. Simple playback (sine wave)")
    print("4. Quit")
    
    while True:
        try:
            choice = safe_input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                play_midi_with_different_waveforms(midi_file)
            elif choice == "2":
                play_individual_tracks(midi_file)
            elif choice == "3":
                print("\n🎵 Playing MIDI file...")
                play_midi_file(midi_file, waveform=Waveform.SINE)
            elif choice == "4":
                break
            else:
                print("❌ Invalid choice")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Cleanup sample file if we created it
    if midi_file == "sample_scale.mid" and os.path.exists(midi_file):
        try:
            os.remove(midi_file)
            print(f"🗑️  Cleaned up sample file: {midi_file}")
        except:
            pass


if __name__ == "__main__":
    main()
