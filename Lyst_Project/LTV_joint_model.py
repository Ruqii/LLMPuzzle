import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from lifelines import CoxPHFitter
import statsmodels.api as sm






df = pd.read_csv('customer_data_ltv_simulation_corrected.csv')

df.head()



def calc_repurchase_intervals():
    intervals = []

    for id, purchases in df.groupby('customer_id'):
        purchases = purchases.sort_values('purchase_date')
        
        for i in range(len(purchases) - 1):
            start = purchases.iloc[i]['purchase_date']
            end = purchases.iloc[i + 1]['purchase_date']
            interval = (end - start).days
            
            # Append the interval to the list
            intervals.append(interval)
    repurchase_window = np.percentile(intervals, 90)
    return repurchase_window



def define_repurchased(purchase_data, censor_window):
    repurchase_status = []

    for i in range(len(purchase_data) - 1):
        current_purchase = purchase_data.iloc[i]
        next_purchase = purchase_data.iloc[i + 1]

        days_between = (next_purchase['purchase_date'] - current_purchase['purchase_date']).days
        if days_between <= censor_window:
            repurchase_status.append({
                'customer_id': current_purchase['customer_id'],
                'purchase_date': current_purchase['purchase_date'],
                'days_since_last_purchase': days_between,
                'repurchased': 1 # purchased within the window
            })
        else:
            repurchase_status.append({
                'customer_id': current_purchase['customer_id'],
                'purchase_date': current_purchase['purchase_date'],
                'days_since_last_purchase': days_between,
                'repurchased': 0 # not purchased within the window
            })
    
    last_purchase = purchase_data.iloc[-1]
    repurchase_status.append({
        'customer_id': last_purchase['customer_id'],
        'purchase_date': last_purchase['purchase_date'],
        'days_since_last_purchase': 0,
        'repurchased': 0 # last purchase is not a repurchase
    })
    return pd.DataFrame(repurchase_status)





repurchase_window = np.percentile(df['days_since_last_purchase'], 90)
df['repurchased'] = df['days_since_last_purchase'].apply(lambda x: 1 if x <= repurchase_window else 0)


survival_df = df.groupby('customer_id').agg({
    'purchase_date': 'count',
    'purchase_value': ['sum', 'mean', 'max'],
    'repurchased': 'max',
    'days_since_last_purchase': 'max',
    'campaign_exposure': 'max',
    'customer_segment': 'max',
    'acquisition_channel': 'max',
    'demographics': 'max'
}).reset_index()


survival_df.columns = ['_'.join(col).rstrip('_') for col in survival_df.columns]

survival_df.rename(columns={
    'purchase_date_count': 'n_purchases',
    'purchase_value_sum': 'total_purchase_value',
    'purchase_value_mean': 'avg_purchase_value',
    'purchase_value_max': 'max_purchase_value',
    'repurchased_max': 'repurchase_status',
    'days_since_last_purchase_max': 'days_since_last_purchase',
    'campaign_exposure_max': 'campaign_exposure',
    'customer_segment_max': 'customer_segment',
    'acquisition_channel_max': 'acquisition_channel',
    'demographics_max': 'demographics'
}, inplace=True)

# survival model for time between purchases
survival_model = CoxPHFitter()
survival_model.fit(
    survival_df,
    duration_col='days_since_last_purchase',
    event_col='repurchase_status',
    formula = 'campaign_exposure + total_purchase_value + customer_segment +  acquisition_channel + demographics',  
)
survival_model.print_summary()
survival_df['hazard_ratio'] = survival_model.predict_partial_hazard(survival_df)
surv_func = survival_model.predict_survival_function(survival_df)

# plot survival function
plt.figure(figsize=(10, 6))
for i in range(len(survival_df)):
    plt.plot(surv_func.index, surv_func.iloc[:, i], label=f'User {i+1}')
plt.title('Survival Function for Each User')
plt.xlabel('Duration (days)')
plt.ylabel('Survival Probability')
plt.grid(True)
plt.show()



df.head()
# longitudinal model for purchase frequency
longitudinal_model = sm.MixedLM.from_formula(
    'purchase_value ~ campaign_exposure + days_since_first_purchase +' +
    'campaign_exposure:days_since_first_purchase +' +
    'campaign_exposure:customer_segment +' +
    'customer_segment + acquisition_channel + demographics',
    groups=df['customer_id'],
    data=df
)
longitudinal_results = longitudinal_model.fit()
print(longitudinal_results.summary())


# JOINT MODEL
joint_model = jointModelBayes(
    longitudinal_object =longitudinal_model,
    survival_object = survival_model,
    id_var = 'customer_id', 
    time_var = 'time_period'
)


# Extract coefficients for campaign impact
campaign_effect_on_timing = joint_model.coefficients['survival']['campaign_exposure']
campaign_effect_on_value = joint_model.coefficients['longitudinal']['campaign_exposure']

# Calculate combined LTV impact
survival_baseline = joint_model.baseline_hazard
longitudinal_baseline = joint_model.baseline_value

# Simulate LTV with/without campaign exposure
predicted_ltv_exposed = calculate_expected_value(joint_model, exposed=True)
predicted_ltv_control = calculate_expected_value(joint_model, exposed=False)

campaign_ltv_impact = predicted_ltv_exposed - predicted_ltv_control



plt.figure(figsize=(12, 8))

# Plot survival curves
plt.subplot(2, 1, 1)
joint_model.plot_survival()

# Plot conditional expected values
plt.subplot(2, 1, 2)
joint_model.plot_conditional_expected_values()

plt.tight_layout()
plt.savefig('joint_model_results.png')










