# GestureMath — Hand-Powered Calculator

A next-level gesture-based math solver with a futuristic web UI.

## Project Structure
```
gesture_math/
├── app.py              ← Flask backend (CV logic)
├── requirements.txt    ← Python dependencies
└── templates/
    └── index.html      ← Futuristic frontend UI
```

## Setup & Run

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Run the app**
```bash
python app.py
```

3. **Open browser**
```
http://localhost:5000
```

## How to Use

| Fingers | Action        |
|---------|---------------|
| 1       | = SOLVE       |
| 2       | Input digit 2 |
| 3       | Input digit 3 |
| 4       | Add (+)       |
| 5       | Subtract (−)  |

- Place your hand inside the **green detection zone**
- Hold each gesture for **1.5 seconds** to register
- Show **1 finger** to solve the expression

## Bug Fixed from Original
- `upper_qqskin` typo → fixed to `upper_skin`
- Added `cos_angle` clamping to prevent `math.acos` domain errors
- Added `−` → `-` replacement before `eval()` for safe parsing
