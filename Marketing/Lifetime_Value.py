import pandas as pd
import numpy as np
from lifelines import CoxPHFitter
import seaborn as sns
import matplotlib.pyplot as plt
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test


df = pd.read_csv('Raw_User_Activity_Dataset.csv')
df.head()

# set a cutoff date for right censored users
date_cols = ['start_date', 'end_date', 'cutoff_date']
df[date_cols] = df[date_cols].apply(pd.to_datetime, errors='coerce')
df['duration'] = np.where(df['event'] == 1, df['end_date'] - df['start_date'],
                          df['cutoff_date'] - df['start_date'])
df['duration'] = df['duration'].dt.days
df['duration'] = df['duration'].astype(int)


# one - hot encode categorical variables
df_encoded = pd.get_dummies(df, columns=['device', 'group'], drop_first=True, dtype=int)
df_encoded.head()

# select features for the Cox model
features = ['duration', 'event', 
            'consult_completed', 'program_started', 'time_on_site',
            'group_control', 'device_mobile']

cox_df = df_encoded[features]
 
# fit the cox proportional hazards model
cph = CoxPHFitter()
cph.fit(cox_df, duration_col='duration', event_col='event')
cph.print_summary()


# predict hazard ratios
cox_df['hazard_ratio'] = cph.predict_partial_hazard(cox_df)
# predict survival probability over time
surv_func = cph.predict_survival_function(cox_df)
# rows: days over time
# columns: users

# plot survival function
plt.figure(figsize=(10, 6))
for i in range(len(cox_df)):
    plt.plot(surv_func.index, surv_func.iloc[:, i], label=f'User {i+1}')
plt.title('Survival Function for Each User')
plt.xlabel('Duration (days)')
plt.ylabel('Survival Probability')
plt.grid(True)
plt.show()


# get survival probability at Day 30
cox_df['survival_prob_30'] = cph.predict_survival_function(cox_df, times=[30]).values.flatten()


# predict median survival time
cox_df['predicted_survival_time'] = cph.predict_median(cox_df)

# assume ARPU is £1.5/day
ARPU = 1.5
cox_df['predicted_LTV'] = (cox_df['predicted_survival_time'] * ARPU).round(2)
cox_df[['duration','predicted_survival_time', 'predicted_LTV']].head()

# join back with original dataframe
cox_df['group'] = cox_df['group_control'].map({0: 'campaign', 1: 'control'})

# boxplot
sns.boxplot(data = cox_df, x = 'group', y = 'predicted_LTV', palette = 'Set2')
plt.title('Predicted LTV by Group')
plt.ylabel('predicted LTV (£)')
plt.grid(True)
plt.show()


# log - rank test: check if survival curves differ significant between groups

kmf = KaplanMeierFitter()

fig, ax = plt.subplots()
for value, label in [(0, 'campaign'), (1, 'control')]:
    kmf.fit(durations = cox_df[cox_df['group_control']==value]['duration'],
            event_observed = cox_df[cox_df['group_control']==value]['event'],
            label = label)
    kmf.plot_survival_function(ax = ax)

plt.title('Survival Curves by Group')
plt.xlabel('Duration (days)')
plt.ylabel('Survival Probability')
plt.grid(True)
plt.show()

# statistical test
results = logrank_test(
    cox_df[cox_df['group_control'] == 0]['duration'],
    cox_df[cox_df['group_control'] == 1]['duration'],
    event_observed_A=cox_df[cox_df['group_control'] == 0]['event'],
    event_observed_B=cox_df[cox_df['group_control'] == 1]['event']
)
print(f"p-value: {results.p_value}")







# Weibull

from lifelines import WeibullAFTFitter

wb_df = df_encoded[features]
wb_df = wb_df[wb_df['duration'] > 0]  # Filter out non-positive durations

aft = WeibullAFTFitter()
aft.fit(wb_df, duration_col='duration', event_col='event')
aft.print_summary()

wb_df['predicted_lifetime'] = aft.predict_median(wb_df)
wb_df['expected_lifetime'] = aft.predict_expectation(wb_df)

wb_df['predicted_LTV'] = wb_df['predicted_lifetime'] * ARPU

aft.plot_partial_effects_on_outcome(covariates='group_control', values=[0, 1], cmap='coolwarm')

cohort_summary = df.groupby("campaign_type").agg(
    avg_lifetime=("predicted_lifetime", "mean"),
    avg_ARPU=("ARPU", "mean"),
    avg_pLTV=("pLTV", "mean"),
    user_count=("user_id", "count")
).reset_index()

# add confidence level
aft.predict_survival_function(df[df["campaign_type"] == "summer"]).mean(axis=1)











# time-varying cox model

import pandas as pd
import numpy as np
from lifelines import CoxTimeVaryingFitter

# Simulate user activity data with time-varying covariates
np.random.seed(42)
n_users = 5
data = []

for user_id in range(n_users):
    total_time = int(np.random.exponential(30)) + 1
    event = np.random.binomial(1, 0.7)
    for t in range(0, total_time, 5):
        stop_time = min(t + 5, total_time)
        data.append({
            "user_id": user_id,
            "start": t,
            "stop": stop_time,
            "event": int(stop_time == total_time and event == 1),
            "time_on_site": np.random.normal(10, 2),
            "group_control": np.random.randint(0, 2)
        })

df_tv = pd.DataFrame(data)

# Fit time-varying Cox model
ctv = CoxTimeVaryingFitter()
ctv.fit(df_tv, id_col="user_id", start_col="start", stop_col="stop", event_col="event")
ctv.print_summary()