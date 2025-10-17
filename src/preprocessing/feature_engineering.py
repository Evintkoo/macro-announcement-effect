"""
Feature engineering module for creating analysis variables.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging
from scipy import stats
from pathlib import Path

# Setup enhanced logging if available
logger = logging.getLogger(__name__)

def setup_enhanced_logging():
    """Setup enhanced logging if available."""
    try:
        import sys
        from pathlib import Path
        # Add project root src to path
        project_root = Path(__file__).parent.parent.parent
        src_path = project_root / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        from utils.logging_config import ComponentLogger
        component_logger = ComponentLogger()
        return component_logger.get_preprocessing_logger("INFO")
    except ImportError as e:
        logger.warning(f"Enhanced logging not available, using standard logger: {e}")
        return logging.getLogger(__name__)

# Initialize logger
logger = setup_enhanced_logging()

class FeatureEngineer:
    """Class for creating features for analysis."""
    
    def __init__(self, log_level: str = "INFO"):
        # Use the global logger or create a new one
        self.logger = logger
        self.logger.info("FeatureEngineer initialized")
        
        # Try to setup enhanced logging
        self._setup_enhanced_logging(log_level)
    
    def _setup_enhanced_logging(self, log_level: str = "INFO"):
        """Setup enhanced logging if available."""
        try:
            import sys
            from pathlib import Path
            # Ensure src is on path
            project_root = Path(__file__).parent.parent.parent
            src_path = project_root / "src"
            if str(src_path) not in sys.path:
                sys.path.insert(0, str(src_path))
            
            from utils.logging_config import EnhancedLogger
            
            enhanced_logger = EnhancedLogger(f"{__name__}.FeatureEngineer")
            
            # Create logs directory if it doesn't exist
            Path("logs").mkdir(exist_ok=True)
            
            # Set up logging with both file and console output
            self.logger = enhanced_logger.setup_logging(
                log_level=log_level,
                log_file="logs/preprocessing.log",
                console_output=True,
                component_name="FeatureEngineering"
            )
            
            self.logger.info("[SUCCESS] Enhanced logging configured successfully (file + console output)")
            
        except ImportError as e:
            self.logger.warning(f"Enhanced logging not available: {e}")
            # Configure basic logging with both console and file
            self._setup_basic_logging(log_level)
    
    def _setup_basic_logging(self, log_level: str = "INFO"):
        """Setup basic logging with both console and file output."""
        import logging.handlers
        
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        # Configure basic logger
        self.logger = logging.getLogger(f"{__name__}.FeatureEngineer")
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - FeatureEngineering - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.handlers.RotatingFileHandler(
            "logs/preprocessing.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - FeatureEngineering - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Prevent propagation to avoid duplicate messages
        self.logger.propagate = False
        
        self.logger.info("[SUCCESS] Basic logging configured (console + file)")
    
    def configure_logging(self, log_level: str = "INFO", enable_console: bool = True, enable_file: bool = True):
        """
        Configure logging for feature engineering operations.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_console: Whether to output to console
            enable_file: Whether to output to file
        """
        self.logger.info(f"Reconfiguring logging: Level={log_level}, Console={enable_console}, File={enable_file}")
        self._setup_enhanced_logging(log_level)
    
    def create_surprise_measures(
        self,
        actual_data: pd.DataFrame,
        expected_data: pd.DataFrame = None
    ) -> pd.DataFrame:
        """
        Create surprise measures as defined in the research plan.
        
        Args:
            actual_data: DataFrame with actual announcement values
            expected_data: DataFrame with expected/forecast values (optional)
            
        Returns:
            DataFrame with surprise measures
        """
        if expected_data is None:
            # If no forecast data, use historical mean as proxy for expected
            return self._create_surprise_from_historical(actual_data)
        else:
            return self._create_surprise_from_forecasts(actual_data, expected_data)
    
    def _create_surprise_from_forecasts(
        self,
        actual_data: pd.DataFrame,
        expected_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Create surprises using actual forecast data."""
        # Use dictionary to collect all features, then create DataFrame once
        all_surprises = {}
        
        for col in actual_data.columns:
            if col in expected_data.columns:
                # Raw surprise: A_t - E_t
                raw_surprise = actual_data[col] - expected_data[col]
                all_surprises[f"{col}_surprise"] = raw_surprise
                
                # Normalized surprise: (A_t - E_t) / σ(E_t)
                # Use rolling standard deviation of surprises
                surprise_std = raw_surprise.rolling(window=12, min_periods=1).std()
                normalized_surprise = raw_surprise / surprise_std
                all_surprises[f"{col}_normalized_surprise"] = normalized_surprise
                
                # Sign indicator
                sign_indicator = np.where(raw_surprise > 0, 1, 
                                        np.where(raw_surprise < 0, -1, 0))
                all_surprises[f"{col}_sign"] = pd.Series(sign_indicator, index=raw_surprise.index)
                
                # Absolute surprise
                all_surprises[f"{col}_abs_surprise"] = np.abs(raw_surprise)
        
        # Create DataFrame efficiently from dictionary
        surprises = pd.DataFrame(all_surprises, index=actual_data.index)
        return surprises
    
    def _create_surprise_from_historical(self, actual_data: pd.DataFrame) -> pd.DataFrame:
        """
        Create surprises using historical mean as expected value.
        
        P1 WARNING: This is a PROXY surprise based on historical rolling mean, 
        not actual forecast data. For publication-grade analysis, use real 
        forecast-based surprises (Bloomberg/Refinitiv/WSJ consensus).
        
        Columns are prefixed with 'proxy_surprise_' to indicate methodology limitation.
        """
        # Use dictionary to collect all features, then create DataFrame once
        all_surprises = {}
        
        # Check config for marking policy
        try:
            from utils.config import Config
            config = Config()
            mark_proxy = config.get('analysis', {}).get('mark_proxy_surprises', True)
        except:
            mark_proxy = True  # Default to marking
        
        # Set prefix based on marking policy
        prefix = "proxy_surprise_" if mark_proxy else ""
        
        if mark_proxy:
            self.logger.warning(
                "Creating PROXY surprises from historical means. "
                "These are NOT forecast-based surprises. "
                "Results should be clearly labeled as using proxy methodology."
            )
        
        for col in actual_data.columns:
            series = actual_data[col].dropna()
            
            # Use rolling mean as "expected" value (12-period window)
            expected = series.rolling(window=12, min_periods=1).mean().shift(1)
            
            # Raw surprise
            raw_surprise = series - expected
            
            # Reindex to match the original dataframe index
            raw_surprise_reindexed = raw_surprise.reindex(actual_data.index)
            # P1 FIX: Mark as proxy surprise
            all_surprises[f"{prefix}{col}_surprise"] = raw_surprise_reindexed
            
            # Normalized surprise
            surprise_std = raw_surprise.rolling(window=12, min_periods=1).std()
            normalized_surprise = raw_surprise / surprise_std
            all_surprises[f"{prefix}{col}_normalized_surprise"] = normalized_surprise.reindex(actual_data.index)
            
            # Sign indicator (use reindexed series)
            sign_indicator = np.where(raw_surprise_reindexed > 0, 1,
                                    np.where(raw_surprise_reindexed < 0, -1, 0))
            all_surprises[f"{prefix}{col}_sign"] = pd.Series(sign_indicator, index=actual_data.index)
            
            # Absolute surprise
            all_surprises[f"{prefix}{col}_abs_surprise"] = np.abs(raw_surprise_reindexed)
        
        # Create DataFrame efficiently from dictionary
        surprises = pd.DataFrame(all_surprises, index=actual_data.index)
        return surprises
    
    def create_return_features(
        self,
        price_data: pd.DataFrame,
        windows: List[int] = [1, 5, 10, 20]
    ) -> pd.DataFrame:
        """
        Create return-based features.
        
        Args:
            price_data: DataFrame with price data
            windows: List of window sizes for features
            
        Returns:
            DataFrame with return features
        """
        # Use a dictionary to collect all features, then create DataFrame once
        all_features = {}
        
        for col in price_data.columns:
            prices = price_data[col]
            valid_count = prices.notna().sum()
            
            if valid_count > max(windows):
                # Log returns on the full index to maintain alignment
                returns = np.log(prices / prices.shift(1)).replace([np.inf, -np.inf], np.nan)
                all_features[f"{col}_return"] = returns
                
                # Rolling return statistics (retain full index)
                for window in windows:
                    rolling_view = returns.rolling(window, min_periods=1)
                    all_features[f"{col}_return_mean_{window}d"] = rolling_view.mean()
                    all_features[f"{col}_volatility_{window}d"] = rolling_view.std()
                    all_features[f"{col}_skewness_{window}d"] = rolling_view.skew()
                    all_features[f"{col}_kurtosis_{window}d"] = rolling_view.kurt()
                    all_features[f"{col}_cumret_{window}d"] = rolling_view.sum()
        
        # Create DataFrame efficiently from dictionary
        features = pd.DataFrame(all_features, index=price_data.index)
        return features
    
    def create_volatility_features(
        self,
        returns_data: pd.DataFrame,
        windows: List[int] = [5, 10, 20, 60]
    ) -> pd.DataFrame:
        """
        Create volatility-based features.
        
        Args:
            returns_data: DataFrame with return data
            windows: List of window sizes
            
        Returns:
            DataFrame with volatility features
        """
        # Use a dictionary to collect all features, then create DataFrame once
        all_features = {}
        
        for col in returns_data.columns:
            returns = returns_data[col]
            valid_count = returns.notna().sum()
            
            if valid_count > max(windows):
                for window in windows:
                    rolling_view = returns.rolling(window, min_periods=1)
                    # Realized volatility
                    realized_vol = np.sqrt(rolling_view.var() * 252)
                    all_features[f"{col}_realized_vol_{window}d"] = realized_vol
                    
                    # Exponential smoothing volatility
                    alpha = 2 / (window + 1)
                    exp_vol = returns.ewm(alpha=alpha).std() * np.sqrt(252)
                    all_features[f"{col}_exp_vol_{window}d"] = exp_vol
                    
                    # Jump indicators (large moves)
                    threshold = rolling_view.std() * 3
                    jump_indicator = (np.abs(returns) > threshold).astype(int)
                    all_features[f"{col}_jump_{window}d"] = jump_indicator
        
        # Create DataFrame efficiently from dictionary
        features = pd.DataFrame(all_features, index=returns_data.index)
        
        return features
    
    def create_market_regime_features(
        self,
        market_data: pd.DataFrame,
        volatility_threshold: float = 0.015
    ) -> pd.DataFrame:
        """
        Create market regime indicators based on market volatility and trends.
        
        Args:
            market_data: DataFrame with market data
            volatility_threshold: Threshold for high/low volatility regime (daily return std)
            
        Returns:
            DataFrame with regime features
        """
        # Use dictionary to collect all features, then create DataFrame once
        all_features = {}
        
        # Market trend regime (using S&P 500 if available)
        sp500_cols = [col for col in market_data.columns 
                     if any(indicator in col.lower() for indicator in ['sp500', 'gspc', '^gspc'])]
        
        if sp500_cols:
            sp500_col = sp500_cols[0]
            sp500_prices = market_data[sp500_col]
            
            # Calculate returns for volatility regime
            sp500_returns = np.log(sp500_prices / sp500_prices.shift(1))
            rolling_vol = sp500_returns.rolling(20).std()
            
            # Volatility-based regime (using realized volatility instead of VIX)
            all_features['high_volatility_regime'] = (rolling_vol > volatility_threshold).astype(int)
            all_features['low_volatility_regime'] = (rolling_vol <= volatility_threshold).astype(int)
            
            # Volatility percentile
            all_features['volatility_percentile'] = rolling_vol.rolling(252).rank(pct=True)
            
            # Bull/bear market based on 200-day MA
            ma_200 = sp500_prices.rolling(200).mean()
            all_features['bull_market'] = (sp500_prices > ma_200).astype(int)
            all_features['bear_market'] = (sp500_prices <= ma_200).astype(int)
            
            # Trend strength
            all_features['trend_strength'] = (sp500_prices - ma_200) / ma_200
        
        # Create DataFrame efficiently from dictionary
        features = pd.DataFrame(all_features, index=market_data.index)
        return features
    
    def create_interaction_features(
        self,
        surprise_data: pd.DataFrame,
        regime_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Create interaction features between surprises and market regimes.
        
        Args:
            surprise_data: DataFrame with surprise measures
            regime_data: DataFrame with regime indicators
            
        Returns:
            DataFrame with interaction features
        """
        # Use dictionary to collect all features, then create DataFrame once
        all_features = {}
        
        # Get surprise columns
        surprise_cols = [col for col in surprise_data.columns if 'surprise' in col]
        regime_cols = [col for col in regime_data.columns if 'regime' in col or 'market' in col]
        
        # Create interactions
        for surprise_col in surprise_cols:
            for regime_col in regime_cols:
                if surprise_col in surprise_data.columns and regime_col in regime_data.columns:
                    interaction_name = f"{surprise_col}_x_{regime_col}"
                    interaction = surprise_data[surprise_col].mul(
                        regime_data[regime_col], fill_value=np.nan
                    )
                    all_features[interaction_name] = interaction
        
        # Create DataFrame efficiently from dictionary
        features = pd.DataFrame(all_features, index=surprise_data.index)
        return features
    
    def create_event_window_features(
        self,
        data: pd.DataFrame,
        event_times: List[datetime],
        pre_window: int = 1,
        post_window: int = 3
    ) -> pd.DataFrame:
        """
        Create event window indicators.
        
        Args:
            data: DataFrame with time series data (must have DatetimeIndex)
            event_times: List of event times
            pre_window: Days before event
            post_window: Days after event
            
        Returns:
            DataFrame with event window indicators
            
        Note:
            P1 FIX: Properly normalizes dates for comparison to avoid timezone/time-of-day issues
        """
        features = pd.DataFrame(index=data.index, columns=[
            'pre_event', 'event_day', 'post_event_1d', 'post_event_2d', 'post_event_3d'
        ], data=0)
        
        # P1 FIX: Normalize data index to date-only for daily comparison
        # This avoids issues when comparing event_time.date() to a DatetimeIndex
        if isinstance(data.index, pd.DatetimeIndex):
            normalized_index = data.index.normalize()  # Set all times to midnight
        else:
            normalized_index = pd.DatetimeIndex(data.index)
        
        for event_time in event_times:
            # Convert event_time to normalized datetime
            if hasattr(event_time, 'date'):
                event_date = pd.Timestamp(event_time.date())
            else:
                event_date = pd.Timestamp(event_time)
            event_date = event_date.normalize()  # Ensure midnight
            
            # Pre-event window
            for i in range(1, pre_window + 1):
                pre_date = event_date - pd.Timedelta(days=i)
                # Use normalized index for comparison
                mask = normalized_index == pre_date
                if mask.any():
                    features.loc[mask, 'pre_event'] = 1
            
            # Event day
            mask = normalized_index == event_date
            if mask.any():
                features.loc[mask, 'event_day'] = 1
            
            # Post-event windows
            for i in range(1, post_window + 1):
                post_date = event_date + pd.Timedelta(days=i)
                mask = normalized_index == post_date
                if mask.any():
                    if i == 1:
                        features.loc[mask, 'post_event_1d'] = 1
                    elif i == 2:
                        features.loc[mask, 'post_event_2d'] = 1
                    elif i == 3:
                        features.loc[mask, 'post_event_3d'] = 1
        
        return features
    
    def create_comprehensive_features(
        self,
        price_data: pd.DataFrame,
        economic_data: pd.DataFrame,
        announcement_times: List[datetime] = None
    ) -> pd.DataFrame:
        """
        Create comprehensive feature set for analysis.
        
        Args:
            price_data: DataFrame with price data
            economic_data: DataFrame with economic indicators
            announcement_times: List of announcement times
            
        Returns:
            DataFrame with all features
        """
        self.logger.info("Starting comprehensive feature creation...")
        all_features = pd.DataFrame(index=price_data.index)
        
        # Return features
        self.logger.info("Creating return features...")
        return_features = self.create_return_features(price_data)
        all_features = all_features.join(return_features, how='outer')
        self.logger.info(f"Added {len(return_features.columns)} return features")
        
        # Volatility features  
        self.logger.info("Creating volatility features...")
        returns_data = pd.DataFrame()
        for col in price_data.columns:
            returns_data[col] = np.log(price_data[col] / price_data[col].shift(1))
        
        volatility_features = self.create_volatility_features(returns_data)
        all_features = all_features.join(volatility_features, how='outer')
        self.logger.info(f"Added {len(volatility_features.columns)} volatility features")
        
        # Surprise features
        self.logger.info("Creating economic surprise features...")
        surprise_features = self.create_surprise_measures(economic_data)
        all_features = all_features.join(surprise_features, how='outer')
        self.logger.info(f"Added {len(surprise_features.columns)} surprise features")
        
        # Market regime features
        self.logger.info("Creating market regime features...")
        regime_features = self.create_market_regime_features(price_data)
        all_features = all_features.join(regime_features, how='outer')
        self.logger.info(f"Added {len(regime_features.columns)} regime features")
        
        # Interaction features
        self.logger.info("Creating interaction features...")
        interaction_features = self.create_interaction_features(surprise_features, regime_features)
        all_features = all_features.join(interaction_features, how='outer')
        self.logger.info(f"Added {len(interaction_features.columns)} interaction features")
        
        # Event window features
        if announcement_times:
            self.logger.info(f"Creating event window features for {len(announcement_times)} events...")
            event_features = self.create_event_window_features(all_features, announcement_times)
            all_features = all_features.join(event_features, how='outer')
            self.logger.info(f"Added {len(event_features.columns)} event window features")
        else:
            self.logger.info("No announcement times provided, skipping event window features")
        
        # Log feature summary
        total_features = len(all_features.columns)
        self.logger.info(f"[SUCCESS] Comprehensive feature creation completed!")
        self.logger.info(f"[INFO] Total features created: {total_features}")
        self.logger.info(f"[INFO] Date range: {all_features.index[0]} to {all_features.index[-1]}")
        self.logger.info(f"[INFO] Data points: {len(all_features)}")
        
        # Log feature categories
        feature_categories = {
            'Return': len([col for col in all_features.columns if 'return' in col.lower()]),
            'Volatility': len([col for col in all_features.columns if 'volatility' in col.lower() or 'vol' in col.lower()]),
            'Surprise': len([col for col in all_features.columns if 'surprise' in col.lower()]),
            'Regime': len([col for col in all_features.columns if 'regime' in col.lower()]),
            'Interaction': len([col for col in all_features.columns if '_x_' in col.lower()]),
            'Event': len([col for col in all_features.columns if 'event' in col.lower()])
        }
        
        self.logger.info("[INFO] Feature breakdown by category:")
        for category, count in feature_categories.items():
            self.logger.info(f"   - {category}: {count} features")
        
        return all_features
    
    def create_analysis_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create analysis features from cleaned data.
        
        Args:
            data: Cleaned DataFrame with price and economic data
            
        Returns:
            DataFrame with engineered features
        """
        self.logger.info("=" * 50)
        self.logger.info("STARTING FEATURE ENGINEERING PROCESS")
        self.logger.info("=" * 50)
        
        self.logger.info(f"Input data shape: {data.shape}")
        self.logger.info(f"Input date range: {data.index[0]} to {data.index[-1]}")
        
        # Separate price and economic data
        exclusion_tokens = ['_return', '_volatility', 'surprise', '_lag', 'dummy']
        price_prefixes = ('stocks_', 'crypto_', 'volatility_', 'fixed_income_')
        price_columns = [
            col for col in data.columns
            if (col.startswith(price_prefixes) or any(token in col.lower() for token in ['btc', 'eth', 'spy', 'qqq']))
            and not any(token in col.lower() for token in exclusion_tokens)
        ]
        economic_columns = [col for col in data.columns if col.startswith('economic_')]
        
        price_data = data[price_columns] if price_columns else pd.DataFrame(index=data.index)
        economic_data = data[economic_columns] if economic_columns else pd.DataFrame(index=data.index)
        
        self.logger.info(f"Identified {len(price_columns)} price columns and {len(economic_columns)} economic columns")
        self.logger.debug(f"Price columns: {price_columns[:5]}{'...' if len(price_columns) > 5 else ''}")
        self.logger.debug(f"Economic columns: {economic_columns[:5]}{'...' if len(economic_columns) > 5 else ''}")
        
        # Create comprehensive features
        if not price_data.empty:
            self.logger.info("Creating comprehensive features from price and economic data...")
            features = self.create_comprehensive_features(
                price_data=price_data,
                economic_data=economic_data,
                announcement_times=None  # Could be enhanced to include actual announcement times
            )
        else:
            # If no price data, just create surprise measures from economic data
            self.logger.warning("No price data found, creating features from economic data only...")
            features = self.create_surprise_measures(economic_data)
        
        self.logger.info("=" * 50)
        self.logger.info("FEATURE ENGINEERING COMPLETED")
        self.logger.info("=" * 50)
        self.logger.info(f"Final feature set: {features.shape}")
        self.logger.info(f"Features created: {features.columns.tolist()[:10]}{'...' if len(features.columns) > 10 else ''}")
        
        return features