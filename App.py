from datetime import datetime
import sqlite3
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Panwar Homoeopathic Clinic", page_icon="💊", layout="wide"
)

# --- CUSTOM CSS & HOMOEOPATHIC WATERMARK / REFLECTION BACKGROUND ---
st.markdown(
    """
    <style>
    /* Professional Homoeopathic Watermark / Background Reflection */
    .stApp {
        background: linear-gradient(rgba(240, 248, 255, 0.90), rgba(220, 235, 252, 0.90)), 
                    url('https://images.unsplash.com/photo-1471864190281-a93a3070b6de?q=80&w=1920&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    /* Smooth Fade-in Animation for Welcome Screen */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animated-welcome {
        animation: fadeIn 1.5s ease-in-out;
        text-align: center;
        padding: 30px;
        background: rgba(255, 255, 255, 0.92);
        border-radius: 15px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
        margin-bottom: 25px;
        border: 1px solid rgba(255, 255, 255, 0.5);
    }
    
    .animated-welcome h1 {
        color: #1b4332;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
    }
    
    .animated-welcome p {
        color: #2d6a4f;
        font-size: 18px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- DATABASE SETUP ---
DB_NAME = "clinic_data.db"


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
  cursor.execute("SELECT * FROM users WHERE username = ?", ("admin",))
  if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        ("admin", "panwar123"),
    )

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age TEXT,
            gender TEXT,
            phone TEXT,
            address TEXT,
            visit_date TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_name TEXT,
            category TEXT,
            stock_qty INTEGER,
            price REAL
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            phone TEXT,
            medicines TEXT,
            total_amount REAL,
            bill_date TEXT
        )
    """)
  conn.commit()
  conn.close()


init_db()


# --- LOGIN & AUTHENTICATION MODULE ---
def check_password():
  if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

  if not st.session_state["password_correct"]:
    # Animated Welcome Banner on Login Screen
    st.markdown(
        """
        <div class="animated-welcome">
            <h1>🌿 Welcome to Panwar Homoeopathic Clinic & Pharmacy 🌿</h1>
            <p>Advanced Digital Management & Prescription Portal</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
      st.markdown(
          "<h3 style='text-align: center; color: #1b4332;'>🔒 Secure Login Portal</h3>",
          unsafe_allow_html=True,
      )
      tab1, tab2, tab3 = st.tabs(
          ["Login", "Register New User", "Forgot Password"]
      )

      with tab1:
        l_user = st.text_input("Username", key="login_user")
        l_pass = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login", use_container_width=True):
          conn = sqlite3.connect(DB_NAME)
          cursor = conn.cursor()
          cursor.execute(
              "SELECT * FROM users WHERE username = ? AND password = ?",
              (l_user, l_pass),
          )
          user = cursor.fetchone()
          conn.close()

          if user:
            st.session_state["password_correct"] = True
            st.rerun()
          else:
            st.error("Invalid User ID or Password")

      with tab2:
        n_user = st.text_input("New Username", key="new_user")
        n_pass = st.text_input("New Password", type="password", key="new_pass")

        if st.button("Register User", use_container_width=True):
          if n_user.strip() == "" or n_pass.strip() == "":
            st.warning("Please fill in all fields.")
          else:
            try:
              conn = sqlite3.connect(DB_NAME)
              cursor = conn.cursor()
              cursor.execute(
                  "INSERT INTO users (username, password) VALUES (?, ?)",
                  (n_user, n_pass),
              )
              conn.commit()
              conn.close()
              st.success(
                  "New user registered successfully! Please go to Login tab."
              )
            except sqlite3.IntegrityError:
              st.error("Username already exists. Choose a different one.")

      with tab3:
        f_user = st.text_input("Enter Username", key="forgot_user")
        f_pass = st.text_input(
            "Enter New Password", type="password", key="forgot_pass"
        )

        if st.button("Update Password", use_container_width=True):
          conn = sqlite3.connect(DB_NAME)
          cursor = conn.cursor()
          cursor.execute("SELECT * FROM users WHERE username = ?", (f_user,))
          user = cursor.fetchone()
          if user:
            cursor.execute(
                "UPDATE users SET password = ? WHERE username = ?",
                (f_pass, f_user),
            )
            conn.commit()
            conn.close()
            st.success("Password updated successfully! You can login now.")
          else:
            conn.close()
            st.error("Username not found.")

    return False
  else:
    return True


if not check_password():
  st.stop()

# --- MAIN APP INTERFACE (AFTER SUCCESSFUL LOGIN) ---

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🏥 Panwar Clinic")
st.sidebar.markdown("---")
menu = ["Billing & Dispensing", "Patient Records", "Inventory Management"]
choice = st.sidebar.selectbox("Navigation Menu", menu)

# --- 1. BILLING & DISPENSING MODULE ---
if choice == "Billing & Dispensing":
  st.subheader("🧾 Quick Billing & Prescription Counter")

  col1, col2 = st.columns(2)
  with col1:
    patient_name = st.text_input("Patient Name")
    phone = st.text_input("Phone Number")
  with col2:
    age = st.text_input("Age")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])

  st.markdown("### Medicines & Potency")

  conn = sqlite3.connect(DB_NAME)
  inv_df = pd.read_sql("SELECT medicine_name, price FROM inventory", conn)
  conn.close()

  med_list = (
      inv_df["medicine_name"].tolist()
      if not inv_df.empty
      else ["Arsenic Alb 30", "Nux Vomica 200", "Sulphur 1M"]
  )

  num_items = st.number_input(
      "Number of items", min_value=1, max_value=10, value=1
  )

  selected_medicines = []
  total_bill = 0.0

  for i in range(int(num_items)):
    c1, c2, c3 = st.columns([3, 2, 2])
    with c1:
      med = st.selectbox(f"Medicine {i+1}", med_list, key=f"med_{i}")
    with c2:
      qty = st.number_input(
          f"Qty {i+1}", min_value=1, value=1, key=f"qty_{i}"
      )
    with c3:
      price = st.number_input(
          f"Price (₹) {i+1}", min_value=0.0, value=50.0, key=f"price_{i}"
      )

    item_total = qty * price
    total_bill += item_total
    selected_medicines.append(f"{med} (Qty: {qty}, ₹{item_total})")

  st.markdown(f"### **Total Amount: ₹ {total_bill:.2f}**")

  if st.button("Save & Generate Bill"):
    if patient_name.strip() == "":
      st.warning("Please enter the patient's name.")
    else:
      conn = sqlite3.connect(DB_NAME)
      cursor = conn.cursor()
      cursor.execute(
          """
                INSERT INTO bills (patient_name, phone, medicines, total_amount, bill_date)
                VALUES (?, ?, ?, ?, ?)
            """,
          (
              patient_name,
              phone,
              ", ".join(selected_medicines),
              total_bill,
              datetime.now().strftime("%Y-%m-%d %H:%M"),
          ),
      )
      conn.commit()
      conn.close()
      st.success(
          f"Bill successfully generated and saved for {patient_name}!"
      )

# --- 2. PATIENT RECORDS MODULE ---
elif choice == "Patient Records":
  st.subheader("👥 Patient Database & History")

  with st.form("patient_form"):
    st.markdown("#### Add New Patient Entry")
    p_name = st.text_input("Full Name")
    p_age = st.text_input("Age")
    p_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    p_phone = st.text_input("Phone")
    p_address = st.text_area("Address")

    submitted = st.form_submit_button("Save Patient Record")
    if submitted and p_name:
      conn = sqlite3.connect(DB_NAME)
      cursor = conn.cursor()
      cursor.execute(
          """
                INSERT INTO patients (name, age, gender, phone, address, visit_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
          (
              p_name,
              p_age,
              p_gender,
              p_phone,
              p_address,
              datetime.now().strftime("%Y-%m-%d"),
          ),
      )
      conn.commit()
      conn.close()
      st.success("Patient record saved successfully!")

  st.markdown("---")
  st.markdown("#### Existing Patients List")
  conn = sqlite3.connect(DB_NAME)
  patients_df = pd.read_sql("SELECT * FROM patients", conn)
  conn.close()
  if not patients_df.empty:
    st.dataframe(patients_df, use_container_width=True)
  else:
    st.info("No patient records found.")

# --- 3. INVENTORY MANAGEMENT MODULE ---
elif choice == "Inventory Management":
  st.subheader("📦 Medicine Stock & Inventory")

  with st.form("inv_form"):
    st.markdown("#### Add New Medicine to Stock")
    m_name = st.text_input("Medicine Name & Potency")
    m_cat = st.text_input(
        "Category (e.g., Mother Tincture, Dilution, Bio-chemic)"
    )
    m_qty = st.number_input("Stock Quantity", min_value=0, value=10)
    m_price = st.number_input("Unit Price (₹)", min_value=0.0, value=100.0)

    inv_submitted = st.form_submit_button("Add to Inventory")
    if inv_submitted and m_name:
      conn = sqlite3.connect(DB_NAME)
      cursor = conn.cursor()
      cursor.execute(
          """
                INSERT INTO inventory (medicine_name, category, stock_qty, price)
                VALUES (?, ?, ?, ?)
            """,
          (m_name, m_cat, m_qty, m_price),
      )
      conn.commit()
      conn.close()
      st.success(f"Added {m_name} to inventory!")

  st.markdown("---")
  st.markdown("#### Current Inventory Stock")
  conn = sqlite3.connect(DB_NAME)
  stock_df = pd.read_sql("SELECT * FROM inventory", conn)
  conn.close()
  if not stock_df.empty:
    st.dataframe(stock_df, use_container_width=True)
  else:
    st.info("Inventory is currently empty.")