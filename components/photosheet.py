import streamlit as st

def show_photosheet():
    st.subheader("📸 Structure Photosheet")
    
    st.info("Upload structure photos below. You can add captions for each to be included in the final report.")

    # Allowing multiple file uploads (JPG, PNG)
    uploaded_files = st.file_uploader("Choose photos", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

    if uploaded_files:
        st.write(f"Total photos uploaded: {len(uploaded_files)}")
        
        # We create a 2-column grid layout for the preview
        cols = st.columns(2)
        
        for index, file in enumerate(uploaded_files):
            # This logic alternates between the two columns
            with cols[index % 2]:
                st.image(file, use_container_width=True)
                # Unique key for each text input so they don't conflict
                st.text_input(f"Caption for Photo {index + 1}", key=f"cap_{index}")
                st.divider()
    else:
        st.warning("No photos uploaded yet. Please upload images to see the layout.")

    return uploaded_files