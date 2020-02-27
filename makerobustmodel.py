import numpy as np
import statsmodels.api as sm

class RobustModel(object):

    def __init__(self, datetimes, num_years):
        
        self.T = 365.25
        self.pi_val = (2 * np.pi) / self.T
        self.pi_val_change = (2 * np.pi) / (num_years * self.T)
        self.datetimes = datetimes
        self.robust_model = None
        self.RMSE = None
        self.start_date = np.min(self.datetimes)
        self.residuals = None

    def fitModel(self, band_data):
        
        x = self.prepareXData(self.datetimes)
        
        self.robust_model = sm.RLM(band_data, x, M=sm.robust.norms.TukeyBiweight(c=0.4685)).fit()

        predicted = self.robust_model.predict(x)

        self.residuals = band_data - predicted
        
        # Get overall RMSE of model
        self.RMSE = np.sqrt(np.mean(self.residuals ** 2))
        
    def prepareXData(self, datetimes):
        
        rescaled = datetimes - np.min(self.datetimes)
        
        x = np.array([np.ones_like(datetimes), # Add constant 
                      np.cos(self.pi_val * rescaled),
                      np.sin(self.pi_val * rescaled),
                      np.cos(self.pi_val_change * rescaled),
                      np.sin(self.pi_val_change * rescaled)]).T

        return(x)       
        
