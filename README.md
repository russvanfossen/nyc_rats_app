# 🐀 NYC Failed Rat Inspections Map
 
A Streamlit app that maps recent failed rat inspections in New York City, using live data from [NYC Open Data](https://data.cityofnewyork.us/) (dataset `p937-wjvj`).
 
## Features
 
- Interactive Folium map with clustered 🐀 markers; click a marker for the address, result and date
- Sidebar slider to choose how many days back to look (7–90)
- Borough filter
- Summary counts and a raw data table
- API and token check on startup, with a clear error if NYC Open Data is down or the token is rejected
