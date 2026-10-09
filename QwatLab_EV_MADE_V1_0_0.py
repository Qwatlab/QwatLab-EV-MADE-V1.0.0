# =====================================================================
# QwatLab – Elektr transport vositalarida akkumulyator batareyalarining dinamikasi
# va energiya sarfini fazaviy yondashuv asosida modellashtirish (v1.0.0)
# QwatLab for EV: Modeling and Analyzing Dynamics and Energy 
# Consumption of Electric Vehicles based on a Phase Approach (v1.0.0)
# Intellectual Property Rights: Registered under Official Software Registration Certificate No. DGU 63675 issued by the Intellectual Property Agency of the Republic of Uzbekistan
# Intellektual mulk huquqlari: O‘zbekiston Respublikasi Intellektual mulk agentligi tomonidan berilgan DGU 63675 raqamli dasturiy ta’minotni rasmiy ro‘yxatdan o‘tkazish guvohnomasi bilan ro‘yxatga olingan
# JO‘RABOYEV AKBAR ZOKIR O‘G‘LI; 
# DAMINOV OYBEK OLIMOVICH;
# MIRZAABDULLAYEV JAXONGIR BAXTIYOROVICH;
# YANGIBAYEV AVAZ ISRAILOVICH
# =====================================================================

# ---------------------------------------------------------------------
# BARCHA IMPORTLAR: yagona markazlashtirilgan import bloki
# ---------------------------------------------------------------------
import os
import tempfile
import math
import time
import io
import datetime
import zipfile
import gc
import signal

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import RegularGridInterpolator, interp1d
from scipy.signal import savgol_filter
from scipy.linalg import inv
from numpy.random import default_rng

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# NUMBA KESH VA ATROF-MUHIT SOZLAMASI
# Numba importidan oldin bajarilishi kerak.
# ---------------------------------------------------------------------
numba_error_msg = None
try:
    numba_cache_path = os.path.join(tempfile.gettempdir(), 'QwatLab_Numba_Cache')
    os.makedirs(numba_cache_path, exist_ok=True)
    os.environ['NUMBA_CACHE_DIR'] = numba_cache_path
except Exception as e:
    numba_error_msg = f"Numba cache xotirasini sozlashda ogohlantirish: {e}"

from numba import njit, float64


# ---------------------------------------------------------------------
# STREAMLIT SAHIFA SOZLAMALARI (birinchi bajarilishi kerak bo‘lgan interfeys buyrug‘i)
# ---------------------------------------------------------------------
st.set_page_config(page_title="QwatLab for EV: Modeling and Analyzing Dynamics and Energy v1.0.0", layout="wide") 

# Agar Numba sozlashda xatolik bo'lgan bo'lsa, sahifa konfiguratsiyasidan keyin ko'rsatamiz
if numba_error_msg:
    st.warning(numba_error_msg)

# HOLATNI BOSHQARISH: bloklar holatini boshqarish 
if 'b1_status' not in st.session_state:
    st.session_state['b1_status'] = "🟡 BLOCK 1: EV PARAMETERS (Pending...)" 
if 'b2_status' not in st.session_state:
    st.session_state['b2_status'] = "🟡 BLOCK 2: KINEMATIC PROFILE (Pending...)" 
if 'b3_status' not in st.session_state:
    st.session_state['b3_status'] = "🟡 BLOCK 3: EV CORE ENGINE (Pending...)" 
if 'b1_saved' not in st.session_state:
    st.session_state['b1_saved'] = False

# FOYDALANUVCHI INTERFEYSI (UI) VA USLUBLASH 
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stButton>button {width: 100%; border-radius: 5px;}
    .block-header {color: #1f77b4; font-weight: bold;}
    .q1-title { text-align: center; color: #1E3A8A; font-family: 'Times New Roman', Times, serif; }
    .q1-subtitle { text-align: center; color: #64748B; font-size: 18px; margin-bottom: 30px; }
    </style>
""", unsafe_allow_html=True) 

st.markdown("""
    <h1 class='q1-title'>QwatLab for EV</h1>
    <p class='q1-subtitle'>Modeling and Analyzing Dynamics and Energy (v1.0.0 - EKF/UKF Architecture)</p>
""", unsafe_allow_html=True) 


# =====================================================================
# 0-BLOK: DASTUR HAQIDA VA MATEMATIK NAZARIY ASOSLAR 
# =====================================================================
with st.expander("📘 INTRO: ABOUT QWATLAB for EV: M.A.D.E. & PROFESSIONAL USER INSTRUCTIONS & THEORETICAL FRAMEWORK & GOVERNING EQUATIONS", expanded=False): 
    tab_about, tab_inst, tab_post, tab_donate, tab_kin, tab_dyn, tab_bat, tab_therm = st.tabs([ 
        "📘 1. About the Platform", 
        "📖 2. Professional Instructions",
        "💻 3. Contact & Support", 
        "🤝 4. Donation",
        "📐 5. Kinematic Equations", 
        "⚙️ 6. Longitudinal Dynamics", 
        "⚡ 7. Electro-Chemical Model", 
        "🌡️ 8. Thermal Dynamics"
    ])

    # --- 1-TAB: DASTUR HAQIDA ---
    with tab_about:
        st.markdown("### QWATLAB EV PARAMETERS PLATFORM (V1.0.0)") 
        st.markdown("*Consumption of Electric Vehicles based on a Phase Approach. Modeling and Analyzing Dynamics and Energy.*") 
        st.markdown("*Phase-based modeling of electric-vehicle battery dynamics and energy consumption.*") 
        st.markdown("#### 1. Platform Purpose") 
        st.markdown(""" 
        * EV energy consumption 
        * Battery behavior & Electro-thermal dynamics 
        * Vehicle motion dynamics & Tire traction limits 
        * BMS safety constraints & Route feasibility 
        * Environmental effects (Wind, Gradient, Temperature) 
        """)
        st.markdown("**The platform functions as an EV parameters simulator of an electric vehicle.**") 
        st.markdown("#### 2. Current Platform Scope") 
        st.markdown("The current V1.0.0 release is a **research-grade simulation platform**, an **engineering analysis tool**, and an **EV parameters prototype**.") 
        st.markdown("The platform is NOT a certified automotive ECU or production BMS system.") 
        st.markdown("#### 3. Professional Applications") 
        st.markdown("QWATLAB is suitable for: EV research, Battery analysis, EV parameters studies, Route feasibility analysis, EV education, Energy consumption estimation, Electro-thermal analysis, and BMS-oriented simulations.") 

    # --- 2-TAB: FOYDALANUVCHI YO'RIQNOMASI ---
    with tab_inst:
        st.markdown("### Professional User Instruction (V1.0.0)") 
        st.markdown("**1. What the Platform Calculates**") 
        st.markdown("The system estimates and simulates: SOC (State of Charge), Battery voltage/current behavior, Battery thermal response, HVAC energy consumption, Aerodynamic drag, Rolling resistance, Gradient effects, Wind influence, Regenerative braking, Weight transfer dynamics, BMS protection logic, and **Reachable driving distance**.") 
        st.markdown("**2. Important Concept: Uploaded Route ≠ Reachable Distance**") 
        st.markdown(""" 
        | Parameter | Value Example |
        |---|---|
        | Uploaded route | 400 km |
        | Reachable distance | 160 km |
        """)
        st.markdown("This is **NOT a software error**. It means the EV physically cannot complete the uploaded route under the given operating conditions.") 
        st.markdown("**3. Drive-Cycle File Requirements & Units**") 
        st.markdown("The uploaded CSV/XLSX file should preferably contain: Time [s], Speed [km/h], Acceleration [m/s²], Gradient [degree], Headwind [m/s].") 
        st.warning("**Speed Units Are Critical:** Incorrect speed units may cause unrealistic distance, energy consumption, and SOC calculations. Ensure speed values are explicitly formatted as km/h or m/s.") 
        st.markdown("**4. Recommended Realistic Driving Parameters**") 
        st.markdown(""" 
        | Parameter | Recommended Range |
        |---|---|
        | Average speed | 40–80 km/h |
        | Maximum speed | 100–130 km/h |
        | Gradient | ±5° |
        | Duration | 500–2000 s | 
        """)
        st.markdown("*For realistic and internationally comparable validation, **WLTP, NEDC, UDDS**, or real-world telemetry profiles are recommended.*") 
        st.markdown("**5. Physical Realism Validation**") 
        st.markdown("The platform can automatically detect physically impossible routes, unrealistic driving conditions, BMS safety violations, and thermal overload situations. If necessary, the simulation may terminate automatically.") 
        st.markdown("**6. Meaning of “BMS Interruption”**") 
        st.markdown("The message `🛑 BMS Interruption` means the battery reached the user-defined minimum SOC threshold, or a thermal/voltage protection limit was exceeded. This indicates the safety logic is functioning correctly. The platform **does NOT guarantee** that the EV can complete the uploaded route; it evaluates whether it is physically feasible.") 
        st.markdown("**7. Platform Philosophy & Final Note**") 
        st.markdown("QWATLAB prioritizes **physical realism over optimistic estimation**. The platform intentionally applies conservative battery behavior, safety-aware BMS logic, and realistic energy limitations instead of unrealistic optimistic range predictions.") 
        st.success("**Realistic results are more valuable than idealized results.** QWATLAB respects physical limitations, detects infeasible driving conditions, and prioritizes engineering realism and safety-oriented behavior.")

    # --- 3-TAB: ALOQA VA QO'LLAB QUVVATLASH ---
    with tab_post:
        st.markdown("### QwatLab Team") 
        st.markdown("**Communication and Support:**") 
        st.markdown("* 🌐 Website: https://t.me/QwatLab") 
        st.markdown("* **Made in Uzbekistan 🇺🇿**") 
        st.markdown("* **License/certificate issued for the created program: № DGU 63675**") 

    # --- 4-TAB: HOMIYLIK ---
    with tab_donate:
        st.markdown("### Support the Project") 
        st.markdown("**For improving and supporting the platform development:**") 
        st.markdown("* ☕ Donate us: https://t.me/QwatLab") 

    # --- 5-TAB: KINEMATIKA ---    
    with tab_kin:
        st.header("📐 Kinematics & Drive Cycle Simulation Engine")
        st.markdown(""" 
        This module serves as the **Core Pre-processing Engine** for the Electric Vehicle (EV) simulation. It establishes the vehicle's trajectory, velocity profile, and discrete acceleration matrices required for downstream longitudinal dynamics and battery State-of-Charge (SoC) estimation.
        """) 
        st.write("---") 
        st.subheader("1. Governing Kinematic Equations") 
        st.markdown(r"The simulation engine performs discrete-time numerical integration at each time step ($\Delta t$) utilizing the following fundamental kinematic laws:") 
        st.markdown("* **Velocity Update Equation:**") 
        st.latex(r''' v(t) = v(t-1) + a(t) \cdot \Delta t ''') 
        st.markdown("* **Discrete Position Integral:**") 
        st.latex(r''' s(t) = s(t-1) + v(t) \cdot \Delta t + \frac{1}{2} a(t) \cdot \Delta t^2 ''') 
        st.write("---") 
        st.subheader("2. Drive Cycle Processing & Signal Conditioning Logic") 
        col1, col2 = st.columns(2) 
        with col1:
            st.markdown("### 🤖 Auto Mode (Synthetic Profile Generator)") 
            st.markdown(""" 
            Generates deterministic **trapezoidal or multi-phase speed profiles** based on user-defined acceleration, cruise, and deceleration constraints. 
            * **1. Stochastic Realism:** To replicate unpredictable real-world driving behaviors, the engine superimposes **Stochastic Speed Fluctuation Noise** onto the ideal profile. 
            * **2. Signal Smoothing:** A digital **Savitzky-Golay (S-G) Filter** is applied to smooth out non-physical sudden transitions while reducing high-frequency measurement noise; it does not strictly conserve kinetic energy or momentum. 
            """)
        with col2:
            st.markdown("### 📊 Manual Mode (Real-World Telemetry Upload)") 
            st.markdown(r""" 
            Processes empirical drive-test datasets imported from external **GPS loggers, OBD-II scanners, or CAN-bus telemetry**.
            
            * **3. Numerical Differentiation:** Acceleration vectors are extracted dynamically via forward/backward $\Delta v / \Delta t$ routines. 
            * **4. Noise Rejection:** Automatically eliminates sensor noise, timestamp jitter, and tracking outliers using adaptive windowing filters to prevent non-physical infinite acceleration spikes ($a \rightarrow \infty$). 
            """)
        st.write("---") 
        st.info(r"💡 **Pro Tip:** Ensure your uploaded telemetry file contains a uniform time series. Any timestamp irregularities ($\Delta t \le 0$) are automatically conditioned by the engine to maintain absolute numerical stability during integration.") 

    # --- 6-TAB: BOYLAMA DINAMIKA ---
    with tab_dyn:
        st.markdown("**2. Vehicle Longitudinal Dynamics**") 
        st.markdown("*Aerodynamic Drag Force (with wind consideration):*") 
        st.latex(r''' F_{aero} = \frac{1}{2}\rho_{air} C_d A\,v_{rel}|v_{rel}|,\quad v_{rel}=v+v_{wind} ''') 
        st.markdown("*Rolling Resistance (Speed Dependent):*") 
        st.latex(r''' F_{roll} = m \cdot g \cdot (C_{r0} + C_{r1} \cdot v(t)) \cdot \cos(\theta) ''') 
        st.markdown("*Gradient/Slope Resistance:*") 
        st.latex(r''' F_{slope} = m \cdot g \cdot \sin(\theta) ''') 
        st.markdown("*Inertial Force:*") 
        st.latex(r''' F_{inertial} = m_{eff} \cdot a(t) ''') 
        st.markdown("*Total Tractive Force & Mechanical Power:*") 
        st.latex(r''' F_{total} = F_{aero} + F_{roll} + F_{slope} + F_{inertial} ''') 
        st.latex(r''' P_{mech} = F_{total} \cdot v(t) ''') 
        st.markdown("**Powertrain Energy Conversion:**") 
        st.markdown("*Electrical Power Demand (Traction vs Regeneration):*") 
        st.latex(r''' P_{elec} = \begin{cases} \frac{P_{mech}}{\eta_m\eta_i\eta_t}, & P_{mech}\ge0 \\ P_{mech}\eta_m\eta_i\eta_t\eta_{regen}, & P_{mech}<0 \end{cases} ''') 
        st.markdown("*Battery Pack Current Request (Including HVAC and Aux loads):*") 
        st.latex(r''' P_{batt,req}=P_{elec}+P_{aux}+P_{hvac}+P_{TMS},\qquad V_{term}=V_{OCV}-IR_0-U_{p1}-U_{p2} ''') 

    # --- 7-TAB: ELEKTROKIMYOVIY MODEL ---
    with tab_bat:
        st.markdown("**3. Electro-Chemical Model (2RC Equivalent Circuit):** Ohmic resistance plus two polarization branches; OCV is supplied by the user-defined SOC lookup table.") 
        st.markdown("*Kirchhoff's Voltage Law for 2RC Equivalent Circuit:*") 
        st.latex(r''' V_{terminal} = OCV(SOC) - I \cdot R_0(T) - U_{p1} - U_{p2} ''') 
        st.markdown("*First Polarization RC Network (Short-term transient):*") 
        st.latex(r''' \dot{U}_{p1} = -\frac{U_{p1}}{R_1(SOC, T) \cdot C_1(SOC, T)} + \frac{I}{C_1(SOC, T)} ''') 
        st.markdown("*Second Polarization RC Network (Long-term transient):*") 
        st.latex(r''' \dot{U}_{p2} = -\frac{U_{p2}}{R_2(SOC, T) \cdot C_2(SOC, T)} + \frac{I}{C_2(SOC, T)} ''') 
        st.markdown("*Coulomb Counting (State of Charge Integration):*") 
        st.latex(r''' SOC(t) = SOC(t-1) - \frac{1}{3600\,Q_{Ah}}\int I(t)\,dt ''') 

    # --- 8-TAB: TERMAL DINAMIKA ---
    with tab_therm:
        st.markdown("**4. Thermal Model (Battery core and surface heating):** Bernardi heat generation + two-node core/surface model.") 
        st.markdown("*Total Heat Generation (Joule & Reversible Entropic Heating):*") 
        st.latex(r''' Q_{gen}=I(OCV-V_{term})-I T_{core}\frac{\partial OCV}{\partial T} ''') 
        st.markdown("*Core Temperature Differential Equation:*") 
        st.latex(r''' C_c \cdot \frac{dT_{core}}{dt} = Q_{gen} - \frac{T_{core} - T_{surf}}{R_{cs}} ''') 
        st.markdown("*Surface Temperature Differential Equation:*") 
        st.latex(r''' C_s \cdot \frac{dT_{surf}}{dt} = \frac{T_{core}-T_{surf}}{R_{cs}}-\frac{T_{surf}-T_{ambient}}{R_{sa}}-Q_{TMS} ''') 

# =====================================================================
# 0-BLOK oxiri
# =====================================================================

# =====================================================================
# 1-BLOK: EV PARAMETRLARI (KONFIGURATSIYA MATRITSASI - V1.0.0 DINAMIK) 
# =====================================================================

with st.expander("🛠️ BLOCK 1: EV PARAMETERS (PHYSICALLY VALIDATED & REFERENCED)", expanded=True): 
    st.markdown("""
    **Instructions:** Welcome to the V1.0.0 Scientific Configurator. All parameters are hard-bounded by physical limits to prevent mathematical divergence. 
    Hover over the **`?`** icon next to any parameter to see the professionally recommended ranges and **Scientific References**. 
    """) 

    col_h1, col_h2 = st.columns([2, 1]) 
    with col_h1:
        v_model_name = st.text_input("🚗 Vehicle Model Name", value="Custom EV/E-Scooter/Mini E-Bus/...", key="cfg_v_model_name", help="Name of your EV model for export tracking.") 
    with col_h2:
        p_cost_kwh = st.number_input("Energy Cost [$/kWh]", value=0.15, min_value=0.01, max_value=5.0, format="%.3f", key="cfg_p_cost_kwh", help="Recommended: 0.10 - 0.40 $/kWh. Used for financial metrics.") 
        
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True) 

    tab_chassis, tab_bat, tab_therm, tab_drivetrain, tab_hvac, tab_coeffs = st.tabs([ 
        "🚙 1. Chassis & Dimensions", "🔋 2. Battery (2RC)", "🌡️ 3. Thermal, TMS & OCV", 
        "⚙️ 4. Powertrain & Dynamics", "❄️ 5. HVAC & Env", "🎛️ 6. Math Coeffs (EKF/UKF & Safety)" 
    ])

    # --- 1. SHASSI VA GABARITLAR ---
    with tab_chassis:
        st.markdown("**Vehicle Weights & Dimensions**") 
        c1, c2, c3 = st.columns(3) 
        with c1:
            p_chassis_mass = st.number_input("Curb Mass (No Battery) [kg]", value=1075.0, min_value=100.0, max_value=10000.0, key="cfg_p_chassis_mass", help="Physical Bound: > 100 kg. Chassis weight excluding battery.") 
            p_payload = st.number_input("Payload/Driver Mass [kg]", value=150.0, min_value=0.0, max_value=5000.0, key="cfg_p_payload", help="Physical Bound: >= 0 kg. Passengers and cargo.") 
            p_g = st.number_input("Gravity (g) [m/s²]", value=9.81, min_value=0.1, max_value=30.0, format="%.2f", key="cfg_p_g", help="Earth standard: 9.81 m/s².") 
        with c2:
            p_width = st.number_input("Vehicle Width [m]", value=1.76, min_value=0.5, max_value=4.0, format="%.2f", key="cfg_p_width", help="Physical Bound: 0.5 - 4.0 m") 
            p_height = st.number_input("Vehicle Height [m]", value=1.53, min_value=0.5, max_value=5.0, format="%.2f", key="cfg_p_height", help="Physical Bound: 0.5 - 5.0 m") 
            p_wheelbase = st.number_input("Wheelbase [m]", value=2.61, min_value=1.0, max_value=8.0, format="%.2f", key="cfg_p_wheelbase", help="Physical Bound: 1.0 - 8.0 m") 
        with c3:
            auto_area = p_width * p_height * 0.85 
            p_area = st.number_input("Frontal Area (A) [m²]", value=auto_area, min_value=0.5, max_value=15.0, format="%.2f", key="cfg_p_area", help="Calculated default: Width x Height x 0.85. Direct impact on aerodynamic drag.") 
            p_cd = st.number_input("Drag Coefficient (Cd)", value=0.29, min_value=0.05, max_value=1.5, format="%.3f", key="cfg_p_cd", help="Physical Bound: 0.05 - 1.5. Typical EV: 0.20 - 0.30.") 
            p_aux_power = st.number_input("Standby/Aux Power [W]", value=250.0, min_value=0.0, max_value=5000.0, key="cfg_p_aux_power", help="Base electrical load (ECU, Screens, Lights, Sensors).") 

    # --- 2. BATAREYA PAKETI VA DEGRADATSIYA ---
    with tab_bat:
        c1, c2, c3 = st.columns(3) 
        with c1:
            b_chem = st.selectbox("Battery Chemistry", ["LiFePO4", "NMC", "Custom Battery"], key="cfg_b_chem", help="Select base chemistry. Influences OCV and Thermal safety limits.") 
            b_cell_mass = st.number_input("Cell Mass [kg]", value=2.5, min_value=0.01, max_value=10.0, format="%.3f", key="cfg_b_cell_mass", help="Weight of a single cell element.") 
            b_cell_v = st.number_input("Cell Nom. Voltage [V]", value=3.2 if b_chem == "LiFePO4" else (3.7 if b_chem == "NMC" else 3.5), min_value=1.0, max_value=5.0, key="cfg_b_cell_v", help="LFP: ~3.2V, NMC: ~3.7V.") 
            b_cell_ah = st.number_input("Cell Capacity [Ah]", value=135.0, min_value=0.1, max_value=2000.0, key="cfg_b_cell_ah", help="Capacity per single cell block.") 
            b_ns = st.number_input("Series Cells (Ns)", value=100, min_value=1, max_value=1000, key="cfg_b_ns", help="Determines overall Pack Voltage.") 
            b_np = st.number_input("Parallel Cells (Np)", value=1, min_value=1, max_value=200, key="cfg_b_np", help="Determines overall Pack Capacity.") 
            b_pack_overhead = st.number_input("Pack Mass Overhead Factor", value=1.20, min_value=1.0, max_value=2.0, key="cfg_b_overhead", help="Multiplier for casing, cooling lines, BMS, wiring weight (1.20 = 20% extra).")
            b_cycle_life = st.number_input("Expected Cycle Life (to 80% SOH)", value=3000.0 if b_chem == "LiFePO4" else 1500.0, min_value=100.0, max_value=20000.0, step=100.0, key="cfg_b_cycle", help="Used to calculate real-time State of Health (SOH) degradation.")
        with c2:
            st.caption("🔬 2RC Equivalent Circuit Parameters")
            b_r0 = st.number_input("Ohmic Res (R0) [Ω]", value=0.001, min_value=1e-5, max_value=0.5, format="%.5f", key="cfg_b_r0", help="Immediate internal resistance. MUST be > 0 to avoid Div/0 errors.") 
            b_r1 = st.number_input("Pol. Res 1 (R1) [Ω]", value=0.002, min_value=1e-5, max_value=0.5, format="%.5f", key="cfg_b_r1", help="Short-term transient resistance.") 
            b_c1 = st.number_input("Pol. Cap 1 (C1) [F]", value=1000.0, min_value=1.0, max_value=100000.0, key="cfg_b_c1", help="Short-term transient capacitance.") 
            b_r2 = st.number_input("Pol. Res 2 (R2) [Ω]", value=0.002, min_value=1e-5, max_value=0.5, format="%.5f", key="cfg_b_r2", help="Long-term transient resistance.") 
            b_c2 = st.number_input("Pol. Cap 2 (C2) [F]", value=6000.0, min_value=1.0, max_value=200000.0, key="cfg_b_c2", help="Long-term transient capacitance.") 
            b_min_volt_cell = st.number_input("Absolute Min Cell Voltage [V]", value=2.5 if b_chem == "LiFePO4" else 2.7, min_value=1.0, max_value=4.0, key="cfg_b_min_v", help="BMS Voltage Sag Protection Limit. Current is throttled to prevent dropping below this.")
        with c3:
            b_max_soc = st.number_input("Max SOC Limit [%]", value=100.0, min_value=10.0, max_value=100.0, key="cfg_b_max_soc", help="Prevents overcharging via Regen.") 
            b_start_soc = st.number_input("Starting SOC [%]", value=98.0, min_value=0.0, max_value=100.0, key="cfg_b_start_soc", help="True Initial State of Charge for the physical battery.") 
            b_min_soc = st.number_input("Min SOC Limit [%]", value=5.0, min_value=0.0, max_value=90.0, key="cfg_b_min_soc", help="BMS triggers hard disconnect (Death Mask) if reached.") 
            b_coulombic = st.number_input("Coulombic Eff. [%]", value=99.5, min_value=50.0, max_value=100.0, format="%.1f", key="cfg_b_coulombic", help="Charge acceptance efficiency during regen.") 
            b_max_dis_c = st.number_input("Max Disch. C-Rate", value=3.0, min_value=0.1, max_value=50.0, key="cfg_b_max_dis_c", help="Hardware limit on peak acceleration discharge current.") 
            b_max_chg_c = st.number_input("Max Charge C-Rate", value=1.5, min_value=0.1, max_value=50.0, key="cfg_b_max_chg_c", help="Hardware limit on peak regen/charging current.") 
            b_init_soc_guess = st.number_input(
                "Initial SOC Guess [%] (For Filters)", 
                value=40.0, min_value=0.0, max_value=100.0, step=0.1,
                help="Scientific Benchmarking: Set this value significantly lower than 'Starting SOC' to observe EKF/UKF convergence."
            )

    # --- 3. TERMAL, TMS VA OCV JADVALLARI ---
    with tab_therm:
        st.markdown("**Electro-Thermal Limits, Active Cooling (TMS) & OCV Mapping**") 
        c_th1, c_th2 = st.columns([1, 1.5]) 
        with c_th1:
            st.markdown("#### 🌡️ Passive Thermal Parameters") 
            estimated_pack_mass = (b_cell_mass * b_ns * b_np) * b_pack_overhead
            default_cc = max(1000.0, estimated_pack_mass * 900.0 * 0.85)
            default_cs = max(500.0, estimated_pack_mass * 900.0 * 0.15)
            t_cc = st.number_input("Core Heat Capacity (Pack) [J/K]", value=float(default_cc), min_value=1000.0, max_value=2000000.0, key="cfg_t_cc_v6", help="Pack-level thermal capacitance of the active/core mass. Default uses 900 J/(kg·K) and an 85% core fraction; calibrate experimentally.")
            t_cs = st.number_input("Surface Heat Capacity (Pack) [J/K]", value=float(default_cs), min_value=500.0, max_value=1000000.0, key="cfg_t_cs_v6", help="Pack-level thermal capacitance of casing/plates/coolant-contact mass. Default uses 900 J/(kg·K) and a 15% surface fraction; calibrate experimentally.")
            t_rcs = st.number_input("Core-Surface Thermal Resistance (Rcs) [K/W]", value=0.01, min_value=0.0001, max_value=10.0, format="%.5f", key="cfg_t_rcs_v6", help="PACK-LEVEL conductive thermal resistance between core and surface. Do not divide this value by the number of cells.")
            t_rsa = st.number_input("Surface-Ambient Thermal Resistance (Rsa) [K/W]", value=0.02, min_value=0.0001, max_value=10.0, format="%.5f", key="cfg_t_rsa_v6", help="PACK-LEVEL external thermal resistance before wind/TMS correction. Calibrate from thermal tests.") 
            t_conv_coeff = st.number_input("Convective Cooling Coeff", value=0.05, min_value=0.0, max_value=1.0, format="%.3f", key="cfg_t_conv", help="How much wind speed dynamically reduces Rsa (Forced Convection).")
            
            st.markdown("#### ❄️ Active Thermal Management (TMS)")
            tms_master_on = st.toggle("❄️ TMS Master Switch", value=True, key="cfg_tms_master", help="ON: active cooling is enabled. OFF: no active TMS cooling; passive thermal model remains active.")
            if tms_master_on:
                st.success("🟢 TMS ACTIVE — active battery cooling is enabled.")
            else:
                st.warning("⚪ TMS OFF — active cooling and coolant circulation are disabled; residual passive heat rejection is reduced.")
            tms_off_passive_factor = st.slider(
                "Residual Passive Cooling when TMS is OFF [%]",
                min_value=0.0, max_value=100.0, value=20.0, step=5.0,
                key="cfg_tms_off_passive_factor",
                help="Fraction of the normal surface-to-ambient heat rejection retained when TMS/coolant circulation is OFF. 0% = no external heat rejection; 20% = reduced natural/residual path."
            )
            st.caption(f"TMS OFF → passive heat rejection = {tms_off_passive_factor:.0f}% of normal Rsa branch.")
            t_cooling_on = st.number_input("Cooling Activation Temp [°C]", value=45.0, min_value=10.0, max_value=80.0, key="cfg_t_cooling_on", help="Temperature at which cooling pump and compressor turn ON.") 
            t_cooling_off = st.number_input("Cooling Deactivation Temp [°C]", value=35.0, min_value=0.0, max_value=75.0, key="cfg_t_cooling_off", help="Temperature at which cooling system turns OFF (Hysteresis loop).") 
            cooling_power = st.number_input("Cooling System Electrical Power [W]", value=2500.0, min_value=0.0, max_value=20000.0, key="cfg_cooling_power", help="Electrical power consumed by the TMS chiller.") 
            tms_cop = st.number_input("TMS Chiller COP", value=2.0, min_value=1.0, max_value=5.0, key="cfg_tms_cop", help="Coefficient of Performance. Actual heat extracted = Power * COP.")
            
            st.markdown("#### ⚠️ BMS Thermal Safety & Derating") 
            def_derate = 55.0 if b_chem == "LiFePO4" else (50.0 if b_chem == "NMC" else 60.0) 
            def_cutoff = 65.0 if b_chem == "LiFePO4" else (60.0 if b_chem == "NMC" else 70.0) 
            t_derate = st.number_input("Power Derate Temp [°C]", value=def_derate, min_value=30.0, max_value=100.0, key="cfg_t_derate", help="BMS starts reducing propulsion power linearly to prevent overheating.") 
            t_cutoff = st.number_input("Critical Cutoff Temp [°C]", value=def_cutoff, min_value=40.0, max_value=150.0, key="cfg_t_cutoff", help="BMS opens main contactors. Vehicle stops.") 
        with c_th2:
            st.markdown(f"#### 📊 OCV-SOC Profile Editor ({b_chem})") 
            st.caption("WARNING: These values dictate the fundamental terminal voltage physics. Ensure monotonic curves.") 
            soc_base = [0.0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0] 
            if b_chem == "LiFePO4":
                ocv_base = [2.5, 2.9, 3.1, 3.2, 3.25, 3.28, 3.3, 3.32, 3.34, 3.345, 3.4, 3.45, 3.65] 
            elif b_chem == "NMC":
                ocv_base = [3.0, 3.3, 3.45, 3.55, 3.62, 3.68, 3.75, 3.82, 3.9, 3.98, 4.08, 4.15, 4.2] 
            else:
                ocv_base = [0.0] * 13 
            df_ocv_template = pd.DataFrame({"SOC (0 to 1)": soc_base, "OCV [V]": ocv_base}) 
            edited_ocv_df = st.data_editor(df_ocv_template, hide_index=True, num_rows="fixed", key=f"ocv_editor_{b_chem}") 

    # --- 4. KUCH UZATMASI VA DINAMIKA ---
    with tab_drivetrain:
        c1, c2, c3 = st.columns(3) 
        with c1:
            dt_drive = st.selectbox("Drive Architecture", ["FWD", "RWD", "AWD"], key="cfg_dt_drive") 
            dt_motors = st.selectbox("Number of Motors", [1, 2, 3, 4], key="cfg_dt_motors") 
            m_max_p = st.number_input("Total Max Motor Power [kW]", value=70.0, min_value=1.0, max_value=2000.0, key="cfg_m_max_p", help="Hard limit on propulsion capability.") 
            m_max_t = st.number_input("Total Max Torque [Nm]", value=180.0, min_value=10.0, max_value=5000.0, key="cfg_m_max_t", help="Maximum torque provided by powertrain.") 
            m_rpm = st.number_input("Base Speed [RPM]", value=3500.0, min_value=100.0, max_value=20000.0, key="cfg_m_rpm", help="RPM threshold where constant torque region ends.") 
        with c2:
            m_gear = st.number_input("Gear Ratio", value=9.2, min_value=1.0, max_value=30.0, key="cfg_m_gear", help="Fixed reducer gear ratio.") 
            p_wheel_rad = st.number_input("Wheel Radius [m]", value=0.315, min_value=0.1, max_value=1.5, key="cfg_p_wheel_rad", help="Tire rolling radius.") 
            p_cr0 = st.number_input("Static Roll Coeff (Cr0)", value=0.012, min_value=0.001, max_value=0.1, format="%.4f", key="cfg_p_cr0", help="Static rolling resistance.") 
            p_cr1 = st.number_input("Dynamic Roll Coeff (Cr1)", value=0.00015, min_value=0.0, max_value=0.01, format="%.5f", key="cfg_p_cr1", help="Speed-dependent rolling friction.") 
            dt_tire_mu = st.number_input("Tire Friction Coeff (μ)", value=0.85, min_value=0.1, max_value=2.0, format="%.2f", key="cfg_dt_tire_mu", help="Road adhesion limit. Used for tire slip loss calculation.") 
        with c3:
            m_eff = st.number_input("Motor Efficiency [%]", value=95.0, min_value=10.0, max_value=100.0, key="cfg_m_eff", help="Average motor efficiency.") 
            m_inv = st.number_input("Inverter Efficiency [%]", value=97.0, min_value=10.0, max_value=100.0, key="cfg_m_inv", help="Power electronics conversion efficiency.") 
            m_tra = st.number_input("Trans. Efficiency [%]", value=96.0, min_value=10.0, max_value=100.0, key="cfg_m_tra", help="Mechanical drivetrain efficiency.") 
            p_inertia_factor = st.number_input("Rotational Inertia Factor", value=1.05, min_value=1.0, max_value=1.5, key="cfg_inertia", help="Multiplies vehicle mass to account for kinetic energy of rotating components.")
            m_regen_cut = st.number_input("Regen Cutoff Speed [km/h]", value=5.0, min_value=0.0, max_value=50.0, key="cfg_m_regen_cut", help="Mechanical brakes take over below this speed.") 

    # --- 5. HVAC VA ATROF-MUHIT ---
    with tab_hvac:
        c_hvac_on, c_hvac_pad = st.columns([1, 3]) 
        with c_hvac_on:
            hvac_active_toggle = st.toggle("❄️/🔥 Enable HVAC System", value=True, key="cfg_hvac_toggle", help="Master switch for Climate Control.") 
            
        c_hvac1, c_hvac2, c_hvac3, c_hvac4 = st.columns(4) 
        with c_hvac1:
            h_target = st.number_input("Target Cabin Temp [°C]", value=22.0, min_value=10.0, max_value=40.0, key="cfg_h_target", help="Desired interior temperature.") 
            h_fan = st.number_input("HVAC Fan Base Power [W]", value=200.0, min_value=0.0, max_value=3000.0, key="cfg_h_fan", help="Base electrical power for blower fans.") 
        with c_hvac2:
            h_cool = st.number_input("Cooling Demand [W/°C]", value=120.0, min_value=0.0, max_value=1000.0, key="cfg_h_cool", help="Power scaling per degree of cooling required.") 
            h_heat = st.number_input("Heating Demand [W/°C]", value=180.0, min_value=0.0, max_value=1000.0, key="cfg_h_heat", help="Power scaling per degree of heating required.") 
        with c_hvac3:
            h_cop_cool = st.number_input("Cooling System COP", value=2.5, min_value=1.0, max_value=6.0, key="cfg_h_cop_cool", help="Compressor efficiency ratio.") 
            h_cop_heat = st.number_input("Heating System COP", value=0.95, min_value=0.5, max_value=5.0, key="cfg_h_cop_heat", help="PTC Heater = 0.95. Heat Pump = 2.0 - 4.0.") 
        with c_hvac4:
            h_c_cabin = st.number_input("Cabin Thermal Mass [J/K]", value=250000.0, min_value=50000.0, max_value=1000000.0, key="cfg_h_c_cabin", help="Energy needed to change cabin temp by 1°C.") 
            h_k_env = st.number_input("Cabin Insulation [W/K]", value=80.0, min_value=10.0, max_value=500.0, key="cfg_h_k_env", help="Heat leakage rate to the outside environment.") 
            
        st.markdown("**Environment Variables**") 
        c_env1, c_env2, c_env3 = st.columns(3) 
        with c_env1:
            h_amb = st.number_input("Ambient Temp [°C]", value=30.0, min_value=-50.0, max_value=65.0, key="cfg_h_amb", help="Outside weather conditions.") 
        with c_env2:
            h_pres = st.number_input("Air Pressure [Pa]", value=101325.0, min_value=50000.0, max_value=150000.0, key="cfg_h_pres", help="Standard Sea Level: 101325 Pa.") 
        with c_env3:
            h_rho = st.number_input("Air Density [kg/m³]", value=1.18, min_value=0.5, max_value=2.0, format="%.3f", key="cfg_h_rho", help="Density impacts Aerodynamic Drag directly.") 

    # --- 6. MATEMATIKA, EKF/UKF VA XAVFSIZLIK (YANGI QO'SHIMCHALAR) ---
    with tab_coeffs:
        st.markdown("**Stochastic Filtering, Chemistry Thermodynamics & Physical Bounds**") 
        c1, c2, c3, c4 = st.columns(4) 
        with c1:
            st.markdown("##### 📉 Filter Matrices")
            ck_q = st.number_input("EKF Process Noise (Q)", value=1e-6, format="%.1e", key="cfg_ck_q", help="Covariance of EKF mathematical model trust.") 
            ck_r = st.number_input("EKF Meas. Noise (R)", value=1e-2, format="%.1e", key="cfg_ck_r", help="Covariance of EKF ADC sensor noise trust.") 
            ukf_q = st.number_input("UKF Process Noise (Q)", value=1e-6, format="%.1e", key="cfg_ukf_q", help="Unscented Kalman Filter Process Covariance.") 
            ukf_r = st.number_input("UKF Meas. Noise (R)", value=1e-2, format="%.1e", key="cfg_ukf_r", help="Unscented Kalman Filter Measurement Covariance.") 
            p0_ekf = st.number_input("EKF Init Covariance (P0)", value=0.1, min_value=0.001, max_value=1.0, format="%.3f", key="cfg_p0_ekf", help="Replaces hardcoded P0. Defines initial EKF uncertainty.") 
            p0_ukf = st.number_input("UKF Init Covariance (P0)", value=0.1, min_value=0.001, max_value=1.0, format="%.3f", key="cfg_p0_ukf", help="Replaces hardcoded P0. Defines initial UKF uncertainty.") 
            csocw = st.number_input("SOC Integration Weight", value=0.5, min_value=0.0, max_value=1.0, key="cfg_csocw", help="Balance between Coulomb Counting and Voltage correction in filters.")
        with c2:
            st.markdown("##### 🔬 Arrhenius Bounds")
            cdudt = st.number_input("Entropic Coeff (dU/dT)", value=0.0001, format="%.4f", key="cfg_cdudt", help="Ref: Bernardi (1985). Reversible heat generation factor based on temperature.") 
            cea = st.number_input("Activation Energy (Ea)", value=25000.0, key="cfg_cea", help="Ref: Arrhenius equation. Determines internal resistance scaling at cold temperatures.") 
            t_ref = st.number_input("Reference Temp [°C]", value=25.0, key="cfg_t_ref", help="Baseline temperature for nominal R0 and OCV parameters.")
            max_arr_r = st.number_input("Max Arrhenius Res [Ω]", value=0.5, min_value=0.01, max_value=5.0, key="cfg_max_arr", help="Prevents infinite resistance at sub-zero temps. Hard ceiling for R0.")
        with c3:
            st.markdown("##### 💥 Thermal Runaway & RK2")
            tr_base_heat = st.number_input("Exothermic Base [W]", value=25000.0, min_value=1000.0, max_value=100000.0, key="cfg_tr_base", help="Base heat generated once thermal runaway is triggered.") 
            tr_rate = st.number_input("Reaction Rate", value=0.08, min_value=0.01, max_value=0.5, format="%.3f", key="cfg_tr_rate", help="Exponential growth rate of thermal runaway heating.") 
            rk2_clip = st.number_input("RK2 Thermal Clip [°C/s]", value=5.0, min_value=0.1, max_value=50.0, format="%.1f", key="cfg_rk2_clip", help="Maximum allowable temperature jump per second. Prevents Euler divergence.")
        with c4:
            st.markdown("##### 🛰️ Dynamics & Fade")
            dt_regen_bias = st.number_input("Regen Front Bias [%]", value=100.0 if dt_drive == "FWD" else 60.0, min_value=0.0, max_value=100.0, key="cfg_dt_regen_bias", help="Percentage of regen braking applied to the driven axle.") 
            cfade = st.number_input("Base Regen Fade Coeff", value=0.9, min_value=0.1, max_value=1.0, key="cfg_cfade", help="Simulates mechanical/braking torque degradation.") 
            regen_capture = st.number_input("Regen Capture Efficiency [%]", value=95.0, min_value=0.0, max_value=100.0, format="%.1f", key="cfg_regen_capture", help="Fraction of motor-generated regenerative energy that reaches the battery.") / 100.0
            r_fade_min_t = st.number_input("Regen Fade Min Temp [°C]", value=-5.0, min_value=-30.0, max_value=20.0, key="cfg_rf_mint", help="Below this core temp, regen scales to 0% to prevent lithium plating.")
            r_fade_max_s = st.number_input("Regen Fade Max SOC [%]", value=90.0, min_value=50.0, max_value=100.0, key="cfg_rf_maxs", help="Above this SOC, regen starts reducing to 0% to prevent overcharging.")
            st.markdown("<hr style='margin-top: 5px; margin-bottom: 5px;'>", unsafe_allow_html=True)
            gps_dt_thresh = st.number_input("GPS Anomaly dt [s]", value=3.0, min_value=1.0, max_value=10.0, format="%.1f", key="cfg_gps_dt", help="If time jump exceeds this, Kalman Smoother acts.")
            gps_accel_clip = st.number_input("GPS Accel Clip [m/s²]", value=2.0, min_value=0.5, max_value=10.0, format="%.1f", key="cfg_gps_clip", help="Clamps artificial acceleration spikes during GPS signal loss.")

    # =====================================================================
    # SAQLASH MANTIQI (ACTION STATE ENGINE - YANADA KENGAYTIRILGAN)
    # =====================================================================
    st.markdown("<br>", unsafe_allow_html=True) 
    
    if st.button("✅ SAVE SCIENTIFIC CONFIGURATION & GENERATE PARAMETERS", type="primary"):
        soc_check = pd.to_numeric(edited_ocv_df["SOC (0 to 1)"], errors="coerce").to_numpy(dtype=float)
        ocv_check = pd.to_numeric(edited_ocv_df["OCV [V]"], errors="coerce").to_numpy(dtype=float)
        ocv_valid = (
            np.all(np.isfinite(soc_check)) and np.all(np.isfinite(ocv_check))
            and np.all(np.diff(soc_check) > 0.0)
            and soc_check[0] >= 0.0 and soc_check[-1] <= 1.0
            and np.all(np.diff(ocv_check) >= -1e-9)
            and np.all(ocv_check > 0.0)
        )
        consistency_errors = []
        if b_start_soc < b_min_soc:
            consistency_errors.append("Starting SOC cannot be below minimum SOC limit.")
        if b_start_soc > b_max_soc:
            consistency_errors.append("Starting SOC cannot exceed maximum SOC limit.")
        if t_cooling_off >= t_cooling_on:
            consistency_errors.append("Cooling OFF temperature must be lower than Cooling ON temperature.")
        if t_cutoff <= t_derate:
            consistency_errors.append("Thermal cutoff temperature must be higher than derating temperature.")
        if not ocv_valid:
            consistency_errors.append("SOC/OCV table must be finite, SOC must increase strictly from 0 to 1, OCV must be positive and non-decreasing.")
        if consistency_errors:
            for err in consistency_errors:
                st.error("🛑 **Validation Error:** " + err)
            st.session_state['b1_saved'] = False
        else:
            pack_v = b_cell_v * b_ns 
            pack_ah = b_cell_ah * b_np 
            pack_energy_kwh = (pack_v * pack_ah) / 1000.0 
            
            p_mass = (b_cell_mass * b_ns * b_np) * b_pack_overhead 
            total_m = p_chassis_mass + p_payload + p_mass 
            
            soc_lut_val = edited_ocv_df["SOC (0 to 1)"].values.astype(float) 
            ocv_lut_val = edited_ocv_df["OCV [V]"].values.astype(float) 
            hvac_state_val = 1.0 if hvac_active_toggle else 0.0 

            # TO'LIQ VA MUKAMMAL DICTIONARY (Barcha eski va Q1 yangi parametrlar bilan - Jami 85 ta)
            st.session_state['sim_params'] = { 
                # 1. Shassi va Gabaritlar (11 parametr)
                'm_total': total_m, 'g': p_g, 'cd': p_cd, 'area': p_area, 'cr0': p_cr0, 'cr1': p_cr1, 
                'aux': p_aux_power, 'rho': h_rho, 'width': p_width, 'height': p_height, 'wheelbase': p_wheelbase, 'rw': p_wheel_rad, 
                
                # 2. Kuch uzatmasi va dinamika (9 parametr)
                'drive_type': dt_drive, 'motors': dt_motors, 'tire_mu': dt_tire_mu, 'regen_bias': dt_regen_bias / 100.0, 
                'p_max': m_max_p * 1000.0, 't_max': m_max_t, 'rpm_b': m_rpm, 'gear': m_gear, 'regen_cutoff': m_regen_cut,
                'eff_m': m_eff / 100.0, 'eff_i': m_inv / 100.0, 'eff_t': m_tra / 100.0, 'inertia_factor': p_inertia_factor,
                
                # 3. Batareya va Degradatsiya (15 parametr)
                'b_chem': b_chem, 'v_pack': pack_v, 'cap_ah': pack_ah, 'e_kwh': pack_energy_kwh, 
                'r0': (b_r0 / b_np) * b_ns, 'r1': (b_r1 / b_np) * b_ns, 'c1': (b_c1 * b_np) / b_ns, 
                'r2': (b_r2 / b_np) * b_ns, 'c2': (b_c2 * b_np) / b_ns, 'max_dis': b_max_dis_c, 'max_chg': b_max_chg_c, 
                'min_s': b_min_soc, 'max_s': b_max_soc, 'start_soc': b_start_soc, 'init_soc_guess': b_init_soc_guess, 
                'coulombic_eff': b_coulombic / 100.0, 'b_ns': b_ns, 'b_np': b_np, 'cycle_life': b_cycle_life, 
                'pack_overhead': b_pack_overhead, 'cell_v': b_cell_v, 'min_volt_cell': b_min_volt_cell,
                
                # 4. Termal, TMS va OCV (14 parametr)
                'cc': t_cc, 'cs': t_cs, 'rcs': t_rcs, 'rsa': t_rsa, 
                'tms_master_on': bool(tms_master_on),
                'tms_off_passive_factor': tms_off_passive_factor / 100.0,
                't_cooling_on': t_cooling_on, 't_cooling_off': t_cooling_off, 'cooling_power': cooling_power, 
                't_derate': t_derate, 't_cutoff': t_cutoff, 'soc_lut': soc_lut_val, 'ocv_lut': ocv_lut_val, 
                'tms_cop': tms_cop, 'tr_base_heat': tr_base_heat, 'tr_rate': tr_rate, 't_conv_coeff': t_conv_coeff,
                
                # 5. HVAC va Atrof-muhit (9 parametr)
                'h_on': hvac_state_val, 't_a': h_amb, 't_t': h_target, 'h_fan': h_fan, 'h_c': h_cool, 'h_h': h_heat, 
                'p_air': h_pres, 'cop_cool': h_cop_cool, 'cop_heat': h_cop_heat, 'c_cabin': h_c_cabin, 'k_env': h_k_env,
                
                # 6. Matematika va Xavfsizlik (Q1 Parametrlari bilan - 15 parametr)
                'q': ck_q, 'r': ck_r, 'ukf_q': ukf_q, 'ukf_r': ukf_r, 'dudt': cdudt, 'ea': cea, 't_ref': t_ref,
                'fade': cfade, 'socw': csocw, 'regen_capture': regen_capture, 'cost': p_cost_kwh, 
                'r_fade_min_t': r_fade_min_t, 'r_fade_max_s': r_fade_max_s / 100.0,
                
                # --- YANGI Q1 PARAMETRLAR ---
                'ekf_p0': p0_ekf, 
                'ukf_p0': p0_ukf, 
                'max_arr_r': max_arr_r, 
                'rk2_clip': rk2_clip, 
                'gps_dt_thresh': gps_dt_thresh, 
                'gps_accel_clip': gps_accel_clip,
                '_thermal_model_version': 9
            }
            st.session_state['b1_saved'] = True
            st.session_state['b1_status'] = "🟢 BLOCK 1: SCIENTIFIC PARAMS (Validated & Saved)"
            st.success("✅ **Boundaries initialized successfully.** 100% of mathematical frameworks are explicitly defined by the user and safely written to Memory.") 
            st.rerun()

    # =====================================================================
    # VIZUALIZATSIYA VA MATRITSA YUKLASH (FREEZE VIEW)
    # =====================================================================
    if st.session_state.get('b1_saved', False):
        sp = st.session_state['sim_params']
        
        c_res1, c_res2 = st.columns([1, 1.5]) 
        with c_res1:
            st.markdown("#### Research Configuration Summary") 
            st.markdown(f"**Gross Mass:** {sp['m_total']:.1f} kg") 
            st.markdown(f"**Battery Energy:** {sp['e_kwh']:.2f} kWh") 
            st.markdown(f"**Chemistry & Thermodynamics:** {sp['b_chem']} | Cycle Life: {sp['cycle_life']}") 
            st.markdown(f"**TMS Status:** {'ACTIVE ❄️' if sp.get('tms_master_on', True) else 'OFF ⚪'}")
            if not sp.get('tms_master_on', True):
                st.markdown(f"**Residual Passive Heat Rejection:** {sp.get('tms_off_passive_factor', 0.20)*100:.0f}%")
            st.markdown(f"**Filter Config:** EKF + UKF Engine Loaded (Custom P0)")
            st.markdown(f"**HVAC Status:** {'ACTIVE ❄️/🔥' if sp['h_on'] == 1.0 else 'DISABLED 🛑'}") 
            
            export_data = [
                ["Vehicle Model Name", v_model_name, "Text"], 
                ["Energy Cost", sp.get('cost', 0.15), "$/kWh"], 
                
                # --- 1. CHASSIS & DIMENSIONS ---
                ["Total Vehicle Mass (Gross)", sp.get('m_total', 1600.0), "kg"],
                ["Gravity (g)", sp.get('g', 9.81), "m/s²"],
                ["Drag Coefficient (Cd)", sp.get('cd', 0.29), "-"],
                ["Frontal Area (A)", sp.get('area', 2.2), "m²"],
                ["Static Roll Coeff (Cr0)", sp.get('cr0', 0.012), "-"],
                ["Dynamic Roll Coeff (Cr1)", sp.get('cr1', 0.00015), "-"],
                ["Standby/Aux Power", sp.get('aux', 250.0), "W"],
                ["Air Density", sp.get('rho', 1.18), "kg/m³"],
                ["Vehicle Width", sp.get('width', 1.76), "m"],
                ["Vehicle Height", sp.get('height', 1.53), "m"],
                ["Wheelbase", sp.get('wheelbase', 2.61), "m"],
                
                # --- 2. KUCH UZATMASI VA DINAMIKA ---
                ["Drive Architecture", sp.get('drive_type', 'FWD'), "Type"],
                ["Number of Motors", sp.get('motors', 1), "-"],
                ["Tire Friction Coeff (μ)", sp.get('tire_mu', 0.85), "-"],
                ["Regen Front Bias", sp.get('regen_bias', 1.0), "%/100"],
                ["Max Motor Power", sp.get('p_max', 70000.0), "W"],
                ["Max Motor Torque", sp.get('t_max', 180.0), "Nm"],
                ["Base Motor Speed", sp.get('rpm_b', 3500.0), "RPM"],
                ["Gear Ratio", sp.get('gear', 9.2), "-"],
                ["Wheel Radius", sp.get('rw', 0.315), "m"],
                ["Motor Efficiency", sp.get('eff_m', 0.95), "%/100"],
                ["Inverter Efficiency", sp.get('eff_i', 0.97), "%/100"],
                ["Transmission Efficiency", sp.get('eff_t', 0.96), "%/100"],
                ["Regen Cutoff Speed", sp.get('regen_cutoff', 5.0), "km/h"],
                ["Rotational Inertia Factor", sp.get('inertia_factor', 1.05), "-"],
                
                # --- 3. BATAREYA VA DEGRADATSIYA ---
                ["Battery Chemistry", sp.get('b_chem', 'LiFePO4'), "Type"],
                ["Pack Nominal Voltage", sp.get('v_pack', 320.0), "V"],
                ["Pack Capacity", sp.get('cap_ah', 135.0), "Ah"],
                ["Pack Energy", sp.get('e_kwh', 43.2), "kWh"],
                ["Expected Cycle Life", sp.get('cycle_life', 3000.0), "Cycles"],
                ["Cell Nominal Voltage", sp.get('cell_v', 3.2), "V"],
                ["Min Safe Cell Voltage", sp.get('min_volt_cell', 2.5), "V"],
                ["Ohmic Res (R0 Pack Level)", sp.get('r0', 0.1), "Ω"],
                ["Pol. Res 1 (R1 Pack Level)", sp.get('r1', 0.2), "Ω"],
                ["Pol. Cap 1 (C1 Pack Level)", sp.get('c1', 1000.0), "F"],
                ["Pol. Res 2 (R2 Pack Level)", sp.get('r2', 0.2), "Ω"],
                ["Pol. Cap 2 (C2 Pack Level)", sp.get('c2', 6000.0), "F"],
                ["Max Discharge C-Rate", sp.get('max_dis', 3.0), "C"],
                ["Max Charge C-Rate", sp.get('max_chg', 1.5), "C"],
                ["Min SOC Limit", sp.get('min_s', 5.0), "%"],
                ["Max SOC Limit", sp.get('max_s', 100.0), "%"],
                ["Starting True SOC", sp.get('start_soc', 98.0), "%"],
                ["Initial SOC Guess (Filter Base)", sp.get('init_soc_guess', 40.0), "%"],
                ["Coulombic Efficiency", sp.get('coulombic_eff', 0.995), "%/100"],
                ["Series Cells (Ns)", sp.get('b_ns', 100), "-"],
                ["Parallel Cells (Np)", sp.get('b_np', 1), "-"],
                ["Pack Mass Overhead", sp.get('pack_overhead', 1.2), "-"],
                
                # --- 4. TERMAL TIZIM, TMS VA OCV ---
                ["Core Heat Cap (Cc)", sp.get('cc', 6000.0), "J/K"],
                ["Surface Heat Cap (Cs)", sp.get('cs', 2000.0), "J/K"],
                ["Core-Surf Res (Rcs)", sp.get('rcs', 1.5), "K/W"],
                ["Surf-Amb Base Res (Rsa)", sp.get('rsa', 3.5), "K/W"],
                ["Convective Cooling Coeff", sp.get('t_conv_coeff', 0.05), "-"],
                ["Cooling Activation Temp", sp.get('t_cooling_on', 45.0), "°C"],
                ["Cooling Deactivation Temp", sp.get('t_cooling_off', 35.0), "°C"],
                ["Cooling System Elec Power", sp.get('cooling_power', 2500.0), "W"],
                ["TMS Chiller COP", sp.get('tms_cop', 2.0), "-"],
                ["Power Derate Temp", sp.get('t_derate', 55.0), "°C"],
                ["Critical Cutoff Temp", sp.get('t_cutoff', 65.0), "°C"],
                ["Thermal Runaway Base Heat", sp.get('tr_base_heat', 25000.0), "W"],
                ["Thermal Runaway Exothermic Rate", sp.get('tr_rate', 0.08), "-"],
                
                # --- 5. HVAC VA ATROF-MUHIT ---
                ["HVAC System State", sp.get('h_on', 1.0), "Boolean"],
                ["Ambient Temp", sp.get('t_a', 30.0), "°C"],
                ["Target Cabin Temp", sp.get('t_t', 22.0), "°C"],
                ["HVAC Fan Base Power", sp.get('h_fan', 200.0), "W"],
                ["Cooling Demand Factor", sp.get('h_c', 120.0), "W/°C"],
                ["Heating Demand Factor", sp.get('h_h', 180.0), "W/°C"],
                ["Air Pressure", sp.get('p_air', 101325.0), "Pa"],
                ["HVAC Cooling COP", sp.get('cop_cool', 2.5), "-"],
                ["HVAC Heating COP", sp.get('cop_heat', 0.95), "-"],
                ["Cabin Thermal Mass", sp.get('c_cabin', 250000.0), "J/K"],
                ["Cabin Insulation Rate", sp.get('k_env', 80.0), "W/K"],
                
                # --- 6. MATEMATIKA, STOXASTIKA VA XAVFSIZLIK (Q1 PARAMETRLARI) ---
                ["EKF Process Noise (Q)", sp.get('q', 1e-6), "-"],
                ["EKF Meas. Noise (R)", sp.get('r', 1e-2), "-"],
                ["UKF Process Noise (Q)", sp.get('ukf_q', 1e-6), "-"],
                ["UKF Meas. Noise (R)", sp.get('ukf_r', 1e-2), "-"],
                ["Entropic Heating Coeff (dU/dT)", sp.get('dudt', 0.0001), "V/K"],
                ["Activation Energy (Ea)", sp.get('ea', 25000.0), "J/mol"],
                ["Arrhenius Reference Temp", sp.get('t_ref', 25.0), "°C"],
                ["Base Regen Fade Coeff", sp.get('fade', 0.9), "-"],
                ["SOC Coulombic Integration Weight", sp.get('socw', 0.5), "-"],
                ["Regen Fade Min Temp", sp.get('r_fade_min_t', -5.0), "°C"],
                ["Regen Fade Max SOC", sp.get('r_fade_max_s', 0.9), "%/100"],
                ["EKF Init Covariance (P0)", sp.get('ekf_p0', 0.1), "-"],
                ["UKF Init Covariance (P0)", sp.get('ukf_p0', 0.1), "-"],
                ["Max Arrhenius Res (Cold Limit)", sp.get('max_arr_r', 0.5), "Ω"],
                ["RK2 Thermal Growth Clip", sp.get('rk2_clip', 5.0), "°C/s"],
                ["GPS Anomaly dt Threshold", sp.get('gps_dt_thresh', 3.0), "s"],
                ["GPS Acceleration Clip", sp.get('gps_accel_clip', 2.0), "m/s²"]
            ]
            
            df_export = pd.DataFrame(export_data, columns=["Parameter Name", "Value", "Unit (SI)"]) 
            excel_buffer = io.BytesIO() 
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer: 
                df_export.to_excel(writer, index=False, sheet_name="Scientific_Specs") 
                edited_ocv_df.to_excel(writer, index=False, sheet_name="Battery_OCV_Curve") 
            excel_buffer.seek(0) 
            
            st.download_button(
                label="📥 Download Scientific Parameters (Excel)",
                data=excel_buffer,
                file_name=f"QwatLab_V5_Params_{v_model_name.strip().replace(' ', '_')}.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                key="b1_frozen_download_btn"
            ) 
            
        with c_res2:
            fig = go.Figure(data=[go.Pie(
                labels=['Chassis Mass', 'Payload/Driver', 'Battery Pack (Inc. BMS & Casing)'], 
                values=[p_chassis_mass, p_payload, (b_cell_mass * b_ns * b_np) * b_pack_overhead], 
                hole=.4, 
                marker=dict(colors=['#1f77b4', '#ff7f0e', '#2ca02c']) 
            )])
            fig.update_layout(title="Mass Distribution Matrix", margin=dict(t=30, b=0, l=0, r=0), height=300) 
            st.plotly_chart(fig, width='stretch', key="mass_distribution_matrix") 

if st.session_state.get('b1_saved', False):
    st.markdown("""
        <style>
        div[data-testid="stExpander"]:nth-of-type(2) { border: 2px solid #28a745 !important; background-color: rgba(40, 167, 69, 0.02) !important; border-radius: 8px; }
        div[data-testid="stExpander"]:nth-of-type(2) summary p { color: #28a745 !important; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        div[data-testid="stExpander"]:nth-of-type(2) { border: 2px solid #ffc107 !important; background-color: rgba(255, 193, 7, 0.02) !important; border-radius: 8px; }
        div[data-testid="stExpander"]:nth-of-type(2) summary p { color: #b58100 !important; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

# =====================================================================
# 1-BLOK oxiri
# =====================================================================

# =====================================================================
# 2-BLOK: KINEMATIKA VA HARAKAT SIKLI (V1.0.0 ILMIY YANGILANISH)
# =====================================================================

# 2-blok uchun holatni boshqarish
if 'b2_saved' not in st.session_state:
    st.session_state['b2_saved'] = False
if 'b2_temp_calc' not in st.session_state:
    st.session_state['b2_temp_calc'] = pd.DataFrame() 

with st.expander("📈 BLOCK 2: KINEMATIC PROFILE & DRIVE CYCLE (SCIENTIFIC DATA ENGINE)", expanded=True):
    st.info("⚠️ **IMPORTANT:** The `Master Table` generated here acts as the spatial-temporal boundary conditions for the differential equations in Block 3.")
    st.success("💡 **Scientific Tip:** Use 'Manual Mode' to upload real-world empirical CAN-bus or GPS telemetry for true Digital Twin validation. Use 'Auto Mode' with Stochastic Noise to simulate WLTP/UDDS-like synthetic profiles.")
    
    use_3d_topo = st.toggle("🏔️ Enable Environment Dynamics (Gradient & Wind Vector)", value=False, help="Injects dynamic Road Slope (Grade) and Aerodynamic Headwind into the time-series.")

    col_rad1, col_rad2 = st.columns([2, 1])
    with col_rad1:
        cycle_mode = st.radio(
            "🔀 Select Kinematic Profile Source:", 
            ["Auto Mode (Stochastic Synthetic Generator)", "Manual Mode (Real-World Telemetry Upload)"],
            horizontal=True
        )

    st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

    df_temp = pd.DataFrame()

    # =========================================================
    # 1-REJIM: AVTO REJIM (STOXASTIK SINTETIK SIKL)
    # =========================================================
    if "Auto" in cycle_mode:
        st.markdown("### ⚙️ Auto Mode: Stochastic Profile Synthesizer")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            a_dur = st.number_input("1. Total Trip Duration [s]", min_value=100, max_value=7200, value=1800, step=10, help="Total simulation length in seconds.")
            a_vmax = st.number_input("2. Max Cruising Speed [km/h]", min_value=10.0, max_value=250.0, value=90.0, step=5.0, help="Physical speed limit of the synthetic route.")
            a_acc = st.number_input("3. Average Acceleration [m/s²]", min_value=0.1, max_value=8.0, value=1.5, step=0.1, help="Positive kinetic energy derivative limit.")
        with c2:
            a_dec = st.number_input("4. Average Deceleration [m/s²]", min_value=0.1, max_value=12.0, value=2.0, step=0.1, help="Negative kinetic energy derivative (Braking).")
            a_stops = st.number_input("5. Traffic Stop Events", min_value=0, max_value=50, value=5, help="Number of complete stops (0 km/h) simulating intersections.")
            a_stop_t = st.number_input("6. Dwell Time per Stop [s]", min_value=5, max_value=300, value=20, help="Idling duration at each stop event.")
        with c3:
            a_noise = st.number_input("7. Stochastic Speed Noise [%]", min_value=0.0, max_value=20.0, value=3.0, help="Superimposes Gaussian noise to mimic human driving micro-adjustments.")
            a_wind = st.number_input("8. Constant Wind Vector [m/s]", min_value=-30.0, max_value=30.0, value=0.0, help="(+) Headwind opposing motion. (-) Tailwind assisting motion.")
            
        if use_3d_topo:
            a_grad = st.number_input("9. Constant Road Gradient [°]", min_value=-25.0, max_value=25.0, value=0.0, help="Incline angle. (-) for downhill, (+) for uphill.")
        else:
            a_grad = 0.0

        if st.button("🔍 Generate Scientific Preview (Auto Mode)", type="secondary"):
            with st.spinner("Synthesizing Kinematic Trajectory via Markov-Gaussian approach..."):
                t_arr = np.arange(0, a_dur + 1, 1.0)
                v_arr = np.zeros_like(t_arr)
                v_target = a_vmax / 3.6
                
                num_segments = a_stops + 1
                seg_len = len(t_arr) // num_segments
                
                current_v = 0.0
                for i in range(1, len(t_arr)):
                    seg_idx = i // seg_len
                    rem_in_seg = (seg_len * (seg_idx + 1)) - i
                    time_needed_to_stop = current_v / a_dec if a_dec > 0 else 0
                    
                    if seg_idx < a_stops and rem_in_seg <= (a_stop_t + time_needed_to_stop):
                        current_v = max(0.0, current_v - a_dec)
                        if rem_in_seg <= a_stop_t:
                            current_v = 0.0
                    else:
                        current_v = min(v_target, current_v + a_acc)
                    v_arr[i] = current_v
               
                # Stoxastik inyektsiya
                if a_noise > 0:
                    np.random.seed(42) # Reproducibility uchun
                    noise = np.random.normal(0, (a_noise/100) * v_target, len(t_arr))
                    v_arr = np.where(v_arr > 0.5, np.clip(v_arr + noise, 0.5, None), 0.0)
                    v_arr = savgol_filter(v_arr, window_length=min(15, len(v_arr)//2 * 2 + 1), polyorder=3)
                    v_arr = np.clip(v_arr, 0, None)
                    v_arr[v_arr < 0.2] = 0.0

                df_temp = pd.DataFrame({
                    "A-Time [s]": t_arr,
                    "B-Speed [km/h]": v_arr * 3.6,
                    "C-Acceleration [m/s2]": np.concatenate(([0.0], np.diff(v_arr) / np.maximum(1e-9, np.diff(t_arr)))),
                    "D-Speed [m/s]": v_arr,
                    "F-Headwind [m/s]": a_wind,
                    "E-Gradient [°]": a_grad if use_3d_topo else 0.0
                })
                
                st.session_state['b2_temp_calc'] = df_temp
                st.session_state['b2_saved'] = False 
                st.rerun()

    # =========================================================
    # 2-REJIM: QO'LDA YUKLASH (EMPIRICAL TELEMETRY MODE)
    # =========================================================
    else:
        st.markdown("### 📁 Manual Mode: Empirical Telemetry Injection")
        st.markdown("**Step 1: Download Standardized Template**")
        c_dur, c_btn = st.columns([1, 2])
        with c_dur:
            m_dur = st.number_input("Target Template Duration [s]", min_value=10, max_value=100000, value=600, step=10)
        with c_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            df_template = pd.DataFrame({
                "A-Time [s]": np.arange(m_dur),
                "B-Speed [km/h]": np.zeros(m_dur),
                "C-Acceleration [m/s2] (Do not edit - Auto calculated)": np.nan,
                "F-Headwind [m/s] (+ Headwind, - Tailwind)": np.zeros(m_dur),
                "E-Gradient [°]": np.zeros(m_dur) if use_3d_topo else 0.0
            })
            
            temp_buffer = io.BytesIO()
            with pd.ExcelWriter(temp_buffer, engine='openpyxl') as writer:
                df_template.to_excel(writer, index=False, sheet_name="Upload_Template")
            temp_buffer.seek(0)
            
            st.download_button(
                label=f"📥 Download Empty Matrix for {m_dur}s (Excel)",
                data=temp_buffer,
                file_name=f"QwatLab_Telemetry_Template_{m_dur}s.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        st.markdown("**Step 2: Upload Empirical Dataset**")
        uploaded_file = st.file_uploader("Upload populated CAN/GPS data (.xlsx)", type=['xlsx'])
        
        if uploaded_file is not None:
            df_raw = pd.read_excel(uploaded_file)
            req_cols = ["A-Time [s]", "B-Speed [km/h]"]
            missing = [c for c in req_cols if c not in df_raw.columns]
            
            if missing:
                st.error(f"❌ **Data Integrity Error:** Missing mandatory columns: {', '.join(missing)}")
            else:
                st.success("✅ **Data Integrity Passed:** Core spatial-temporal columns mapped.")
                
                st.markdown("**Step 3: Signal Conditioning (Optional)**")
                sg_on = st.toggle("Enable Savitzky-Golay Low-Pass Filter (For noisy CAN-bus velocity data)", value=False)
                if sg_on:
                    c_sg1, c_sg2 = st.columns(2)
                    with c_sg1:
                        sg_win = st.number_input("Window Length (Must be odd)", min_value=5, max_value=101, value=21, step=2)
                    with c_sg2:
                        sg_poly = st.number_input("Polynomial Order", min_value=1, max_value=5, value=3)
                
                if st.button("🔄 Process Empirical Data (Extract Vectors)", type="secondary"):
                    df_temp = df_raw.copy()
                    
                    df_temp["A-Time [s]"] = pd.to_numeric(df_temp["A-Time [s]"], errors='coerce').fillna(0)
                    df_temp["B-Speed [km/h]"] = pd.to_numeric(df_temp["B-Speed [km/h]"], errors='coerce').fillna(0)
                    df_temp["D-Speed [m/s]"] = df_temp["B-Speed [km/h]"] / 3.6
                    
                    # Gradient va shamol ma’lumotlarini zaxira qiymatlar bilan tahlil qilish
                    wind_col = next((c for c in df_temp.columns if "Headwind" in c), None)
                    grad_col = next((c for c in df_temp.columns if "Gradient" in c), None)
                    
                    df_temp["F-Headwind [m/s]"] = pd.to_numeric(df_temp[wind_col], errors='coerce').fillna(0.0) if wind_col else 0.0
                    df_temp["E-Gradient [°]"] = pd.to_numeric(df_temp[grad_col], errors='coerce').fillna(0.0) if (use_3d_topo and grad_col) else 0.0

                    # Filtrlash
                    if sg_on:
                        actual_win = min(sg_win, len(df_temp))
                        if actual_win % 2 == 0: actual_win -= 1
                        if actual_win > sg_poly:
                            df_temp["D-Speed [m/s]"] = savgol_filter(df_temp["D-Speed [m/s]"], actual_win, sg_poly)
                            df_temp["D-Speed [m/s]"] = np.clip(df_temp["D-Speed [m/s]"], 0, None)
                        df_temp["B-Speed [km/h]"] = df_temp["D-Speed [m/s]"] * 3.6

                    # Hosila qiymatini dinamik ajratib olish (tezlanish)
                    dt_series = df_temp["A-Time [s]"].diff().fillna(1.0)
                    dt_series = np.where(dt_series <= 0, 0.1, dt_series)
                    dv_series = df_temp["D-Speed [m/s]"].diff().fillna(0.0)
                    
                    # Fizik cheklov: odatiy elektromobillarda tezlanish ±15 m/s² dan oshmasligi kerak
                    df_temp["C-Acceleration [m/s2]"] = np.clip(dv_series / dt_series, -15.0, 15.0) 
                    
                    st.session_state['b2_temp_calc'] = df_temp
                    st.session_state['b2_saved'] = False
                    st.rerun()

    # =========================================================
    # PREVIEW VA QABUL QILISH (TWO-STEP VERIFICATION)
    # =========================================================
    display_cols = ["A-Time [s]", "B-Speed [km/h]", "C-Acceleration [m/s2]", "D-Speed [m/s]", "F-Headwind [m/s]", "E-Gradient [°]"]

    if not st.session_state['b2_temp_calc'].empty:
        df_show = st.session_state['b2_temp_calc']
        
        # 🛡️ Xavfsizlik nazorati tuzilmasini bajarish
        if "B-Speed [km/h]" in df_show.columns and "D-Speed [m/s]" not in df_show.columns:
            df_show["D-Speed [m/s]"] = df_show["B-Speed [km/h]"] / 3.6
        if "C-Acceleration [m/s2]" not in df_show.columns: df_show["C-Acceleration [m/s2]"] = 0.0
        if "F-Headwind [m/s]" not in df_show.columns: df_show["F-Headwind [m/s]"] = 0.0
        if "E-Gradient [°]" not in df_show.columns: df_show["E-Gradient [°]"] = 0.0
        if "A-Time [s]" not in df_show.columns: df_show["A-Time [s]"] = np.arange(len(df_show))

        try:
            time_vals = df_show["A-Time [s]"].fillna(0).values
            speed_vals = df_show["D-Speed [m/s]"].fillna(0).values
            total_dist = np.trapezoid(speed_vals, time_vals) if hasattr(np, 'trapezoid') else np.trapz(speed_vals, time_vals)
        except Exception:
            total_dist = 0.0
            
        st.info(f"🛣️ **Trajectory Validated.** Total Trip Distance: **{(total_dist/1000):.3f} km**.")
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=df_show["A-Time [s]"], y=df_show["B-Speed [km/h]"], name="Speed [km/h]", line=dict(color='#1E3A8A', width=2)), secondary_y=False)
        fig.add_trace(go.Scatter(x=df_show["A-Time [s]"], y=df_show["C-Acceleration [m/s2]"], name="Acceleration [m/s²]", line=dict(color='#E53E3E', width=1, dash='dot')), secondary_y=True)
        fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=350, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig.update_yaxes(title_text="Speed [km/h]", secondary_y=False)
        fig.update_yaxes(title_text="Derivative (Accel) [m/s²]", secondary_y=True)
        st.plotly_chart(fig, width='stretch', key="trajectory_preview_chart")
        
        with st.expander("🔍 View Raw Vector Data (First 1000 nodes)"):
            safe_cols_show = [c for c in display_cols if c in df_show.columns]
            st.dataframe(df_show[safe_cols_show].head(1000), hide_index=True)

        if not st.session_state.get('b2_saved', False):
            st.warning("⚠️ The spatial-temporal boundary conditions are generated but **NOT YET SAVED**. Click 'Accept' to lock them for Block 3.")
            if st.button("✅ ACCEPT & LOCK TRAJECTORY FOR PHYSICS ENGINE", type="primary"):
                st.session_state['df_for_calc'] = df_show.copy()
                st.session_state['b2_saved'] = True
                st.session_state['b2_status'] = "🟢 BLOCK 2: KINEMATIC PROFILE (Validated & Locked)"
                st.success("✅ **Master Table securely saved to Memory!** The differential solver in Block 3 is now ready.")
                st.rerun()
                
    if st.session_state.get('b2_saved', False) and 'df_for_calc' in st.session_state:
        df_export = st.session_state['df_for_calc']
        export_cols = [c for c in display_cols if c in df_export.columns]
        if not export_cols: export_cols = df_export.columns.tolist()

        master_buffer = io.BytesIO()
        try:
            with pd.ExcelWriter(master_buffer, engine='openpyxl') as writer:
                if not df_export.empty:
                    df_export[export_cols].to_excel(writer, index=False, sheet_name="Master_Calculation_Table")
                else:
                    pd.DataFrame(["No data available"]).to_excel(writer, index=False, sheet_name="Error_Empty_Table")
            master_buffer.seek(0)
            
            st.download_button(
                label="📥 Download Master Kinematic Vectors (Excel format)",
                data=master_buffer,
                file_name="EV_Kinematic_Master.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="secondary",
                key="b2_frozen_download_btn"
            )
        except Exception as e:
            st.error(f"⚠️ Internal Export Error: {e}")

# =====================================================================
# 🎨 DINAMIK CSS INTERFEYS: 2-BLOK UCHUN
# =====================================================================
if st.session_state.get('b2_saved', False):
    st.markdown("""
        <style>
        div[data-testid="stExpander"]:nth-of-type(3) { border: 2px solid #28a745 !important; background-color: rgba(40, 167, 69, 0.02) !important; border-radius: 8px; }
        div[data-testid="stExpander"]:nth-of-type(3) summary p { color: #28a745 !important; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        div[data-testid="stExpander"]:nth-of-type(3) { border: 2px solid #ffc107 !important; background-color: rgba(255, 193, 7, 0.02) !important; border-radius: 8px; }
        div[data-testid="stExpander"]:nth-of-type(3) summary p { color: #b58100 !important; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

# =====================================================================
# 2-BLOK oxiri
# =====================================================================

# =====================================================================
# 3-BLOK: EV PARAMETRLARI DVIGATELI (FIZIKA - V1.0.0)
# =====================================================================

if 'b3_saved' not in st.session_state:
    st.session_state['b3_saved'] = False

# =========================================================
# 1. YORDAMCHI FUNKSIYALAR (NUMBA UCHUN)
# =========================================================
@njit(fastmath=True, cache=True)
def generate_gaussian_noise(std_dev):
    u1 = max(1e-10, np.random.rand())
    u2 = np.random.rand()
    z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return z0 * std_dev

@njit(fastmath=True, cache=True)
def numba_interp1d(x_val, xp, fp):
    # O(log N) ikkilik qidiruv — tezkor interpolatsiya uchun
    if x_val <= xp[0]: return fp[0]
    if x_val >= xp[-1]: return fp[-1]
    idx = np.searchsorted(xp, x_val) - 1
    idx = max(0, min(idx, len(xp) - 2))
    weight = (x_val - xp[idx]) / (xp[idx+1] - xp[idx])
    return fp[idx] + weight * (fp[idx+1] - fp[idx])

@njit(fastmath=True, cache=True)
def get_docv_dsoc(soc, xp, fp):
    # EKF Yakobian qadami 1e-4 qilib belgilandi (singulyarlikning oldini olish uchun)
    delta = 1e-4
    soc_up = min(1.0, soc + delta)
    soc_dn = max(0.0, soc - delta)
    ocv_up = numba_interp1d(soc_up, xp, fp)
    ocv_dn = numba_interp1d(soc_dn, xp, fp)
    return (ocv_up - ocv_dn) / (soc_up - soc_dn + 1e-8)

# =========================================================
# 2. ASOSIY DVIGATEL (KINETICS & THERMODYNAMICS)
# =========================================================

@njit(fastmath=True, cache=True)
def run_ev_core_engine(
    N_route, dt_arr_in, v_ms_in, a_ms2_in, grad_deg_in, headwind_ms_in,
    soc_lut, ocv_lut, p_params, true_start_soc, filter_guess_soc
):
    """
    QwatLab EV V1.0.0 ilmiy elektro-termal yadrosi.

    Holatlarning ishoraviy kelishuvi
    --------------------------------
    I > 0  : batareya razryadi
    I < 0  : batareya zaryadi / regenerativ tormozlanish
    P_batt > 0 : batareyadan energiya olinishi
    P_batt < 0 : batareyaga energiya qaytishi

    Termal model
    -----------
    Ikki tugunli yig‘ma batareya modeli:
        Cc*dTc/dt = Qgen + Qrun - (Tc-Ts)/Rcs
        Cs*dTs/dt = (Tc-Ts)/Rcs - (Ts-Ta)/Rsa - Qcool

    Qgen energiya jihatdan izchil Bernardi ko‘rinishida hisoblanadi:
        Qirr = I*(OCV - Vterminal)
        Qrev = -I*T*dOCV/dT
        Qgen = Qirr + Qrev

    Bu kalibrlangan muhandislik teskari-dinamika va marshrutni qayta ijro etish
    modeli bo‘lib, birinchi tamoyillarga asoslangan elektro-kimyoviy model emas.
    Transport vositasining tezligi va o‘lchangan tezlanishi marshrut kirishi sifatida
    olinadi; shu sababli motor cheklovlari tezlikni qayta integratsiya qilish o‘rniga
    erishish mumkin bo‘lgan kuch chegaralari sifatida baholanadi.
    R/C, OCV va dOCV/dT parametrlari nashr darajasidagi validatsiya uchun tajribada aniqlanishi kerak.
    """
    # -------------------- parametrlarni ajratib olish --------------------
    m_tot = max(1e-6, p_params[0]); g = max(1e-6, p_params[1])
    cd = max(0.0, p_params[2]); area = max(0.0, p_params[3])
    cr0 = max(0.0, p_params[4]); cr1 = max(0.0, p_params[5])
    aux_baseline = max(0.0, p_params[6]); rho_air = max(0.0, p_params[7])
    tire_mu = max(0.0, p_params[8]); rw = max(1e-6, p_params[9]); gear_ratio = max(1e-6, p_params[10])
    eff_m = max(1e-3, min(1.0, p_params[11])); eff_i = max(1e-3, min(1.0, p_params[12])); eff_t = max(1e-3, min(1.0, p_params[13]))
    motor_max_p = max(0.0, p_params[14]); regen_bias = max(0.0, min(1.0, p_params[15])); regen_cutoff = max(0.0, p_params[16])
    cap_ah = max(1e-6, p_params[17]); r0_ref = max(1e-9, p_params[18])
    r1 = max(1e-9, p_params[19]); c1 = max(1e-9, p_params[20]); r2 = max(1e-9, p_params[21]); c2 = max(1e-9, p_params[22])
    max_c_charge = max(0.0, p_params[23]); max_c_discharge = max(0.0, p_params[24])
    ns_series = max(1.0, p_params[25]); np_parallel = max(1.0, p_params[26]); coulombic_eff = max(0.0, min(1.0, p_params[27]))
    t_amb = p_params[28]
    cc_core = max(1.0, p_params[29]); cc_surf = max(1.0, p_params[30])
    r_cs = max(1e-7, p_params[31]); r_sa_base = max(1e-7, p_params[32])
    t_cool_on = p_params[33]; t_cool_off = p_params[34]; p_cool_power = max(0.0, p_params[35])
    t_derate = p_params[36]; t_cutoff_limit = p_params[37]
    hvac_on = p_params[38]; t_cabin_set = p_params[39]; h_fan = max(0.0, p_params[40]); h_cool = max(0.0, p_params[41]); h_heat = max(0.0, p_params[42])
    min_soc_limit = max(0.0, min(100.0, p_params[43])); max_soc_limit = max(0.0, min(100.0, p_params[44]))
    bms_on = p_params[45]; tr_on = p_params[46]; tr_temp = p_params[47]; t_max_sim = max(t_cutoff_limit + 1.0, p_params[48])
    ekf_q = max(0.0, p_params[49]); ekf_r = max(1e-12, p_params[50]); ukf_q = max(0.0, p_params[51]); ukf_r = max(1e-12, p_params[52])
    dudt = p_params[53]; ea = max(0.0, p_params[54]); t_ref_c = p_params[55]; regen_fade = max(0.0, min(1.0, p_params[56]))
    calib_factor = p_params[58]; is_hp = p_params[59]
    cycle_life = max(1.0, p_params[60]); inertia_factor = max(1.0, p_params[62])
    cop_cool = max(1.0, p_params[63]); cop_heat = max(0.1, p_params[64]); c_cabin = max(1.0, p_params[65]); k_env = max(0.0, p_params[66])
    tms_cop = max(1.0, p_params[67]); tr_base_heat = max(0.0, p_params[68]); tr_rate = max(0.0, p_params[69]); t_conv_coeff = max(0.0, p_params[70])
    tms_master_on = p_params[82]
    tms_off_passive_factor = max(0.0, min(1.0, p_params[83]))
    regen_capture = max(0.0, min(1.0, p_params[84]))
    min_volt_cell = max(0.0, p_params[71]); r_fade_min_t = p_params[72]; r_fade_max_s = max(0.0, min(1.0, p_params[73]))
    p0_ekf = max(1e-12, p_params[74]); p0_ukf = max(1e-12, p_params[75]); max_arr_r = max(1e-9, p_params[76]); rk2_clip = max(0.01, p_params[77])
    gps_dt_thresh = max(0.0, p_params[78]); gps_accel_clip = max(0.0, p_params[79])
    motor_max_torque = max(0.0, p_params[80]); motor_base_rpm = max(1.0, p_params[81])

    if N_route < 2:
        z = np.zeros(1)
        return (0, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z, z)

    max_steps = N_route - 1
    t_sim_arr = np.zeros(max_steps); dt_out = np.zeros(max_steps)
    v_out = np.zeros(max_steps); a_out = np.zeros(max_steps); grad_out = np.zeros(max_steps); wind_out = np.zeros(max_steps)
    f_aero_arr = np.zeros(max_steps); f_roll_arr = np.zeros(max_steps); f_grade_arr = np.zeros(max_steps); f_inert_arr = np.zeros(max_steps); f_tot_arr = np.zeros(max_steps); slip_loss_arr = np.zeros(max_steps)
    rpm_arr = np.zeros(max_steps); torque_arr = np.zeros(max_steps); p_mech_arr = np.zeros(max_steps); p_trac_arr = np.zeros(max_steps); p_regen_arr = np.zeros(max_steps); p_elec_arr = np.zeros(max_steps)
    p_aux_arr = np.zeros(max_steps); p_hvac_arr = np.zeros(max_steps); p_tms_arr = np.zeros(max_steps); curr_arr = np.zeros(max_steps); crate_arr = np.zeros(max_steps); ocv_arr = np.zeros(max_steps); v_term_arr = np.zeros(max_steps)
    soc_true_arr = np.zeros(max_steps); soc_ekf_arr = np.zeros(max_steps); soc_ukf_arr = np.zeros(max_steps); ah_thru_arr = np.zeros(max_steps); soh_arr = np.zeros(max_steps)
    t_c_arr = np.zeros(max_steps); t_s_arr = np.zeros(max_steps); q_loss_arr = np.zeros(max_steps); q_ent_arr = np.zeros(max_steps); q_gen_arr = np.zeros(max_steps); q_cool_arr = np.zeros(max_steps); q_fire_arr = np.zeros(max_steps)
    q_cs_arr = np.zeros(max_steps); q_sa_arr = np.zeros(max_steps); t_coolant_arr = np.zeros(max_steps); tms_state_arr = np.zeros(max_steps); q_balance_arr = np.zeros(max_steps)
    status_flag = np.zeros(max_steps); dist_arr = np.zeros(max_steps); energy_arr = np.zeros(max_steps)

    soc_true = max(0.0, min(1.0, true_start_soc / 100.0)); soc_ekf = max(0.0, min(1.0, filter_guess_soc / 100.0)); soc_ukf = soc_ekf
    t_core = t_amb; t_surf = t_amb; t_cabin = t_amb
    u_p1 = 0.0; u_p2 = 0.0
    # EKF holati: [SoC, Up1, Up2]. Qutblanish holatlari endi
    # simulyatorning yashirin (haqiqiy) qiymatlaridan olinmaydi, balki filtrda baholanadi.
    ekf_up1 = 0.0; ekf_up2 = 0.0
    P_ekf = np.zeros((3, 3))
    P_ekf[0, 0] = p0_ekf
    P_ekf[1, 1] = 0.05 * 0.05
    P_ekf[2, 2] = 0.05 * 0.05
    P_ukf = p0_ukf
    tms_is_on = 0.0; t_clock = 0.0; cum_dist = 0.0; cum_energy = 0.0; cum_ah = 0.0
    total_ah_life = max(1.0, 2.0 * cap_ah * cycle_life)
    m_eff = max(1.0, m_tot * inertia_factor)
    R_gas = 8.314462618; t_ref_k = max(200.0, t_ref_c + 273.15)
    v_min_safe_pack = min_volt_cell * ns_series
    max_ocv_cell = numba_interp1d(1.0, soc_lut, ocv_lut); v_max_safe_pack = max_ocv_cell * ns_series
    omega_base = motor_base_rpm * 2.0 * math.pi / 60.0
    physical_pmax = motor_max_p if motor_max_p > 0.0 else 0.0
    if motor_max_torque > 0.0:
        physical_pmax = min(physical_pmax if physical_pmax > 0.0 else motor_max_torque * omega_base, motor_max_torque * omega_base)

    step_idx = 0; terminal_stop = False
    while step_idx < max_steps and not terminal_stop:
        dt = dt_arr_in[step_idx]
        if not math.isfinite(dt) or dt <= 0.0: break

        # ---------- kirishlar va xavfsizlik holati ----------
        v_curr = max(0.0, v_ms_in[step_idx]); a_curr = a_ms2_in[step_idx]
        if not math.isfinite(a_curr): a_curr = 0.0
        if dt > gps_dt_thresh and gps_accel_clip > 0.0: a_curr = max(-gps_accel_clip, min(gps_accel_clip, a_curr))
        grad_curr = grad_deg_in[step_idx] if math.isfinite(grad_deg_in[step_idx]) else 0.0
        wind_curr = headwind_ms_in[step_idx] if math.isfinite(headwind_ms_in[step_idx]) else 0.0
        theta = grad_curr * math.pi / 180.0
        v_air = v_curr + wind_curr
        t_core_k = max(200.0, t_core + 273.15)

        is_tr = tr_on > 0.5 and t_core >= tr_temp
        if bms_on > 0.5:
            if soc_true <= min_soc_limit / 100.0 + 1e-10:
                status_flag[step_idx] = 3.0; terminal_stop = True; break
            if t_core >= t_cutoff_limit and not is_tr:
                status_flag[step_idx] = 1.0; terminal_stop = True; break

        q_fire = 0.0
        if is_tr:
            status_flag[step_idx] = 2.0
            exponent = min(20.0, tr_rate * max(0.0, t_core - tr_temp))
            q_fire = min(1e7, tr_base_heat * math.exp(exponent))

        # ---------- transport vositasining bo‘ylama dinamikasi ----------
        f_aero = 0.5 * rho_air * cd * area * v_air * abs(v_air)
        f_roll = m_tot * g * max(0.0, cr0 + cr1 * abs(v_curr)) * math.cos(theta)
        f_grade = m_tot * g * math.sin(theta)
        f_inert = m_eff * a_curr
        f_total = f_aero + f_roll + f_grade + f_inert
        f_adhesion = max(0.0, m_tot * g * math.cos(theta) * tire_mu)
        traction_deficit = max(0.0, abs(f_total) - f_adhesion)
        slip_loss = traction_deficit * abs(v_curr)
        p_wheel = f_total * v_curr
        wheel_omega = v_curr / rw; motor_omega = wheel_omega * gear_ratio; motor_rpm = motor_omega * 60.0 / (2.0 * math.pi)

        # Kuchga asoslangan teskari dinamika momenti. Tortish va regeneratsiyada
        # energiya oqimi yo‘nalishlari qarama-qarshi bo‘lgani uchun samaradorlik
        # tegishli yo‘nalishda qo‘llanadi. Ilashish faqat hisobot ko‘rsatkichi emas, haqiqiy kuch cheklovidir.
        f_drive_demand = max(0.0, f_total)
        f_regen_demand = max(0.0, -f_total)
        f_drive_limited = min(f_drive_demand, f_adhesion)
        f_regen_limited = min(f_regen_demand, f_adhesion)
        torque_drive_required = (f_drive_demand * rw) / max(1e-9, gear_ratio * eff_t)
        torque_regen_required = (f_regen_demand * rw * eff_t) / max(1e-9, gear_ratio)
        torque_required = torque_drive_required if f_total >= 0.0 else -torque_regen_required

        p_trac = 0.0; p_regen = 0.0; p_motor_elec = 0.0; power_limited = False
        traction_limited = False
        derate_factor = 1.0
        if bms_on > 0.5 and t_core > t_derate:
            derate_factor = max(0.0, 1.0 - (t_core - t_derate) / max(1.0, t_cutoff_limit - t_derate))
        local_tmax = motor_max_torque * derate_factor
        local_pmax = physical_pmax * derate_factor
        if not is_tr:
            if f_total >= 0.0:
                req_motor_torque = torque_drive_required
                adhesion_torque = (f_adhesion * rw) / max(1e-9, gear_ratio * eff_t)
                actual_motor_torque = min(req_motor_torque, adhesion_torque, local_tmax)
                if req_motor_torque > adhesion_torque + 1e-9:
                    traction_limited = True
                if motor_omega > 1e-9:
                    actual_motor_torque = min(actual_motor_torque, local_pmax / motor_omega)
                power_limited = req_motor_torque > actual_motor_torque + 1e-9 and not traction_limited
                actual_motor_mech = actual_motor_torque * motor_omega
                p_trac = actual_motor_mech / (eff_m * eff_i)
                p_motor_elec = p_trac
            else:
                if v_curr * 3.6 > regen_cutoff and motor_omega > 1e-9:
                    req_regen_torque = torque_regen_required
                    adhesion_torque = (f_adhesion * rw * eff_t) / max(1e-9, gear_ratio)
                    regen_torque_limit = min(local_tmax, local_pmax / motor_omega) * regen_fade
                    actual_regen_torque = min(req_regen_torque, adhesion_torque, regen_torque_limit)
                    if req_regen_torque > adhesion_torque + 1e-9:
                        traction_limited = True
                    req_regen_mech = req_regen_torque * motor_omega
                    actual_regen_mech = actual_regen_torque * motor_omega
                    # regen_bias talab qilingan tormozlash momentining
                    # modellashtirilayotgan yetakchi o‘q yoki motorga ajratilgan ulushidir. U batareya
                    # samaradorligi emas; regen_capture elektr energiyani qabul qilish yo‘qotishini ifodalaydi.
                    p_regen = actual_regen_mech * eff_m * eff_i * regen_capture * regen_bias
                    p_motor_elec = -p_regen
                    power_limited = req_regen_mech > actual_regen_mech + 1e-9 and not traction_limited
        if (power_limited or traction_limited) and status_flag[step_idx] == 0.0: status_flag[step_idx] = 4.0

        # ---------- salon HVAC tizimi ----------
        p_hvac = 0.0; q_hvac = 0.0
        if hvac_on > 0.5 and not is_tr:
            err = t_cabin - t_cabin_set
            if err > 0.5:
                p_active = min(h_cool * err, h_cool * 15.0); p_hvac = h_fan + p_active; q_hvac = -p_active * cop_cool
            elif err < -0.5:
                p_active = min(h_heat * abs(err), h_heat * 15.0); p_hvac = h_fan + p_active; q_hvac = p_active * cop_heat
            else:
                p_hvac = h_fan
            q_env = -k_env * (t_cabin - t_amb)
            t_cabin += (q_hvac + q_env) * dt / c_cabin

        # ---------- TMS boshqaruvi, gisterezis va energiya izchil sovitish ----------
        if tms_master_on < 0.5:
            tms_is_on = 0.0
        elif not is_tr:
            if tms_is_on < 0.5 and t_core >= t_cool_on: tms_is_on = 1.0
            elif tms_is_on > 0.5 and t_core <= t_cool_off: tms_is_on = 0.0
        q_cool_max = max(0.0, p_cool_power * tms_cop) if tms_master_on > 0.5 else 0.0
        # Muhandislik chilleri chegarasi: sovituvchi suyuqlik faqat TMS yoqilganda
        # tashqi muhitdan sovuqroq bo‘lishiga ruxsat etiladi. Bu faol chillerning yig‘ma modeli.
        t_coolant = t_amb - (5.0 if tms_is_on > 0.5 else 0.0)
        tms_ua = q_cool_max / 10.0 if q_cool_max > 0.0 else 0.0
        q_cooling_extract = 0.0; p_tms = 0.0
        if tms_is_on > 0.5 and not is_tr and q_cool_max > 0.0:
            q_cooling_extract = min(q_cool_max, max(0.0, tms_ua * (t_surf - t_coolant)))
            p_tms = q_cooling_extract / tms_cop

        p_aux_actual = 0.0 if is_tr else aux_baseline
        p_elec_request = 0.0 if is_tr else (p_motor_elec + p_aux_actual + p_tms + p_hvac)
        p_elec_request *= max(0.0, 1.0 + calib_factor)

        # ---------- elektr batareya modeli ----------
        r0_dyn = r0_ref
        if ea > 0.0:
            exponent_r = (ea / R_gas) * ((1.0 / t_core_k) - (1.0 / t_ref_k)); exponent_r = max(-20.0, min(20.0, exponent_r))
            r0_dyn = r0_ref * math.exp(exponent_r)
        r0_dyn = min(max_arr_r, max(1e-9, r0_dyn))
        ocv_cell = numba_interp1d(max(0.0, min(1.0, soc_true)), soc_lut, ocv_lut); ocv_pack = ocv_cell * ns_series
        v_eff = ocv_pack - u_p1 - u_p2
        I_batt = 0.0; v_term = max(0.0, v_eff)
        if not is_tr:
            p_req = p_elec_request
            disc = v_eff * v_eff - 4.0 * r0_dyn * p_req
            if disc >= 0.0:
                I_batt = (v_eff - math.sqrt(max(0.0, disc))) / (2.0 * r0_dyn)
            else:
                I_batt = v_eff / (2.0 * r0_dyn)
                if status_flag[step_idx] == 0.0: status_flag[step_idx] = 4.0
            # Regenerativ zaryadni dinamik qabul qilish chegarasi. Yakuniy batareya tokini
            # barcha SOC/kuchlanish/tok cheklovlaridan keyin qabul qilingan regeneratsiya
            # quvvati yakuniy batareya quvvatidan qayta tiklanadi, shunda jurnaldagi qiymatlar mos bo‘ladi.
            regen_active = I_batt < 0.0 and p_motor_elec < 0.0
            if regen_active:
                i_charge_hw = max_c_charge * cap_ah
                soc_min = min_soc_limit / 100.0; soc_max = max_soc_limit / 100.0
                i_charge_soc = max(0.0, (soc_max - soc_true) * cap_ah * 3600.0 / (max(1e-9, coulombic_eff) * dt))
                i_charge_v = max(0.0, (v_max_safe_pack - v_eff) / r0_dyn)
                i_charge_accept = min(i_charge_hw, i_charge_soc, i_charge_v)
                if i_charge_accept <= 0.0 or regen_capture <= 1e-12:
                    I_batt = 0.0
                    p_regen = 0.0
                    p_motor_elec = 0.0
                else:
                    I_batt = max(I_batt, -i_charge_accept)
            I_before_batt_limits = I_batt
            I_batt = max(-max_c_charge * cap_ah, min(max_c_discharge * cap_ah, I_batt))
            soc_min = min_soc_limit / 100.0; soc_max = max_soc_limit / 100.0
            if I_batt > 0.0:
                max_i_soc = max(0.0, (soc_true - soc_min) * cap_ah * 3600.0 / dt); I_batt = min(I_batt, max_i_soc)
            elif I_batt < 0.0:
                max_i_soc = max(0.0, (soc_max - soc_true) * cap_ah * 3600.0 / (max(1e-9, coulombic_eff) * dt)); I_batt = -min(abs(I_batt), max_i_soc)
            if I_batt > 0.0:
                i_vmin = (v_eff - v_min_safe_pack) / r0_dyn
                I_batt = 0.0 if i_vmin <= 0.0 else min(I_batt, i_vmin)
            elif I_batt < 0.0:
                i_vmax = (v_eff - v_max_safe_pack) / r0_dyn
                I_batt = max(I_batt, i_vmax)
            v_term = max(0.0, v_eff - I_batt * r0_dyn)
            if abs(I_batt - I_before_batt_limits) > 1e-9 and status_flag[step_idx] == 0.0:
                status_flag[step_idx] = 4.0
            p_batt_actual_pre = I_batt * v_term
            p_loads_final = p_aux_actual + p_tms + p_hvac
            calib_mult = max(1e-12, 1.0 + calib_factor)
            if p_motor_elec < 0.0 and p_batt_actual_pre < 0.0:
                # Kalibrlash koeffitsienti qo‘llangan umumiy elektr talabini
                # yakuniy batareya quvvatidan izchil ravishda qayta tiklash.
                p_motor_elec = p_batt_actual_pre / calib_mult - p_loads_final
                p_regen = max(0.0, -p_motor_elec)
            elif p_motor_elec >= 0.0:
                p_regen = 0.0

        c_rate = abs(I_batt) / cap_ah
        p_batt_actual = I_batt * v_term
        dsoc = -(I_batt * dt) / (cap_ah * 3600.0)
        if I_batt < 0.0: dsoc *= coulombic_eff
        soc_new = max(0.0, min(1.0, soc_true + dsoc))
        cum_ah += abs(I_batt) * dt / 3600.0
        soh_now = max(80.0, 100.0 - 20.0 * cum_ah / total_ah_life)

        # 2RC holatlarini nol-tartibli ushlab turish usuli bilan aniq yangilash.
        alpha1 = math.exp(-dt / max(1e-9, r1 * c1)); alpha2 = math.exp(-dt / max(1e-9, r2 * c2))
        u_p1_next = alpha1 * u_p1 + r1 * (1.0 - alpha1) * I_batt
        u_p2_next = alpha2 * u_p2 + r2 * (1.0 - alpha2) * I_batt

        # ---------- SOC filtrlari ----------
        ekf_new = soc_ekf; ukf_new = soc_ukf
        if is_hp > 0.5 and not is_tr:
            # Sun'iy o'lchovlar: tok shovqini (A) va terminal kuchlanish shovqini (V).
            sigma_i = 0.5
            I_meas = I_batt + generate_gaussian_noise(sigma_i)
            V_meas = v_term + generate_gaussian_noise(0.1)

            # 3 holatli EKF bashorati: x = [SoC, Up1, Up2]^T.
            dsoc_filter = -(I_meas * dt) / (cap_ah * 3600.0)
            if I_meas < 0.0:
                dsoc_filter *= coulombic_eff
            soc_pred = max(0.0, min(1.0, soc_ekf + dsoc_filter))
            up1_pred = alpha1 * ekf_up1 + r1 * (1.0 - alpha1) * I_meas
            up2_pred = alpha2 * ekf_up2 + r2 * (1.0 - alpha2) * I_meas

            # F = diag(1, alpha1, alpha2); tok shovqinining holatga tarqalishi
            # G = [-dt/(3600 QAh), R1(1-a1), R2(1-a2)]^T.
            fdiag0 = 1.0; fdiag1 = alpha1; fdiag2 = alpha2
            g0 = -dt / (cap_ah * 3600.0)
            g1 = r1 * (1.0 - alpha1)
            g2 = r2 * (1.0 - alpha2)
            q_soc = max(0.0, ekf_q)
            # Q ning RC holatlaridagi kichik model-noaniqligi (V^2); SoC Q esa parametrdan olinadi.
            q_up1 = 1.0e-6; q_up2 = 1.0e-6
            P_pred = np.zeros((3, 3))
            for ii in range(3):
                for jj in range(3):
                    fi = fdiag0 if ii == 0 else (fdiag1 if ii == 1 else fdiag2)
                    fj = fdiag0 if jj == 0 else (fdiag1 if jj == 1 else fdiag2)
                    gi = g0 if ii == 0 else (g1 if ii == 1 else g2)
                    gj = g0 if jj == 0 else (g1 if jj == 1 else g2)
                    P_pred[ii, jj] = fi * fj * P_ekf[ii, jj] + gi * gj * sigma_i * sigma_i
            P_pred[0, 0] += q_soc
            P_pred[1, 1] += q_up1
            P_pred[2, 2] += q_up2

            # Kuzatuv modeli: Vt = Ns*OCV(SoC) - I*R0 - Up1 - Up2.
            H0 = get_docv_dsoc(soc_pred, soc_lut, ocv_lut) * ns_series
            H1 = -1.0; H2 = -1.0
            V_pred = (numba_interp1d(soc_pred, soc_lut, ocv_lut) * ns_series
                      - I_meas * r0_dyn - up1_pred - up2_pred)
            # S = H P- H^T + R; K = P- H^T / S.
            S = (H0 * (P_pred[0, 0] * H0 + P_pred[0, 1] * H1 + P_pred[0, 2] * H2)
                 + H1 * (P_pred[1, 0] * H0 + P_pred[1, 1] * H1 + P_pred[1, 2] * H2)
                 + H2 * (P_pred[2, 0] * H0 + P_pred[2, 1] * H1 + P_pred[2, 2] * H2)
                 + ekf_r)
            S = max(1e-12, S)
            K0 = (P_pred[0, 0] * H0 + P_pred[0, 1] * H1 + P_pred[0, 2] * H2) / S
            K1 = (P_pred[1, 0] * H0 + P_pred[1, 1] * H1 + P_pred[1, 2] * H2) / S
            K2 = (P_pred[2, 0] * H0 + P_pred[2, 1] * H1 + P_pred[2, 2] * H2) / S
            innovation = V_meas - V_pred
            ekf_new = max(0.0, min(1.0, soc_pred + K0 * innovation))
            ekf_up1_new = up1_pred + K1 * innovation
            ekf_up2_new = up2_pred + K2 * innovation

            # Joseph covariance update: P+ = (I-KH)P-(I-KH)^T + K R K^T.
            A = np.zeros((3, 3))
            for ii in range(3):
                for jj in range(3):
                    hij = H0 if jj == 0 else (H1 if jj == 1 else H2)
                    kij = K0 if ii == 0 else (K1 if ii == 1 else K2)
                    A[ii, jj] = (1.0 if ii == jj else 0.0) - kij * hij
            P_new = np.zeros((3, 3))
            for ii in range(3):
                for jj in range(3):
                    acc = 0.0
                    for aa in range(3):
                        for bb in range(3):
                            acc += A[ii, aa] * P_pred[aa, bb] * A[jj, bb]
                    ki = K0 if ii == 0 else (K1 if ii == 1 else K2)
                    kj = K0 if jj == 0 else (K1 if jj == 1 else K2)
                    P_new[ii, jj] = acc + ki * ekf_r * kj
            # Sonli simmetriya va musbat diagonalni saqlash.
            for ii in range(3):
                P_new[ii, ii] = max(1e-12, P_new[ii, ii])
                for jj in range(ii + 1, 3):
                    sym = 0.5 * (P_new[ii, jj] + P_new[jj, ii])
                    P_new[ii, jj] = sym; P_new[jj, ii] = sym
            P_ekf = P_new
            ekf_up1 = ekf_up1_new; ekf_up2 = ekf_up2_new

            # Skalyar UKF (taqqoslash algoritmi alohida saqlanadi).
            n = 1.0; alpha = 1.0; beta = 2.0; lam = alpha * alpha * n - n; c_ut = n + lam
            wm0 = lam / c_ut; wc0 = wm0 + (1.0 - alpha * alpha + beta); wi = 1.0 / (2.0 * c_ut)
            dsoc_ukf = -(I_meas * dt) / (cap_ah * 3600.0)
            if I_meas < 0.0:
                dsoc_ukf *= coulombic_eff
            soc_pu = max(0.0, min(1.0, soc_ukf + dsoc_ukf)); P_pu = max(1e-12, P_ukf + ukf_q)
            sig = math.sqrt(max(1e-12, c_ut * P_pu))
            x0 = soc_pu
            # Boundary-aware reflection keeps sigma points inside [0,1] without the
            # one-sided clipping that previously destroyed the UKF sigma-point symmetry
            # near SOC limits. Reflection is applied repeatedly for unusually large P.
            x1 = soc_pu + sig
            x2 = soc_pu - sig
            for _ in range(4):
                if x1 > 1.0: x1 = 2.0 - x1
                if x1 < 0.0: x1 = -x1
                if x2 > 1.0: x2 = 2.0 - x2
                if x2 < 0.0: x2 = -x2
            x1 = max(0.0, min(1.0, x1)); x2 = max(0.0, min(1.0, x2))
            y0 = numba_interp1d(x0, soc_lut, ocv_lut) * ns_series - I_meas * r0_dyn - u_p1_next - u_p2_next
            y1 = numba_interp1d(x1, soc_lut, ocv_lut) * ns_series - I_meas * r0_dyn - u_p1_next - u_p2_next
            y2 = numba_interp1d(x2, soc_lut, ocv_lut) * ns_series - I_meas * r0_dyn - u_p1_next - u_p2_next
            ym = wm0*y0 + wi*y1 + wi*y2; Pyy = max(1e-12, wc0*(y0-ym)**2 + wi*(y1-ym)**2 + wi*(y2-ym)**2 + ukf_r)
            Pxy = wc0*(x0-soc_pu)*(y0-ym) + wi*(x1-soc_pu)*(y1-ym) + wi*(x2-soc_pu)*(y2-ym); Ku = Pxy / Pyy
            ukf_new = max(0.0, min(1.0, soc_pu + Ku*(V_meas-ym))); P_ukf = max(1e-12, P_pu - Ku*Pyy*Ku)
        else:
            ekf_new = soc_new; ukf_new = soc_new

        # ---------- Bernardi heat generation ----------
        # Ekvivalent sxemaning qaytmas issiqligi: omik va qutblanish qarshiliklaridagi yo‘qotishlar.
        # Bu qiymat razryad hamda regenerativ zaryad vaqtida musbat bo‘lib qoladi.
        q_irreversible = (I_batt * I_batt * r0_dyn
                          + (u_p1 * u_p1) / max(1e-12, r1)
                          + (u_p2 * u_p2) / max(1e-12, r2))
        q_reversible = -I_batt * t_core_k * dudt
        q_gen = q_irreversible + q_reversible
        # Sonli himoya: qaytar issiqlik manfiy bo‘lishi mumkin, ammo umumiy issiqlik
        # elektr yo‘qotishlariga nisbatan fizik ma’nosiz katta issiqlik yutgichiga aylanishiga yo‘l qo‘yilmaydi.
        q_gen = max(-0.25 * max(1.0, q_irreversible), min(1.0e7, q_gen))

        # ---------- ikki tugunli termal integratsiya ----------
        # Rsa — batareya paketi uchun ekvivalent tashqi issiqlik qarshiligi. Shamol Rsa ni silliq kamaytiradi.
        # TMS o‘chirilganda sovituvchi aylanishi to‘xtaydi va faqat kamaytirilgan
        # passiv tashqi issiqlik chiqarish yo‘li qoladi. Kamaytirish koeffitsiyenti
        # interfeysda aniq beriladi va termal tenglamalarda yashirilmaydi.
        r_sa_dynamic = r_sa_base / max(1.0, 1.0 + t_conv_coeff * abs(v_air))
        passive_factor = 1.0 if tms_is_on > 0.5 else tms_off_passive_factor
        def thermal_rates(tc, ts):
            q_cs = (tc - ts) / r_cs
            q_sa_full = (ts - t_amb) / r_sa_dynamic
            q_sa = passive_factor * q_sa_full
            dtc = (q_gen + q_fire - q_cs) / cc_core
            dts = (q_cs - q_sa - q_cooling_extract) / cc_surf
            # Bir tomonlama passiv chegara: sirt harorati
            # passiv issiqlik almashinuvi orqali tashqi muhit haroratidan pastga tushirilmaydi. Bu shart
            # RK2 ning oraliq hosilalarida ham bir xil fizik cheklovni ta’minlaydi.
            if tms_is_on < 0.5 and ts <= t_amb and dts < 0.0:
                dts = 0.0
            return dtc, dts
        n_sub = max(1, int(math.ceil(dt / 0.5))); h = dt / n_sub
        tc = t_core; ts = t_surf
        for _ in range(n_sub):
            k1c, k1s = thermal_rates(tc, ts); k1c = max(-rk2_clip, min(rk2_clip, k1c)); k1s = max(-rk2_clip, min(rk2_clip, k1s))
            tc_m = tc + 0.5*h*k1c; ts_m = ts + 0.5*h*k1s
            k2c, k2s = thermal_rates(tc_m, ts_m); k2c = max(-rk2_clip, min(rk2_clip, k2c)); k2s = max(-rk2_clip, min(rk2_clip, k2s))
            tc += 0.5*h*(k1c+k2c); ts += 0.5*h*(k1s+k2s)
            tc = max(-80.0, min(t_max_sim, tc)); ts = max(-80.0, min(t_max_sim, ts))
        # Passiv rejim izchilligi: ichki issiqlik hosil bo‘lishi manfiy bo‘lmaganda sirt
        # faqat tashqi muhit bilan issiqlik almashinuvi sababli muhitdan sovuqroq bo‘lib qolmaydi.
        if tms_is_on < 0.5 and q_gen + q_fire >= 0.0 and ts < t_amb: ts = t_amb

        q_cs_final = (tc - ts) / r_cs; q_sa_final = passive_factor * (ts - t_amb) / r_sa_dynamic
        # To‘liq ikki-tugunli termal energiya balansining sonli qoldig‘i.
        # Bu residual core-only emas, core + surface energiya o‘zgarishini tashqi
        # issiqlik chiqishi va TMS ekstraksiyasi bilan birgalikda tekshiradi.
        dTc_avg = (tc - t_core) / dt
        dTs_avg = (ts - t_surf) / dt
        q_balance = (q_gen + q_fire - q_sa_final - q_cooling_extract
                     - cc_core * dTc_avg - cc_surf * dTs_avg)

        cum_dist += v_curr * dt / 1000.0
        if p_batt_actual > 0.0: cum_energy += p_batt_actual * dt / 3600000.0

        # ---------- store a coherent interval-end sample ----------
        t_clock += dt
        t_sim_arr[step_idx] = t_clock; dt_out[step_idx] = dt; v_out[step_idx] = v_curr; a_out[step_idx] = a_curr; grad_out[step_idx] = grad_curr; wind_out[step_idx] = wind_curr
        f_aero_arr[step_idx] = f_aero; f_roll_arr[step_idx] = f_roll; f_grade_arr[step_idx] = f_grade; f_inert_arr[step_idx] = f_inert; f_tot_arr[step_idx] = f_total; slip_loss_arr[step_idx] = slip_loss
        rpm_arr[step_idx] = motor_rpm; torque_arr[step_idx] = torque_required; p_mech_arr[step_idx] = p_wheel; p_trac_arr[step_idx] = p_trac; p_regen_arr[step_idx] = p_regen; p_elec_arr[step_idx] = p_batt_actual
        p_aux_arr[step_idx] = p_aux_actual; p_hvac_arr[step_idx] = p_hvac; p_tms_arr[step_idx] = p_tms; curr_arr[step_idx] = I_batt; crate_arr[step_idx] = c_rate; ocv_arr[step_idx] = ocv_pack; v_term_arr[step_idx] = v_term
        soc_true_arr[step_idx] = soc_new; soc_ekf_arr[step_idx] = ekf_new; soc_ukf_arr[step_idx] = ukf_new; ah_thru_arr[step_idx] = cum_ah; soh_arr[step_idx] = soh_now
        t_c_arr[step_idx] = tc; t_s_arr[step_idx] = ts; q_loss_arr[step_idx] = q_irreversible; q_ent_arr[step_idx] = q_reversible; q_gen_arr[step_idx] = q_gen; q_cool_arr[step_idx] = q_cooling_extract; q_fire_arr[step_idx] = q_fire
        q_cs_arr[step_idx] = q_cs_final; q_sa_arr[step_idx] = q_sa_final; t_coolant_arr[step_idx] = t_coolant; tms_state_arr[step_idx] = tms_is_on; q_balance_arr[step_idx] = q_balance
        dist_arr[step_idx] = cum_dist; energy_arr[step_idx] = cum_energy

        soc_true = soc_new; soc_ekf = ekf_new; soc_ukf = ukf_new; t_core = tc; t_surf = ts; u_p1 = u_p1_next; u_p2 = u_p2_next
        step_idx += 1

    return (step_idx, t_sim_arr, dt_out, v_out, a_out, grad_out, wind_out,
            f_aero_arr, f_roll_arr, f_grade_arr, f_inert_arr, f_tot_arr, slip_loss_arr,
            rpm_arr, torque_arr, p_mech_arr, p_trac_arr, p_regen_arr, p_elec_arr,
            p_aux_arr, p_hvac_arr, p_tms_arr, curr_arr, crate_arr, ocv_arr, v_term_arr,
            soc_true_arr, soc_ekf_arr, soc_ukf_arr, ah_thru_arr, soh_arr,
            t_c_arr, t_s_arr, q_loss_arr, q_ent_arr, q_gen_arr, q_cool_arr, q_fire_arr,
            q_cs_arr, q_sa_arr, t_coolant_arr, tms_state_arr, q_balance_arr,
            status_flag, dist_arr, energy_arr)


# =====================================================================
# FOYDALANUVCHI INTERFEYSI VA BAJARISH QATLAMI
# =====================================================================
with st.expander("🚀 BLOCK 3: EV CORE ENGINE (Sci-Grade EKF/UKF Simulation)", expanded=True):
    
    b1_ready = st.session_state.get('b1_saved', False)
    b2_ready = st.session_state.get('b2_saved', False)
    
    if not (b1_ready and b2_ready):
        st.error("🛑 **SYSTEM LOCKED:** EV Core Engine cannot start. You must complete and 'SAVE' both Block 1 and Block 2 first.")
    else:
        st.markdown("### ⚙️ Engine Control Panel")
        col_em1, col_em2 = st.columns([2, 1])
        with col_em1:
            engine_mode = st.radio("🎛️ Select Simulation Architecture:", ["Standard Physics Engine (Idealized)", "High-Precision Benchmark Engine (EKF vs UKF Noise Injection)"], index=1, horizontal=True)
        with col_em2:
            calib_val = st.slider("Energy Calibration Factor [%]", min_value=-10.0, max_value=10.0, value=0.0, step=0.5)

        st.markdown("---")
        st.markdown("### 🛡️ BMS & Thermal Safety Constraints")
        st.caption("BMS protects the battery; TMS actively removes heat. They are independent master controls.")
        
        col_bms1, col_bms2, col_bms3 = st.columns(3)
        with col_bms1:
            bms_active = st.toggle("🟢 BMS Master Switch (Safety Mode)", value=True)
        with col_bms2:
            tr_active = st.toggle("🔥 Enable Thermal Runaway", value=False, disabled=not bms_active)
        with col_bms3:
            tr_trigger_temp = st.number_input("Thermal Runaway Trigger Temp [°C]", min_value=60.0, max_value=200.0, value=90.0, disabled=not tr_active)

        t_max_sim = 1200.0 
        if tr_active:
            t_max_sim = st.number_input("Maximum Simulation Temperature Ceiling [°C]", min_value=150.0, max_value=1500.0, value=1000.0, step=50.0)
            st.error(f"🚨 **DANGER:** If core reaches {tr_trigger_temp}°C, Arrhenius exponential breakdown triggers up to {t_max_sim}°C.")
        elif not bms_active:
            st.warning("⚠️ **WARNING: BMS IS OFF.** Vehicle will ignore thermal cutoffs and SOC limits.")

        tms_gui_state = st.session_state.get("cfg_tms_master", True)
        if bms_active and not tms_gui_state:
            st.info("🔵 **BMS-ONLY TEST MODE:** BMS = ON, TMS = OFF. Coolant circulation OFF; passive heat rejection is reduced; BMS derating/cutoff remains active.")
        elif bms_active and tms_gui_state:
            st.success("🟢 **NORMAL THERMAL-SAFETY MODE:** BMS = ON, TMS = ON.")
        elif (not bms_active) and (not tms_gui_state):
            st.warning("🟠 **UNPROTECTED THERMAL TEST:** BMS = OFF, TMS = OFF.")
        else:
            st.warning("🟡 **TMS-ONLY TEST:** BMS = OFF, TMS = ON.")

        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            st.markdown("<br>", unsafe_allow_html=True)
            run_sim = st.button("▶️ RUN DYNAMIC MULTI-PHYSICS SIMULATION", type="primary")
             
        if run_sim:
            df = st.session_state['df_for_calc'].copy()
            sp = st.session_state['sim_params']
            if int(sp.get('_thermal_model_version', 0)) < 9:
                st.error(
                    "❌ Old thermal parameter state detected. Please press 'SAVE' in Block 1 once, then run the simulation again. "
                    "This prevents the previous Rcs/Rsa/ambient values from contaminating the article temperature curves."
                )
                st.stop()

            # Ilmiy vaqt qatorini tayyorlash: integratsiyadan oldin vaqt tartibi va takroriy vaqt belgilari tuzatiladi.
            df["A-Time [s]"] = pd.to_numeric(df["A-Time [s]"], errors="coerce")
            df = (df.dropna(subset=["A-Time [s]"]).sort_values("A-Time [s]")
                    .drop_duplicates("A-Time [s]", keep="last").reset_index(drop=True))
            N_route = len(df)
            if N_route < 2:
                st.error("❌ At least two distinct time samples are required for a dynamic simulation.")
                st.stop()

            time_route = df["A-Time [s]"].to_numpy(dtype=float)
            raw_dt = np.diff(time_route)
            positive_dt = raw_dt[raw_dt > 0.0]
            fallback_dt = float(np.median(positive_dt)) if positive_dt.size else 1.0
            dt_intervals = np.empty(N_route, dtype=float)
            dt_intervals[:-1] = np.where(raw_dt > 0.0, raw_dt, fallback_dt)
            dt_intervals[-1] = 0.0

            v_ms_route = (
                pd.to_numeric(df["B-Speed [km/h]"], errors="coerce").fillna(0.0).to_numpy(dtype=float) / 3.6
                if "B-Speed [km/h]" in df.columns else np.zeros(N_route)
            )
            
            accel_key = "C-Acceleration [m/s2]" if "C-Acceleration [m/s2]" in df.columns else "C-Acceleration [m/s2] (Do not edit - Auto calculated)"
            a_ms2_route = np.nan_to_num(df[accel_key].values if accel_key in df.columns else np.zeros(N_route))
            grad_deg_route = df["E-Gradient [°]"].values if "E-Gradient [°]" in df.columns else np.zeros(N_route)
            headwind_ms_route = df["F-Headwind [m/s]"].values if "F-Headwind [m/s]" in df.columns else np.zeros(N_route)
   
            is_hp_flag = 1.0 if "High-Precision" in engine_mode else 0.0
            
            # 🌟 Xavfsiz, indekslari moslashtirilgan massiv xaritasi (yakuniy 0..84 elementlar)
            p_array = np.array([
                float(sp.get('m_total', 1600.0)), float(sp.get('g', 9.81)), float(sp.get('cd', 0.24)), float(sp.get('area', 2.2)),
                float(sp.get('cr0', 0.01)), float(sp.get('cr1', 0.0001)), float(sp.get('aux', 250.0)), float(sp.get('rho', 1.18)),
                float(sp.get('tire_mu', 0.85)), float(sp.get('rw', 0.315)), float(sp.get('gear', 9.2)), 
                float(sp.get('eff_m', 0.95)), float(sp.get('eff_i', 0.97)), float(sp.get('eff_t', 0.96)),
                float(sp.get('p_max', 150000.0)), float(sp.get('regen_bias', 1.0)), float(sp.get('regen_cutoff', 5.0)), 
                float(sp.get('cap_ah', 135.0)), float(sp.get('r0', 0.001)), float(sp.get('r1', 0.002)), float(sp.get('c1', 1000.0)),
                float(sp.get('r2', 0.002)), float(sp.get('c2', 6000.0)), float(sp.get('max_chg', 1.5)), float(sp.get('max_dis', 3.0)), 
                float(sp.get('b_ns', 100.0)), float(sp.get('b_np', 1.0)), float(sp.get('coulombic_eff', 0.995)), 
                float(sp.get('t_a', 30.0)), float(sp.get('cc', 6000.0)), float(sp.get('cs', 2000.0)),
                float(sp.get('rcs', 0.01)), float(sp.get('rsa', 0.02)), float(sp.get('t_cooling_on', 45.0)), float(sp.get('t_cooling_off', 35.0)), 
                float(sp.get('cooling_power', 2500.0)), float(sp.get('t_derate', 55.0)), float(sp.get('t_cutoff', 65.0)), 
                float(sp.get('h_on', 1.0)), float(sp.get('t_t', 22.0)), float(sp.get('h_fan', 200.0)),
                float(sp.get('h_c', 120.0)), float(sp.get('h_h', 180.0)), float(sp.get('min_s', 5.0)), float(sp.get('max_s', 100.0)), 
                1.0 if bms_active else 0.0, 1.0 if tr_active else 0.0, float(tr_trigger_temp), float(t_max_sim), 
                float(sp.get('q', 1e-6)), float(sp.get('r', 1e-2)), float(sp.get('ukf_q', 1e-6)), float(sp.get('ukf_r', 1e-2)), 
                float(sp.get('dudt', 0.0001)), float(sp.get('ea', 25000.0)), float(sp.get('t_ref', 25.0)), 
                float(sp.get('fade', 0.9)), float(sp.get('socw', 0.5)), float(calib_val / 100.0), float(is_hp_flag),
                float(sp.get('cycle_life', 3000.0)), float(sp.get('pack_overhead', 1.2)), float(sp.get('inertia_factor', 1.05)),
                float(sp.get('cop_cool', 2.5)), float(sp.get('cop_heat', 0.95)), float(sp.get('c_cabin', 250000.0)), 
                float(sp.get('k_env', 80.0)), float(sp.get('tms_cop', 2.0)), float(sp.get('tr_base_heat', 25000.0)), 
                float(sp.get('tr_rate', 0.08)), float(sp.get('t_conv_coeff', 0.05)), float(sp.get('min_volt_cell', 2.5)),
                float(sp.get('r_fade_min_t', -5.0)), float(sp.get('r_fade_max_s', 0.9)),
                
                # --- YANGI PARAMETRLAR (Massivning yakuniy elementlari (0..84)) ---
                float(sp.get('ekf_p0', 0.1)), float(sp.get('ukf_p0', 0.1)), float(sp.get('max_arr_r', 0.5)),
                float(sp.get('rk2_clip', 5.0)), float(sp.get('gps_dt_thresh', 3.0)), float(sp.get('gps_accel_clip', 2.0)),
                float(sp.get('t_max', 180.0)), float(sp.get('rpm_b', 3500.0)),
                1.0 if sp.get('tms_master_on', True) else 0.0,
                float(sp.get('tms_off_passive_factor', 0.20)),
                float(sp.get('regen_capture', 0.95))
            ], dtype=np.float64)

            try:
                start_time = time.time()
                
                results = run_ev_core_engine(
                    N_route, dt_intervals, v_ms_route, a_ms2_route, grad_deg_route, headwind_ms_route, 
                    np.array(sp.get('soc_lut')), np.array(sp.get('ocv_lut')), p_array, 
                    float(sp.get('start_soc', 98.0)), float(sp.get('init_soc_guess', 40.0))
                )
                
                idx = results[0]
                exec_time = time.time() - start_time
                
                # Termal mantiqiy tekshiruv: qayd etilgan tashqi muhit harorati aynan
                # yadro dvigatelida ishlatilgan qiymat bilan bir xil bo‘lishi kerak. Bu eski sessiya parametrlarining
                # tajriba bilan mos kelmaydigan sirt harorati egri chizig‘ini yashirincha hosil qilishining oldini oladi.
                ambient_used = float(sp.get('t_a', 30.0))
                if not np.isfinite(ambient_used):
                    raise ValueError("Ambient temperature is not finite.")

                df_res = pd.DataFrame({
                    "A-Time [s]": results[1][:idx],
                    "Interval_dt [s]": results[2][:idx],
                    "B-Speed [km/h]": results[3][:idx] * 3.6,
                    "C-Acceleration [m/s2]": results[4][:idx],
                    "E-Gradient [°]": results[5][:idx],
                    "F-Headwind [m/s]": results[6][:idx],
                    "F_Aerodynamic [N]": results[7][:idx],
                    "F_Rolling [N]": results[8][:idx],
                    "F_Gradient [N]": results[9][:idx],
                    "F_Inertial [N]": results[10][:idx],
                    "F_total [N]": results[11][:idx],
                    "Tire_Traction_Deficit_Power [W]": results[12][:idx],
                    "Motor_RPM": results[13][:idx],
                    "Motor_Torque_Required [Nm]": results[14][:idx],
                    "P_Mechanical [W]": results[15][:idx],
                    "P_Motor_Traction [kW]": results[16][:idx] / 1000.0,
                    "P_Regenerative [kW]": results[17][:idx] / 1000.0,
                    "E-Total Power [W]": results[18][:idx],
                    "P_Auxiliary [W]": results[19][:idx],
                    "P_HVAC_Dynamic_W": results[20][:idx],
                    "P_TMS_Dynamic_W": results[21][:idx],
                    "F-Current [A]": results[22][:idx],
                    "C_Rate [C]": results[23][:idx],
                    "V_Pack_OCV [V]": results[24][:idx],
                    "G-Terminal Voltage [V]": results[25][:idx],
                    "I-SOC_True [%]": results[26][:idx] * 100.0,
                    "I-SOC_EKF [%]": results[27][:idx] * 100.0,
                    "I-SOC_UKF [%]": results[28][:idx] * 100.0,
                    "Cumulative_Ah [Ah]": results[29][:idx],
                    "SOH [%]": results[30][:idx],
                    "H-Core Temp [°C]": results[31][:idx],
                    "H-Surf Temp [°C]": results[32][:idx],
                    "Q_Irreversible_Heat [W]": results[33][:idx],
                    "Q_Entropic_Heating [W]": results[34][:idx],
                    "Q_Battery_Heat_Gen [W]": results[35][:idx],
                    "Q_Cooling_Extracted [W]": results[36][:idx],
                    "Q_Thermal_Runaway [W]": results[37][:idx],
                    "Q_Core_Surface [W]": results[38][:idx],
                    "Q_Surface_Ambient [W]": results[39][:idx],
                    "T_Coolant [°C]": results[40][:idx],
                    "TMS_State": results[41][:idx],
                    "Thermal_Balance_Residual [W]": results[42][:idx],
                    "Status_Flag": results[43][:idx],
                    "C-Distance [km]": results[44][:idx],
                    "Energy_Discharged_Exact [kWh]": results[45][:idx]
                })
                
                st.session_state['df_for_calc_raw'] = df 
                st.session_state['df_result'] = df_res

                # Tashqi muhit haroratidan boshlangan passiv termal tajribada sirt harorati
                # sof ichki issiqlik hosil bo‘lishi manfiy bo‘lmaganda muhit haroratidan pastga siljimasligi kerak.
                # Farqni maqola grafiklarida yashirmasdan, uni aniq hisobot qilish kerak.
                if len(df_res) > 0:
                    min_surface = float(np.nanmin(df_res["H-Surf Temp [°C]"].to_numpy()))
                    if ambient_used >= min_surface + 1e-6 and float(np.nanmax(df_res["Q_Cooling_Extracted [W]"].to_numpy())) <= 1e-9:
                        st.warning(f"Thermal check: surface reached {min_surface:.2f} °C while ambient is {ambient_used:.2f} °C. Review thermal parameters/session state before using the article figures.")
                st.session_state['b3_saved'] = True
                st.session_state['b3_status'] = "🟢 BLOCK 3: EV CORE ENGINE (Computed & Ready)"
                
                st.success(f"✅ **COMPUTED:** True Digital Twin Physical Simulation complete. Numba engine solved all differential equations seamlessly in {exec_time:.4f} seconds.")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ **CRITICAL MATHEMATICAL ERROR:** Physical limits breached or inputs diverge. Details: {e}")

if st.session_state.get('b3_saved', False):
    st.markdown("""
        <style>
        div[data-testid="stExpander"]:nth-of-type(4) { border: 2px solid #28a745 !important; background-color: rgba(40, 167, 69, 0.02) !important; border-radius: 8px; }
        div[data-testid="stExpander"]:nth-of-type(4) summary p { color: #28a745 !important; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        div[data-testid="stExpander"]:nth-of-type(4) { border: 2px solid #ffc107 !important; background-color: rgba(255, 193, 7, 0.02) !important; border-radius: 8px; }
        div[data-testid="stExpander"]:nth-of-type(4) summary p { color: #b58100 !important; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

# =====================================================================
# 3-BLOK oxiri
# =====================================================================

# =====================================================================
# 4-BLOK: ILMIY DASHBOARD, RASM YARATISH VA EKSPORT (V1.0.0)
# =====================================================================
matplotlib.use('Agg') 

st.markdown("<hr style='margin-top: 30px; margin-bottom: 20px;'>", unsafe_allow_html=True)
export_status_placeholder = st.empty()
progress_bar_placeholder = st.empty()

if 'df_result' in st.session_state and st.session_state.get('b3_saved', False):
    df_res = st.session_state['df_result'].copy() 
    sp = st.session_state['sim_params'] 
    
    with st.expander("📊 BLOCK 4: SCIENTIFIC DASHBOARD & PUBLICATION BUILDER", expanded=True):
        # -----------------------------------------------------------------
        # 1. 3-BLOKDAN SINXRON MA'LUMOTLARNI AJRATIB OLISH
        # -----------------------------------------------------------------
        t_arr = df_res["A-Time [s]"].to_numpy()
        v_ms = df_res["B-Speed [km/h]"].to_numpy() / 3.6
        a_ms2 = df_res["C-Acceleration [m/s2]"].to_numpy()
        
        f_aero = df_res["F_Aerodynamic [N]"].to_numpy()
        f_roll = df_res["F_Rolling [N]"].to_numpy()
        f_grade = df_res["F_Gradient [N]"].to_numpy()
        f_inert = df_res["F_Inertial [N]"].to_numpy()
        f_total = df_res["F_total [N]"].to_numpy()
        
        motor_rpm = df_res["Motor_RPM"].to_numpy()
        torque = df_res["Motor_Torque_Required [Nm]"].to_numpy()
        p_mech_kw = df_res["P_Mechanical [W]"].to_numpy() / 1000.0
        p_trac_kw = df_res["P_Motor_Traction [kW]"].to_numpy()
        p_regen_kw = df_res["P_Regenerative [kW]"].to_numpy()
        
        current = df_res["F-Current [A]"].to_numpy()
        c_rate = df_res["C_Rate [C]"].to_numpy()
        ocv_pack = df_res["V_Pack_OCV [V]"].to_numpy()
        v_term = df_res["G-Terminal Voltage [V]"].to_numpy()
        p_elec = df_res["E-Total Power [W]"].to_numpy()
        
        t_core = df_res["H-Core Temp [°C]"].to_numpy()
        t_surf = df_res["H-Surf Temp [°C]"].to_numpy()
        q_joule_w = df_res["Q_Irreversible_Heat [W]"].to_numpy()
        q_entropic_w = df_res["Q_Entropic_Heating [W]"].to_numpy()
        q_total_gen_w = df_res["Q_Battery_Heat_Gen [W]"].to_numpy()
        q_cooling_extract_w = df_res["Q_Cooling_Extracted [W]"].to_numpy()
        q_fire_w = df_res["Q_Thermal_Runaway [W]"].to_numpy()
        q_cs_w = df_res["Q_Core_Surface [W]"].to_numpy()
        q_sa_w = df_res["Q_Surface_Ambient [W]"].to_numpy()
        t_coolant = df_res["T_Coolant [°C]"].to_numpy()
        tms_state = df_res["TMS_State"].to_numpy()
        thermal_balance_residual = df_res["Thermal_Balance_Residual [W]"].to_numpy()
        
        soc_true = df_res["I-SOC_True [%]"].to_numpy()
        soc_ekf = df_res["I-SOC_EKF [%]"].to_numpy()
        soc_ukf = df_res["I-SOC_UKF [%]"].to_numpy()
        
        cum_ah_throughput = df_res["Cumulative_Ah [Ah]"].to_numpy()
        soh_arr = df_res["SOH [%]"].to_numpy()
        
        status_flag = df_res["Status_Flag"].to_numpy()
        hvac_power_w = df_res["P_HVAC_Dynamic_W"].to_numpy()
        tms_power_w = df_res["P_TMS_Dynamic_W"].to_numpy()
        
        dt_arr = df_res["Interval_dt [s]"].to_numpy()
        
        dist_km_arr = df_res["C-Distance [km]"].to_numpy()
        energy_kwh_arr = df_res["Energy_Discharged_Exact [kWh]"].to_numpy()
        dist_km = dist_km_arr[-1]
        energy_kwh = energy_kwh_arr[-1] 
        
        soc_disp = pd.Series(soc_true).ewm(alpha=0.02).mean().values 
        slip_loss_w = df_res["Tire_Traction_Deficit_Power [W]"].to_numpy()
        slip_kwh_arr = np.cumsum(slip_loss_w * dt_arr) / 3600000.0 

        # -----------------------------------------------------------------
        # 2. VALIDATION METRICS KPI PANEL
        # -----------------------------------------------------------------
        trip_cost = energy_kwh * sp.get('cost', 0.15) 
        ekf_rmse = np.sqrt(np.mean((soc_true - soc_ekf)**2)) 
        ukf_rmse = np.sqrt(np.mean((soc_true - soc_ukf)**2)) 
        total_slip_kwh = slip_kwh_arr[-1]

        st.markdown(f"""
        <style>
            .m-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 15px; margin-bottom: 20px; }}
            .m-card {{ background: white; padding: 15px; border-radius: 12px; text-align: center; border-bottom: 4px solid #1E3A8A; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            .v-card {{ background: #f8fafc; border-bottom: 4px solid #F59E0B; }}
            .t-card {{ background: #FEF2F2; border-bottom: 4px solid #EF4444; }}
            .m-val {{ font-size: 1.4rem; font-weight: bold; color: #1E3A8A; margin-top: 5px; }}
            .v-val {{ color: #D97706; }}
            .t-val {{ color: #EF4444; }}
            .m-title {{ color: #64748b; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
        </style>
        <div class='m-grid'>
            <div class='m-card'><div class='m-title'>Distance Covered</div><div class='m-val'>{dist_km:.2f} km</div></div>
            <div class='m-card'><div class='m-title'>Battery Discharged Energy</div><div class='m-val'>{energy_kwh:.2f} kWh</div></div>
            <div class='m-card'><div class='m-title'>Final Battery SOC</div><div class='m-val'>{soc_disp[-1]:.1f} %</div></div>
            <div class='m-card' style='border-color:#10b981'><div class='m-title'>Energy Efficiency</div><div class='m-val'>{(energy_kwh/max(0.001, dist_km)*1000):.0f} Wh/km</div></div>
        </div>
        <div class='m-grid'>
            <div class='m-card v-card'><div class='m-title'>EKF Tracker RMSE</div><div class='m-val v-val'>{ekf_rmse:.4f}%</div></div>
            <div class='m-card v-card' style='border-color:#10b981;'><div class='m-title'>UKF Tracker RMSE</div><div class='m-val' style='color:#10b981;'>{ukf_rmse:.4f}%</div></div>
            <div class='m-card t-card'><div class='m-title'>Peak Core Temp</div><div class='m-val t-val'>{np.max(t_core):.1f} °C</div></div>
            <div class='m-card v-card'><div class='m-title'>Traction Deficit Energy</div><div class='m-val v-val'>{total_slip_kwh:.3f} kWh</div></div>
            <div class='m-card v-card' style='border-color:#3B82F6;'><div class='m-title'>Total Journey Cost</div><div class='m-val' style='color:#3B82F6;'>${trip_cost:.2f}</div></div>
        </div>
        """, unsafe_allow_html=True) 

        # -----------------------------------------------------------------
        # 3. INTERACTIVE PLOTLY PLOTS CONFIG
        # 32 va 33-rasmlar yadro va sirt haroratining yakuniy termal natijalaridir.
        # Ular to‘ldirilgan maydon emas, chiziq ko‘rinishida va mahalliy harorat shkalasida chiziladi.
        # -----------------------------------------------------------------
        instant_economy = np.zeros_like(v_ms, dtype=float)

        valid_speed = v_ms > 0.5

        np.divide(
            p_elec,
            v_ms * 3.6,
            out=instant_economy,
            where=valid_speed
        )

        instant_economy = np.clip(instant_economy, -500, 1000)
        
        plot_configs = [
            ("1. Vehicle Speed [km/h]", v_ms * 3.6, "#1E3A8A", True, t_arr, "lines"), 
            ("2. Distance Traveled [km]", dist_km_arr, "#10b981", True, t_arr, "lines"), 
            ("3. Acceleration [m/s²]", a_ms2, "#E53E3E", False, t_arr, "lines"), 
            ("4. Total Traction Force [N]", f_total, "#2D3748", False, t_arr, "lines"), 
            ("5. Aerodynamic Drag Force [N]", f_aero, "#A0D468", False, t_arr, "lines"),
            ("6. Rolling Resistance Force [N]", f_roll, "#4FC1E9", False, t_arr, "lines"),
            ("7. Slope/Grade Resistance Force [N]", f_grade, "#AC92EC", False, t_arr, "lines"),
            ("8. Inertial Acceleration Force [N]", f_inert, "#EC87C0", False, t_arr, "lines"),
            ("9. Motor Speed [RPM]", motor_rpm, "#4A5568", True, t_arr, "lines"), 
            ("10. Motor Torque [Nm]", torque, "#D53F8C", False, t_arr, "lines"), 
            ("11. Mechanical Traction Power [kW]", p_mech_kw, "#38A169", True, t_arr, "lines"),
            ("12. Tire Traction Deficit Power [W]", slip_loss_w, "#E53E3E", True, t_arr, "lines"), 
            ("13. Cumulative Traction Deficit Energy [kWh]", slip_kwh_arr, "#D53F8C", True, t_arr, "lines"), 
            ("14. Battery Electrical Power [kW]", p_elec/1000, "#3182CE", True, t_arr, "lines"), 
            ("15. Motor Electrical Power Demand [kW]", p_trac_kw, "#2B6CB0", True, t_arr, "lines"),
            ("16. Regenerative Power Recovery [kW]", p_regen_kw, "#2ECC71", True, t_arr, "lines"),
            ("17. Auxiliary Power Demand [W]", df_res["P_Auxiliary [W]"].to_numpy(), "#718096", True, t_arr, "lines"), 
            ("18. HVAC Dynamic Power Consumption [W]", hvac_power_w, "#00B5D8", True, t_arr, "lines"), 
            ("19. TMS Active Cooling Power [W]", tms_power_w, "#4299E1", True, t_arr, "lines"),
            ("20. Battery Current [A]", current, "#E53E3E", False, t_arr, "lines"), 
            ("21. Battery C-Rate [C]", c_rate, "#D97706", False, t_arr, "lines"),
            ("22. Battery OCV (Ideal Voltage) [V]", ocv_pack, "#9F7AEA", False, t_arr, "lines"),
            ("23. Terminal Voltage (V_eff) [V]", v_term, "#805AD5", False, t_arr, "lines"), 
            ("24. Dashboard Display SOC [%]", soc_disp, "#10b981", True, t_arr, "lines"), 
            ("25. Physical Raw SOC [%]", soc_true, "#64748b", False, t_arr, "lines"), 
            ("26. Stochastic Filters (EKF vs UKF) [%]", soc_ekf, "#D97706", False, t_arr, "lines"), 
            ("27. Tracking Error (True - Filter) [%]", soc_ekf, "#E53E3E", False, t_arr, "lines"), 
            ("28. Cumulative Ah Throughput [Ah]", cum_ah_throughput, "#4A5568", True, t_arr, "lines"), 
            ("29. Battery State of Health (SOH) [%]", soh_arr, "#38A169", True, t_arr, "lines"), 
            ("30. Battery Discharged Energy [kWh]", energy_kwh_arr, "#1E3A8A", True, t_arr, "lines"), 
            ("31. Instantaneous Economy [Wh/km]", instant_economy, "#3182CE", False, t_arr, "lines"),
            ("32. Core Temperature [°C]", t_core, "#E53E3E", False, t_arr, "lines"), 
            ("33. Surface Temperature [°C]", t_surf, "#F6AD55", False, t_arr, "lines"), 
            ("34. Temp Gradient (Core - Surface) [°C]", t_core - t_surf, "#DD6B20", True, t_arr, "lines"),
            ("35. Battery Total Heat Generation Rate [W]", q_total_gen_w, "#C53030", True, t_arr, "lines"),
            ("36. Irreversible (Ohmic + Polarization) Heating [W]", q_joule_w, "#E53E3E", True, t_arr, "lines"),
            ("37. Reversible Entropic Heating [W]", q_entropic_w, "#D69E2E", True, t_arr, "lines"),
            ("38. TMS Heat Extraction Rate [W]", q_cooling_extract_w, "#3182CE", True, t_arr, "lines"),
            ("39. Thermal Runaway Exothermal Heat [W]", q_fire_w, "#9B2C2C", True, t_arr, "lines"),
            ("40. Voltage vs Current Correlation [V-I Curve]", v_term, "#9F7AEA", False, current, "markers"),
            ("41. SOC ±1.5% Reference Tube [%]", soc_true, "#475569", False, t_arr, "lines"),
            ("42. Absolute Tracking Error Comparison [%]", np.abs(soc_true - soc_ekf), "#D97706", False, t_arr, "lines"),
            ("43. Core → Surface Heat Flow [W]", q_cs_w, "#805AD5", True, t_arr, "lines"),
            ("44. Surface → Ambient Heat Flow [W]", q_sa_w, "#4A5568", True, t_arr, "lines"),
            ("45. TMS Coolant Temperature [°C]", t_coolant, "#3182CE", True, t_arr, "lines"),
            ("46. TMS State (0=OFF, 1=ON)", tms_state, "#2B6CB0", False, t_arr, "lines"),
            ("47. Thermal Balance Residual [W]", thermal_balance_residual, "#C53030", False, t_arr, "lines")
        ] 
        
        plot_dict = {cfg[0]: {"y": cfg[1], "color": cfg[2], "fill": cfg[3], "x": cfg[4], "mode": cfg[5]} for cfg in plot_configs}

        academic_labels = {
            "Vehicle Speed": "Vehicle Speed (km/h)", "Distance Traveled": "Distance (km)", "Acceleration": "Acceleration (m/s²)",
            "Total Traction Force": "Total Traction Force (N)", "Aerodynamic Drag Force": "Aerodynamic Drag Force (N)",
            "Rolling Resistance Force": "Rolling Resistance Force (N)", "Slope/Grade Resistance Force": "Slope Resistance Force (N)",
            "Inertial Acceleration Force": "Inertial Force (N)", "Motor Speed": "Motor Speed (RPM)", "Motor Torque": "Motor Torque (Nm)",
            "Mechanical Traction Power": "Mechanical Power (kW)", "Tire Traction Deficit Power": "Traction Deficit Power (W)",
            "Cumulative Traction Deficit Energy": "Slip Energy Loss (kWh)", "Battery Electrical Power": "Battery Electrical Power (kW)",
            "Motor Electrical Power Demand": "Motor Electrical Power (kW)", "Regenerative Power Recovery": "Regenerative Power (kW)",
            "Auxiliary Power Demand": "Auxiliary Power (W)", "HVAC Dynamic Power Consumption": "HVAC Power (W)",
            "TMS Active Cooling Power": "TMS Power (W)", "Battery Current": "Battery Current (A)", "Battery C-Rate": "Battery C-Rate (C)",
            "Battery OCV (Ideal Voltage)": "Open-Circuit Voltage (V)", "Terminal Voltage (V_eff)": "Terminal Voltage (V)",
            "Dashboard Display SOC": "Display SOC (%)", "Physical Raw SOC": "True SOC (%)",
            "Stochastic Filters (EKF vs UKF)": "SOC Filter Estimation (%)", "Tracking Error (True - Filter)": "SOC Estimation Error (%)",
            "Cumulative Ah Throughput": "Ah Throughput (Ah)", "Battery State of Health (SOH)": "SOH (%)",
            "Battery Discharged Energy": "Battery Discharged Energy (kWh)", "Instantaneous Economy": "Energy Economy (Wh/km)",
            "Core Temperature": "Core Temperature (°C)", "Surface Temperature": "Surface Temperature (°C)",
            "Temp Gradient (Core - Surface)": "Thermal Gradient (°C)", "Battery Total Heat Generation Rate": "Total Heat Gen. Rate (W)",
            "Irreversible (Ohmic + Polarization) Heating": "Joule Heat Gen. (W)", "Reversible Entropic Heating": "Entropic Heat Gen. (W)",
            "TMS Heat Extraction Rate": "TMS Heat Extraction (W)", "Thermal Runaway Exothermal Heat": "Exothermal Heat (W)",
            "Voltage vs Current Correlation": "Terminal Voltage (V)",
            "SOC ±1.5% Reference Tube": "SOC Estimation with Bounds (%)",
            "Absolute Tracking Error Comparison": "Absolute SOC Error (%)"
        }

        def render_plotly_chart(name, data, color, fill, x_data, mode="lines", plot_key=None):
            fig = go.Figure()
            y = np.asarray(data, dtype=float)
            clean_name = name.split(". ")[1] if ". " in name else name
            x_title = "Current [A]" if "V-I" in name else "Time [s]"
            y_title = clean_name.split("[")[0].strip()
            
            if "26. Stochastic" in name:
                fig.add_trace(go.Scatter(x=x_data, y=soc_true, mode='lines', name='True SOC', line=dict(color='#64748b', width=2)))
                fig.add_trace(go.Scatter(x=x_data, y=soc_ekf, mode='lines', name='EKF', line=dict(color='#D97706', width=2, dash='dash')))
                fig.add_trace(go.Scatter(x=x_data, y=soc_ukf, mode='lines', name='UKF', line=dict(color='#10b981', width=2, dash='dot')))
            elif "27. Tracking Error" in name:
                fig.add_trace(go.Scatter(x=x_data, y=soc_true - soc_ekf, mode='lines', name='EKF Error', line=dict(color='#D97706', width=1.5)))
                fig.add_trace(go.Scatter(x=x_data, y=soc_true - soc_ukf, mode='lines', name='UKF Error', line=dict(color='#10b981', width=1.5)))
            
            # 🌟 41-grafik: xatolik diapazonlari (±1.5%)
            elif "41. SOC ±1.5% Reference Tube" in name:
                fig.add_trace(go.Scatter(x=x_data, y=soc_true + 1.5, mode='lines', line=dict(width=0), showlegend=False))
                fig.add_trace(go.Scatter(x=x_data, y=soc_true - 1.5, mode='lines', fill='tonexty', fillcolor='rgba(203, 213, 225, 0.4)', line=dict(width=0), name='±1.5% Reference Tube'))
                fig.add_trace(go.Scatter(x=x_data, y=soc_true, mode='lines', name='True SOC', line=dict(color='#475569', width=2)))
                fig.add_trace(go.Scatter(x=x_data, y=soc_ekf, mode='lines', name='EKF', line=dict(color='#D97706', width=1.5, dash='dash')))
                fig.add_trace(go.Scatter(x=x_data, y=soc_ukf, mode='lines', name='UKF', line=dict(color='#10b981', width=1.5, dash='dot')))
            
            # 🌟 42-grafik: mutlaq xatolik taqqoslanishi
            elif "42. Absolute Tracking Error Comparison" in name:
                fig.add_trace(go.Scatter(x=x_data, y=np.abs(soc_true - soc_ekf), mode='lines', name='EKF Absolute Error', line=dict(color='#D97706', width=1.5)))
                fig.add_trace(go.Scatter(x=x_data, y=np.abs(soc_true - soc_ukf), mode='lines', name='UKF Absolute Error', line=dict(color='#10b981', width=1.5)))
                fig.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="1% Safety Limit")
            else:
                line_style = dict(color=color, width=2) if mode != "markers" else dict(color=color)
                fig.add_trace(go.Scatter(x=x_data, y=data, mode=mode, name=clean_name, line=line_style, fill='tozeroy' if fill and mode != "markers" else 'none', marker=dict(size=4) if mode=="markers" else None))
            
            bms_pause_mask = (status_flag == 1)
            tr_mask = (status_flag >= 2)
            
            def add_vrect_from_mask(mask, fillcolor, opacity, annotation):
                if mode == "markers": return 
                changes = np.diff(mask.astype(int))
                starts = np.where(changes == 1)[0]
                ends = np.where(changes == -1)[0]
                if mask[0]: starts = np.insert(starts, 0, 0)
                if mask[-1]: ends = np.append(ends, len(mask)-1)
                for s, e in zip(starts, ends):
                    fig.add_vrect(x0=t_arr[s], x1=t_arr[e], fillcolor=fillcolor, opacity=opacity, layer="below", line_width=0, annotation_text=annotation, annotation_position="top left")

            add_vrect_from_mask(bms_pause_mask, "#F59E0B", 0.15, "BMS Intervention")
            add_vrect_from_mask(tr_mask, "#EF4444", 0.25, "⚠️ RAPID HEATING")

            # Maqola uchun harorat shkalasi: chalg‘ituvchi nol-bazali maydon to‘ldirishidan saqlanish
            # va termal o‘zgarishni ma’lumotga asoslangan tor Y-o‘qi bilan ko‘rsatish.
            if name.startswith("32. Core Temperature") or name.startswith("33. Surface Temperature"):
                temp_min = float(np.nanmin(y))
                temp_max = float(np.nanmax(y))
                pad = max(0.5, 0.15 * max(1e-6, temp_max - temp_min))
                fig.update_yaxes(range=[temp_min - pad, temp_max + pad])

            fig.update_layout(title=dict(text=name, font=dict(size=14, color="#1E3A8A")), margin=dict(l=0, r=0, t=40, b=0), height=300, xaxis_title=x_title, yaxis_title=y_title, plot_bgcolor='rgba(0,0,0,0)', hovermode="x unified" if mode!="markers" else "closest", showlegend=("26." in name or "27." in name or "41." in name or "42." in name))
            st.plotly_chart(fig, width='stretch', key=plot_key or f"plotly_chart_{clean_name}_{id(fig)}")

        # -----------------------------------------------------------------
        # 4. TABLAR VA FIGURE BUILDER
        # -----------------------------------------------------------------
        tab_kin, tab_batt, tab_therm, tab_builder, tab_rep = st.tabs(["🏎️ Kinematics", "🔋 Powertrain & SOC", "🌡️ Thermal", "🖌️ Q1 Figure Builder", "📑 Scientific Export"]) 

        def dispatch_plots(indices, columns=2):
            cols = st.columns(columns)
            for count, idx in enumerate(indices):
                with cols[count % columns]: render_plotly_chart(*plot_configs[idx], plot_key=f"plotly_chart_{idx}_{count}")

        with tab_kin: dispatch_plots(list(range(0, 13))) 
        with tab_batt: dispatch_plots(list(range(13, 31)) + [39, 40, 41]) # 47 ta jami
        with tab_therm: dispatch_plots(list(range(31, 40)) + [42, 43, 44, 45, 46]) 
        
        with tab_builder:
            st.markdown("### 🛠️ Python Publication Standard Configuration")
            st.info("Configure the global Matplotlib styles to meet specific journal requirements (Elsevier, IEEE, Springer, Nature).")
            
            cdes1, cdes2, cdes3, cdes4 = st.columns(4)
            with cdes1:
                ui_font = st.selectbox("Font Family", ["Arial", "Times New Roman", "Helvetica", "Dejavu Sans"])
                ui_grid = st.selectbox("Grid Lines Opacity", ["20% Lighter Grid (Q1 Style)", "Standard Grid", "No Grid"])
                ui_format = st.selectbox("📷 Image Export Format", ["pdf", "tiff", "png", "svg", "jpeg"])
            with cdes2:
                ui_font_size = st.number_input("Base Font Size (pt)", min_value=6, max_value=16, value=9)
                ui_line_width = st.slider("📈 Signal Line Width (pt)", min_value=0.5, max_value=5.0, value=2.2, step=0.1)
                ui_dpi = st.selectbox("Export Resolution (DPI)", [150, 300, 600, 1200], index=2)
            with cdes3:
                ui_legend = st.selectbox("Legend Location", ["upper right", "best", "upper left", "lower right"])
                ui_enable_sync_line = st.toggle("⏱️ Enable Time Cross-Sync Line", value=True, help="Draws a vertical synchronized line across subplots during peak acceleration.")
                ui_enable_peaks = st.toggle("🎯 Enable Auto Peak Annotations", value=True, help="Draws an elegant arrow pointing to the maximum value of key signals.")
            with cdes4:
                ui_fig_width = st.number_input("Figure Width (inch)", value=7.08, min_value=3.0, max_value=12.0, step=0.1)
                ui_fig_height = st.number_input("Figure Base Height", value=8.5, min_value=3.0, max_value=15.0, step=0.5)

            st.markdown("---")
            st.markdown("### 🧩 Build Custom Subplot Figures (Max 10 Figures)")
            
            all_names = ["- None -"] + [p[0] for p in plot_configs]
            default_figures = {
                0: [2, 3, 8, 0, 0], 1: [1, 3, 4, 0, 0], 2: [4, 5, 6, 7, 3],
                3: [10, 9, 11, 14, 30], 4: [20, 21, 22, 23, 40], # Figure 5 now includes SOC Confidence Bounds (index 40)
                5: [35, 32, 33, 34, 0], 6: [25, 26, 41, 0, 0] # Figure 7 now includes Absolute Tracking Error (index 41)
            }

            figure_selections = {}
            for i in range(10):
                with st.expander(f"📝 Configure Figure {i+1}", expanded=(i==0 or i==4 or i==6)):
                    f_cols = st.columns(5)
                    sub_selections = []
                    for j, sub in enumerate(["(a)", "(b)", "(c)", "(d)", "(e)"]):
                        default_idx = default_figures[i][j] if i in default_figures and default_figures[i][j] > 0 else 0
                        with f_cols[j]:
                            sel = st.selectbox(f"Subplot {sub}", all_names, index=default_idx, key=f"fig_v57_{i}_sub_{j}")
                            if sel != "- None -":
                                sub_selections.append(sel)
                    figure_selections[i] = sub_selections

        # -----------------------------------------------------------------
        # 5. MASTER SCIENTIFIC ZIP EXPORT MACHINE
        # -----------------------------------------------------------------
        with tab_rep:
            st.markdown("### 💾 Master ZIP Export Engine") 
            st.info("💡 Generates the entire workspace inside one single ZIP archive including calculation data sheets and all customized high-res figures.")
            file_base_name = st.text_input("📝 Archive Base Name:", value="QwatLab_V1_0_0_Publication_Suite") 
              
            if st.button("🚀 GENERATE PUBLICATION ARCHIVE", type="primary", width='stretch'): 
                with st.spinner(f"⏳ Rendering Custom Figures in '{ui_format.upper()}' format ({ui_dpi} DPI)..."):
                    
                    grid_status = True if ui_grid != "No Grid" else False
                    grid_alpha = 0.25 if "20% Lighter" in ui_grid else 0.6
                    
                    PUBLICATION_STYLE = {
                        'font.family': ui_font, 'font.size': ui_font_size, 'axes.linewidth': 1.2,
                        'axes.labelsize': ui_font_size, 'axes.titlesize': ui_font_size + 1,
                        'xtick.labelsize': 8, 'ytick.labelsize': 8,
                        'lines.linewidth': ui_line_width,
                        'legend.loc': ui_legend, 'legend.fontsize': 7.5, 'legend.frameon': False,
                        'axes.grid': grid_status,
                        'grid.color': '#CBD5E1' if grid_alpha > 0.3 else '#E2E8F0',
                        'grid.linestyle': '--', 'grid.linewidth': 0.5, 'figure.dpi': ui_dpi
                    }
                    plt.rcParams.update(PUBLICATION_STYLE)
                    
                    Q1_COLORS = ['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e', '#7f7f7f']
                    peak_idx = np.argmax(np.abs(a_ms2))
                    peak_time = t_arr[peak_idx]

                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                         
                        # A. EXCEL MA’LUMOTLARI
                        excel_buf = io.BytesIO()
                        with pd.ExcelWriter(excel_buf, engine='openpyxl') as writer:
                            df_res.to_excel(writer, sheet_name='Temporal_Data', index=False)
                            pd.DataFrame(list(sp.items()), columns=["Parameter", "Value"]).to_excel(writer, sheet_name='Boundary_Conditions', index=False)
                        zip_file.writestr(f"Source_Data/{file_base_name}_Calculations.xlsx", excel_buf.getvalue())
                        
                        # B. STANDART 42 TA RASM
                        fig_std, ax_std = plt.subplots(figsize=(8.0, 4.0), dpi=100) 
                        for idx, cfg in enumerate(plot_configs):
                            name, data, color, fill, x_data, mode = cfg
                            ax_std.clear() 
                            clean_name = name.split(". ")[1] if ". " in name else name
                            core_label = clean_name.split("[")[0].strip()
                            final_y_label = academic_labels.get(core_label, clean_name)
                            
                            if "26. Stochastic" in name:
                                ax_std.plot(x_data, soc_true, color='#64748b', linewidth=ui_line_width, label='True SOC')
                                ax_std.plot(x_data, soc_ekf, color='#D97706', linewidth=ui_line_width, linestyle='--', label='EKF SOC')
                                ax_std.plot(x_data, soc_ukf, color='#10b981', linewidth=ui_line_width, linestyle=':', label='UKF SOC')
                                ax_std.legend()
                            elif "27. Tracking Error" in name:
                                ax_std.plot(x_data, soc_true - soc_ekf, color='#D97706', linewidth=ui_line_width, label='EKF Error')
                                ax_std.plot(x_data, soc_true - soc_ukf, color='#10b981', linewidth=ui_line_width, label='UKF Error')
                                ax_std.legend()
                            elif "41. SOC ±1.5% Reference Tube" in name:
                                ax_std.fill_between(x_data, soc_true - 1.5, soc_true + 1.5, color='#CBD5E1', alpha=0.4, label='±1.5% Reference Tube')
                                ax_std.plot(x_data, soc_true, color='#475569', linewidth=ui_line_width, label='True SOC')
                                ax_std.plot(x_data, soc_ekf, color='#D97706', linewidth=ui_line_width, linestyle='--', label='EKF')
                                ax_std.plot(x_data, soc_ukf, color='#10b981', linewidth=ui_line_width, linestyle=':', label='UKF')
                                ax_std.legend()
                            elif "42. Absolute Tracking Error Comparison" in name:
                                ax_std.plot(x_data, np.abs(soc_true - soc_ekf), color='#D97706', linewidth=ui_line_width, label='EKF Absolute Error')
                                ax_std.plot(x_data, np.abs(soc_true - soc_ukf), color='#10b981', linewidth=ui_line_width, label='UKF Absolute Error')
                                ax_std.axhline(y=1.0, color='red', linestyle='--', linewidth=1.0, label='1% Safety Limit')
                                ax_std.legend()
                            else:
                                if mode == "markers": ax_std.scatter(x_data, data, color=color, s=2)
                                else: ax_std.plot(x_data, data, color=color, linewidth=ui_line_width) 
                                
                            ax_std.set_xlabel("Current (A)" if mode=="markers" else "Time (s)", fontweight='bold') 
                            ax_std.set_ylabel(final_y_label, fontweight='bold') 
                            ax_std.spines['top'].set_visible(False)
                            ax_std.spines['right'].set_visible(False)
                            fig_std.tight_layout() 
                            
                            img_buf = io.BytesIO()
                            fig_std.savefig(img_buf, format=ui_format, bbox_inches='tight')
                            safe_title = clean_name.replace("/", "_").replace("[", "").replace("]", "").replace("%", "Pct").replace("°C", "C").replace(" ", "_")
                            zip_file.writestr(f"Standard_42_Plots/Fig_{idx+1}_{safe_title}.{ui_format}", img_buf.getvalue())
                            gc.collect()

                        # C. NASHR UCHUN SUBPLOT RASMLARI
                        valid_figures_count = 0
                        caption_summary = []

                        for fig_idx, sub_names in figure_selections.items():
                            num_subs = len(sub_names)
                            if num_subs == 0: continue
                            
                            valid_figures_count += 1
                            dynamic_height = max(4.0, ui_fig_height * (num_subs / 4.5))
                            fig_q1, axs = plt.subplots(num_subs, 1, figsize=(ui_fig_width, dynamic_height), sharex=True)
                            
                            if num_subs == 1: axs = [axs]
                            subplot_letters = ['(a)', '(b)', '(c)', '(d)', '(e)']
                            caption_parts = []

                            for sub_idx, s_name in enumerate(sub_names):
                                item = plot_dict[s_name]
                                clean_name = s_name.split(". ")[1]
                                core_label = clean_name.split("[")[0].strip()
                                final_y_label = academic_labels.get(core_label, clean_name)
                                use_color = Q1_COLORS[sub_idx % len(Q1_COLORS)]
                                
                                caption_parts.append(f"{subplot_letters[sub_idx]} {core_label.lower()}")

                                if "26. Stochastic" in s_name:
                                    axs[sub_idx].plot(item['x'], soc_true, color='#475569', linewidth=ui_line_width, label='True SOC')
                                    axs[sub_idx].plot(item['x'], soc_ekf, color=Q1_COLORS[1], linewidth=ui_line_width, linestyle='--', label='EKF')
                                    axs[sub_idx].plot(item['x'], soc_ukf, color=Q1_COLORS[2], linewidth=ui_line_width, linestyle=':', label='UKF')
                                    axs[sub_idx].legend(loc=ui_legend)
                                elif "27. Tracking Error" in s_name:
                                    axs[sub_idx].plot(item['x'], soc_true - soc_ekf, color=Q1_COLORS[1], linewidth=ui_line_width, label='EKF Error')
                                    axs[sub_idx].plot(item['x'], soc_true - soc_ukf, color=Q1_COLORS[2], linewidth=ui_line_width, label='UKF Error')
                                    axs[sub_idx].legend(loc=ui_legend)
                                elif "41. SOC ±1.5% Reference Tube" in s_name:
                                    axs[sub_idx].fill_between(item['x'], soc_true - 1.5, soc_true + 1.5, color='#CBD5E1', alpha=0.4, label='±1.5% Reference Tube')
                                    axs[sub_idx].plot(item['x'], soc_true, color='#475569', linewidth=ui_line_width, label='True SOC')
                                    axs[sub_idx].plot(item['x'], soc_ekf, color=Q1_COLORS[1], linewidth=ui_line_width, linestyle='--', label='EKF')
                                    axs[sub_idx].plot(item['x'], soc_ukf, color=Q1_COLORS[2], linewidth=ui_line_width, linestyle=':', label='UKF')
                                    axs[sub_idx].legend(loc=ui_legend)
                                elif "42. Absolute Tracking Error Comparison" in s_name:
                                    axs[sub_idx].plot(item['x'], np.abs(soc_true - soc_ekf), color=Q1_COLORS[1], linewidth=ui_line_width, label='EKF Error')
                                    axs[sub_idx].plot(item['x'], np.abs(soc_true - soc_ukf), color=Q1_COLORS[2], linewidth=ui_line_width, label='UKF Error')
                                    axs[sub_idx].axhline(y=1.0, color='red', linestyle='--', linewidth=1.0, label='1% Limit')
                                    axs[sub_idx].legend(loc=ui_legend)
                                else:
                                    if item['mode'] == "markers": 
                                        axs[sub_idx].scatter(item['x'], item['y'], s=3, color=use_color)
                                    else: 
                                        axs[sub_idx].plot(item['x'], item['y'], color=use_color, linewidth=ui_line_width)

                                # Maksimal nuqtalarni belgilash
                                if ui_enable_peaks and not "Correlation" in s_name and len(item['y']) > 0:
                                    max_v_idx = np.argmax(item['y'])
                                    if max_v_idx < len(item['x']):
                                        p_x = item['x'][max_v_idx]
                                        p_y = item['y'][max_v_idx]
                                        if "Acceleration" in s_name or "Torque" in s_name or "Heat" in s_name:
                                            axs[sub_idx].annotate('Peak Value', xy=(p_x, p_y), 
                                                                  xytext=(p_x + (np.max(item['x'])*0.05), p_y * 0.9),
                                                                  arrowprops=dict(facecolor='#475569', arrowstyle='->', lw=0.8),
                                                                  fontsize=ui_font_size-2, color='#475569')

                                # Sinxronlashtirish chizig‘i
                                if ui_enable_sync_line:
                                    axs[sub_idx].axvline(x=peak_time, color='#CBD5E1', linestyle=':', linewidth=1.0, alpha=0.8, zorder=1)

                                axs[sub_idx].set_ylabel(final_y_label, fontweight='normal')
                                axs[sub_idx].set_title(subplot_letters[sub_idx], loc='left', fontweight='bold', pad=5)
                                axs[sub_idx].spines['top'].set_visible(False)
                                axs[sub_idx].spines['right'].set_visible(False)
                                if ui_grid != "No Grid":
                                    axs[sub_idx].grid(True, which='both', color='#E2E8F0', linestyle='--', linewidth=0.5, alpha=grid_alpha)

                            axs[-1].set_xlabel("Time (s)" if "V-I" not in sub_names[-1] else "Current (A)")
                            fig_q1.align_ylabels(axs)
                            fig_q1.tight_layout(h_pad=2.2) 
                            
                            caption_text = f"Figure {fig_idx+1}. High-fidelity synchronized physical response during the driving cycle: {', '.join(caption_parts)}."
                            caption_summary.append(caption_text)

                            img_buf_q1 = io.BytesIO()
                            fig_q1.savefig(img_buf_q1, format=ui_format, dpi=ui_dpi, bbox_inches='tight')
                            zip_file.writestr(f"Publication_Figures_Q1/Figure_{fig_idx+1}.{ui_format}", img_buf_q1.getvalue())
                            
                            # Majburiy ravishda yuqori aniqlikdagi LZW TIFF faylini ham saqlab qo'yamiz (Nature Standard)
                            if ui_format != "tiff":
                                tiff_buf = io.BytesIO()
                                fig_q1.savefig(tiff_buf, format="tiff", dpi=600, bbox_inches='tight', pil_kwargs={"compression": "tiff_lzw"})
                                zip_file.writestr(f"Publication_Figures_Q1/Figure_{fig_idx+1}_HighRes.tiff", tiff_buf.getvalue())
                            
                            plt.close(fig_q1)
                            gc.collect()

                        zip_file.writestr("Publication_Figures_Q1/Figure_Captions_Q1_Style.txt", "\n\n".join(caption_summary))
                        plt.close('all') 

                    zip_buffer.seek(0)
                    st.session_state['zip_data'] = zip_buffer.getvalue()
                    st.session_state['zip_name'] = f"{file_base_name}_V1_0_0_Suite.zip"
                    export_status_placeholder.success(f"✅ Suite built! Exported {valid_figures_count} custom figures & 42 standard plots.")

            if 'zip_data' in st.session_state:
                st.download_button(label="📥 DOWNLOAD SCIENTIFIC ARCHIVE (ZIP)", data=st.session_state['zip_data'], file_name=st.session_state['zip_name'], mime="application/zip", type="primary")

# Tizim boshqaruv tugmalari 
c_ctrl1, c_ctrl2 = st.columns(2) 
with c_ctrl1:
    if st.button("🔄 Clear Cache & Restart System", width='stretch'):
        st.session_state.clear() 
        st.rerun() 
with c_ctrl2:
    if st.button("🚪 Shutdown & Exit Server", width='stretch'): 
        os.kill(os.getpid(), signal.SIGINT)
# =====================================================================
# 4-BLOK OXIRI
# =====================================================================
