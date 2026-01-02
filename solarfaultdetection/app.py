import streamlit as st
from PIL import Image
from src.predict import load_model, predict, CLASS_NAMES
from src.fault_info import get_fault_info
from src.office_locator import find_nearest_office, format_contact_info
import json
from datetime import datetime
from urllib.parse import quote

st.set_page_config(
    page_title="Solar Fault Detection",
    page_icon="🔆",
    layout="wide"
)

st.title("🔆 Solar Panel Fault Detection System")
st.markdown("Upload an EL (Electroluminescence) image of a solar panel to detect faults and get repair instructions.")

@st.cache_resource
def get_model():
    return load_model()

model = get_model()

# Sidebar with information
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This system detects common solar panel faults:
    - Microcracks
    - Hot Spots
    - Snail Trails
    - Cell Breakage
    - Delamination
    - Bypass Diode Failure
    - PID (Potential Induced Degradation)
    """)
    st.markdown("---")
    st.header("📍 Service Office Locator")
    st.markdown("""
    Enter your pincode to:
    - Find nearest service office
    - Get contact information
    - Send fault report directly
    """)
    st.markdown("---")
    st.markdown("**Note:** This is a demonstration system. For production use, train with your specific dataset.")
    
    # Download report if available
    if 'fault_report' in st.session_state:
        st.markdown("---")
        st.download_button(
            label="📥 Download Fault Report",
            data=st.session_state.get('report_text', ''),
            file_name=f"fault_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    uploaded_image = st.file_uploader(
        "Upload Solar Panel EL Image",
        type=["jpg", "jpeg", "png"],
        help="Upload an electroluminescence image of a solar panel"
    )

    if uploaded_image:
        image = Image.open(uploaded_image).convert("RGB")
        st.image(image, caption="Uploaded EL Image", use_container_width=True)

with col2:
    if uploaded_image:
        with st.spinner("Analyzing image..."):
            result = predict(image, model)
        
        fault_type = result["fault_type"]
        confidence = result["confidence"]
        fault_info = get_fault_info(fault_type)
        
        # Display main result
        st.markdown("### 🧪 Detection Result")
        
        # Color code based on severity
        if fault_type == "Healthy Panel":
            st.success(f"**{fault_type}** (Confidence: {confidence*100:.1f}%)")
        elif fault_info.get("severity") == "High":
            st.error(f"**{fault_type}** (Confidence: {confidence*100:.1f}%)")
        elif fault_info.get("severity") == "Medium":
            st.warning(f"**{fault_type}** (Confidence: {confidence*100:.1f}%)")
        else:
            st.info(f"**{fault_type}** (Confidence: {confidence*100:.1f}%)")
        
        # Fault description
        st.markdown("---")
        st.markdown("### 📋 Fault Description")
        st.write(fault_info.get("description", "No description available."))
        
        # Severity
        if fault_type != "Healthy Panel":
            st.markdown(f"**Severity:** {fault_info.get('severity', 'Unknown')}")
        
        # Symptoms (if available)
        if "symptoms" in fault_info:
            st.markdown("### 🔍 Symptoms")
            for symptom in fault_info["symptoms"]:
                st.markdown(f"- {symptom}")
        
        # Repair steps
        st.markdown("---")
        st.markdown("### 🔧 Repair Instructions")
        st.markdown("**Step-by-step repair process:**")
        for i, step in enumerate(fault_info.get("repair_steps", []), 1):
            st.markdown(f"{i}. {step}")
        
        # Prevention tips
        st.markdown("---")
        st.markdown("### 🛡️ Prevention Tips")
        for tip in fault_info.get("prevention", []):
            st.markdown(f"- {tip}")
        
        # Cost estimate (if available)
        if "cost_estimate" in fault_info:
            st.markdown("---")
            st.markdown(f"### 💰 Estimated Repair Cost: **{fault_info['cost_estimate']}**")
        
        # Show all probabilities in expander
        with st.expander("📊 View All Predictions"):
            st.markdown("**Prediction probabilities:**")
            sorted_probs = sorted(
                result["probabilities"].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            for fault_name, prob in sorted_probs:
                st.progress(prob, text=f"{fault_name}: {prob*100:.1f}%")
        
        # Service Office Location Section
        st.markdown("---")
        st.markdown("### 📍 Find Nearest Service Office")
        
        col_pin1, col_pin2 = st.columns([2, 1])
        with col_pin1:
            user_pincode = st.text_input(
                "Enter your Pincode/Zip Code",
                placeholder="e.g., 110001, 400001",
                help="Enter the pincode where your solar panel is located"
            )
        
        with col_pin2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            find_office_btn = st.button("🔍 Find Office", type="primary", use_container_width=True)
        
        if find_office_btn or (user_pincode and len(user_pincode) >= 4):
            if user_pincode:
                office = find_nearest_office(user_pincode)
                
                if office:
                    st.markdown("---")
                    st.markdown("### 🏢 Nearest Service Office")
                    
                    # Display office information
                    st.markdown(format_contact_info(office))
                    
                    # Generate fault report
                    if fault_type != "Healthy Panel":
                        st.markdown("---")
                        st.markdown("### 📧 Send Fault Report to Office")
                        
                        # User details form
                        with st.form("fault_report_form"):
                            st.markdown("**Fill in your details to send the fault report:**")
                            
                            col_form1, col_form2 = st.columns(2)
                            with col_form1:
                                user_name = st.text_input("Your Name *", placeholder="John Doe")
                                user_phone = st.text_input("Phone Number *", placeholder="+91-XXXXXXXXXX")
                            with col_form2:
                                user_email = st.text_input("Email Address *", placeholder="your.email@example.com")
                                panel_location = st.text_input("Panel Location", placeholder="Address where panel is installed")
                            
                            additional_notes = st.text_area(
                                "Additional Notes (Optional)",
                                placeholder="Any additional information about the fault...",
                                height=100
                            )
                            
                            submitted = st.form_submit_button("📤 Send Report to Office", type="primary", use_container_width=True)
                            
                            if submitted:
                                if user_name and user_phone and user_email:
                                    # Generate report
                                    report = {
                                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "user_details": {
                                            "name": user_name,
                                            "phone": user_phone,
                                            "email": user_email,
                                            "pincode": user_pincode,
                                            "panel_location": panel_location
                                        },
                                        "fault_detection": {
                                            "fault_type": fault_type,
                                            "confidence": f"{confidence*100:.1f}%",
                                            "severity": fault_info.get("severity", "Unknown"),
                                            "description": fault_info.get("description", "")
                                        },
                                        "office_details": {
                                            "office_name": office["office_name"],
                                            "email": office["email"],
                                            "phone": office["phone"],
                                            "address": office["address"]
                                        },
                                        "additional_notes": additional_notes
                                    }
                                    
                                    # Display success message with contact options
                                    st.success("✅ Report Generated Successfully!")
                                    
                                    # Show report summary
                                    with st.expander("📄 View Generated Report"):
                                        st.json(report)
                                    
                                    # Generate report text
                                    report_text = f"""FAULT DETECTION REPORT
======================

Date: {report['timestamp']}
User: {user_name}
Phone: {user_phone}
Email: {user_email}
Pincode: {user_pincode}
Location: {panel_location}

FAULT DETECTED:
- Type: {fault_type}
- Confidence: {confidence*100:.1f}%
- Severity: {fault_info.get('severity', 'Unknown')}
- Description: {fault_info.get('description', '')}

SERVICE OFFICE:
- Name: {office['office_name']}
- Address: {office['address']}
- Phone: {office['phone']}
- Email: {office['email']}

Additional Notes: {additional_notes}
"""
                                    
                                    # Contact options
                                    st.markdown("### 📞 Contact Office")
                                    col_contact1, col_contact2, col_contact3 = st.columns(3)
                                    
                                    with col_contact1:
                                        st.markdown(f"**📧 Email Office**")
                                        email_subject = quote(f"Fault Report - {fault_type}")
                                        email_body = quote(f"""Dear {office['office_name']},

I am reporting a solar panel fault detected through the fault detection system.

FAULT DETAILS:
- Type: {fault_type}
- Confidence: {confidence*100:.1f}%
- Severity: {fault_info.get('severity', 'Unknown')}

MY DETAILS:
- Name: {user_name}
- Phone: {user_phone}
- Email: {user_email}
- Pincode: {user_pincode}
- Panel Location: {panel_location}

Additional Notes: {additional_notes}

Please contact me to schedule a service visit.

Thank you.""")
                                        email_link = f"mailto:{office['email']}?subject={email_subject}&body={email_body}"
                                        st.markdown(f"[📧 {office['email']}]({email_link})")
                                    
                                    with col_contact2:
                                        st.markdown(f"**📞 Call Office**")
                                        phone_clean = office['phone'].replace('-', '').replace('+', '').replace(' ', '')
                                        st.markdown(f"[📞 {office['phone']}](tel:{phone_clean})")
                                    
                                    with col_contact3:
                                        st.markdown(f"**📋 Office Address**")
                                        st.markdown(f"{office['address']}")
                                        st.markdown(f"**Working Hours:** {office['working_hours']}")
                                    
                                    # Display report text
                                    st.markdown("---")
                                    st.markdown("### 📄 Report Summary")
                                    st.code(report_text, language="text")
                                    
                                    # Store in session state for download
                                    st.session_state['fault_report'] = report
                                    st.session_state['report_text'] = report_text
                                else:
                                    st.error("Please fill in all required fields (marked with *)")
                else:
                    st.warning("No service office found for this pincode. Please contact our main office.")
            else:
                st.info("Please enter a pincode to find the nearest service office.")
    else:
        st.info("👆 Please upload an EL image to begin analysis.")
