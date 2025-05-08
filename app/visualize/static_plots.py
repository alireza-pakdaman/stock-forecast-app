import matplotlib.pyplot as plt, pandas as pd
def volume_plot(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10,3))
    ax.bar(df.index, df['volume'])
    ax.set_title('Volume Traded')
    return fig
