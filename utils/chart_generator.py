import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import io
import base64
from datetime import datetime, timedelta

class ChartGenerator:
    """
    A utility class for generating chart images for reports
    """
    
    def __init__(self, alphavantage_tool=None):
        """
        Initialize the chart generator
        
        Args:
            alphavantage_tool (AlphaVantageData, optional): AlphaVantage data source
        """
        self.alphavantage_tool = alphavantage_tool
        self.plt_style = 'ggplot'
        plt.style.use(self.plt_style)
    
    def _fig_to_base64(self, fig):
        """
        Convert a matplotlib figure to a base64 encoded string
        
        Args:
            fig (matplotlib.figure.Figure): Figure to convert
            
        Returns:
            str: Base64 encoded PNG image
        """
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close(fig)
        return f"data:image/png;base64,{image_base64}"
    
    def candlestick_chart(self, data, title="", timeframe="Daily", show_volume=False):
        """
        Generate a candlestick chart
        
        Args:
            data (pandas.DataFrame): DataFrame with OHLC data
            title (str): Chart title
            timeframe (str): Timeframe description
            show_volume (bool): Whether to show volume
            
        Returns:
            str: Base64 encoded PNG image
        """
        if not isinstance(data, pd.DataFrame) or data.empty:
            return None
            
        # Create figure and axis
        if show_volume and 'volume' in data.columns:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
        else:
            fig, ax1 = plt.subplots(figsize=(10, 6))
        
        # Format dates on x-axis
        if timeframe.lower() in ['daily', 'weekly']:
            date_format = mdates.DateFormatter('%Y-%m-%d')
            major_locator = mdates.WeekdayLocator(interval=1)
        else:  # intraday
            date_format = mdates.DateFormatter('%m-%d %H:%M')
            major_locator = mdates.HourLocator(interval=4)
        
        ax1.xaxis.set_major_formatter(date_format)
        ax1.xaxis.set_major_locator(major_locator)
        
        # Calculate the width of each candlestick
        dates = data.index
        width = 0.6
        if len(dates) > 1:
            width = 0.6 * (dates[1] - dates[0]).total_seconds() / 86400  # width in days
        
        # Plot the candlesticks
        up = data[data['close'] >= data['open']]
        down = data[data['close'] < data['open']]
        
        # Plot up candles
        ax1.bar(up.index, up['high'] - up['low'], width, bottom=up['low'], color='green', alpha=0.5)
        ax1.bar(up.index, up['close'] - up['open'], width, bottom=up['open'], color='green')
        
        # Plot down candles
        ax1.bar(down.index, down['high'] - down['low'], width, bottom=down['low'], color='red', alpha=0.5)
        ax1.bar(down.index, down['open'] - down['close'], width, bottom=down['close'], color='red')
        
        # Add moving averages if there are enough data points
        if len(data) >= 20:
            data['MA20'] = data['close'].rolling(window=20).mean()
            ax1.plot(data.index, data['MA20'], color='blue', linewidth=1.5, label='20-period MA')
            
            if len(data) >= 50:
                data['MA50'] = data['close'].rolling(window=50).mean()
                ax1.plot(data.index, data['MA50'], color='orange', linewidth=1.5, label='50-period MA')
                
            ax1.legend(loc='upper left')
        
        # Add volume subplot if requested and available
        if show_volume and 'volume' in data.columns and 'ax2' in locals():
            ax2.bar(up.index, up['volume'], width, color='green', alpha=0.5)
            ax2.bar(down.index, down['volume'], width, color='red', alpha=0.5)
            ax2.set_ylabel('Volume')
            
            # Add volume moving average
            if len(data) >= 20:
                data['VolMA20'] = data['volume'].rolling(window=20).mean()
                ax2.plot(data.index, data['VolMA20'], color='blue', linewidth=1.5)
        
        # Add title and labels
        full_title = f"{title} - {timeframe} Chart"
        ax1.set_title(full_title)
        ax1.set_ylabel('Price')
        ax1.grid(True, alpha=0.3)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def generate_daily_chart(self, from_currency="EUR", to_currency="USD", days=60):
        """
        Generate a daily candlestick chart for a currency pair
        
        Args:
            from_currency (str): Base currency
            to_currency (str): Quote currency
            days (int): Number of days to show
            
        Returns:
            str: Base64 encoded PNG image
        """
        if not self.alphavantage_tool:
            return None
            
        try:
            # Get daily data
            daily_data = self.alphavantage_tool.get_daily_forex(from_currency, to_currency, "full")
            
            if 'error' in daily_data.columns:
                return None
                
            # Filter to the requested number of days
            daily_data = daily_data.iloc[-days:]
            
            # Generate the chart
            title = f"{from_currency}/{to_currency}"
            return self.candlestick_chart(daily_data, title, "Daily")
            
        except Exception as e:
            print(f"Error generating daily chart: {e}")
            return None
    
    def generate_intraday_chart(self, from_currency="EUR", to_currency="USD", interval="30min", periods=48):
        """
        Generate an intraday candlestick chart for a currency pair
        
        Args:
            from_currency (str): Base currency
            to_currency (str): Quote currency
            interval (str): Time interval (1min, 5min, 15min, 30min, 60min)
            periods (int): Number of periods to show
            
        Returns:
            str: Base64 encoded PNG image
        """
        if not self.alphavantage_tool:
            return None
            
        try:
            # Get intraday data
            intraday_data = self.alphavantage_tool.get_intraday_forex(from_currency, to_currency, interval, "full")
            
            if 'error' in intraday_data.columns:
                return None
                
            # Filter to the requested number of periods
            intraday_data = intraday_data.iloc[-periods:]
            
            # Generate the chart
            title = f"{from_currency}/{to_currency}"
            return self.candlestick_chart(intraday_data, title, interval)
            
        except Exception as e:
            print(f"Error generating intraday chart: {e}")
            return None
    
    def generate_key_levels_chart(self, from_currency="EUR", to_currency="USD", days=30, key_levels=None):
        """
        Generate a chart with key support and resistance levels
        
        Args:
            from_currency (str): Base currency
            to_currency (str): Quote currency
            days (int): Number of days to show
            key_levels (dict): Dictionary of key levels with labels
            
        Returns:
            str: Base64 encoded PNG image
        """
        if not self.alphavantage_tool:
            return None
            
        try:
            # Get daily data
            daily_data = self.alphavantage_tool.get_daily_forex(from_currency, to_currency, "full")
            
            if 'error' in daily_data.columns:
                return None
                
            # Filter to the requested number of days
            daily_data = daily_data.iloc[-days:]
            
            # Create the figure
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Format dates on x-axis
            date_format = mdates.DateFormatter('%Y-%m-%d')
            major_locator = mdates.WeekdayLocator(interval=1)
            ax.xaxis.set_major_formatter(date_format)
            ax.xaxis.set_major_locator(major_locator)
            
            # Calculate candlestick width
            dates = daily_data.index
            width = 0.6
            if len(dates) > 1:
                width = 0.6 * (dates[1] - dates[0]).total_seconds() / 86400
            
            # Plot the candlesticks
            up = daily_data[daily_data['close'] >= daily_data['open']]
            down = daily_data[daily_data['close'] < daily_data['open']]
            
            # Plot up candles
            ax.bar(up.index, up['high'] - up['low'], width, bottom=up['low'], color='green', alpha=0.5)
            ax.bar(up.index, up['close'] - up['open'], width, bottom=up['open'], color='green')
            
            # Plot down candles
            ax.bar(down.index, down['high'] - down['low'], width, bottom=down['low'], color='red', alpha=0.5)
            ax.bar(down.index, down['open'] - down['close'], width, bottom=down['close'], color='red')
            
            # Add key levels if provided
            if key_levels and isinstance(key_levels, dict):
                min_price = daily_data['low'].min()
                max_price = daily_data['high'].max()
                
                # Add some padding to the price range
                price_range = max_price - min_price
                padding = price_range * 0.1
                
                # Determine colors for different level types
                level_colors = {
                    'resistance': 'red',
                    'support': 'green',
                    'pivot': 'blue',
                    'weekly_high': 'purple',
                    'weekly_low': 'orange',
                    'daily_high': 'darkred',
                    'daily_low': 'darkgreen'
                }
                
                # Draw the levels
                for label, level in key_levels.items():
                    try:
                        price = float(level)
                        level_type = next((k for k in level_colors.keys() if k in label.lower()), 'pivot')
                        color = level_colors.get(level_type, 'gray')
                        
                        # Draw horizontal line
                        ax.axhline(y=price, color=color, linestyle='--', alpha=0.7)
                        
                        # Add label at the right side
                        ax.text(daily_data.index[-1], price, f" {label}: {price:.5f}", 
                                verticalalignment='center', horizontalalignment='left',
                                color=color, fontweight='bold', fontsize=8)
                    except (ValueError, TypeError):
                        # Skip invalid levels
                        pass
            
            # Add title and labels
            title = f"{from_currency}/{to_currency} - Key Levels"
            ax.set_title(title)
            ax.set_ylabel('Price')
            ax.grid(True, alpha=0.3)
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            print(f"Error generating key levels chart: {e}")
            return None
    
    def generate_weekly_profile_chart(self, from_currency="EUR", to_currency="USD", weeks=8):
        """
        Generate a chart showing weekly profile patterns
        
        Args:
            from_currency (str): Base currency
            to_currency (str): Quote currency
            weeks (int): Number of weeks to show
            
        Returns:
            str: Base64 encoded PNG image
        """
        if not self.alphavantage_tool:
            return None
            
        try:
            # Get daily data
            daily_data = self.alphavantage_tool.get_daily_forex(from_currency, to_currency, "full")
            
            if 'error' in daily_data.columns:
                return None
                
            # Calculate the number of days needed (weeks * 7)
            days_needed = weeks * 7
            
            # Filter to the requested number of days
            daily_data = daily_data.iloc[-days_needed:]
            
            # Create the figure
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Format dates on x-axis
            date_format = mdates.DateFormatter('%Y-%m-%d')
            major_locator = mdates.WeekdayLocator(interval=1)
            ax.xaxis.set_major_formatter(date_format)
            ax.xaxis.set_major_locator(major_locator)
            
            # Calculate candlestick width
            dates = daily_data.index
            width = 0.6
            if len(dates) > 1:
                width = 0.6 * (dates[1] - dates[0]).total_seconds() / 86400
            
            # Plot the candlesticks
            up = daily_data[daily_data['close'] >= daily_data['open']]
            down = daily_data[daily_data['close'] < daily_data['open']]
            
            # Plot up candles
            ax.bar(up.index, up['high'] - up['low'], width, bottom=up['low'], color='green', alpha=0.5)
            ax.bar(up.index, up['close'] - up['open'], width, bottom=up['open'], color='green')
            
            # Plot down candles
            ax.bar(down.index, down['high'] - down['low'], width, bottom=down['low'], color='red', alpha=0.5)
            ax.bar(down.index, down['open'] - down['close'], width, bottom=down['close'], color='red')
            
            # Add 20-day moving average
            if len(daily_data) >= 20:
                daily_data['MA20'] = daily_data['close'].rolling(window=20).mean()
                ax.plot(daily_data.index, daily_data['MA20'], color='blue', linewidth=1.5, label='20-day MA')
                ax.legend(loc='upper left')
            
            # Highlight weeks with different background colors
            # First, determine the start of each week
            daily_data['week_start'] = daily_data.index.to_series().dt.weekday
            week_starts = daily_data[daily_data['week_start'] == 0].index
            
            # Draw vertical lines at week boundaries
            for week_start in week_starts:
                ax.axvline(x=week_start, color='gray', linestyle='-', alpha=0.3)
            
            # Label the weeks
            for i, week_start in enumerate(week_starts):
                # Only label a subset of weeks to avoid crowding
                if i % 2 == 0:
                    week_label = f"Week {i+1}"
                    ax.text(week_start, daily_data['low'].min(), week_label, 
                            horizontalalignment='left', verticalalignment='bottom',
                            fontsize=8, rotation=90, alpha=0.7)
            
            # Add title and labels
            title = f"{from_currency}/{to_currency} - Weekly Profile"
            ax.set_title(title)
            ax.set_ylabel('Price')
            ax.grid(True, alpha=0.3)
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            return self._fig_to_base64(fig)
            
        except Exception as e:
            print(f"Error generating weekly profile chart: {e}")
            return None
    
    def generate_report_charts(self, from_currency="EUR", to_currency="USD"):
        """
        Generate a set of charts for a market report
        
        Args:
            from_currency (str): Base currency
            to_currency (str): Quote currency
            
        Returns:
            dict: Dictionary of chart images
        """
        if not self.alphavantage_tool:
            return None
            
        try:
            charts = {}
            
            # Generate daily chart (60 days)
            daily_chart = self.generate_daily_chart(from_currency, to_currency, 60)
            if daily_chart:
                charts['daily'] = daily_chart
            
            # Generate intraday charts (4 hours and 30 minutes)
            intraday_4h = self.generate_intraday_chart(from_currency, to_currency, "60min", 48)
            if intraday_4h:
                charts['intraday_4h'] = intraday_4h
                
            intraday_30m = self.generate_intraday_chart(from_currency, to_currency, "30min", 48)
            if intraday_30m:
                charts['intraday_30m'] = intraday_30m
            
            # Generate weekly profile chart
            weekly_chart = self.generate_weekly_profile_chart(from_currency, to_currency, 8)
            if weekly_chart:
                charts['weekly_profile'] = weekly_chart
            
            return charts
            
        except Exception as e:
            print(f"Error generating report charts: {e}")
            return None