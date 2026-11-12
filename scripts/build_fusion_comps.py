import pathlib

FUSION_DIR = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX/fusion")
FUSION_DIR.mkdir(parents=True, exist_ok=True)

# 1. WhipPan_MotionBlur.comp
whip_pan_comp = """{
  Tools = ordered() {
    MediaIn1 = MediaIn {
      Inputs = {
        GlobalIn = Input { Value = 0, },
        GlobalOut = Input { Value = 30, },
        MediaID = Input { Value = "MediaIn1", },
      },
      ViewInfo = OperatorInfo { Pos = { 220, 165 } },
    },
    MediaIn2 = MediaIn {
      Inputs = {
        GlobalIn = Input { Value = 0, },
        GlobalOut = Input { Value = 30, },
        MediaID = Input { Value = "MediaIn2", },
      },
      ViewInfo = OperatorInfo { Pos = { 220, 264 } },
    },
    Dissolve1 = Dissolve {
      Transitions = {
        [0] = "DFMStatic",
        [1] = "DFMStatic"
      },
      Inputs = {
        Mix = Input {
          SourceOp = "MixSpline",
          Source = "Value",
        },
        Background = Input {
          SourceOp = "MediaIn1",
          Source = "Output",
        },
        Foreground = Input {
          SourceOp = "MediaIn2",
          Source = "Output",
        },
      },
      ViewInfo = OperatorInfo { Pos = { 385, 214 } },
    },
    MixSpline = BezierSpline {
      SplineColor = { Red = 16, Green = 154, Blue = 248 },
      KeyFrames = {
        [0] = { 0, RH = { 10, 0 } },
        [15] = { 0.5, LH = { 10, 0.2 }, RH = { 20, 0.8 } },
        [30] = { 1, LH = { 20, 1 } }
      }
    },
    Transform_Whip = Transform {
      Inputs = {
        MotionBlur = Input { Value = 1, },
        Quality = Input { Value = 8, },
        ShutterAngle = Input { Value = 240, },
        Center = Input {
          SourceOp = "CenterSpline",
          Source = "Value",
        },
        Edges = Input { Value = 3, }, -- Wrap edges
        Input = Input {
          SourceOp = "Dissolve1",
          Source = "Output",
        },
      },
      ViewInfo = OperatorInfo { Pos = { 550, 214 } },
    },
    CenterSpline = BezierSpline {
      SplineColor = { Red = 255, Green = 215, Blue = 0 },
      KeyFrames = {
        [0] = { { 0.5, 0.5 }, RH = { 10, { 0.45, 0.5 } } },
        [15] = { { -0.2, 0.5 }, LH = { 10, { 0.1, 0.5 } }, RH = { 20, { 0.9, 0.5 } } },
        [30] = { { 0.5, 0.5 }, LH = { 20, { 0.55, 0.5 } } }
      }
    },
    DirectionalBlur1 = DirectionalBlur {
      Inputs = {
        Type = Input { Value = 0, },
        Length = Input {
          SourceOp = "BlurLengthSpline",
          Source = "Value",
        },
        Angle = Input { Value = 0, },
        Input = Input {
          SourceOp = "Transform_Whip",
          Source = "Output",
        },
      },
      ViewInfo = OperatorInfo { Pos = { 715, 214 } },
    },
    BlurLengthSpline = BezierSpline {
      SplineColor = { Red = 255, Green = 50, Blue = 50 },
      KeyFrames = {
        [0] = { 0, RH = { 8, 0 } },
        [15] = { 0.085, LH = { 8, 0.04 }, RH = { 22, 0.04 } },
        [30] = { 0, LH = { 22, 0 } }
      }
    },
    MediaOut1 = MediaOut {
      Inputs = {
        Index = Input { Value = "0", },
        Input = Input {
          SourceOp = "DirectionalBlur1",
          Source = "Output",
        },
      },
      ViewInfo = OperatorInfo { Pos = { 880, 214 } },
    },
  }
}
"""

# 2. Directional_ZoomBlur.comp
zoom_blur_comp = """{
  Tools = ordered() {
    MediaIn1 = MediaIn {
      Inputs = {
        GlobalIn = Input { Value = 0, },
        GlobalOut = Input { Value = 24, },
        MediaID = Input { Value = "MediaIn1", },
      },
      ViewInfo = OperatorInfo { Pos = { 220, 165 } },
    },
    MediaIn2 = MediaIn {
      Inputs = {
        GlobalIn = Input { Value = 0, },
        GlobalOut = Input { Value = 24, },
        MediaID = Input { Value = "MediaIn2", },
      },
      ViewInfo = OperatorInfo { Pos = { 220, 264 } },
    },
    Dissolve1 = Dissolve {
      Transitions = {
        [0] = "DFMStatic",
        [1] = "DFMStatic"
      },
      Inputs = {
        Mix = Input {
          SourceOp = "DissolveSpline",
          Source = "Value",
        },
        Background = Input {
          SourceOp = "MediaIn1",
          Source = "Output",
        },
        Foreground = Input {
          SourceOp = "MediaIn2",
          Source = "Output",
        },
      },
      ViewInfo = OperatorInfo { Pos = { 385, 214 } },
    },
    DissolveSpline = BezierSpline {
      SplineColor = { Red = 0, Green = 200, Blue = 255 },
      KeyFrames = {
        [0] = { 0, RH = { 6, 0 } },
        [12] = { 0.5, LH = { 8, 0.3 }, RH = { 16, 0.7 } },
        [24] = { 1, LH = { 18, 1 } }
      }
    },
    Transform_Zoom = Transform {
      Inputs = {
        MotionBlur = Input { Value = 1, },
        Quality = Input { Value = 6, },
        ShutterAngle = Input { Value = 180, },
        Size = Input {
          SourceOp = "ZoomSizeSpline",
          Source = "Value",
        },
        Edges = Input { Value = 1, }, -- Duplicate edges
        Input = Input {
          SourceOp = "Dissolve1",
          Source = "Output",
        },
      },
      ViewInfo = OperatorInfo { Pos = { 550, 214 } },
    },
    ZoomSizeSpline = BezierSpline {
      SplineColor = { Red = 255, Green = 180, Blue = 0 },
      KeyFrames = {
        [0] = { 1.0, RH = { 6, 1.05 } },
        [12] = { 1.42, LH = { 8, 1.25 }, RH = { 16, 1.25 } },
        [24] = { 1.0, LH = { 18, 1.05 } }
      }
    },
    RadialBlur1 = DirectionalBlur {
      Inputs = {
        Type = Input { Value = 1, }, -- Radial Zoom Blur
        Length = Input {
          SourceOp = "RadialLengthSpline",
          Source = "Value",
        },
        Input = Input {
          SourceOp = "Transform_Zoom",
          Source = "Output",
        },
      },
      ViewInfo = OperatorInfo { Pos = { 715, 214 } },
    },
    RadialLengthSpline = BezierSpline {
      SplineColor = { Red = 255, Green = 100, Blue = 0 },
      KeyFrames = {
        [0] = { 0.0, RH = { 6, 0.0 } },
        [12] = { 0.12, LH = { 8, 0.06 }, RH = { 16, 0.06 } },
        [24] = { 0.0, LH = { 18, 0.0 } }
      }
    },
    MediaOut1 = MediaOut {
      Inputs = {
        Index = Input { Value = "0", },
        Input = Input {
          SourceOp = "RadialBlur1",
          Source = "Output",
        },
      },
      ViewInfo = OperatorInfo { Pos = { 880, 214 } },
    },
  }
}
"""

# 3. Impact_Flash_Chroma.comp
impact_flash_comp = """{
  Tools = ordered() {
    MediaIn1 = MediaIn {
      Inputs = {
        GlobalIn = Input { Value = 0, },
        GlobalOut = Input { Value = 18, },
        MediaID = Input { Value = "MediaIn1", },
      },
      ViewInfo = OperatorInfo { Pos = { 220, 214 } },
    },
    ColorCorrector_Flash = ColorCorrector {
      Inputs = {
        MasterRGBGain = Input {
          SourceOp = "FlashGainSpline",
          Source = "Value",
        },
        MasterRGBGamma = Input {
          SourceOp = "FlashGammaSpline",
          Source = "Value",
        },
        Input = Input {
          SourceOp = "MediaIn1",
          Source = "Output",
        },
      },
      ViewInfo = OperatorInfo { Pos = { 400, 214 } },
    },
    FlashGainSpline = BezierSpline {
      SplineColor = { Red = 255, Green = 255, Blue = 255 },
      KeyFrames = {
        [0] = { 1.0, RH = { 0.5, 2.5 } },
        [1] = { 3.6, LH = { 0.5, 2.5 }, RH = { 4, 2.2 } },
        [6] = { 1.5, LH = { 3, 2.0 }, RH = { 10, 1.2 } },
        [18] = { 1.0, LH = { 12, 1.05 } }
      }
    },
    FlashGammaSpline = BezierSpline {
      SplineColor = { Red = 200, Green = 200, Blue = 255 },
      KeyFrames = {
        [0] = { 1.0, RH = { 0.5, 1.3 } },
        [1] = { 1.45, LH = { 0.5, 1.3 }, RH = { 3, 1.2 } },
        [18] = { 1.0, LH = { 8, 1.02 } }
      }
    },
    SoftGlow1 = SoftGlow {
      Inputs = {
        Filter = Input { Value = 1, },
        Threshold = Input { Value = 0.65, },
        Gain = Input {
          SourceOp = "GlowGainSpline",
          Source = "Value",
        },
        GlowSize = Input { Value = 24.0, },
        Input = Input {
          SourceOp = "ColorCorrector_Flash",
          Source = "Output",
        },
      },
      ViewInfo = OperatorInfo { Pos = { 580, 214 } },
    },
    GlowGainSpline = BezierSpline {
      SplineColor = { Red = 255, Green = 220, Blue = 100 },
      KeyFrames = {
        [0] = { 0.0, RH = { 0.5, 1.5 } },
        [1] = { 2.4, LH = { 0.5, 1.5 }, RH = { 4, 1.2 } },
        [12] = { 0.0, LH = { 6, 0.4 } }
      }
    },
    Displace_Chroma = Displace {
      Inputs = {
        Type = Input { Value = 1, }, -- Radial chromatic displacement
        XOffset = Input {
          SourceOp = "ChromaSpline",
          Source = "Value",
        },
        YOffset = Input { Value = 0.0, },
        Input = Input {
          SourceOp = "SoftGlow1",
          Source = "Output",
        },
      },
      ViewInfo = OperatorInfo { Pos = { 760, 214 } },
    },
    ChromaSpline = BezierSpline {
      SplineColor = { Red = 0, Green = 255, Blue = 200 },
      KeyFrames = {
        [0] = { 0.0, RH = { 0.5, 0.015 } },
        [1] = { 0.024, LH = { 0.5, 0.015 }, RH = { 3, 0.012 } },
        [9] = { 0.0, LH = { 5, 0.004 } }
      }
    },
    MediaOut1 = MediaOut {
      Inputs = {
        Index = Input { Value = "0", },
        Input = Input {
          SourceOp = "Displace_Chroma",
          Source = "Output",
        },
      },
      ViewInfo = OperatorInfo { Pos = { 940, 214 } },
    },
  }
}
"""

(FUSION_DIR / "WhipPan_MotionBlur.comp").write_text(whip_pan_comp, encoding="utf-8")
(FUSION_DIR / "Directional_ZoomBlur.comp").write_text(zoom_blur_comp, encoding="utf-8")
(FUSION_DIR / "Impact_Flash_Chroma.comp").write_text(impact_flash_comp, encoding="utf-8")

readme = """# Fusion VFX Compositions Manifest

This directory contains production Blackmagic Fusion compositions for DaVinci Resolve.

## 1. WhipPan_MotionBlur.comp
- **Nodes:** MediaIn1, MediaIn2 -> Dissolve1 -> Transform_Whip (Wrap edges, Motion Blur, 240° shutter angle) -> DirectionalBlur1 (Keyframed Length 0.0 -> 0.085 -> 0.0) -> MediaOut1
- **Usage:** Used at 02.5s (Transition from Shoulder Approach to Hero POV) and 15.5s (Transition to Climax Orbit).

## 2. Directional_ZoomBlur.comp
- **Nodes:** MediaIn1, MediaIn2 -> Dissolve1 -> Transform_Zoom (Size 1.0 -> 1.42 -> 1.0, Motion Blur 180°) -> RadialBlur1 (Keyframed Length 0.0 -> 0.12 -> 0.0) -> MediaOut1
- **Usage:** Used at 11.7s (Fast zoom into Victim POV) and 13.1s (Snap back to Hero POV for 4K).

## 3. Impact_Flash_Chroma.comp
- **Nodes:** MediaIn1 -> ColorCorrector_Flash (Gain 3.6x spike on hit frame, decaying over 18 frames) -> SoftGlow1 (Threshold 0.65, GlowSize 24.0, Gain 2.4) -> Displace_Chroma (RGB prism split on edges) -> MediaOut1
- **Usage:** Applied at 12.41s on Frag 3 (Headshot on ProfyfGames) for impact emphasis.
"""
(FUSION_DIR / "README.md").write_text(readme, encoding="utf-8")

print("Created 3 Fusion compositions and README in renders/ACE_FINAL_V2_COLOR_VFX/fusion/")
