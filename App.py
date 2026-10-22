import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# Database connection setup
conn = sqlite3.connect("clinic_data.db", check_same_thread=False)
cursor = conn.cursor()

# Tables creation with migrations
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age TEXT,
        gender TEXT,
        phone TEXT,
        address TEXT,
        treatment_history TEXT,
        complaints TEXT,
        thermal TEXT,
        modalities TEXT,
        created_at TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_name TEXT,
        med_type TEXT,
        stock_qty INTEGER,
        price REAL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT,
        phone TEXT,
        medicines TEXT,
        total_amount REAL,
        bill_date TEXT
    )
''')
conn.commit()

st.set_page_config(page_title="Panwar Homoeopathic Clinic & Pharmacy", page_icon="🌿", layout="wide")

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'nav_page' not in st.session_state:
    st.session_state.nav_page = "Dashboard"

# ----------------- AUTHENTICATION SYSTEM -----------------
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🌿 Panwar Homoeopathic Clinic & Pharmacy</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #555;'>Advanced Digital Management & Prescription Portal</h4>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Secure Login", "📝 Register New User"])
    
    with tab1:
        st.subheader("Login to Portal")
        l_user = st.text_input("Username", key="l_user")
        l_pass = st.text_input("Password", type="password", key="l_pass")
        if st.button("Login"):
            cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (l_user, l_pass))
            if cursor.fetchone():
                st.session_state.logged_in = True
                st.session_state.username = l_user
                st.rerun()
            else:
                st.error("Invalid username or password!")
                
    with tab2:
        st.subheader("Create New User Account")
        r_user = st.text_input("Choose Username", key="r_user")
        r_pass = st.text_input("Choose Password", type="password", key="r_pass")
        if st.button("Register"):
            if r_user and r_pass:
                try:
                    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (r_user, r_pass))
                    conn.commit()
                    st.success("Account created successfully! Please login.")
                except sqlite3.IntegrityError:
                    st.error("Username already exists!")
            else:
                st.warning("Please fill all fields.")

else:
    # ----------------- SIDEBAR PRO BUTTONS NAVIGATION -----------------
    st.sidebar.title("🌿 Panwar Clinic")
    st.sidebar.write(f"Welcome, **{st.session_state.username}**")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Navigation Menu")

    if st.sidebar.button("📊 Dashboard", use_container_width=True):
        st.session_state.nav_page = "Dashboard"
    if st.sidebar.button("🌿 Add New Patient", use_container_width=True):
        st.session_state.nav_page = "Add Patient"
    if st.sidebar.button("📋 Billing & WhatsApp Bill", use_container_width=True):
        st.session_state.nav_page = "Billing"
    if st.sidebar.button("✏️ Amend / Edit Bills", use_container_width=True):
        st.session_state.nav_page = "Amend Bills"
    if st.sidebar.button("📦 Medicine Inventory", use_container_width=True):
        st.session_state.nav_page = "Inventory"
    if st.sidebar.button("📂 Patient History", use_container_width=True):
        st.session_state.nav_page = "History"
        
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    page = st.session_state.nav_page

    # 1. DASHBOARD
    if page == "Dashboard":
        st.markdown("### 📊 Clinic Overview & Dashboard")
        cursor.execute("SELECT COUNT(*) FROM patients")
        total_patients = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM bills")
        total_bills = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(total_amount) FROM bills")
        total_revenue = cursor.fetchone()[0] or 0.0

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Patients", total_patients)
        c2.metric("Total Bills Issued", total_bills)
        c3.metric("Total Revenue (₹)", f"₹ {total_revenue:.2f}")

    # 2. ADD NEW PATIENT (CASE-TAKING)
    elif page == "Add Patient":
        st.markdown("### 🌿 Pro Homeopathic Patient Case-Taking & Registration")
        with st.form("patient_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                p_name = st.text_input("Full Name")
                p_age = st.text_input("Age / Sex")
            with col2:
                p_phone = st.text_input("Mobile Number")
                p_gender = st.selectbox("Gender", ["Male", "Female", "Transgender", "Child"])
            with col3:
                p_address = st.text_area("Complete Address", placeholder="Village / City, District")
            
            st.markdown("---")
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                treatment_history = st.text_area("Treatment History (Previous Treatment / Kahan se ilaaj chala)")
                chief_complaints = st.text_area("Chief Complaints (Kya takleef hai?)")
            with col_h2:
                thermal_reaction = st.selectbox("Thermal Reaction", ["Select", "Hot Patient", "Chilly Patient"])
                modalities = st.text_area("Modalities (Aggravation / Amelioration)")
            
            if st.form_submit_button("Save Patient Case"):
                if p_name and p_phone:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    cursor.execute('''
                        INSERT INTO patients (name, age, gender, phone, address, treatment_history, complaints, thermal, modalities, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (p_name, p_age, p_gender, p_phone, p_address, treatment_history, chief_complaints, thermal_reaction, modalities, now))
                    conn.commit()
                    st.success(f"Patient '{p_name}' successfully registered!")
                else:
                    st.error("Please enter Name and Mobile Number.")

    # 3. BILLING & WHATSAPP INTEGRATION & PDF PRINT
    elif page == "Billing":
        st.markdown("### 📋 Quick Billing & Prescription Counter")
        cursor.execute("SELECT name, phone FROM patients")
        patients_list = cursor.fetchall()
        patient_options = [f"{p[0]} ({p[1]})" for p in patients_list] if patients_list else ["No Patients Found"]
        
        selected_pat = st.selectbox("Select Registered Patient", patient_options)
        
        # Fetch inventory for medicine dropdowns
        cursor.execute("SELECT medicine_name FROM inventory")
        inv_meds = [row[0] for row in cursor.fetchall()]
        if not inv_meds:
            inv_meds = ["Arsenic Alb 30", "Nux Vomica 200", "Paracetamol 650"]

        num_items = st.number_input("Number of items", min_value=1, max_value=10, value=1)
        med_summary = []
        total_amount = 0.0
        
        for i in range(int(num_items)):
            cols = st.columns(3)
            with cols[0]:
                med_name = st.selectbox(f"Medicine {i+1}", inv_meds, key=f"med_{i}")
            with cols[1]:
                qty = st.number_input(f"Qty {i+1}", min_value=1, value=1, key=f"qty_{i}")
            with cols[2]:
                price = st.number_input(f"Price (₹) {i+1}", min_value=0.0, value=50.0, key=f"price_{i}")
            sub = qty * price
            total_amount += sub
            med_summary.append(f"{med_name} (Qty: {qty}, ₹{sub})")
            
        st.markdown(f"### Total Amount: ₹ {total_amount:.2f}")
        
        if st.button("Save Bill & Generate WhatsApp Link"):
            if selected_pat != "No Patients Found":
                p_name_ext = selected_pat.split(" (")[0]
                p_phone_ext = selected_pat.split(" (")[1].replace(")", "")
                med_str = " | ".join(med_summary)
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                cursor.execute('''
                    INSERT INTO bills (patient_name, phone, medicines, total_amount, bill_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (p_name_ext, p_phone_ext, med_str, total_amount, now))
                conn.commit()
                st.success("Bill saved successfully!")
                
                # WhatsApp message link generator
                wa_msg = f"Hello {p_name_ext}, Thanks for visiting the Panwar Clinic. Your total bill amount is ₹{total_amount:.2f}. Get well soon!"
                wa_url = f"https://wa.me/91{p_phone_ext}?text={urllib.parse.quote(wa_msg)}" if 'urllib' else "#"
                
                import urllib.parse
                wa_url = f"https://wa.me/91{p_phone_ext}?text={urllib.parse.quote(wa_msg)}"
                st.markdown(f"📲 [Click here to send WhatsApp message to Patient]({wa_url})", unsafe_allow_html=True)
                
                # Printable Bill Invoice View / PDF option simulation
                st.markdown("---")
                st.markdown(f"### 🧾 Panwar Homoeopathic Clinic Invoice")
                st.write(f"**Patient Name:** {p_name_ext}")
                st.write(f"**Date:** {now}")
                st.write(f"**Medicines:** {med_str}")
                st.write(f"**Total Payable:** ₹ {total_amount:.2f}")
                st.info("💡 Tip: You can press Ctrl+P in your browser to print this bill as PDF!")
            else:
                st.error("Please select a valid patient.")

    # 4. AMEND / EDIT BILLS
    elif page == "Amend Bills":
        st.markdown("### ✏️ Amend / Edit Existing Bills")
        cursor.execute("SELECT id, patient_name, total_amount, bill_date FROM bills ORDER BY id DESC LIMIT 20")
        bills_data = cursor.fetchall()
        
        if bills_data:
            bill_opts = [f"Bill ID: {b[0]} | Patient: {b[1]} | Amount: ₹{b[2]} | Date: {b[3]}" for b in bills_data]
            selected_b = st.selectbox("Select Bill to Edit", bill_opts)
            b_id = int(selected_b.split(" | ")[0].replace("Bill ID: ", ""))
            
            cursor.execute("SELECT patient_name, phone, medicines, total_amount FROM bills WHERE id = ?", (b_id,))
            b_info = cursor.fetchone()
            
            with st.form("amend_form"):
                new_p_name = st.text_input("Patient Name", value=b_info[0])
                new_phone = st.text_input("Phone", value=b_info[1])
                new_meds = st.text_area("Medicines Details", value=b_info[2])
                new_amt = st.number_input("Total Amount", value=b_info[3])
                
                if st.form_submit_button("Update / Amend Bill"):
                    cursor.execute("UPDATE bills SET patient_name=?, phone=?, medicines=?, total_amount=? WHERE id=?", 
                                   (new_p_name, new_phone, new_meds, new_amt, b_id))
                    conn.commit()
                    st.success("Bill successfully amended!")
        else:
            st.info("No bills found to amend.")

    # 5. MEDICINE INVENTORY (Homeopathic & Other)
    elif page == "Inventory":
        st.markdown("### 📦 Clinic Medicine Inventory (Homeopathic & Other)")
        
        with st.form("inv_form"):
            st.markdown("#### Add New Medicine")
            m_name = st.text_input("Medicine Name & Potency")
            m_type = st.selectbox("Medicine Type", ["Homeopathic", "Other Medicine (Allopathy/Supplements)"])
            m_qty = st.number_input("Stock Quantity", min_value=0, value=10)
            m_price = st.number_input("Unit Price (₹)", min_value=0.0, value=100.0)
            
            if st.form_submit_button("Add to Inventory"):
                if m_name:
                    cursor.execute("INSERT INTO inventory (medicine_name, med_type, stock_qty, price) VALUES (?, ?, ?, ?)",
                                   (m_name, m_type, m_qty, m_price))
                    conn.commit()
                    st.success(f"Added {m_name} ({m_type}) to inventory!")
                else:
                    st.error("Enter medicine name.")
                    
        st.markdown("---")
        st.markdown("#### Current Inventory Records")
        inv_df = pd.read_sql("SELECT * FROM inventory", conn)
        if not inv_df.empty:
            st.dataframe(inv_df, use_container_width=True)
        else:
            st.info("Inventory is empty.")

    # 6. PATIENT HISTORY & TRACKING
    elif page == "History":
        st.markdown("### 📂 Patient Medical History & Tracking")
        search_q = st.text_input("🔍 Search Patient by Name or Mobile")
        if search_q:
            cursor.execute("SELECT * FROM patients WHERE name LIKE ? OR phone LIKE ?", (f"%{search_q}%", f"%{search_q}%"))
        else:
            cursor.execute("SELECT * FROM patients ORDER BY id DESC")
        patients = cursor.fetchall()
        
        if patients:
            for row in patients:
                p_id, p_name, p_age, p_gender, p_phone, p_address, p_hist, p_comp, p_therm, p_mod, p_date = row
                with st.expander(f"👤 {p_name} | 📱 {p_phone} | Age: {p_age} | Added: {p_date}"):
                    st.write(f"**Address:** {p_address}")
                    st.write(f"**Previous Treatment History:** {p_hist}")
                    st.write(f"**Chief Complaints:** {p_comp}")
                    st.write(f"**Thermal Reaction:** {p_therm}")
                    st.write(f"**Modalities:** {p_mod}")
                    st.markdown("---")
                    st.markdown("#### 💊 Previous Bills & Prescriptions Given:")
                    cursor.execute("SELECT bill_date, medicines, total_amount FROM bills WHERE patient_name = ?", (p_name,))
                    bills = cursor.fetchall()
                    if bills:
                        for idx, b in enumerate(bills, 1):
                            st.success(f"**Visit {idx} ({b[0]}):** {b[1]} — **Paid: ₹ {b[2]}**")
                    else:
                        st.info("No past bills found.")
        else:
            st.info("No patient records found.")