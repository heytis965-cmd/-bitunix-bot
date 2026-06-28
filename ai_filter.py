import json
import os
import math

MODEL_FILE = os.path.join(os.path.dirname(__file__), "ai_model.json")


def load_model():
    try:
        with open(MODEL_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "weights": {
                "score_strength": 0.3,
                "confirmations": 0.25,
                "trend_align": 0.2,
                "volume": 0.1,
                "rsi_position": 0.1,
                "pump_dump": 0.05,
                "bb_position": 0.0,
                "trend_strength": 0.0,
                "candle_pattern": 0.0,
            },
            "bias": 0.0,
            "history": [],
            "min_confidence": 0.50,
            "total_trades": 0,
            "correct": 0,
            "learning_rate": 0.08,
            "adaptive_threshold": True,
            "performance_window": 20,
        }


def save_model(model):
    try:
        with open(MODEL_FILE, "w") as f:
            json.dump(model, f, indent=2)
    except Exception:
        pass


def sigmoid(x):
    return 1 / (1 + math.exp(-max(-10, min(10, x))))


def extract_features(signal, analysis):
    score = signal.get("score", 0)
    confirmations = signal.get("confirmations", 0)
    threshold = signal.get("threshold", 4)
    direction = signal["signal"]

    mtf = signal.get("mtf", {})
    trend_aligned = 0
    if mtf.get("4h", 0) > 0 and direction == "LONG":
        trend_aligned = 1
    elif mtf.get("4h", 0) < 0 and direction == "SHORT":
        trend_aligned = 1
    elif mtf.get("4h", 0) == 0:
        trend_aligned = 0.5

    if not isinstance(analysis, dict):
        analysis = {}

    vol_ratio = analysis.get("vol_ratio", 1.0)
    vol_score = min(vol_ratio / 3.0, 1.0)

    rsi = analysis.get("rsi", 50)
    if direction == "LONG":
        rsi_score = max(0, (50 - rsi) / 30)
    else:
        rsi_score = max(0, (rsi - 50) / 30)

    pd = analysis.get("pump_dump", {})
    pd_score = 0
    if direction == "LONG" and pd.get("pump"):
        pd_score = min(pd.get("pump_s", 0) / 10, 1.0)
    elif direction == "SHORT" and pd.get("dump"):
        pd_score = min(pd.get("dump_s", 0) / 10, 1.0)

    bb_pos = analysis.get("bb_position", 50)
    bb_score = 0
    if direction == "LONG" and bb_pos < 30:
        bb_score = (30 - bb_pos) / 30
    elif direction == "SHORT" and bb_pos > 70:
        bb_score = (bb_pos - 70) / 30

    trend_str = analysis.get("trend_strength", 0)
    ts_score = min(abs(trend_str) / 30, 1.0) if (trend_str > 0 and direction == "UP") or (trend_str < 0 and direction == "DOWN") else 0

    candle = analysis.get("candle_score", 0)
    candle_score = 0
    if direction == "LONG" and candle > 0: candle_score = 1.0
    elif direction == "SHORT" and candle < 0: candle_score = 1.0

    return {
        "score_strength": min(score / max(threshold, 1), 2.0) / 2.0,
        "confirmations": min(confirmations / 7.0, 1.0),
        "trend_align": trend_aligned,
        "volume": vol_score,
        "rsi_position": rsi_score,
        "pump_dump": pd_score,
        "bb_position": bb_score,
        "trend_strength": ts_score,
        "candle_pattern": candle_score,
    }


def evaluate_signal(signal, analysis):
    model = load_model()
    features = extract_features(signal, analysis)
    weights = model["weights"]

    raw_score = sum(features[k] * weights.get(k, 0) for k in features) + model.get("bias", 0)
    confidence = sigmoid(raw_score)

    min_conf = model.get("min_confidence", 0.42)
    approved = confidence >= min_conf

    recent = model.get("history", [])[-model.get("performance_window", 20):]
    if len(recent) >= 10:
        recent_wr = sum(1 for h in recent if h["won"]) / len(recent)
        if recent_wr > 0.60:
            model["min_confidence"] = max(0.38, min_conf - 0.01)
        elif recent_wr < 0.35:
            model["min_confidence"] = min(0.45, min_conf + 0.005)
        min_conf = model.get("min_confidence", 0.42)
        approved = confidence >= min_conf

    return {
        "approved": approved,
        "confidence": round(confidence, 3),
        "min_confidence": min_conf,
        "features": features,
        "raw_score": round(raw_score, 3),
    }


def learn_from_trade(signal, analysis, won):
    model = load_model()
    features = extract_features(signal, analysis)

    lr = model.get("learning_rate", 0.08)
    target = 1.0 if won else 0.0
    raw_score = sum(features[k] * model["weights"].get(k, 0) for k in features) + model.get("bias", 0)
    predicted = sigmoid(raw_score)
    error = target - predicted

    for k in features:
        model["weights"][k] = max(-2, min(2, model["weights"].get(k, 0) + lr * error * features[k]))
    model["bias"] = max(-2, min(2, model.get("bias", 0) + lr * error))

    model["total_trades"] = model.get("total_trades", 0) + 1
    if won:
        model["correct"] = model.get("correct", 0) + 1

    total = model["total_trades"]
    if total > 10:
        wr = model["correct"] / total
        model["min_confidence"] = max(0.38, min(0.45, 0.42 - (wr - 0.5) * 0.1))

    model["history"].append({"features": features, "won": won, "confidence": round(predicted, 3)})
    if len(model["history"]) > 300:
        model["history"] = model["history"][-300:]

    if total > 20 and total % 10 == 0:
        recent = model["history"][-20:]
        recent_wr = sum(1 for h in recent if h["won"]) / len(recent)
        if recent_wr < 0.40:
            model["learning_rate"] = min(0.15, lr + 0.02)
        elif recent_wr > 0.70:
            model["learning_rate"] = max(0.03, lr - 0.01)

    save_model(model)
    return predicted
