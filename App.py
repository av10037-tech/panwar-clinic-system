import sqlite3
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import urllib.parse

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
        days_supply INTEGER,
        next_visit_date TEXT,
        total_amount REAL,
        bill_date TEXT
    )
''')
conn.commit()

# Safe migration for bills table if columns are missing
for col_def in [("days_supply", "INTEGER"), ("next_visit_date", "TEXT")]:
    try:
        cursor.execute(f"ALTER TABLE bills ADD COLUMN {col_def[0]} {col_def[1]}")
        conn.commit()
    except sqlite3.OperationalError:
        pass

st.set_page_config(page_title="Panwar Homoeopathic Clinic & Pharmacy", page_icon="🌿", layout="wide")

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'nav_page' not in st.session_state:
    st.session_state.nav_page = "Dashboard"

# ----------------- GLOBAL MEDICAL THEME BACKGROUND -----------------
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, rgba(240, 247, 244, 0.92) 0%, rgba(232, 245, 233, 0.92) 100%), 
                          url('https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?q=80&w=1920&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- AUTHENTICATION SYSTEM -----------------
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #1b5e20;'>🌿 Panwar Homoeopathic Clinic & Pharmacy</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #2e7d32;'>Advanced Digital Management & Prescription Portal</h4>", unsafe_allow_html=True)
    
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
    if st.sidebar.button("🌿 Add Patient & Quick Check", use_container_width=True):
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

    # 2. ADD NEW PATIENT & QUICK CHECK OPTION JUST BELOW IT
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

        st.markdown("---")
        st.markdown("### 🔍 Quick Patient Record Check (Instant Lookup)")
        quick_query = st.text_input("Enter Patient Name or Mobile Number to Check History instantly")
        if quick_query:
            cursor.execute("SELECT id, name, age, gender, phone, address, treatment_history, complaints, thermal, modalities, created_at FROM patients WHERE name LIKE ? OR phone LIKE ?", (f"%{quick_query}%", f"%{quick_query}%"))
            q_patients = cursor.fetchall()
            if q_patients:
                for q_row in q_patients:
                    qp_id, qp_name, qp_age, qp_gender, qp_phone, qp_address, qp_hist, qp_comp, qp_therm, qp_mod, qp_date = q_row
                    with st.expander(f"👤 Found: {q_row[1]} | 📱 {q_row[4]} | Age: {q_row[2]}"):
                        st.write(f"**Address:** {qp_address}")
                        st.write(f"**Treatment History:** {qp_hist}")
                        st.write(f"**Chief Complaints:** {qp_comp}")
                        st.write(f"**Thermal / Modalities:** {qp_therm} | {qp_mod}")
                        st.markdown("#### 💊 Prescriptions & Days Supply History:")
                        cursor.execute("SELECT bill_date, medicines, days_supply, next_visit_date, total_amount FROM bills WHERE patient_name = ?", (qp_name,))
                        q_bills = cursor.fetchall()
                        if q_bills:
                            for qb in q_bills:
                                st.success(f"**Date:** {qb[0]} | **Medicines:** {qb[1]} | **Given for:** {qb[2]} Days | **Next Visit:** {qb[3]} | **Paid:** ₹{qb[4]}")
                        else:
                            st.info("No prescription bills found for this patient.")
            else:
                st.warning("No patient found matching this name or mobile number.")

    # 3. BILLING WITH MULTIPLE MEDICINES & NO AMOUNT IN WHATSAPP
    elif page == "Billing":
        st.markdown("### 📋 Quick Billing & Prescription Counter")
        cursor.execute("SELECT name, phone FROM patients")
        patients_list = cursor.fetchall()
        patient_options = [f"{p[0]} ({p[1]})" for p in patients_list] if patients_list else ["No Patients Found"]
        
        selected_pat = st.selectbox("Select Registered Patient", patient_options)
        
        cursor.execute("SELECT medicine_name FROM inventory")
        inv_meds = [row[0] for row in cursor.fetchall()]
        if not inv_meds:
            inv_meds = ["Arsenic Alb 30", "Nux Vomica 200", "Paracetamol 650"]

        # Days supply and next visit date selection
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            days_supply = st.number_input("Medicine given for how many days? (Days Supply)", min_value=1, value=10)
        with col_d2:
            default_next_visit = datetime.now() + timedelta(days=int(days_supply))
            next_visit_date = st.date_input("Next Visit Date", value=default_next_visit)

        st.markdown("### 💊 Add Multiple Medicines with Quantity (Drum/Strip Option)")
        
        if 'bill_items' not in st.session_state:
            st.session_state.bill_items = []

        with st.form("add_med_form"):
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                add_med = st.selectbox("Select Medicine", inv_meds)
            with col_m2:
                add_qty = st.number_input("Quantity / Units", min_value=1, value=1)
            with col_m3:
                add_price = st.number_input("Unit Price (₹)", min_value=0.0, value=50.0)
            
            add_btn = st.form_submit_button("➕ Add Medicine to List")
            if add_btn:
                st.session_state.bill_items.append({"med": add_med, "qty": add_qty, "price": add_price, "sub": add_qty * add_price})

        # Display current added items list
        if st.session_state.bill_items:
            st.markdown("#### 📝 Current Added Medicines List:")
            item_df = pd.DataFrame(st.session_state.bill_items)
            st.dataframe(item_df, use_container_width=True)
            
            total_amount = sum([item["sub"] for item in st.session_state.bill_items])
            st.markdown(f"### Total Amount: ₹ {total_amount:.2f}")

            if st.button("🗑️ Clear Medicine List"):
                st.session_state.bill_items = []
                st.rerun()

            if st.button("Save Bill & Generate WhatsApp Message Link"):
                if selected_pat != "No Patients Found":
                    p_name_ext = selected_pat.split(" (")[0]
                    p_phone_ext = selected_pat.split(" (")[1].replace(")", "")
                    med_str = " | ".join([f"{it['med']} (Qty: {it['qty']})" for it in st.session_state.bill_items])
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    formatted_next_visit = next_visit_date.strftime("%Y-%m-%d")
                    
                    cursor.execute('''
                        INSERT INTO bills (patient_name, phone, medicines, days_supply, next_visit_date, total_amount, bill_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (p_name_ext, p_phone_ext, med_str, days_supply, formatted_next_visit, total_amount, now))
                    conn.commit()
                    st.success("Bill saved successfully!")
                    
                    # WhatsApp message without amount, featuring next visit date
                    wa_msg = f"Hello {p_name_ext}, Thanks for visiting Panwar Homoeopathic Clinic. Your next visit date is {formatted_next_visit}. Get well soon!"
                    wa_url = f"https://wa.me/91{p_phone_ext}?text={urllib.parse.quote(wa_msg)}"
                    st.markdown(f"📲 [Click here to send WhatsApp message to Patient]({wa_url})", unsafe_allow_html=True)
                    
                    st.markdown("---")
                    st.markdown(f"### 🧾 Panwar Homoeopathic Clinic Invoice")
                    st.write(f"**Patient Name:** {p_name_ext}")
                    st.write(f"**Date:** {now}")
                    st.write(f"**Medicines Given for:** {days_supply} Days")
                    st.write(f"**Next Visit Date:** {formatted_next_visit}")
                    st.write(f"**Medicines:** {med_str}")
                    st.write(f"**Total Payable:** ₹ {total_amount:.2f}")
                    st.info("💡 Tip: You can press Ctrl+P in your browser to print this bill as PDF!")
                    
                    # Clear session items after save
                    st.session_state.bill_items = []
                else:
                    st.error("Please select a valid patient.")
        else:
            st.info("No medicines added yet. Use the form above to add items.")

    # 4. AMEND / EDIT BILLS
    elif page == "Amend Bills":
        st.markdown("### ✏️ Amend / Edit Existing Bills")
        cursor.execute("SELECT id, patient_name, total_amount, bill_date FROM bills ORDER BY id DESC LIMIT 20")
        bills_data = cursor.fetchall()
        
        if bills_data:
            bill_opts = [f"Bill ID: {b[0]} | Patient: {b[1]} | Amount: ₹{b[2]} | Date: {b[3]}" for b in bills_data]
            selected_b = st.selectbox("Select Bill to Edit", bill_opts)
            b_id = int(selected_b.split(" | ")[0].replace("Bill ID: ", ""))
            
            cursor.execute("SELECT patient_name, phone, medicines, days_supply, next_visit_date, total_amount FROM bills WHERE id = ?", (b_id,))
            b_info = cursor.fetchone()
            
            with st.form("amend_form"):
                new_p_name = st.text_input("Patient Name", value=b_info[0])
                new_phone = st.text_input("Phone", value=b_info[1])
                new_meds = st.text_area("Medicines Details", value=b_info[2])
                new_days = st.number_input("Days Supply", value=b_info[3] if b_info[3] else 10)
                new_amt = st.number_input("Total Amount", value=b_info[5])
                
                if st.form_submit_button("Update / Amend Bill"):
                    cursor.execute("UPDATE bills SET patient_name=?, phone=?, medicines=?, days_supply=?, total_amount=? WHERE id=?", 
                                   (new_p_name, new_phone, new_meds, new_days, new_amt, b_id))
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
            cursor.execute("SELECT id, name, age, gender, phone, address, treatment_history, complaints, thermal, modalities, created_at FROM patients WHERE name LIKE ? OR phone LIKE ?", (f"%{search_q}%", f"%{search_q}%"))
        else:
            cursor.execute("SELECT id, name, age, gender, phone, address, treatment_history, complaints, thermal, modalities, created_at FROM patients ORDER BY id DESC")
        patients = cursor.fetchall()
        
        if patients:
            for row in patients:
                p_id = row[0]
                p_name = row[1] if len(row) > 1 and row[1] else "N/A"
                p_age = row[2] if len(row) > 2 and row[2] else "N/A"
                p_gender = row[3] if len(row) > 3 and row[3] else "N/A"
                p_phone = row[4] if len(row) > 4 and row[4] else "N/A"
                p_address = row[5] if len(row) > 5 and row[5] else "N/A"
                p_hist = row[6] if len(row) > 6 and row[6] else "N/A"
                p_comp = row[7] if len(row) > 7 and row[7] else "N/A"
                p_therm = row[8] if len(row) > 8 and row[8] else "N/A"
                p_mod = row[9] if len(row) > 9 and row[9] else "N/A"
                p_date = row[10] if len(row) > 10 and row[10] else "N/A"

                with st.expander(f"👤 {p_name} | 📱 {p_phone} | Age: {p_age} | Added: {p_date}"):
                    st.write(f"**Address:** {p_address}")
                    st.write(f"**Previous Treatment History:** {p_hist}")
                    st.write(f"**Chief Complaints:** {p_comp}")
                    st.write(f"**Thermal Reaction:** {p_therm}")
                    st.write(f"**Modalities:** {p_mod}")
                    st.markdown("---")
                    st.markdown("#### 💊 Previous Bills, Days Supply & Prescriptions:")
                    cursor.execute("SELECT bill_date, medicines, days_supply, next_visit_date, total_amount FROM bills WHERE patient_name = ?", (p_name,))
                    bills = cursor.fetchall()
                    if bills:
                        for idx, b in enumerate(bills, 1):
                            st.success(f"**Visit {idx} ({b[0]}):** {b[1]} | **Given for:** {b[2]} Days | **Next Visit:** {b[3]} — **Paid: ₹{b[4]}**")
                    else:
                        st.info("No past bills found.")
        else:
            st.info("No patient records found.")