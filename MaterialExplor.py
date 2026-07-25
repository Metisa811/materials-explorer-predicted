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

# تنظیمات اولیه صفحه استریم‌لیت
st.set_page_config(page_title="Materials Explorer", layout="wide")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        # در استریم‌لیت معمولاً مسیر پوشه جاری ملاک است
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

st.title("🧪 Interactive Materials Property Explorer")
st.markdown("---")

if global_df.empty:
    st.warning("No valid data could be loaded. Please ensure `ptable2.csv` and `vaspkit_output.json` are in the directory.")
    st.stop()

# انتخاب محورها
col1, col2 = st.columns(2)
with col1:
    x_axis_name = st.selectbox("Select Atomic Feature (X-Axis):", atomic_features)
with col2:
    y_axis_name = st.selectbox("Select Mechanical Property (Y-Axis):", mechanical_properties)

if x_axis_name and y_axis_name:
    plot_df = global_df[['material', x_axis_name, y_axis_name]].copy()
    plot_df[x_axis_name] = pd.to_numeric(plot_df[x_axis_name], errors='coerce')
    plot_df[y_axis_name] = pd.to_numeric(plot_df[y_axis_name], errors='coerce')
    plot_df = plot_df.dropna(subset=[x_axis_name, y_axis_name])

    if plot_df.empty:
        st.warning(f"No valid data for {x_axis_name} vs {y_axis_name}")
    else:
        fig = px.scatter(
            plot_df, x=x_axis_name, y=y_axis_name, hover_data=['material'], custom_data=['material']
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
                    line=dict(color='red', dash='dash'),
                    name=f'Regression (R² = {r**2:.3f})'
                ))
        except Exception as e:
            st.toast(f"Could not compute regression: {e}")

        fig.update_layout(
            title=f'{y_axis_name} vs. {x_axis_name}',
            xaxis_title=x_axis_name,
            yaxis_title=y_axis_name,
            hovermode="closest",
            template="plotly_white",
            height=600
        )

        st.markdown("💡 *Click on any point (or select multiple) in the scatter plot below to see detailed information.*")
        
        # نمایش نمودار با قابلیت کلیک (on_select)
        selected_data = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="scatter_plot")

        if selected_data and "selection" in selected_data and selected_data["selection"].get("points"):
            points = selected_data["selection"]["points"]
            
            st.markdown("### 🔍 Selected Material Details")
            
            # ایجاد ستون برای نمایش اطلاعات چند ماده در صورت انتخاب گروهی
            cols = st.columns(min(len(points), 3)) 
            
            for idx, point in enumerate(points):
                material_name = point.get("customdata", [None])[0]
                if material_name:
                    material_data = global_df[global_df['material'] == material_name].iloc[0]
                    
                    # حذف مقادیر خالی و ستون ماده
                    display_data = material_data.drop('material').dropna()
                    
                    display_df = pd.DataFrame({
                        "Property": display_data.index,
                        "Value": display_data.values
                    })
                    
                    # نمایش در ستون‌ها
                    col_idx = idx % 3
                    with cols[col_idx]:
                        st.subheader(f"{material_name}")
                        st.dataframe(display_df, hide_index=True, use_container_width=True)
