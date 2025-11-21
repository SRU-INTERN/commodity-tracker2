import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import DatastreamPy as dsweb
import pandas as pd

# Initialize Datastream
DS_USERNAME = "jiachen.tian@allianz-trade.com"
DS_PASSWORD = "Sunmeiqing414516!"
username = st.secrets["DS_USERNAME"]
password = st.secrets["DS_PASSWORD"]
ds = dsweb.DataClient(None, username, password)

summary_fields = {
    'NAME':'Name',
    'PCH#(X,-1M)':'(%) Change',
    'X':'Current',
    'VAL#(X,-1M)':'Previous',
    'MAX#(X,-1Y)':'1 Year High',
    'MAXD#(X,-1Y)':'High Date',
    'MIN#(X,-1Y)':'1 Year Low',
    'MIND#(X,-1Y)':'Low Date'
}

commodities = {
    'Metals': {
        'Items': ['GOLDBLN','SILVERH','PLATFRE','LAHCASH', 'LCPCASH','LEDCASH','LNICASH','LTICASH','LZZCASH','SHCNI62','SHCNI58','SGPDTOT'],
        'Fields': summary_fields
    },
    'Energy': {
        'Items': ['OILBREN','OILWTXI', 'GASUREG','DIESELA','JETCNWE','FUELOIL','GOTTYOS','NAFCNWE','NATBGAS','LMCYSPT','EEXPEAK','ES15PSN'],
        'Fields': summary_fields
    },
    'Chemicals': {
        'Items': ['OLETFPU','OLPRNPU','ARSYUPU','VPVCUPU','PFHPEPU','PFPCOPU','STGPDPU','ABSCAUP','OLBUUPU','UREAGRN','DAPNOCB','ETHANYH'],
        'Fields': summary_fields
    },
    'Agriculture': {
        'Items': ['WHEATSF','CORNUS2','COCINUS','COTTONM','SOYBEAN','CLHINDX','USTEERS','MILKGDA','CFCNCLC','CLCNRLC','WOLAWCE','SPG2LHS'],
        'Fields': summary_fields
    },
    'Indices': {
        'Items': ['GSCITOT','DJUBSTR','RICIXTR','MLCXTOT','CRBSPOT','CXCMTRE','BALTICF','LMEINDX','DRAMDXI','DBKLCIX','MSWDCY$','RJEFCRT'],
        'Fields': summary_fields
    },
    'SemiConductors & Other Commodities': {
        'Items': ['SILFEEU','FMS32GB','FSS16GB','FSS08GB','FMS64GB','TUNGSFE','RUBBSMR','PLPLPBL','MLRIC2S','CTJOP3M','EIANYHO','SPGSLTU'],
        'Fields': summary_fields
    }
}

@st.cache_data(ttl=600)
def fetch_data(commodity_name, item_list, time_range):
    # Determine the start date based on the selected time range
    time_map = {
        '1Y': '-1Y',
        '2Y': '-2Y',
        '3Y': '-3Y',
        '5Y': '-5Y'
    }
    start_date = time_map.get(time_range, '-1Y')  # Default to 1Y

    # Fetch time series data
    df = ds.get_data(tickers=",".join(item_list), start=start_date, kind=1)

    # Fetch static snapshot
    static_data = ds.get_data(tickers=",".join(item_list), fields=list(summary_fields.keys()), kind=0)
    static_data = static_data.pivot(index='Instrument', columns='Datatype', values='Value')
    present_fields = [f for f in summary_fields.keys() if f in static_data.columns]
    static_data = static_data[present_fields].rename(columns=summary_fields)

    return static_data, df  # <- return 对齐函数体

def plot_commodity_data(name, static_data, df):
    import math
    n_items = df.shape[1]
    ncols = 3
    nrows = math.ceil(n_items / ncols)

    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(5*ncols, 3*nrows), squeeze=False)
    plt.subplots_adjust(hspace=0.5, wspace=0.3)

    for index in range(n_items):
        row, col = divmod(index, ncols)
        ax = axs[row][col]

        s = df.iloc[:, index].dropna()
        if s.empty:
            ax.set_title("No recent data")
            ax.axis('off')
            continue

        X = mdates.date2num(pd.to_datetime(s.index))
        y = s.values

        # Safe title lookup
        name_key = s.name[0] if isinstance(s.name, (list, tuple)) else s.name
        if name_key in static_data.index and 'Name' in static_data.columns:
            title = static_data.loc[name_key]['Name']
        else:
            title = str(name_key)

        # Trend line
        if len(s) >= 2:
            z = np.polyfit(X, y, 1)
            p = np.poly1d(z)
            ax.plot_date(mdates.num2date(X), p(X), linestyle='--', marker=None)

        ax.plot_date(mdates.num2date(X), y, linestyle='-', marker=None)
        ax.set_title(title)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_minor_locator(mdates.MonthLocator())
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        for tick in ax.get_xticklabels():
            tick.set_rotation(45)

    # Hide empty subplots
    total_slots = nrows * ncols
    for extra in range(n_items, total_slots):
        row, col = divmod(extra, ncols)
        axs[row][col].axis('off')

    st.pyplot(fig)
    st.dataframe(static_data)


# Streamlit UI
st.title('Commodity Overview Dashboard')

commodity_options = list(commodities.keys())
selected_commodity = st.selectbox('Select a commodity category', commodity_options)

time_range = st.selectbox('Select time range', ['1Y', '2Y', '3Y', '5Y'])

if selected_commodity:
    static_data, df = fetch_data(selected_commodity, commodities[selected_commodity]['Items'], time_range)
    st.header(f'{selected_commodity} Data Overview ({time_range})')
    plot_commodity_data(selected_commodity, static_data, df)
