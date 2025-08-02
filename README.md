# Automated-Zoom-and-Focus-Control

# AI-Driven Integrated Zoom and Focus Control System for Enhanced OCC Performance
*Military Drone OCC Project*

## 1. Introduction

In high-mobility environments such as military drone-based Optical Camera Communication (OCC) systems, maintaining sharp image focus and accurate framing is essential for preserving data link reliability and situational awareness.

Zoom and focus adjustments are traditionally performed manually through software interfaces, which require constant operator involvement. While precise, this method lacks scalability and real-time responsiveness.

Existing methods offer limited automation but fall short in dynamic adaptability and low-latency performance. They require manual tuning and exhibit slow convergence in high-mobility scenarios.

To overcome these limitations, we present a novel **AI-based automated zoom and focus control system**, combining real-time object detection, feedback-based control, and mathematical modeling through **curve fitting**. The system achieves dynamic, low-latency optical control and is optimized for autonomous drone OCC applications.

<p align="center">
  <img src="https://github.com/user-attachments/assets/25369079-a415-4892-9fc4-aa86b5878c33" alt="Manual Control Platform" width="600"/>
  <br>
  <em>Figure: Interface of the manual control platform for zoom and focus adjustment.</em>
</p>

---

## 2. Proposed Methodology

### 2.1 System Overview

<p align="center">
  <img src="https://github.com/user-attachments/assets/e26b0afa-b9df-4537-9747-c1bde31f3ea4" alt="Implementation Diagram" width="500"/>
  <br>
  <em>Figure: System implementation of the AI-driven zoom and focus control mechanism using ROI.</em>
</p>


- **Real-time feedback loop** using ROI (Region of interest)
- **Motor control** using time-stepped DC motor signals
- **Focus prediction model** using polynomial curve fitting
- **Adaptive correction loop** with moving average filtering and timeout safety

<p align="center">
  <img src="https://github.com/user-attachments/assets/cc56f7d3-1573-4046-b825-ea7da2d12d1c" alt="Zoom In/Out Command Interface" width="600"/>
  <br>
  <em>Figure: Proposed Zoom in and zoom out operations for automated control.</em>
</p>


---

### 2.2 Motor Control Logic

- **Zoom Motor**: Incremental steps of about 30 ms
- **Focus Motor**: Incremental steps of about 10 ms
- **Control Logic**:
  - Forward: `IN1 = HIGH`, `IN2 = LOW`
  - Backward: `IN1 = LOW`, `IN2 = HIGH`
  - Stop: `IN1 = LOW`, `IN2 = LOW`

**Moving Average Filtering** (for noise suppression):
x̄(t) = (1/N) * Σ x(t - i)

---

### 2.3 Curve Fitting for Focus Prediction

We model the focus value as a function of zoom using a **5th-degree polynomial**:
F(Z) = a₀ + a₁Z + a₂Z² + a₃Z³ + a₄Z⁴ + a₅Z⁵


#### Least Squares Estimation:

To find the coefficients `a₀` to `a₅`, we minimize the squared error:

Matrix form solution:
a = (Aᵀ·A)⁻¹ · Aᵀ·F


Where:
- `A` is the Vandermonde matrix of zoom inputs
- `F` is the vector of observed focus values

#### Least Squares Cost Function:

To fit the polynomial curve, we minimize the following cost function:

$$
J(\mathbf{a}) = \sum_{i=1}^{n} \left(F_i - \left(a_0 + a_1 Z_i + a_2 Z_i^2 + a_3 Z_i^3 + a_4 Z_i^4 + a_5 Z_i^5\right)\right)^2
$$

Where:
- `Fᵢ`: observed focus value  
- `Zᵢ`: zoom input  
- `a₀` to `a₅`: polynomial coefficients

This function measures how well the polynomial fits the observed focus data.

#### Model Evaluation – Coefficient of Determination (R²)

To evaluate how well the curve fitting model predicts focus values, we use the coefficient of determination (R²):

R² = 1 - [Σ(Fᵢ - F̂ᵢ)² / Σ(Fᵢ - F̄)²]

Where:
- `Fᵢ` = actual focus value
- `F̂ᵢ` = predicted focus value from the model
- `F̄` = mean of all actual focus values

An R² value close to 1.0 indicates excellent model fit.

---

### 2.4 Control Loop Summary

1. **Initialize** motor pins and direction calibration  
2. **Acquire sensor feedback**, including ROI (Region of Interest) values from object detection using the YOLO model  
3. **Smooth sensor and ROI data** via moving average filter  
4. **Compare** current zoom/focus vs. target values derived from ROI and distance measurements  
5. **Predict focus** using a polynomial equation based on zoom and ROI information  
6. **Adjust motors** in a stepwise manner according to the control logic  
7. **Timeout** after 5 seconds if no convergence is achieved
8. 

### 2.5 ROI Bounding Box Centering for Zoom and Focus Control

The Region of Interest (ROI) bounding box, obtained from the YOLO object detection model, is used to center the LED array in the camera frame and dynamically adjust zoom and focus based on the bounding box area. The bounding box is defined by its center coordinates `(x_c, y_c)`, width `x`, and height `y`. The system zooms in when the LED array’s bounding box area is too small and zooms out when it exceeds a threshold, with focus adjustments synchronized to zoom changes using the polynomial model.

---

#### ROI Centering

To keep the LED array centered in the camera frame, the system computes the centering error between the ROI bounding box center `(x_c, y_c)` and the frame center `(x_frame, y_frame)`:

```
∆x = x_c - x_frame  
∆y = y_c - y_frame
```

These error terms guide ROI cropping to align the LED array with the frame center, ensuring optimal framing for Optical Camera Communication (OCC).

---

#### Zoom Adjustment Based on Bounding Box Area

The zoom level is adjusted based on the area of the LED array’s bounding box:

```
A_ROI = x * y
```

Where:

* `x`: Width of the ROI bounding box (in pixels)
* `y`: Height of the ROI bounding box (in pixels)

The relative area compared to the full camera frame is:

```
A_rel = A_ROI / A_frame = (x * y) / (W_frame * H_frame)
```

Where:

* `W_frame`: Width of the camera frame (in pixels)
* `H_frame`: Height of the camera frame (in pixels)

The zoom adjustment logic is:

* **Zoom In**: If `A_rel < A_min` ( `A_min=0.50`, indicating the LED array occupies less than 50% of the frame area), increase the zoom level:

  ```
  Z_new = Z_current + ∆Z
  ```

* **Zoom Out**: If `A_rel > A_max` (`A_max=0.80`, indicating the LED array exceeds 80% of the frame area), decrease the zoom level:

  ```
  Z_new = Z_current - ∆Z
  ```

* **No Adjustment**: If `A_min <= A_rel <= A_max`, keep the current zoom level.

Where:

* `∆Z`: A predefined zoom step (e.g., corresponding to a 30 ms motor pulse)
* `A_min`, `A_max`: Thresholds defining the desired bounding box area (representing 50% and 80% of the frame area)

---

#### Focus Adjustment Based on Zoom

The focus value is adjusted based on the new zoom level using a 5th-degree polynomial model:

```
F(Z_new) = a0 + a1 * Z_new + a2 * Z_new^2 + a3 * Z_new^3 + a4 * Z_new^4 + a5 * Z_new^5
```

Where:

* `Z_new`: New zoom level after adjustment
* `a0` to `a5`: Polynomial coefficients obtained via least squares fitting

The focus motor is adjusted in 10 ms steps to reach `F(Z_new)`, ensuring the LED array remains in sharp focus.

To reduce noise and avoid erratic zooming caused by fluctuating YOLO detections, a moving average filter is applied to `A_ROI`.

---

This approach ensures the LED array is maintained at an optimal size and centered in the frame, with focus dynamically adjusted to preserve image clarity. It enhances the stability and reliability of the Optical Camera Communication (OCC) link, particularly in high-mobility drone environments.


---


## 3. Results and Discussion

Our proposed approach achieves fully automated, low-latency adjustments with response times of less than 100 ms, enabling real-time adaptability crucial for high-mobility drone OCC applications. The system integrates object detection using a YOLO model to extract Region of Interest (ROI) values in real-time, which are then used to guide zoom and focus correction. Testing with a real-world system across distances of 15–20 m and drone speeds of up to 10 km/h showed that the polynomial curve fitting model predicts focus values accurately, maintaining stability and system integrity even under moderate motion.

The evaluation of curve fitting accuracy yielded an excellent coefficient of determination \(R² approx 0.9999\) using a 5th-degree polynomial, indicating a highly reliable predictive model. The use of ROI as a dynamic feedback parameter allowed for adaptive focus tuning aligned with object position and scale, while moving average filtering helped suppress noise in sensor data. Overall, the system supports smooth optical adjustments during drone movement and improves OCC link stability in dynamic field environments.











