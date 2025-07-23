import streamlit as st
import subprocess
import sys
import os

# Script options
script_map = {
    "Pacifica vs Extended": "pac.py",
    "Pacifica vs Lighter": "pac1.py",
    "Lighter vs Extended": "test3.py"
}

st.title("📊 Funding Rate Arbitrage Comparison Tool")
st.write("Choose exchange pair for comparison:")

option = st.selectbox("Select comparison pair", list(script_map.keys()))

# Sort option only for test3.py
sort_choice = None
if option == "Lighter vs Extended":
    sort_choice = st.radio("Sort by:", ["ROI ascending", "Difference descending"])
    sort_value = "2" if sort_choice == "ROI ascending" else "1"
else:
    sort_value = None

if st.button("Run Comparison"):
    script_file = script_map[option]
    st.write(f"🔍 Running: `{script_file}`")
    
    try:
        env = os.environ.copy()
        if sort_value:
            env["SORT_MODE"] = sort_value

        command = [sys.executable, "injector.py", script_file] if script_file == "test3.py" else [sys.executable, script_file]
        
        result = subprocess.run(command, capture_output=True, text=True, env=env)
        
        if result.returncode != 0:
            st.error(f"❌ Error running {script_file}")
            st.text(result.stderr)
        else:
            st.success(f"✅ Output from {script_file}:")
            st.text(result.stdout)
    
    except Exception as e:
        st.error(f"An exception occurred: {e}")
