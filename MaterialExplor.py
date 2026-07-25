import streamlit as st
import pandas as pd
import json
import re
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import linregress
import numpy as np
import os
import sys

# تنظیمات اولیه صفحه
st.set_page_config(page_title="Materials Explorer Pro", layout="wide")

def resource_path(relative_path):
    """ مسیر فایل‌ها را پیدا می‌کند (سازگار با محیط‌های مختلف) """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

@st.cache_data
def load_data():
    try:
        ptable_path = resource_path("ptable2.csv")
        ptable_df = pd.read_csv(ptable_path)
        ptable_df.rename(columns={"symbol": "element"}, inplace=True)
        ptable_df['element'] = ptable_df['element'].str.strip()

        json_path = resource_path("vaspkit_output.json")
        with open(json_path, "r") as f:
            mech_data_nested = json.load(f)

        mechanical_properties_list = []
        for material, data in mech_data_nested.items():
            if not data:
                continue
                
            props = {"material": material}
            for root_key in ["Crystal_System", "Space_Group", "Independent_Elastic_Constants", "Is_DFT_Verified"]:
                if root_key in data:
                    props[root_key] = data[root_key]

            if "Elastic_Tensor_Voigt" in data:
                for k, v in data["Elastic_Tensor_Voigt"].items():
                    props[f"Elastic_{k}"] = v

            if "Anisotropic_Mechanical_Properties" in data:
                for key, stats in data["Anisotropic_Mechanical_Properties"].items():
                    clean_key = key.lstrip('|__').replace('__', '_')
                    if isinstance(stats, dict):
                        for stat in ["Min", "Max", "Anisotropy"]:
                            if stat in stats:
                                props[f"Aniso_{clean_key}_{stat}"] = stats[stat]

            if "Average_Mechanical_Properties" in data:
                for key, stats in data["Average_Mechanical_Properties"].items():
                    clean_key = key.lstrip('|__').replace('__', '_')
                    if isinstance(stats, dict):
                        for stat in ["Voigt", "Reuss", "Hill"]:
                            if stat in stats:
                                props[f"Avg_{clean_key}_{stat}"] = stats[stat]

            if "Additional_Properties" in data:
                for key, val in data["Additional_Properties"].items():
                    props[key] = val
            
            mechanical_properties_list.append(props)

        mech_df = pd.DataFrame(mechanical_properties_list)
        if mech_df.empty:
            return pd.DataFrame(), [], []

    except Exception as e:
        st.error(f"An error occurred during data loading: {e}")
        return pd.DataFrame(), [], []

    def extract_elements(formula):
        return re.findall(r'[A-Z][a-z]?', formula)

    feature_cols = [c for c in ptable_df.columns if c not in ['element']]
    materials_data = []

    for _, row in mech_df.iterrows():
        material = row['material']
        elements = extract_elements(material)
        sub_df = ptable_df[ptable_df['element'].isin(elements)]
        
        if len(sub_df) == 0 or len(sub_df) != len(elements):
            continue
            
        averaged = sub_df[feature_cols].mean(numeric_only=True)
        averaged['material'] = material
        materials_data.append(averaged)

    features_avg_df = pd.DataFrame(materials_data)
    if features_avg_df.empty:
        return pd.DataFrame(), [], []

    merged_df = pd.merge(features_avg_df, mech_df, on='material', how='inner')
    atomic_features = sorted([c for c in features_avg_df.columns if c not in ['material']])
    numeric_mech_cols = mech_df.select_dtypes(include=[np.number]).columns.tolist()
    excluded_y_cols = ['material', 'Independent_Elastic_Constants', 'Is_DFT_Verified']
    mechanical_properties = sorted([c for c in numeric_mech_cols if c not in excluded_y_cols])
    
    return merged_df, atomic_features, mechanical_properties

global_df, atomic_features, mechanical_properties = load_data()

st.title("🧪 Materials & Elastic Properties Explorer Pro")
st.markdown("**Blue = DFT Verified | Orange = Not Verified | Click → View 3D Structure**")
st.markdown("---")

if global_df.empty:
    st.warning("No valid data could be loaded. Please ensure `ptable2.csv` and `vaspkit_output.json` are in the directory.")
    st.stop()

# استایل اسلایدر نئونی
st.markdown("""
<style>
    .stSlider > div > div > div > div {
        background: linear-gradient(to right, #00ccff11, #00f2ff33) !important;
        height: 6px !important;
    }
    .stSlider > div > div > div[role="slider"] {
        background: #00ccff !important;
        border: 1.5px solid #00f2ff !important;
        box-shadow: 0 0 10px #00f2ff !important;
    }
</style>
""", unsafe_allow_html=True)

# مقداردهی متغیرهای استیت
if "selected_material" not in st.session_state:
    st.session_state.selected_material = None
if "show_3d" not in st.session_state:
    st.session_state.show_3d = False

# ====================== سایدبار ======================
with st.sidebar:
    st.header("🔍 Material Details")

    if st.session_state.selected_material:
        mat = st.session_state.selected_material
        
        # چک کردن اینکه ماده انتخاب شده در دیتاست موجود باشد
        if mat in global_df['material'].values:
            row = global_df[global_df['material'] == mat].iloc[0]

            # نمایش وضعیت DFT با رنگ‌ها
            dft_status = str(row.get("Is_DFT_Verified", "Unknown"))
            if dft_status.lower() == "true":
                st.info("🔹 DFT Verified")
            else:
                st.warning("🔸 Not DFT Verified")

            st.markdown(f"### **{mat}**")

            # دکمه 3D
            if st.button("View 3D Crystal Structure", type="primary", use_container_width=True):
                st.session_state.show_3d = True

            # نمایش خواص
            st.divider()
            details = row.drop("material")
            for col, val in details.items():
                if pd.isna(val): continue
                # مخفی کردن ستون‌های خیلی طولانی
                if isinstance(val, (int, float, np.number)):
                    st.write(f"**{str(col).replace('_', ' ')}**: {val:.4f}")
                else:
                    st.write(f"**{str(col).replace('_', ' ')}**: {val}")

            st.divider()
            if st.button("Clear Selection"):
                st.session_state.selected_material = None
                st.session_state.show_3d = False
                st.rerun()
        else:
            st.warning("Selected material data not found.")
    else:
        st.info("Click on a point in the chart to view its details and 3D structure here.")

# ====================== 3D VIEWER ======================
if st.session_state.show_3d and st.session_state.selected_material:
    mat = st.session_state.selected_material

    col_3d_btn, _ = st.columns([1, 5])
    with col_3d_btn:
        if st.button("✖ Close 3D Viewer", type="secondary"):
            st.session_state.show_3d = False
            st.rerun()

    try:
        with open("poscars.txt", "r", encoding="utf-8") as f:
            content = f.read()

        escaped_mat = re.escape(mat)
        pattern = rf"^>>> {escaped_mat}\n(.*?)(?=^>>> |\Z)"
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)

        if match:
            block = match.group(1).strip()
            lines = [line.strip() for line in block.splitlines() if line.strip()]

            if len(lines) < 9:
                st.warning("POSCAR format is too short.")
            else:
                try:
                    scale = float(lines[1])
                    lattice = []
                    for i in range(2, 5):
                        vec = list(map(float, lines[i].split()[:3]))
                        lattice.append(vec)

                    elements = lines[5].split()
                    counts = list(map(int, lines[6].split()))
                    coord_type = lines[7].lower().startswith("d")

                    coords = []
                    for line in lines[8:]:
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 3:
                                coords.append([float(parts[0]), float(parts[1]), float(parts[2])])

                    xyz_lines = [str(sum(counts)), mat]
                    idx = 0
                    for elem, cnt in zip(elements, counts):
                        for _ in range(cnt):
                            c = coords[idx]
                            if coord_type: 
                                x = c[0]*lattice[0][0] + c[1]*lattice[1][0] + c[2]*lattice[2][0]
                                y = c[0]*lattice[0][1] + c[1]*lattice[1][1] + c[2]*lattice[2][1]
                                z = c[0]*lattice[0][2] + c[1]*lattice[1][2] + c[2]*lattice[2][2]
                            else: 
                                x, y, z = c
                            xyz_lines.append(f"{elem} {x*scale:.6f} {y*scale:.6f} {z*scale:.6f}")
                            idx += 1

                    xyz_content = "\n".join(xyz_lines)
                    st.markdown(f"### 3D Structure — {mat}")

                    html_code = f"""
                    <div id="viewer3d" style="width:100%; height:500px; background:#0e1117; border-radius:15px; overflow:hidden; border: 1px solid #333;"></div>
                    <script src="https://3dmol.org/build/3Dmol-min.js"></script>
                    <script>
                        let viewer = $3Dmol.createViewer("viewer3d", {{backgroundColor: "#0e1117"}});
                        viewer.addModel(`{xyz_content}`, "xyz");
                        viewer.setStyle({{stick: {{radius: 0.18, color: 'spectrum'}}, sphere: {{scale: 0.4, colorscheme: 'Jmol'}}}});
                        viewer.zoomTo();
                        viewer.spin(true);
                        viewer.render();
                    </script>
                    """
                    st.components.v1.html(html_code, height=520, scrolling=False)

                except Exception as e:
                    st.error(f"POSCAR parsing error for {mat}: {e}")
        else:
            st.warning(f"3D Structure data not found for '{mat}' inside `poscars.txt`.")
    except FileNotFoundError:
        st.error("File `poscars.txt` not found! Please place it in the same directory to enable the 3D Viewer.")
    except Exception as e:
        st.error(f"Unexpected Error in 3D viewer: {e}")

# ====================== نمودار اصلی ======================
st.markdown("### Chart Settings")

dft_filter = st.radio(
    "Filter by DFT Verification:",
    options=["Show All", "Only DFT Verified (Blue)", "Only Not Verified (Orange)"],
    horizontal=True
)

all_features = sorted(list(set(atomic_features + mechanical_properties)))

col1, col2 = st.columns(2)
with col1:
    x_axis_name = st.selectbox("Select X-Axis Feature:", all_features, 
                               index=all_features.index("atomic_number") if "atomic_number" in all_features else 0)
with col2:
    y_axis_name = st.selectbox("Select Y-Axis Feature:", all_features,
                               index=all_features.index("Elastic_C11") if "Elastic_C11" in all_features else 0)

if x_axis_name and y_axis_name:
    # پاکسازی داده‌ها و تبدیل به عددی برای اسلایدر
    clean_df = global_df.copy()
    clean_df[x_axis_name] = pd.to_numeric(clean_df[x_axis_name], errors='coerce')
    clean_df[y_axis_name] = pd.to_numeric(clean_df[y_axis_name], errors='coerce')
    clean_df = clean_df.dropna(subset=[x_axis_name, y_axis_name])
    
    if clean_df.empty:
        st.warning("No numeric data available for the selected axes.")
        st.stop()

    x_min_val, x_max_val = float(clean_df[x_axis_name].min()), float(clean_df[x_axis_name].max())
    y_min_val, y_max_val = float(clean_df[y_axis_name].min()), float(clean_df[y_axis_name].max())

    col_a, col_b = st.columns(2)
    with col_a:
        if x_min_val < x_max_val:
            x_range = st.slider(f"X Range ({x_axis_name.replace('_', ' ')})", 
                                min_value=x_min_val, max_value=x_max_val, value=(x_min_val, x_max_val))
        else:
            x_range = (x_min_val, x_max_val)

    with col_b:
        if y_min_val < y_max_val:
            y_range = st.slider(f"Y Range ({y_axis_name.replace('_', ' ')})", 
                                min_value=y_min_val, max_value=y_max_val, value=(y_min_val, y_max_val))
        else:
            y_range = (y_min_val, y_max_val)

    # اعمال فیلتر بر اساس اسلایدرها
    plot_df = clean_df[(clean_df[x_axis_name] >= x_range[0]) & (clean_df[x_axis_name] <= x_range[1]) & 
                       (clean_df[y_axis_name] >= y_range[0]) & (clean_df[y_axis_name] <= y_range[1])].copy()

    # اعمال فیلتر وضعیت DFT
    if dft_filter == "Only DFT Verified (Blue)":
        plot_df = plot_df[plot_df['Is_DFT_Verified'].astype(str).str.lower() == 'true']
    elif dft_filter == "Only Not Verified (Orange)":
        plot_df = plot_df[plot_df['Is_DFT_Verified'].astype(str).str.lower() == 'false']

    if plot_df.empty:
        st.warning("No data in the selected range.")
    else:
        # تنظیم ستون Is_DFT_Verified به عنوان رشته برای رنگ‌آمیزی Plotly
        plot_df['Is_DFT_Verified'] = plot_df['Is_DFT_Verified'].astype(str)

        fig = px.scatter(
            plot_df, 
            x=x_axis_name, 
            y=y_axis_name, 
            hover_data=['material'], 
            custom_data=['material'],
            color='Is_DFT_Verified',
            color_discrete_map={
                'True': '#1f77b4',  # Blue
                'False': '#ff7f0e'  # Orange
            }
        )

        try:
            x = plot_df[x_axis_name]
            y = plot_df[y_axis_name]
            if x.nunique() > 1:
                slope, intercept, r, p, stderr = linregress(x, y)
                line_x = np.array([x.min(), x.max()])
                line_y = slope * line_x + intercept
                
                fig.add_trace(go.Scatter(
                    x=line_x, y=line_y, mode='lines',
                    line=dict(color='red', dash='dash', width=3),
                    name=f'Regression (R² = {r**2:.3f})'
                ))
        except Exception as e:
            pass

        fig.update_layout(
            title=f'{y_axis_name} vs. {x_axis_name}',
            xaxis_title=x_axis_name,
            yaxis_title=y_axis_name,
            hovermode="closest",
            template="plotly_white",
            height=600,
            margin=dict(l=40, r=40, t=60, b=40)
        )

        # دریافت رویداد کلیک
        selected_data = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="scatter_plot")

        # در صورت کلیک کردن روی یک نقطه، آن را در سایدبار نمایش می‌دهیم
        if selected_data and "selection" in selected_data and selected_data["selection"].get("points"):
            clicked_material = selected_data["selection"]["points"][0]["customdata"][0]
            if st.session_state.selected_material != clicked_material:
                st.session_state.selected_material = clicked_material
                # با rerun، برنامه دوباره اجرا شده و اطلاعات در سایدبار رندر می‌شود
                st.rerun()

st.caption("Materials Explorer Pro — 3D Viewer with HTML/3Dmol.js • Neon Sliders • Data Filter • 2026")
