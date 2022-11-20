from io import BytesIO
import base64
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import pandas as pd


def fig_to_svg(fig):
    buf = BytesIO()
    fig.savefig(buf, format="svg")
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"<img src='data:image/svg+xml;base64,{data}'/>"


def make_nice_plot(dates, values):
    fig = Figure()
    ax = fig.subplots()

    myFmt = mdates.DateFormatter('%b %d')
    ax.xaxis.set_major_formatter(myFmt)
    ax.plot(dates, values, '-o')
    return fig_to_svg(fig)


def make_nice_html_table(df):
    df = df.set_index('split_group')
    df = df.T
    styler = df.style.format("{:.2%}", subset=pd.IndexSlice['buyers_prcnt', :])
    styler.format("${:.2f}", subset=pd.IndexSlice[['arpu', 'gross_usd'], :])
    styler.format('{:0,.0f}', subset=pd.IndexSlice[['registered_users', 'orders_count'], :])

    return styler.to_html(table_attributes='border=1')
