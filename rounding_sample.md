# 📘 Why 1.7 Does *Not* Become 2 When Rounding to 2 Decimal Places  
### _Mathematical Explanation for QA & Management_

---

## 🧮 1. What Does Rounding Mean?

When rounding a number, the **number of decimal places** determines **which digit is used for the rounding decision**.

> **If rounding to N decimal places → check the (N+1)-th decimal place.**  
> - If that digit is **≥ 5**, round up  
> - If that digit is **< 5**, keep the digit unchanged

---

## 🎯 2. Why 1.7 Does *Not* Become 2 When Rounding to 2 Decimal Places

### Step 1 — Expand to 2 decimals
```
1.7 → 1.70
```

### Step 2 — Identify rounding digit  
For 2 decimals, check the **3rd decimal place**:
```
1.700000
       ^
       0  (3rd decimal)
```

### Step 3 — Apply rounding rule  
Since:
```
0 < 5
```
➡️ Do **not** round up.

### ✅ Final Result  
```
1.70
```

---

## 🎯 3. Why 1.7 *Does* Become 2 When Rounding to 0 Decimal Places

Rounding to **0 decimals** means checking the **1st decimal place**:
```
1.7
   ^
   7
```

Since:
```
7 ≥ 5
```
➡️ Round up.

### ✅ Final Result  
```
1.7 → 2
```

---

## 📊 4. Summary Table

| Rounding Setting | Digit Checked | Result for 1.7 |
|------------------|---------------|----------------|
| **0 decimals** | 1st decimal → 7 | **2** |
| **1 decimal** | 2nd decimal → 0 | **1.7** |
| **2 decimals** | 3rd decimal → 0 | **1.70** |
| **3 decimals** | 4th decimal → 0 | **1.700** |

---

## 🧠 5. Ceil and Floor Explanation (Important for QA)

### ✔ **Ceil (Ceiling Function)**  
Ceil always rounds **up to the nearest integer**, regardless of decimal value.

Examples:
```
ceil(1.1) = 2  
ceil(1.7) = 2  
ceil(1.0001) = 2  
ceil(-1.2) = -1   (moves toward +∞)
```

> **Ceil does NOT consider decimal places — it always "pushes up".**

---

### ✔ **Floor (Floor Function)**  
Floor always rounds **down to the nearest integer**, regardless of decimal value.

Examples:
```
floor(1.9) = 1  
floor(1.1) = 1  
floor(-1.2) = -2  (moves toward -∞)
```

> **Floor does NOT consider decimal places — it always "pushes down".**

---

### 📌 Key Difference from Decimal Rounding  
| Method | Behavior |
|--------|----------|
| **Round(n decimals)** | Only affects digits *after* the rounding position |
| **Ceil()** | Always goes upward to next integer |
| **Floor()** | Always goes downward to previous integer |

---

## 📌 Executive Summary

> **1.7 becomes 2 ONLY when rounding to 0 decimals or using ceil().  
> For rounding to 2 decimals, the rounding decision happens at the 3rd decimal place,  
> which is 0 — so the integer part never changes.**

---

## ✔ This markdown file is ready to share with QA & Management.

