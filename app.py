import streamlit as st
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Poto to Plate Delivery", page_icon="🇿🇼", layout="centered")

st.title("🇿🇼 Poto to Plate Delivery")
st.subheader("Enterprise-Grade Inclusive Logistics System")
st.write("---")

@st.cache_resource
def get_db_engine():
    db_url = st.secrets["SUPABASE_URL"]
    clean_url = db_url.replace("https://", "postgresql://").split(".co")[0] + ".co:5432/postgres"
    return create_engine(
        clean_url,
        pool_size=10,
        max_overflow=20,
        pool_recycle=1800
    )

try:
    engine = get_db_engine()
except Exception as e:
    st.error("Database connection initialization failed.")
    st.stop()

st.markdown("### 🪙 Today's Currency Exchange Rate")
zig_rate = st.number_input("Current USD to ZiG Market Rate:", value=25.00, step=0.10)

st.markdown("### 📦 Place an Inclusive Delivery Order")

suburb_options = {
    "Avondale": {"id": 1, "is_low_density": True},
    "Borrowdale": {"id": 3, "is_low_density": True},
    "Mbare": {"id": 4, "is_low_density": False},
    "Chitungwiza": {"id": 2, "is_low_density": False}
}

selected_suburb_name = st.selectbox("Choose Destination Suburb:", list(suburb_options.keys()))
suburb_meta = suburb_options[selected_suburb_name]

needs_assistance = st.checkbox("♿ I require driver assistance upon arrival (Visual/Hearing/Motor disability)")
driver_notes = st.text_area("Provide special driver instructions:") if needs_assistance else "Standard drop-off."

delivery_mode = st.radio("Select Delivery Pricing Option:", ["Solo Delivery", "Pooled Delivery"])

base_usd = 12.00
delivery_usd = 3.00 if suburb_meta["is_low_density"] else 6.00

if delivery_mode == "Pooled Delivery":
    delivery_usd *= 0.4

total_usd = base_usd + delivery_usd
total_zig = total_usd * zig_rate

col1, col2 = st.columns(2)
with col1:
    st.metric(label="Total Price (USD)", value=f"${total_usd:,.2f}")
with col2:
    st.metric(label="Total Price (ZiG)", value=f"{total_zig:,.2f} ZiG")

if st.button(" Process & Route Order"):
    try:
        with engine.begin() as connection:
            insert_query = text(
                "INSERT INTO delivery_orders "
                "(suburb_id, order_text_raw, total_usd, delivery_mode, accessibility_notes) "
                "VALUES (:suburb_id, :order_text, :total_usd, :delivery_mode, :driver_notes);"
            )
            connection.execute(
                insert_query,
                {
                    "suburb_id": suburb_meta["id"],
                    "order_text": f"Web Order for {selected_suburb_name}",
                    "total_usd": total_usd,
                    "delivery_mode": delivery_mode,
                    "driver_notes": driver_notes
                }
            )
        st.success("Order processed and securely logged in Supabase!")
        st.balloons()
    except Exception as error:
        st.error(f"Transaction aborted due to runtime error: {str(error)}")
