


from pathlib import Path

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LEFT_PATH = ROOT / "models" / "candidates" / "357.joblib"
RIGHT_PATH = ROOT / "models" / "candidates" / "247.joblib"
OUT_PATH = ROOT / "models" / "candidates" / "blend_357_247.joblib"


class MaxRankBlend:
    

    def __init__(self, left, right) -> None:
        self.left = left
        self.right = right
        self.parts = ("357.joblib", "247.joblib")

    def score_year(self, path: Path, chunk: int = 40_000) -> np.ndarray:
        left = self.left.score_year(Path(path), chunk=chunk)
        right = self.right.score_year(Path(path), chunk=chunk)
        return np.maximum(left, right)


def main() -> None:
    
    blend = MaxRankBlend(joblib.load(LEFT_PATH), joblib.load(RIGHT_PATH))
    joblib.dump(blend, OUT_PATH)
    print(f"saved {OUT_PATH.name}", flush=True)


if __name__ == "__main__":
    main()
