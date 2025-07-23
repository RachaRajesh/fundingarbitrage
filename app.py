import streamlit as st
import subprocess
import sys
import os

# Mapping script choices to filenames
script_map = {
    "Pacifica vs Extended": "pac.py",
    "Pacifica vs Lighter": "pac1.py",
    "Lighter vs Extended": "test3.py"
}

st.title("📊 Funding Rate Arbitrage Comparison Tool")
st.write("Choose exchange pair for comparison:")

option = st.selectbox(
    "Select comparison pair",
    list(script_map.keys())
)

if st.button("Run Comparison"):
    script_file = script_map[option]
    st.write(f"🔍 Running: `{script_file}`")
    
    try:
        # Run the selected script and capture the output
        result = subprocess.run([sys.executable, script_file], capture_output=True, text=True)
        
        if result.returncode != 0:
            st.error(f"❌ Error running {script_file}")
            st.text(result.stderr)
        else:
            st.success(f"✅ Output from {script_file}:")
            st.text(result.stdout)
    
    except Exception as e:
        st.error(f"An exception occurred: {e}")
