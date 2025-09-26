
import warnings
import numpy as np

# Suppress specific statsmodels warnings
warnings.filterwarnings('ignore', category=RuntimeWarning, 
                       message='.*invalid value encountered in subtract.*')
warnings.filterwarnings('ignore', category=RuntimeWarning, 
                       message='.*invalid value encountered.*')
# Note: np.RankWarning was removed in NumPy 2.0
# Only filter if it exists (for compatibility with older NumPy versions)
if hasattr(np, 'RankWarning'):
    warnings.filterwarnings('ignore', category=np.RankWarning)
warnings.filterwarnings('ignore', category=FutureWarning, 
                       module='statsmodels')
warnings.filterwarnings('ignore', category=UserWarning, 
                       module='statsmodels')
