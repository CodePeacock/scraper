import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split


# Load the car price dataset and cache it
@st.cache_data(show_spinner=True)
def load_data():
    ds = pd.read_csv("car_dataset_.csv", encoding="utf-8")
    ds["Price"] = ds["Price"].str.replace(",", "").astype(float)
    return ds


data = load_data()


# Split the dataset into training and test sets and cache it
@st.cache_data(show_spinner=True)
def preprocess_data(ds):
    X = pd.get_dummies(
        ds[["Model", "Year", "Fuel_Type", "Engine_Size"]],
        columns=["Model", "Fuel_Type"],
    )
    y = ds["Price"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42
    )
    return X_train, X_test, y_train, y_test


X_train, X_test, y_train, y_test = preprocess_data(data)


# Load or train the Random Forest Regressor model and cache it
@st.cache_resource(show_spinner=True)
def train_model(X_train, y_train):
    model = RandomForestRegressor(n_estimators=100, n_jobs=-1)
    model.fit(X_train, y_train)
    return model


model = train_model(X_train, y_train)

# Create a Streamlit app for making predictions on new data
st.title("Car Price Prediction App")

# Add a sidebar to select the car features
sidebar = st.sidebar
car_model = sidebar.selectbox("Car Model", data["Model"].unique())
year = sidebar.slider("Year", 2011, 2023)
fuel_type = sidebar.selectbox("Fuel Type", data["Fuel_Type"].unique())
engine_size = sidebar.number_input(
    "Engine Capacity", 1, 6, step=1, value=1, format="%d"
)
if calculate_button := st.button("Calculate Price"):
    # Prepare input for prediction using one-hot encoding
    with st.spinner("Calculating..."):
        input_data = pd.DataFrame(
            {
                "Year": [year],
                "Engine_Size": [engine_size],
                "Model_" + car_model: [1],
                "Fuel_Type_" + fuel_type: [1],
            }
        )

        # Ensure that the input_data DataFrame has the same one-hot encoded columns as the model was trained on
        # You can use reindex to align columns
        input_data = input_data.reindex(columns=X_train.columns, fill_value=0)

        prediction = model.predict(input_data)

        # Convert the predicted price from dollars to Indian rupees
        indian_rupee_prediction = prediction[0]

        # Display the prediction to the user
        st.markdown(
            "Predicted car price in Indian rupees: **₹{:.2f}**".format(
                indian_rupee_prediction
            )
        )
