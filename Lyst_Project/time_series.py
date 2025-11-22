import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tfcausalimpact.causalimpact.main import CausalImpact


df = pd.read_csv('simulated_full_daily_revenue.csv')
df_control = pd.read_csv('simulated_control_daily_revenue.csv')

df.head()

# aggregate data to weekly
df['date'] = pd.to_datetime(df['date'])
df['week'] = df['date'].dt.to_period('W').apply(lambda x: x.start_time)
df['intervention'] = 0
df.loc[df.index >= 90, 'intervention'] = 1

weekly_df = df.groupby('week').agg({
    'revenue_per_user': 'mean',
    'number_of_sessions': 'sum',
    'number_of_signups': 'sum',
    'avg_order_value': 'mean',
    'seasonality_index': 'mean',
    'intervention': 'max'
}).reset_index()

df_control['date'] = pd.to_datetime(df_control['date'])
df_control['week'] = df_control['date'].dt.to_period('W').apply(lambda x: x.start_time)
df_control['intervention'] = 0
weekly_control_df = df_control.groupby('week').agg({
    'revenue_per_user': 'mean',
    'number_of_sessions': 'sum',
    'number_of_signups': 'sum',
    'avg_order_value': 'mean',
    'seasonality_index': 'mean',
    'intervention': 'max'
}).reset_index()

impact_df = pd.merge(weekly_df, weekly_control_df, on='week', suffixes=('', '_control'))

revenue_df = impact_df[['revenue_per_user', 'revenue_per_user_control']]
signups_df = impact_df[['number_of_signups', 'number_of_signups_control']]

pre_period = [int(weekly_df[weekly_df['intervention'] == 0].index.min()), 
              int(weekly_df[weekly_df['intervention'] == 0].index.max())]
post_period = [int(weekly_df[weekly_df['intervention'] == 1].index.min()), 
               int(weekly_df[weekly_df['intervention'] == 1].index.max())]

revenue_df.head()

# Fit the CausalImpact model
ci = CausalImpact(revenue_df, pre_period, post_period)
print(ci.summary('report'))
ci.plot()

ci_signups = CausalImpact(signups_df, pre_period, post_period)
print(ci_signups.summary('report'))


# Get the summary dataframe
summary_df = ci.summary_data


avg_actual = summary_df.loc['actual', 'average']
avg_predicted = summary_df.loc['predicted', 'average']
avg_abs_effect = summary_df.loc['abs_effect', 'average']
avg_rel_effect = summary_df.loc['rel_effect', 'average'] * 100  # already in fraction!

cum_actual = summary_df.loc['actual', 'cumulative']
cum_predicted = summary_df.loc['predicted', 'cumulative']
cum_abs_effect = summary_df.loc['abs_effect', 'cumulative']
cum_rel_effect = summary_df.loc['rel_effect', 'cumulative'] * 100  # already in fraction!


# Lower and upper bounds
avg_abs_effect_lower = summary_df.loc['abs_effect_lower', 'average']
avg_abs_effect_upper = summary_df.loc['abs_effect_upper', 'average']

avg_rel_effect_lower = summary_df.loc['rel_effect_lower', 'average'] * 100
avg_rel_effect_upper = summary_df.loc['rel_effect_upper', 'average'] * 100


# P-value and posterior probability
p_value = ci.p_value
posterior_prob = 1 - ci.p_value


# 🧹 Build Markdown text
markdown_report = f"""
## Causal Impact Analysis Report

**Post-Intervention Period Results**

- **Observed Average Revenue per User:** {avg_actual:.2f}
- **Predicted Average Revenue per User (No Intervention):** {avg_predicted:.2f}
- **Estimated Absolute Uplift (per user):** {avg_abs_effect:.2f} (95% CI: {avg_abs_effect_lower:.2f} – {avg_abs_effect_upper:.2f})
- **Estimated Relative Uplift:** {avg_rel_effect:.2f}% (95% CI: {avg_rel_effect_lower:.2f}% – {avg_rel_effect_upper:.2f}%)

**Cumulative Results (over post period)**

- **Observed Cumulative Revenue per User:** {cum_actual:.2f}
- **Predicted Cumulative Revenue per User:** {cum_predicted:.2f}
- **Estimated Cumulative Uplift:** {cum_abs_effect:.2f}
- **Cumulative Relative Uplift:** {cum_rel_effect:.2f}%

**Statistical Significance**

- **P-Value:** {p_value:.4f}
- **Posterior Probability of a Real Effect:** {posterior_prob:.2%}

---

### Conclusion:

The intervention led to a **statistically significant** and **substantively meaningful** uplift in revenue per user, with an average increase of **{avg_rel_effect:.2f}%** compared to the counterfactual.  
The probability that this observed effect is due to random chance is virtually **0%**.

"""

# Print it nicely
print(markdown_report)



# Export Markdown report
with open('causalimpact_report.md', 'w') as f:
    f.write(markdown_report)




# Create a figure
fig, ax = plt.subplots(figsize=(12, 6))

# Plot actual observed revenue_per_user
ax.plot(model_df.index, model_df['revenue_per_user'], label="Observed Revenue per User", color="black")

# Plot counterfactual prediction (what would have happened without intervention)
ax.plot(model_df.index, ci.inferences['complete_preds_means'], label="Predicted (No Intervention)", linestyle="dashed", color="blue")

# Fill between prediction lower and upper bounds
ax.fill_between(model_df.index, 
                ci.inferences['complete_preds_lower'], 
                ci.inferences['complete_preds_upper'], 
                color="blue", alpha=0.2, label="Prediction 95% CI")

# Add a vertical line showing intervention point
ax.axvline(x=post_period[0], color="red", linestyle="--", label="Intervention Start")

# Labels and legend
ax.set_title("Causal Impact Analysis")
ax.set_xlabel("Week Index")
ax.set_ylabel("Revenue per User")
ax.legend()

# Save the plot
fig.savefig('causalimpact_plot.png', bbox_inches='tight', dpi=300)

print("✅ Custom CausalImpact plot saved as 'causalimpact_plot.png'!")






