"""
Chart generation module for financial data visualization
"""
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime


def create_ma_crossover_chart(symbol, data, crossover_type, crossover_date, save_path=None):
    """
    Create a chart showing price action and moving average crossover
    
    Args:
        symbol (str): Stock symbol
        data (pd.DataFrame): Historical data with MA_50, MA_200 columns
        crossover_type (str): 'golden_cross' or 'death_cross'
        crossover_date (str): Date of crossover
        save_path (str, optional): Path to save chart
    
    Returns:
        str: Path to saved chart or None if error
    """
    try:
        # Set up the plot
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Get recent data (last 100 days for clarity)
        recent_data = data.tail(100).copy()
        
        # Convert date index to datetime for plotting
        dates = recent_data.index
        
        # Plot the price line
        ax.plot(dates, recent_data['Close'], 
                label=f'{symbol} Price', 
                color='white', 
                linewidth=2, 
                alpha=0.9)
        
        # Plot moving averages - dynamically detect MA columns
        ma_columns = [col for col in recent_data.columns if col.startswith('MA_')]
        ma_periods = [int(col.split('_')[1]) for col in ma_columns]
        ma_periods.sort()
        
        if len(ma_periods) >= 2:
            short_period = ma_periods[0]
            long_period = ma_periods[-1]
            
            ax.plot(dates, recent_data[f'MA_{short_period}'], 
                    label=f'{short_period}-day MA', 
                    color='orange', 
                    linewidth=2, 
                    alpha=0.8)
            
            ax.plot(dates, recent_data[f'MA_{long_period}'], 
                    label=f'{long_period}-day MA', 
                    color='blue', 
                    linewidth=2, 
                    alpha=0.8)
        else:
            # Fallback to hardcoded if no MA columns found
            ax.plot(dates, recent_data.get('MA_50', recent_data['Close']), 
                    label='50-day MA', 
                    color='orange', 
                    linewidth=2, 
                    alpha=0.8)
            
            ax.plot(dates, recent_data.get('MA_200', recent_data['Close']), 
                    label='200-day MA', 
                    color='blue', 
                    linewidth=2, 
                    alpha=0.8)
        
        # Highlight crossover point
        if crossover_date:
            try:
                crossover_idx = pd.to_datetime(crossover_date)
                if crossover_idx in recent_data.index:
                    crossover_price = recent_data.loc[crossover_idx, 'Close']
                    
                    # Add crossover marker
                    if crossover_type == 'golden_cross':
                        ax.scatter(crossover_idx, crossover_price, 
                                 color='gold', s=200, marker='*', 
                                 label='Golden Cross', zorder=5)
                        ax.annotate('🌟 Golden Cross', 
                                  xy=(crossover_idx, crossover_price),
                                  xytext=(10, 10), textcoords='offset points',
                                  bbox=dict(boxstyle='round,pad=0.3', facecolor='gold', alpha=0.7),
                                  arrowprops=dict(arrowstyle='->', color='gold'),
                                  fontsize=10, fontweight='bold')
                    else:  # death_cross
                        ax.scatter(crossover_idx, crossover_price, 
                                 color='red', s=200, marker='X', 
                                 label='Death Cross', zorder=5)
                        ax.annotate('💀 Death Cross', 
                                  xy=(crossover_idx, crossover_price),
                                  xytext=(10, 10), textcoords='offset points',
                                  bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7),
                                  arrowprops=dict(arrowstyle='->', color='red'),
                                  fontsize=10, fontweight='bold')
            except Exception as e:
                print(f"⚠️ Could not highlight crossover point: {e}")
        
        # Fill area between MAs to show trend - use dynamic periods
        if len(ma_periods) >= 2:
            short_ma_values = recent_data[f'MA_{short_period}'].values
            long_ma_values = recent_data[f'MA_{long_period}'].values
            
            # Fill green when short MA > long MA (bullish), red when short MA < long MA (bearish)
            ax.fill_between(dates, short_ma_values, long_ma_values,
                           where=(short_ma_values >= long_ma_values),
                           color='green', alpha=0.2, interpolate=True, label='Bullish Zone')
            
            ax.fill_between(dates, short_ma_values, long_ma_values,
                           where=(short_ma_values < long_ma_values),
                           color='red', alpha=0.2, interpolate=True, label='Bearish Zone')
        
        # Format the chart
        ax.set_title(f'{symbol} - Moving Average Crossover Analysis', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Price ($)', fontsize=12)
        
        # Format dates on x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.xticks(rotation=45)
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Add legend
        ax.legend(loc='upper left', framealpha=0.9)
        
        # Add current values text box - use dynamic periods
        current_price = recent_data['Close'].iloc[-1]
        
        if len(ma_periods) >= 2:
            current_short_ma = recent_data[f'MA_{short_period}'].iloc[-1]
            current_long_ma = recent_data[f'MA_{long_period}'].iloc[-1]
            info_text = f"Current Price: ${current_price:.2f}\n{short_period}-day MA: ${current_short_ma:.2f}\n{long_period}-day MA: ${current_long_ma:.2f}"
        else:
            # Fallback
            info_text = f"Current Price: ${current_price:.2f}\nMA data not available"
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
                verticalalignment='top', fontsize=10,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.8))
        
        # Tight layout to prevent label cutoff
        plt.tight_layout()
        
        # Save the chart
        if save_path is None:
            save_path = f'{symbol}_ma_crossover_{crossover_type}.png'
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                   facecolor='black', edgecolor='none')
        plt.close()  # Close the figure to free memory
        
        print(f"📊 Chart saved: {save_path}")
        return save_path
        
    except Exception as e:
        print(f"❌ Error creating chart: {e}")
        plt.close()  # Make sure to close figure even on error
        return None


def create_price_trend_chart(symbol, data, title="Price Trend", save_path=None):
    """
    Create a basic price trend chart
    
    Args:
        symbol (str): Stock symbol
        data (pd.DataFrame): Historical data with Close column
        title (str): Chart title
        save_path (str, optional): Path to save chart
    
    Returns:
        str: Path to saved chart or None if error
    """
    try:
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot price
        ax.plot(data.index, data['Close'], 
                color='cyan', linewidth=2, label=f'{symbol} Price')
        
        # Format chart
        ax.set_title(f'{symbol} - {title}', fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Price ($)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Format dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save chart
        if save_path is None:
            save_path = f'{symbol}_price_trend.png'
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight',
                   facecolor='black', edgecolor='none')
        plt.close()
        
        print(f"📊 Price chart saved: {save_path}")
        return save_path
        
    except Exception as e:
        print(f"❌ Error creating price chart: {e}")
        plt.close()
        return None