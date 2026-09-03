import streamlit as st
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Sadza2Go Storefront", page_icon="🍔", layout="centered")

st.html(
    """
    <style>
        .stApp {
            background-color: #121212 !important;
            color: #FFFFFF !important;
        }
        h1, h2, h3, .stSubheader {
            color: #FF6B00 !important;
            font-family: 'Arial Rounded MT Bold', sans-serif !important;
        }
        div[data-testid="stMetricValue"] {
            color: #FF6B00 !important;
            font-size: 2rem !important;
            font-weight: bold !important;
        }
        div[data-testid="stMetricLabel"] {
            color: #AAAAAA !important;
        }
        .stButton > button {
            background-color: #FF6B00 !important;
            color: white !important;
            border-radius: 20px !important;
            border: none !important;
            padding: 0.5rem 2rem !important;
            font-weight: bold !important;
            font-size: 1.1rem !important;
            width: 100% !important;
            box-shadow: 0px 4px 10px rgba(255, 107, 0, 0.3) !important;
        }
        .stButton > button:hover {
            background-color: #E05E00 !important;
            color: white !important;
        }
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #FF6B00 !important;
        }
        .stSelectbox, .stNumberInput, .stTextArea, div[role="radiogroup"] {
            background-color: #1E1E1E !important;
            border-radius: 10px !important;
            color: white !important;
        }
    </style>
    """
)

st.title("Sadza2Go 🍔")
st.subheader("Authentic Flavors, Delivered Inclusively")
st.write("---")

@st.cache_resource
def get_db_engine():
    clean_url = st.secrets["DATABASE_URL"]
    if clean_url.startswith("postgresql://"):
        clean_url = clean_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return create_engine(clean_url, pool_size=10, max_overflow=20, pool_recycle=1800)

try:
    engine = get_db_engine()
except Exception as e:
    st.error(f"Database layer connection failed: {e}")
    st.stop()

st.markdown("### Today's Currency Exchange Rate")
zig_rate = st.number_input("Current USD to ZiG Market Rate:", value=25.00, step=0.10)
st.write("---")

st.markdown("### Browse Our Fresh Local Menu")

menu_items = {
    "Sadza with Flame-Grilled T-Bone Beef": {"price_usd": 6.50, "emoji": "🥩"},
    "Traditional Pod Pod Chicken Stew": {"price_usd": 5.50, "emoji": "🍗"},
    "Fresh Tilapia Bream with Greens": {"price_usd": 7.00, "emoji": "🐟"},
    "Chilled Mazoe Orange Juice Jug": {"price_usd": 2.50, "emoji": "🍹"}
}

col1, col2 = st.columns(2)
with col1:
    selected_dish = st.selectbox("Select Dish:", list(menu_items.keys()))
with col2:
    quantity = st.number_input("Quantity:", min_value=1, max_value=10, value=1, step=1)

item_meta = menu_items[selected_dish]
items_subtotal_usd = item_meta["price_usd"] * quantity

st.write("---")
st.markdown("###  Delivery & Accessibility Configuration")

suburb_options = {
    "Avondale": {"id": 1, "is_low_density": True},
    "Borrowdale": {"id": 3, "is_low_density": True},
    "Mbare": {"id": 4, "is_low_density": False},
    "Chitungwiza": {"id": 2, "is_low_density": False}
}

selected_suburb = st.selectbox("Choose Destination Suburb:", list(suburb_options.keys()))
suburb_meta = suburb_options[selected_suburb]

delivery_mode = st.radio("Select Delivery Mode:", ["Solo Delivery", "Pooled Delivery (Share routes to save cash)"])

needs_assistance = st.checkbox("♿ I require driver assistance upon arrival")
driver_notes = st.text_area("Provide special driver instructions:") if needs_assistance else "Standard drop-off."

base_delivery_usd = 3.00 if suburb_meta["is_low_density"] else 6.00
if delivery_mode == "Pooled Delivery (Share routes to save cash)":
    base_delivery_usd *= 0.4

final_total_usd = items_subtotal_usd + base_delivery_usd
final_total_zig = final_total_usd * zig_rate

st.write("---")
st.markdown("### Your Order Receipt Summary")

summary_col1, summary_col2 = st.columns(2)
with summary_col1:
    st.markdown(f"**Item ordered:** {item_meta['emoji']} {selected_dish} (x{quantity})")
    st.markdown(f"**Delivery Destination:** {selected_suburb} ({delivery_mode})")
with summary_col2:
    st.metric(label="Total Balance (USD)", value=f"${final_total_usd:,.2f}")
    st.metric(label="Total Balance (ZiG)", value=f"{final_total_zig:,.2f} ZiG")

st.write("---")
if st.button("Order"):
    try:
        with engine.begin() as connection:
            insert_query = text(
                """
                INSERT INTO delivery_orders 
                (suburb_id, order_text_raw, total_usd, delivery_mode, accessibility_notes) 
                VALUES 
                (:suburb_id, :order_text_raw, :total_usd, :delivery_mode, :accessibility_notes);
                """
            )
            connection.execute(
                insert_query,
                {
                    "suburb_id": int(suburb_meta["id"]),
                    "order_text_raw": str(f"Ordered {quantity}x {selected_dish}"),
                    "total_usd": float(final_total_usd),
                    "delivery_mode": str(delivery_mode),
                    "accessibility_notes": str(driver_notes)
                }
            )
        st.success(f"Excellent choice! Your kitchen order has been pushed to the grid to {selected_suburb}.")
        st.balloons()
    except Exception as e:
        st.error(f"Database Error details: {e}")
