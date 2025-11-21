import streamlit as st

# PAGE CONFIG
st.set_page_config(layout="wide")

# Main logic
with st.status("Product Architecture", expanded=True):
    st.image("data/images/app_architecture.PNG")

with st.status("Product Description"):
    # Read the PM guide from markdown file
    try:
        with open("data/info/product_description.md", "r", encoding="utf-8") as f:
            pm_guide_content = f.read()
        st.markdown(pm_guide_content)
    except FileNotFoundError:
        st.error("product_description.md file not found. Please ensure the file exists in the project root.")
    except Exception as e:
        st.error(f"Error reading product_description.md: {str(e)}")

with st.status("Product Technical Stack"):
    # Read the PM guide from markdown file
    try:
        with open("data/info/product_stack.md", "r", encoding="utf-8") as f:
            pm_guide_content = f.read()
        st.markdown(pm_guide_content)
    except FileNotFoundError:
        st.error("product_stack.md file not found. Please ensure the file exists in the project root.")
    except Exception as e:
        st.error(f"Error reading product_stack.md: {str(e)}")

with st.status("Product Manual"):
    # Read the PM guide from markdown file
    try:
        with open("data/info/product_manual.md", "r", encoding="utf-8") as f:
            pm_guide_content = f.read()
        st.markdown(pm_guide_content)
    except FileNotFoundError:
        st.error("product_manual.md file not found. Please ensure the file exists in the project root.")
    except Exception as e:
        st.error(f"Error reading product_manual.md: {str(e)}")