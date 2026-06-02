"""Examples for first-class Degree support across Scale, Chord, and Interval."""

from chordelia import Chord, Degree, Interval, IntervalQuality, Scale, ScaleType


def scale_degree_examples() -> None:
    c_major = Scale("C", ScaleType.MAJOR)

    print("Scale degree lookup:")
    print("degree(1):", c_major.degree(1))
    print("degree('ii'):", c_major.degree("ii"))
    print("degree(Degree(5)):", c_major.degree(Degree(5)))

    print("\nMode selection:")
    print("mode_from_degree('iii'):", c_major.mode_from_degree("iii").name)


def harmonization_examples() -> None:
    c_major = Scale("C", ScaleType.MAJOR)

    ii = c_major.chord_for_degree("ii")
    v = c_major.chord_for_degree("V")
    i = c_major.chord_for_degree("I")

    print("\nDiatonic harmonization:")
    for chord in (ii, v, i):
        print(chord.name, [str(note) for note in chord.notes])

    progression = c_major.chords_for_degrees("ii", "V", "I")
    print("chords_for_degrees:", [chord.name for chord in progression])

    print("\nPost-construction refinement:")
    print("V7:", v.with_extension("7").name)


def chord_and_interval_examples() -> None:
    g7 = Chord("G").with_extension("7")

    print("\nChord degree helpers:")
    print("tone_at(1):", g7.tone_at(1))
    print("tone_at('III'):", g7.tone_at("III"))
    print("degree_for_tone(F):", g7.degree_for_tone(g7.tone_at(4)))

    major_ninth = Interval(IntervalQuality.MAJOR, 9)
    print("\nInterval degree helpers:")
    print("interval.degree:", major_ninth.degree)
    print("interval.simple_degree:", major_ninth.simple_degree)


if __name__ == "__main__":
    scale_degree_examples()
    harmonization_examples()
    chord_and_interval_examples()
