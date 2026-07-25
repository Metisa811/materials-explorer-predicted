# 🔬 Materials Explorer - Interactive Materials Property Explorer

**An interactive web application for exploring and analyzing material properties with a modern user interface**

![Python](https://img.shields.io/badge/Python-100%25-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Web_App-red)
![Status](https://img.shields.io/badge/Status-Active-success)

## 📱 Live Demo

🚀 **[Materials Explorer - Streamlit App](https://materials-explorer-lh67agch9bk6y42p96yxa5.streamlit.app/)**

## 📋 About This Project

Materials Explorer is an interactive web application that empowers researchers and students to:

✨ **Explore and compare mechanical properties** of various materials
✨ **Investigate MAX Phase characteristics** with comprehensive data
✨ **Visualize relationships** with interactive 2D scatter plots
✨ **View 3D crystal structures** with full 3D visualization using 3Dmol.js
✨ **Apply advanced filtering** based on multiple material properties

## 🎯 Key Features

### 🔍 Search & Filtering
- Select X and Y axes from all available numerical properties
- Adjustable range sliders for precise data selection
- Real-time dynamic data updates

### 📊 Data Visualization
- Interactive scatter plots powered by Plotly
- Color-coded display based on **mechanical stability** (Green = Stable | Red = Unstable)
- Automatic linear regression with R² value display

### 🧬 3D Crystal Structure Viewer
- Full 3D visualization of crystal structures
- Automatic POSCAR → XYZ format conversion
- Complete interactivity: rotation, zooming, and inspection
- No external software installation required

### 📌 Material Details Panel
- Complete property display for each material
- Mechanical stability and brittleness classification
- Dynamic sidebar with instant updates

## 🛠️ Technologies Used

| Technology | Purpose |
|-----------|---------|
| **Streamlit** | Interactive web framework |
| **Pandas** | Data processing and analysis |
| **Plotly** | Interactive visualizations |
| **NumPy** | Numerical computations |
| **SciPy** | Statistical analysis (linear regression) |
| **3Dmol.js** | 3D molecular visualization |

## 📦 Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Metisa811/materials-explorer.git
cd materials-explorer
```

### 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Run the Application
```bash
streamlit run MaterialExplor.py
```

Your browser will automatically open to `http://localhost:8501`

## 📁 Project Structure

```
materials-explorer/
├── MaterialExplor.py        # Main Streamlit application
├── requirements.txt         # Python dependencies
├── ptable2.csv             # Periodic table element properties
├── vaspkit_output.json     # Material mechanical properties
├── poscars.txt             # Crystal structures (POSCAR format)
└── README.md               # This file
```

## 📊 Data Sources

### `ptable2.csv`
Periodic table of elements containing:
- Chemical symbol
- Atomic number
- Atomic mass
- Electronegativity
- Additional elemental properties

### `vaspkit_output.json`
Mechanical properties of MAX Phase materials:
- Elastic tensor (Voigt notation)
- Compliance tensor
- Anisotropic mechanical properties
- Average mechanical properties
- Mechanical stability indicators

### `poscars.txt`
Crystal structures in POSCAR format (VASP standard)

## 🎨 UI Features

✅ **Neon Slider Styling** - Modern sliders with glowing effects
✅ **Responsive Design** - Adapts to all screen sizes
✅ **Dark Theme** - Eye-friendly dark interface
✅ **Multilingual Support** - Code comments in multiple languages

## 💡 How to Use

### Step 1: Select Properties
Choose X and Y axes from the dropdowns at the top

### Step 2: Adjust Ranges
Drag the sliders to focus on the data range you need

### Step 3: Click for Details
Click any point on the scatter plot to:
- View complete material properties in the left sidebar
- Enable the "View 3D Crystal Structure" button

### Step 4: Explore 3D Structure
Click "View 3D Crystal Structure" to:
- Rotate and zoom the crystal structure
- Inspect atomic positions and bonding
- Understand material geometry

## 📈 Usage Examples

### 🔎 Find Stable Materials
1. Set Y-axis to "Brittleness_Indicator"
2. Limit X range to intrinsically stable materials
3. Explore green (stable) data points

### 🔬 Investigate Elasticity
1. X-axis: Bulk_Modulus_Hill
2. Y-axis: Shear_Modulus_Hill
3. Observe correlations between stiffness and shear resistance

### 💪 Material Strength Analysis
1. X-axis: Atomic_Number (weighted average)
2. Y-axis: Young_Modulus_Hill
3. Discover relationships between composition and mechanical properties

## 🤝 Contributing

Found a bug or have improvement ideas?

1. **Open an Issue** - Describe the problem or feature request
2. **Fork the Repository** - Make your changes
3. **Submit a Pull Request** - We'll review your contribution

## 📝 License

This project is released under the **MIT License** - feel free to use it in your projects!

## ✍️ Author

👤 **[Metisa811](https://github.com/Metisa811)**

## 🙏 Acknowledgments

- **Streamlit** for the amazing interactive web framework
- **3Dmol.js** for powerful molecular visualization
- **VASP and VASPKIT** for computational materials tools
- **Scientific community** for materials data and insights

---

### 🌟 If this project helped you, please give it a star!

**Live Application:** https://materials-explorer-lh67agch9bk6y42p96yxa5.streamlit.app/

---

## 📚 Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Python Documentation](https://plotly.com/python/)
- [3Dmol.js Documentation](https://3Dmol.csb.pitt.edu/)
- [VASP Official Website](https://www.vasp.at/)
- [VASPKIT Documentation](https://vaspkit.com/)

## 📧 Contact & Support

For questions or support, feel free to open an issue on the GitHub repository.

---

**Last Updated:** 2025
**Version:** 1.0.0
