import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error

# Estimate the impact of marketing channels on sales while controlling for non-marketing factors
# linear regression as baseline 

df = pd.read_csv('Marketing_Mix_Data.csv')
df.head()

# apply adstock transformation
# adstock[t] = spend[t] + adstock[t-1] * decay
def apply_adstock(series, decay):
    """apply adstock transformation to a media spend series"""
    adstocked = []
    carryover = 0
    for spend in series:
        carryover = spend + carryover * decay
        adstocked.append(carryover)
    return adstocked
# apply hill function to model diminishing returns
def hill_function(x, alpha, theta):
    """hill function for diminishing returns"""
    return x**alpha / (x**alpha + theta**alpha)

alpha_grid = np.linspace(1, 2, 11)
theta_grid = np.linspace(50000, 150000, 11)
sales = df['Sales'].values

best_mse = float('inf')
best_alpha = None
best_theta = None


decay = 0.5 # how do we choose this?
media_channels = ['TV', 'Paid_Social', 'Display']


for channel in media_channels:
    df[f'{channel}_adstock'] = apply_adstock(df[channel], decay)
    
    x = df[f'{channel}_adstock'].values

    for alpha in alpha_grid:
        for theta in theta_grid:
            transformed = hill_function(x, alpha, theta)
            # simple linear regression against sales
            beta = np.sum(transformed * sales) / np.sum(transformed**2)
            prediction = transformed * beta
            
            mse = np.mean((sales - prediction)**2)


            if mse < best_mse:
                best_mse = mse
                best_alpha = alpha
                best_theta = theta
    df[f'{channel}_saturation'] = hill_function(df[f'{channel}_adstock'], best_alpha, best_theta)
    


# fit a Linear regression model as a baseline
transformed_channels = [f'{channel}_saturation' for channel in media_channels]
features = transformed_channels + ['Price', 'Competitor_Spend', 'Seasonality_Index']

X = df[features]
y = df['Sales']

model = LinearRegression()
model.fit(X, y)

# evaluate the model
y_pred = model.predict(X)
root_mean_squared_error(y, y_pred)


import sys
print(sys.executable)

# Fit a Bayesian MMM
import pymc as pm
import arviz as az



# Prior predictive distribution
def iROAS_to_prior(iROAS, ci= None, se= None):
    mu = iROAS
    if ci:
        # convert confidence interval to standard error
        sigma = (ci[1] - ci[0]) / 3.92
    elif se:
        sigma = se
    else:
        raise ValueError("Either ci or se must be provided")
    return mu, sigma


with pm.Model() as bayesian_mmm:
    # Priors for the coefficients
    # intercept is the baseline sales without any media spend
    # mu = mean(sales)
    # sigma = std(sales) the bigger the sigma the weaker the prior
    intercept = pm.Normal('intercept', mu = 0, sigma = 10)
    # priors useing iROAS
    betas = pm.Normal('betas', mu = 0, sigma = 5, shape = X.shape[1])

    # Expected_sales (linear model)
    mu = intercept + pm.math.dot(X.values, betas)

    # Noise
    # noise sigma = std(residuals): residuals from baseline model
    # residuals = y - y_pred
    sigma = pm.HalfNormal('sigma', sigma = 10)
    
    # Likelihood of seeing y, given the current parameters
    sales_obs = pm.Normal('sales_obs', mu = mu, sigma = sigma, observed = y)

    # Inference
    trace = pm.sample(2000, tune=1000, target_accept=0.95, return_inferencedata=True)

# posterior summary
summary = az.summary(trace, hdi_prob=0.95)
print(summary)

# plot the posterior distributions
az.plot_trace(trace, var_names=['betas'], combined=True)
az.plot_posterior(trace, var_names=['betas'])

# ROI

# posterior samples
posterior_betas = trace.posterior['betas']
n_draws = posterior_betas.sizes['draw']

# Get total saturated spend per channel
total_saturated_spend = df[[f'{col}_saturation' for col in media_channels]].sum().values
total_effective_spend = df[media_channels].sum().values

# Estimate the ROI
roi_samples = []
for i, sample in enumerate(media_channels):
    # get the posterior samples for the betas
    # select i-th beta coefficient
    beta_samples = posterior_betas.sel(betas_dim_0=i).stack(sample=('chain', 'draw')).values
    # calculate the ROI
    roi = (beta_samples * total_saturated_spend[i]) / (total_effective_spend[i] * n_draws)
    roi_samples.append(roi)

# convert to dataframe
roi_df = pd.DataFrame({channel: roi for channel, roi in zip(media_channels, roi_samples)})

# Summary statistics
roi_summary = roi_df.describe(percentiles=[0.025, 0.5, 0.975]).T[["mean", "2.5%", "50%", "97.5%"]]
roi_summary.columns = ["mean", "hdi_2.5%", "median", "hdi_97.5%"]
roi_summary
# mean: average ROI across posterior samples
# 2.5% / 97.5%: 95% credible interval (uncertainty)
# 50%: median ROI



# Vis
import seaborn as sns
import matplotlib.pyplot as plt


# Melt posterior ROI samples into long format
roi_long = roi_df.melt(var_name="Channel", value_name="ROI")

# Violin plot
plt.figure(figsize=(10, 6))
sns.violinplot(x="ROI", y="Channel", data=roi_long, inner="quartile", scale="width", cut=0)
plt.axvline(1, color="red", linestyle="--", label="ROI = 1 (Break-even)")
plt.title("Posterior ROI Distributions per Channel")
plt.legend()
plt.show()



# From roi_summary earlier
roi_summary["Channel"] = roi_summary.index

plt.figure(figsize=(8, 5))
plt.errorbar(
    roi_summary["mean"],
    roi_summary["Channel"],
    xerr=[roi_summary["mean"] - roi_summary["hdi_2.5%"],
          roi_summary["hdi_97.5%"] - roi_summary["mean"]],
    fmt='o', color='black', capsize=4
)
plt.axvline(1, color="red", linestyle="--")
plt.xlabel("ROI")
plt.title("Mean ROI with 95% Credible Intervals")
plt.show()


with bayesian_mmm:
    ppc = pm.sample_posterior_predictive(trace, random_seed=42)

az.plot_ppc(az.from_pymc3(posterior_predictive=ppc, model=bayesian_mmm))
