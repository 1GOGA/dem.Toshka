"""Generates 11 production-ready DaVinci Resolve / Fusion .setting presets for dem.Toshka.

Presets:
1. Player_Outline_Subtle.setting
2. Player_Outline_Cyan.setting
3. Player_Outline_Gold.setting
4. Weapon_RimLight.setting
5. Hands_AccentGlow.setting
6. Sky_Cinematic_Grade.setting
7. Headshot_Impact.setting
8. ACE_Climax.setting
9. Motion_WhipPan.setting
10. Radial_Zoom_Impact.setting
11. SpeedRamp_Accent.setting
"""

import pathlib

presets_dir = pathlib.Path("assets/fusion_presets")
presets_dir.mkdir(parents=True, exist_ok=True)

# 1. Player_Outline_Subtle.setting
p1 = '''{
	Tools = ordered() {
		Player_Outline_Subtle = GroupOperator {
			CtrlWZoom = false,
			CustomData = {
				Path = {
					Map = {
						["Setting:"] = "FusionTemplates:/Edit/Effects/"
					}
				},
			},
			Inputs = ordered() {
				Input1 = InstanceInput {
					SourceOp = "MediaIn",
					Source = "Output",
				},
				RimWidth = InstanceInput {
					SourceOp = "ErodeDilate",
					Source = "FilterWidth",
					Default = 0.0015,
					Name = "Rim Edge Width",
				},
				GlowGain = InstanceInput {
					SourceOp = "Glow",
					Source = "Gain",
					Default = 1.35,
					Name = "Rim Glow Gain",
				},
			},
			Outputs = ordered() {
				Output1 = InstanceOutput {
					SourceOp = "MergeFinal",
					Source = "Output",
				},
			},
			ViewInfo = GroupInfo { Pos = { 0, 0 } },
			Tools = ordered() {
				MediaIn = PipeRouter {
					ViewInfo = PipeRouterInfo { Pos = { -220, 0 } },
				},
				EdgeDetect = EdgeDetect {
					Inputs = {
						Input = Input {
							SourceOp = "MediaIn",
							Source = "Output",
						},
						Threshold = Input { Value = 0.45, },
						Edges = Input { Value = 1, },
					},
					ViewInfo = OperatorInfo { Pos = { -110, -50 } },
				},
				ErodeDilate = DilateErode {
					Inputs = {
						Input = Input {
							SourceOp = "EdgeDetect",
							Source = "Output",
						},
						FilterWidth = Input { Value = 0.0015, },
					},
					ViewInfo = OperatorInfo { Pos = { 0, -50 } },
				},
				Glow = Glow {
					Inputs = {
						Input = Input {
							SourceOp = "ErodeDilate",
							Source = "Output",
						},
						Blend = Input { Value = 0.6, },
						Filter = Input { Value = 1, },
						Gain = Input { Value = 1.35, },
						Threshold = Input { Value = 0.5, },
					},
					ViewInfo = OperatorInfo { Pos = { 110, -50 } },
				},
				MergeFinal = Merge {
					Inputs = {
						Background = Input {
							SourceOp = "MediaIn",
							Source = "Output",
						},
						Foreground = Input {
							SourceOp = "Glow",
							Source = "Output",
						},
						ApplyMode = Input { Value = "Screen", },
						PerformDepthMerge = Input { Value = 0, },
					},
					ViewInfo = OperatorInfo { Pos = { 220, 0 } },
				},
			},
		}
	}
}
'''
(presets_dir / "Player_Outline_Subtle.setting").write_text(p1, encoding="utf-8")

# 2. Player_Outline_Cyan.setting
p2 = '''{
	Tools = ordered() {
		Player_Outline_Cyan = GroupOperator {
			Inputs = ordered() {
				Input1 = InstanceInput {
					SourceOp = "MediaIn",
					Source = "Output",
				},
			},
			Outputs = ordered() {
				Output1 = InstanceOutput {
					SourceOp = "MergeFinal",
					Source = "Output",
				},
			},
			Tools = ordered() {
				MediaIn = PipeRouter {
					ViewInfo = PipeRouterInfo { Pos = { -220, 0 } },
				},
				LumaKeyer = LumaKeyer {
					Inputs = {
						Input = Input { SourceOp = "MediaIn", Source = "Output", },
						High = Input { Value = 0.95, },
						Low = Input { Value = 0.55, },
					},
					ViewInfo = OperatorInfo { Pos = { -110, -40 } },
				},
				ColorTint = ColorCorrector {
					Inputs = {
						Input = Input { SourceOp = "LumaKeyer", Source = "Output", },
						CorrectionRange = Input { Value = 1, },
						MasterHue = Input { Value = 0.53, }, -- Cyan hue
						MasterSaturation = Input { Value = 1.8, },
						Gain = Input { Value = 1.5, },
					},
					ViewInfo = OperatorInfo { Pos = { 0, -40 } },
				},
				SoftGlow = SoftGlow {
					Inputs = {
						Input = Input { SourceOp = "ColorTint", Source = "Output", },
						Gain = Input { Value = 1.4, },
						GlowSize = Input { Value = 12.0, },
					},
					ViewInfo = OperatorInfo { Pos = { 110, -40 } },
				},
				MergeFinal = Merge {
					Inputs = {
						Background = Input { SourceOp = "MediaIn", Source = "Output", },
						Foreground = Input { SourceOp = "SoftGlow", Source = "Output", },
						ApplyMode = Input { Value = "Screen", },
					},
					ViewInfo = OperatorInfo { Pos = { 220, 0 } },
				},
			},
		}
	}
}
'''
(presets_dir / "Player_Outline_Cyan.setting").write_text(p2, encoding="utf-8")

# 3. Player_Outline_Gold.setting
p3 = '''{
	Tools = ordered() {
		Player_Outline_Gold = GroupOperator {
			Inputs = ordered() {
				Input1 = InstanceInput {
					SourceOp = "MediaIn",
					Source = "Output",
				},
			},
			Outputs = ordered() {
				Output1 = InstanceOutput {
					SourceOp = "MergeFinal",
					Source = "Output",
				},
			},
			Tools = ordered() {
				MediaIn = PipeRouter {
					ViewInfo = PipeRouterInfo { Pos = { -220, 0 } },
				},
				LumaKeyer = LumaKeyer {
					Inputs = {
						Input = Input { SourceOp = "MediaIn", Source = "Output", },
						Low = Input { Value = 0.60, },
					},
					ViewInfo = OperatorInfo { Pos = { -110, -40 } },
				},
				ColorTint = ColorCorrector {
					Inputs = {
						Input = Input { SourceOp = "LumaKeyer", Source = "Output", },
						MasterHue = Input { Value = 0.08, }, -- Gold/Amber
						MasterSaturation = Input { Value = 2.0, },
						Gain = Input { Value = 1.8, },
					},
					ViewInfo = OperatorInfo { Pos = { 0, -40 } },
				},
				Glow = Glow {
					Inputs = {
						Input = Input { SourceOp = "ColorTint", Source = "Output", },
						Gain = Input { Value = 1.8, },
						Glow = Input { Value = 0.8, },
					},
					ViewInfo = OperatorInfo { Pos = { 110, -40 } },
				},
				MergeFinal = Merge {
					Inputs = {
						Background = Input { SourceOp = "MediaIn", Source = "Output", },
						Foreground = Input { SourceOp = "Glow", Source = "Output", },
						ApplyMode = Input { Value = "Screen", },
					},
					ViewInfo = OperatorInfo { Pos = { 220, 0 } },
				},
			},
		}
	}
}
'''
(presets_dir / "Player_Outline_Gold.setting").write_text(p3, encoding="utf-8")

# 4. Weapon_RimLight.setting
p4 = '''{
	Tools = ordered() {
		Weapon_RimLight = GroupOperator {
			Inputs = ordered() {
				Input1 = InstanceInput { SourceOp = "MediaIn", Source = "Output", },
			},
			Outputs = ordered() {
				Output1 = InstanceOutput { SourceOp = "MergeFinal", Source = "Output", },
			},
			Tools = ordered() {
				MediaIn = PipeRouter { ViewInfo = PipeRouterInfo { Pos = { -200, 0 } }, },
				HighPass = HighPass {
					Inputs = {
						Input = Input { SourceOp = "MediaIn", Source = "Output", },
						FilterWidth = Input { Value = 0.002, },
					},
					ViewInfo = OperatorInfo { Pos = { -80, -40 } },
				},
				Brightness = BrightnessContrast {
					Inputs = {
						Input = Input { SourceOp = "HighPass", Source = "Output", },
						Gain = Input { Value = 1.6, },
						ClipBlack = Input { Value = 1, },
					},
					ViewInfo = OperatorInfo { Pos = { 40, -40 } },
				},
				MergeFinal = Merge {
					Inputs = {
						Background = Input { SourceOp = "MediaIn", Source = "Output", },
						Foreground = Input { SourceOp = "Brightness", Source = "Output", },
						ApplyMode = Input { Value = "Linear Light", },
					},
					ViewInfo = OperatorInfo { Pos = { 160, 0 } },
				},
			},
		}
	}
}
'''
(presets_dir / "Weapon_RimLight.setting").write_text(p4, encoding="utf-8")

# 5. Hands_AccentGlow.setting
p5 = '''{
	Tools = ordered() {
		Hands_AccentGlow = GroupOperator {
			Inputs = ordered() {
				Input1 = InstanceInput { SourceOp = "MediaIn", Source = "Output", },
			},
			Outputs = ordered() {
				Output1 = InstanceOutput { SourceOp = "MergeFinal", Source = "Output", },
			},
			Tools = ordered() {
				MediaIn = PipeRouter { ViewInfo = PipeRouterInfo { Pos = { -200, 0 } }, },
				MaskBottom = RectangleMask {
					Inputs = {
						Center = Input { Value = { 0.5, 0.2 }, },
						Width = Input { Value = 1.0, },
						Height = Input { Value = 0.45, },
						SoftEdge = Input { Value = 0.15, },
					},
					ViewInfo = OperatorInfo { Pos = { 0, -100 } },
				},
				FastGlow1 = FastGlow {
					Inputs = {
						Input = Input { SourceOp = "MediaIn", Source = "Output", },
						EffectMask = Input { SourceOp = "MaskBottom", Source = "Mask", },
						Gain = Input { Value = 1.25, },
						Threshold = Input { Value = 0.65, },
					},
					ViewInfo = OperatorInfo { Pos = { 0, -40 } },
				},
				MergeFinal = Merge {
					Inputs = {
						Background = Input { SourceOp = "MediaIn", Source = "Output", },
						Foreground = Input { SourceOp = "FastGlow1", Source = "Output", },
						Blend = Input { Value = 0.5, },
					},
					ViewInfo = OperatorInfo { Pos = { 160, 0 } },
				},
			},
		}
	}
}
'''
(presets_dir / "Hands_AccentGlow.setting").write_text(p5, encoding="utf-8")

# 6. Sky_Cinematic_Grade.setting
p6 = '''{
	Tools = ordered() {
		Sky_Cinematic_Grade = GroupOperator {
			Inputs = ordered() {
				Input1 = InstanceInput { SourceOp = "MediaIn", Source = "Output", },
			},
			Outputs = ordered() {
				Output1 = InstanceOutput { SourceOp = "MergeFinal", Source = "Output", },
			},
			Tools = ordered() {
				MediaIn = PipeRouter { ViewInfo = PipeRouterInfo { Pos = { -200, 0 } }, },
				SkyGradMask = RectangleMask {
					Inputs = {
						Center = Input { Value = { 0.5, 0.8 }, },
						Width = Input { Value = 1.0, },
						Height = Input { Value = 0.5, },
						SoftEdge = Input { Value = 0.25, },
					},
					ViewInfo = OperatorInfo { Pos = { 0, -100 } },
				},
				ColorGrade = ColorCorrector {
					Inputs = {
						Input = Input { SourceOp = "MediaIn", Source = "Output", },
						EffectMask = Input { SourceOp = "SkyGradMask", Source = "Mask", },
						MasterHue = Input { Value = 0.55, }, -- Deep Azure
						MasterSaturation = Input { Value = 1.25, },
						MasterGamma = Input { Value = 0.85, },
					},
					ViewInfo = OperatorInfo { Pos = { 0, -40 } },
				},
				MergeFinal = Merge {
					Inputs = {
						Background = Input { SourceOp = "MediaIn", Source = "Output", },
						Foreground = Input { SourceOp = "ColorGrade", Source = "Output", },
					},
					ViewInfo = OperatorInfo { Pos = { 160, 0 } },
				},
			},
		}
	}
}
'''
(presets_dir / "Sky_Cinematic_Grade.setting").write_text(p6, encoding="utf-8")

# 7. Headshot_Impact.setting
p7 = '''{
	Tools = ordered() {
		Headshot_Impact = GroupOperator {
			Inputs = ordered() {
				Input1 = InstanceInput { SourceOp = "MediaIn", Source = "Output", },
			},
			Outputs = ordered() {
				Output1 = InstanceOutput { SourceOp = "FlashGrade", Source = "Output", },
			},
			Tools = ordered() {
				MediaIn = PipeRouter { ViewInfo = PipeRouterInfo { Pos = { -150, 0 } }, },
				MicroPunch = Transform {
					Inputs = {
						Input = Input { SourceOp = "MediaIn", Source = "Output", },
						Size = Input { Value = 1.06, },
					},
					ViewInfo = OperatorInfo { Pos = { -30, 0 } },
				},
				FlashGrade = BrightnessContrast {
					Inputs = {
						Input = Input { SourceOp = "MicroPunch", Source = "Output", },
						Gain = Input { Value = 1.35, },
					},
					ViewInfo = OperatorInfo { Pos = { 90, 0 } },
				},
			},
		}
	}
}
'''
(presets_dir / "Headshot_Impact.setting").write_text(p7, encoding="utf-8")

# 8. ACE_Climax.setting
p8 = '''{
	Tools = ordered() {
		ACE_Climax = GroupOperator {
			Inputs = ordered() {
				Input1 = InstanceInput { SourceOp = "MediaIn", Source = "Output", },
			},
			Outputs = ordered() {
				Output1 = InstanceOutput { SourceOp = "VignetteNode", Source = "Output", },
			},
			Tools = ordered() {
				MediaIn = PipeRouter { ViewInfo = PipeRouterInfo { Pos = { -180, 0 } }, },
				WarmBloom = SoftGlow {
					Inputs = {
						Input = Input { SourceOp = "MediaIn", Source = "Output", },
						Gain = Input { Value = 1.25, },
						Threshold = Input { Value = 0.65, },
					},
					ViewInfo = OperatorInfo { Pos = { -60, 0 } },
				},
				VignetteNode = ColorCorrector {
					Inputs = {
						Input = Input { SourceOp = "WarmBloom", Source = "Output", },
						MasterGain = Input { Value = 1.05, },
						MasterSaturation = Input { Value = 1.15, },
					},
					ViewInfo = OperatorInfo { Pos = { 60, 0 } },
				},
			},
		}
	}
}
'''
(presets_dir / "ACE_Climax.setting").write_text(p8, encoding="utf-8")

# 9. Motion_WhipPan.setting
p9 = '''{
	Tools = ordered() {
		Motion_WhipPan = GroupOperator {
			Inputs = ordered() {
				Input1 = InstanceInput { SourceOp = "MediaIn", Source = "Output", },
			},
			Outputs = ordered() {
				Output1 = InstanceOutput { SourceOp = "DirBlur", Source = "Output", },
			},
			Tools = ordered() {
				MediaIn = PipeRouter { ViewInfo = PipeRouterInfo { Pos = { -150, 0 } }, },
				PanTransform = Transform {
					Inputs = {
						Input = Input { SourceOp = "MediaIn", Source = "Output", },
						Center = Input { Value = { 0.35, 0.5 }, },
					},
					ViewInfo = OperatorInfo { Pos = { -20, 0 } },
				},
				DirBlur = DirectionalBlur {
					Inputs = {
						Input = Input { SourceOp = "PanTransform", Source = "Output", },
						Angle = Input { Value = 0.0, },
						Length = Input { Value = 0.12, },
					},
					ViewInfo = OperatorInfo { Pos = { 100, 0 } },
				},
			},
		}
	}
}
'''
(presets_dir / "Motion_WhipPan.setting").write_text(p9, encoding="utf-8")

# 10. Radial_Zoom_Impact.setting
p10 = '''{
	Tools = ordered() {
		Radial_Zoom_Impact = GroupOperator {
			Inputs = ordered() {
				Input1 = InstanceInput { SourceOp = "MediaIn", Source = "Output", },
			},
			Outputs = ordered() {
				Output1 = InstanceOutput { SourceOp = "RadialBlur1", Source = "Output", },
			},
			Tools = ordered() {
				MediaIn = PipeRouter { ViewInfo = PipeRouterInfo { Pos = { -150, 0 } }, },
				ZoomTransform = Transform {
					Inputs = {
						Input = Input { SourceOp = "MediaIn", Source = "Output", },
						Size = Input { Value = 1.12, },
					},
					ViewInfo = OperatorInfo { Pos = { -20, 0 } },
				},
				RadialBlur1 = DirectionalBlur {
					Inputs = {
						Input = Input { SourceOp = "ZoomTransform", Source = "Output", },
						Length = Input { Value = 0.08, },
					},
					ViewInfo = OperatorInfo { Pos = { 100, 0 } },
				},
			},
		}
	}
}
'''
(presets_dir / "Radial_Zoom_Impact.setting").write_text(p10, encoding="utf-8")

# 11. SpeedRamp_Accent.setting
p11 = '''{
	Tools = ordered() {
		SpeedRamp_Accent = GroupOperator {
			Inputs = ordered() {
				Input1 = InstanceInput { SourceOp = "MediaIn", Source = "Output", },
			},
			Outputs = ordered() {
				Output1 = InstanceOutput { SourceOp = "DirBlur", Source = "Output", },
			},
			Tools = ordered() {
				MediaIn = PipeRouter { ViewInfo = PipeRouterInfo { Pos = { -150, 0 } }, },
				TimeScale = TimeSpeed {
					Inputs = {
						Input = Input { SourceOp = "MediaIn", Source = "Output", },
						Speed = Input { Value = 3.5, },
						InterpolateBetweenFrames = Input { Value = 1, },
					},
					ViewInfo = OperatorInfo { Pos = { -20, 0 } },
				},
				DirBlur = DirectionalBlur {
					Inputs = {
						Input = Input { SourceOp = "TimeScale", Source = "Output", },
						Length = Input { Value = 0.06, },
					},
					ViewInfo = OperatorInfo { Pos = { 100, 0 } },
				},
			},
		}
	}
}
'''
(presets_dir / "SpeedRamp_Accent.setting").write_text(p11, encoding="utf-8")

print(f"Generated 11 Fusion presets in {presets_dir}")
