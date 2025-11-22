import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression

np.random.seed(1)

n = 1000
df = pd.DataFrame({
    'age': np.random.normal(35, 10, n),
    'tenure_months': np.random.exponential(10, n),
    'web_visits_last_week': np.random.poisson(3, n),
})

# Simulate non-random treatment assignment
df['treatment'] = ((df['web_visits_last_week'] > 2) & (df['tenure_months'] > 5)).astype(int)

# Simulate outcome: spend in next week
df['spend'] = 20 + 5 * df['treatment'] + np.random.normal(0, 5, n)


df.head()

X = df[['age', 'tenure_months', 'web_visits_last_week']]
y = df['treatment']

model = LogisticRegression()
df['propensity_score'] = model.fit(X, y).predict_proba(X)[:,1]



from sklearn.neighbors import NearestNeighbors

treated = df[df['treatment'] == 1]
control = df[df['treatment'] == 0]

nn = NearestNeighbors(n_neighbors=1)
nn.fit(control[['propensity_score']])

distances, indices = nn.kneighbors(treated[['propensity_score']])
matched_control = control.iloc[indices.flatten()].copy()
matched_control.index = treated.index  # Align indices for subtraction



