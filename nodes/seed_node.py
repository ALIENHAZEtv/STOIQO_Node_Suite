"""
[STOIQO] Smart Seed & Variance Controller Node
Essential deterministic seed manager with Krea 2 micro-variance control,
increment/decrement/randomize states, and pass-through string formatting.
"""

import random
import time


class StoiqoSeedControllerNode:
    """
    [STOIQO] Smart Seed & Variance Controller
    Provides rock-solid seed management for Krea 2, MiniMax, and generative workflows.
    Includes secondary variance delta to introduce controlled composition shifts
    without breaking character consistency or scene alignment.
    """

    CONTROL_MODES = [
        "randomize",
        "fixed",
        "increment",
        "decrement",
    ]

    def __init__(self):
        self.last_seed = None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "step": 1,
                        "tooltip": "Base integer seed. In randomize mode, this is regenerated on every run.",
                    },
                ),
                "control_mode": (
                    cls.CONTROL_MODES,
                    {
                        "default": "randomize",
                        "tooltip": "Seed lifecycle mode: randomize (new seed every run), fixed, increment (+1), decrement (-1).",
                    },
                ),
                "variance_strength": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Krea 2 micro-variance delta (0.0 = exact deterministic seed, >0.0 = structured perturbation).",
                    },
                ),
            },
            "optional": {
                "variance_seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "step": 1,
                        "tooltip": "Secondary seed for deterministic variance blending.",
                    },
                ),
                "seed_prefix": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "Optional prefix prepended to seed_str output (e.g. 'seed_').",
                    },
                ),
            },
        }

    RETURN_TYPES = ("INT", "INT", "FLOAT", "STRING")
    RETURN_NAMES = ("seed", "effective_seed", "variance_strength", "seed_str")
    FUNCTION = "resolve_seed"
    CATEGORY = "STOIQO"

    @classmethod
    def IS_CHANGED(cls, seed, control_mode, variance_strength, variance_seed=0, seed_prefix=""):
        if control_mode == "randomize":
            return float("nan")
        return f"{seed}_{control_mode}_{variance_strength}_{variance_seed}_{seed_prefix}"

    def resolve_seed(
        self,
        seed,
        control_mode,
        variance_strength,
        variance_seed=0,
        seed_prefix="",
    ):
        MAX_SEED = 0xFFFFFFFFFFFFFFFF

        # 1. Resolve primary seed based on control mode
        if control_mode == "randomize":
            active_seed = random.randint(0, MAX_SEED)
        elif control_mode == "increment":
            active_seed = (seed + 1) % MAX_SEED
        elif control_mode == "decrement":
            active_seed = (seed - 1) if seed > 0 else MAX_SEED
        else:
            # fixed mode
            active_seed = seed

        # 2. Compute effective seed if variance is applied (Krea 2 micro-variance)
        if variance_strength > 0.0:
            # Deterministic linear congruential perturbation based on secondary variance seed
            v_seed = variance_seed if variance_seed > 0 else (active_seed ^ 0x5DEECE66D)
            perturbation = int((v_seed % 1000003) * variance_strength)
            effective_seed = (active_seed + perturbation) % MAX_SEED
        else:
            effective_seed = active_seed

        seed_str = f"{seed_prefix}{active_seed}"

        return (active_seed, effective_seed, float(variance_strength), seed_str)
