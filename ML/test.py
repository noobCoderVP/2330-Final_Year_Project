import joblib
import numpy as np
import pandas as pd

model = joblib.load("model.joblib")
le_proto = joblib.load("dummy_columns.joblib")
le_label = joblib.load("label.joblib")
sc = joblib.load("scaler.joblib")

t = pd.DataFrame({
    'duration': [0],
    'protocol_type': ['tcp'],
    'service': ['private'],
    'src_bytes': [0],
    'dst_bytes': [0],
    'count': [136],
    'srv_count': [1]
})

# t = np.array([t])
dummy_columns = joblib.load('dummy_columns.joblib')
print(dummy_columns)
new_data_encoded = pd.get_dummies(t)

# Reindex to match the training dummy columns
new_data_encoded = new_data_encoded.reindex(columns=dummy_columns, fill_value=0)
print(new_data_encoded)

new_data_encoded = new_data_encoded.drop(columns=['attack'])
# t[:, 0] = le_proto.transform(t[:, 0])
t = sc.transform(new_data_encoded)

pred = model.predict(t)
original_label = le_label.inverse_transform(pred)[0]
print(original_label)
# print(t)