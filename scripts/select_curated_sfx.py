import json
import pathlib

matches = json.loads(pathlib.Path("scripts/categorized_gdc_matches.json").read_text(encoding="utf-8"))

curated_selection = {
    "1_cinematic_impacts": [
        ("bundle1", "344 Audio - Bass Drops & Downers Vol. 1/DSGNBass_Bass Drop & Downer Fast 16_344 Audio_Bass Drops & Downers.wav", "impact_sub_downer_fast16.wav", "Deep sub-bass impact transient for kill accent"),
        ("bundle1", "344 Audio - Bass Drops & Downers Vol. 1/DSGNBass_Bass Drop & Downer Medium 04_344 Audio_Bass Drops & Downers.wav", "impact_sub_downer_med04.wav", "Heavy sub-bass downer with extended cinematic tail"),
        ("bundle1", "344 Audio - Haunting Ambiences Vol. 3/METLImpt_Metal Bangs, Metal Hits, Banging On Doors_344 Audio_Haunting Ambiences Vol 3.wav", "impact_metal_bang_door.wav", "Heavy metallic strike with industrial resonance"),
        ("bundle1", "344 Audio - Historical Weapons Vol. 2/WEAPSwrd_Sword Slide Cuts, Metallic, Impact CM4 2_344 Audio_Medieval Weapons Vol 2.wav", "impact_metal_slice_cut.wav", "Crisp sharp metallic impact transient")
    ],
    "2_whooshes": [
        ("bundle1", "344 Audio - Air Designed/AEROJet_Blast Off Clean_344 Audio_Air Designed.wav", "whoosh_air_blast_clean.wav", "Fast airy jet-style whoosh with punchy envelope"),
        ("bundle1", "344 Audio - Elemental Palette Designed Vol. 1/WINDDsgn_Wind, Rush, Whoosh, Long x5 01_344 Audio_Elemental Palette Designed Vol 1.wav", "whoosh_wind_rush_long.wav", "Cinematic wind rush whoosh with smooth stereo pan"),
        ("bundle1", "344 Audio - Elemental Palette Designed Vol. 1/METLMisc_Metal, Slow Whoosh, Rattle, Pass By x4 01_344 Audio_Elemental Palette Designed Vol 1.wav", "whoosh_metal_passby.wav", "Metallic passby whoosh with tonal presence")
    ],
    "3_transitions": [
        ("bundle2", "Epic Stock Media - Synthesized Nature Loops and Sounds/WINDInt_Loop Weather Wind Whipping Constricted Flow Turbulent 01_ESM_SNLS.wav", "transition_wind_whip_turbulent.wav", "High-velocity air whip transition with fast decay"),
        ("bundle1", "344 Audio - Cinema Experience Vol. 1/FOODMisc_Broom Sweeping Up Snacks On Hard Floor 2_344 Audio_CInema Experience.wav", "transition_sweep_texture.wav", "Textured friction sweep for fast camera repositioning"),
        ("bundle2", "Alexander Kopeikin - 100 kHz Designed Ice/ice, crack, ice block snapping-001.wav", "transition_ice_crack_snap.wav", "Sharp transient snap for sudden camera cuts")
    ],
    "4_risers": [
        ("bundle2", "Alexander Kopeikin - Emotion and Magic/magic, drone, tension, spellbound, evanescence-002.wav", "riser_magic_drone_tension.wav", "Atmospheric tension riser with harmonic overtone build"),
        ("bundle2", "Federico Soler - Effective Trailer Alarms Vol. 2/EffectiveTrailer_Alarms_Vol2_QuarterNotes_013.wav", "riser_trailer_alarm_pulse.wav", "Rhythmic trailer alarm swell building tension before drop"),
        ("bundle1", "344 Audio - Cinematic Fight Vol. 1/FGHTGrab_Choking, Tension 03_344 Audio_Cinematic Fight Vol 1.wav", "riser_cinematic_tension_swell.wav", "Organic cinematic tension riser with rising frequency curve")
    ],
    "5_glitch_digital": [
        ("bundle2", "Epic Stock Media - HD Lock And Mechanism Sound Design Kit/MACHMech_Mechanism Counting Machine Interact Loose Container Short 01_ESM_HDLM.wav", "glitch_mechanism_counting_tick.wav", "Rapid mechanical clicks with digital UI texture"),
        ("bundle2", "Epic Stock Media - HD Lock And Mechanism Sound Design Kit/MECHLtch_Click Deep Mechanism Latch Button Nearfield Thunk 02_ESM_HDLM.wav", "glitch_latch_button_thunk.wav", "Punchy mechanical click thunk for killfeed event badge"),
        ("bundle2", "Epic Stock Media - HD Lock And Mechanism Sound Design Kit/METLTonl_Item Spring Wire Impact Flick Top Clatter Light Tap Roll Handling Short 01_ESM_HDLM.wav", "glitch_wire_flick_tap.wav", "High-frequency spring tap for UI badge notification")
    ],
    "6_atmospheric": [
        ("bundle1", "344 Audio - Ghostly Presences Vol. 1/AMBDsgn_Evil Spell Ambience_344 Audio_Ghostly Presences.wav", "atmos_dark_spell_drone.wav", "Subtle low-frequency ambient drone bed for intro atmosphere"),
        ("bundle1", "344 Audio - East Coast America Vol. 1/AMBSubn_Ambience, Forest Crickets, Birds, Connecticut 02_344 Audio_East Coast America.wav", "atmos_open_air_subtle.wav", "Open-air environmental acoustic texture")
    ],
    "7_gameplay_accents": [
        ("bundle1", "344 Audio - Climbing Gear Foley Vol. 1/EQUISprt_Climbing Gear, Carabiner, Screwing Lock 01_344 Audio_Climbing Gear Foley Vol 1.wav", "accent_carabiner_lock_turn.wav", "Crisp mechanical gear screw for weapon switch accent"),
        ("bundle1", "344 Audio - Climbing Gear Foley Vol. 1/EQUISprt_Climbing Gear, Flicking Carabiner On Rope_344 Audio_Climbing Gear Foley Vol 1.wav", "accent_flicking_metal_snap.wav", "Sharp metal flick transient for headshot confirmation"),
        ("bundle1", "344 Audio - Historical Weapons Vol. 2/WEAPArmr_Metal Shield Spin On Floor, Buckler MKH_344 Audio_Medieval Weapons Vol 2.wav", "accent_metal_ricochet_spin.wav", "High-frequency metallic spin and ricochet resonance")
    ]
}

out_p = pathlib.Path("scripts/curated_sfx_selection.json")
out_p.write_text(json.dumps(curated_selection, indent=2), encoding="utf-8")
print(f"Curated {sum(len(v) for v in curated_selection.values())} files across 7 categories.")
