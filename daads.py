import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import dateutil
import matplotlib.dates as mdates
import DatastreamPy as dsweb
import pandas as pd

# Initialize Datastream
ds = dsweb.DataClient(None, 'jiachen.tian@allianz-trade.com', 'Sunmeiqing414516!')

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

@st.cache
def fetch_data(commodity_name, item_list, time_range):
    # Determine the start date based on the selected time range
    time_map = {
        '1Y': '-1Y',
        '2Y': '-2Y',
        '3Y': '-3Y',
        '5Y': '-5Y'
    }
    start_date = time_map.get(time_range, '-1Y')  # Default to 1Y if invalid
    today_str = pd.Timestamp.today().strftime('%Y-%m-%d')
    # Fetch data for the selected time range
    df = ds.get_data(tickers=",".join(item_list), start=start_date, end=today_str)

    
    
    # Fetch static data
    static_data = ds.get_data(tickers=",".join(item_list), fields=list(summary_fields.keys()), kind=0)
    static_data = static_data.pivot(index='Instrument', columns='Datatype')["Value"]
    static_data = static_data[list(summary_fields.keys())].rename(columns=summary_fields)
    
    return static_data, df

def plot_commodity_data(name, static_data, df):
    fig, axs = plt.subplots(nrows=4, ncols=3, figsize=(20, 20))
    plt.subplots_adjust(hspace=0.5, wspace=0.3)

    for index in range(df.shape[1]):
        ax = axs[int(index/3), int(index%3)]

        # ⬇️ Work per series to avoid NaN issues
        s = df.iloc[:, index].dropna()
        if s.empty:
            ax.set_title("No recent data")
            ax.axis('off')
            continue

        X = mdates.date2num(pd.to_datetime(s.index))
        y = s.values

        # Safe title lookup (works whether the column name is a tuple or a string)
        name_key = s.name[0] if isinstance(s.name, (list, tuple)) else s.name
        title = static_data.loc[name_key]['Name'] if (name_key in static_data.index and 'Name' in static_data.columns) else str(name_key)

        # Trendline only if enough points
        if len(s) >= 2:
            z = np.polyfit(X, y, 1)
            p = np.poly1d(z)
            ax.plot(X, p(X), "r--")

        ax.plot(X, y)
        loc = mdates.AutoDateLocator()
        years_fmt = mdates.DateFormatter('%Y-%m')
        ax.set_title(title)
        ax.xaxis.set_major_formatter(years_fmt)
        ax.xaxis.set_minor_locator(mdates.MonthLocator())
        ax.xaxis.set_major_locator(loc)
        for tick in ax.get_xticklabels():
            tick.set_rotation(45)

    st.pyplot(fig)
    st.dataframe(static_data)


# Streamlit app
st.title('Commodity Overview Dashboard')

commodity_options = list(commodities.keys())
selected_commodity = st.selectbox('Select a commodity category', commodity_options)

# Time range selection
time_range = st.selectbox('Select time range', ['1Y', '2Y', '3Y', '5Y'])

if selected_commodity:
    static_data, df = fetch_data(selected_commodity, commodities[selected_commodity]['Items'], time_range)
    st.header(f'{selected_commodity} Data Overview ({time_range})')
    plot_commodity_data(selected_commodity, static_data, df)
