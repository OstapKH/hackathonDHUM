# PluG2 Linguistic Corpus Explorer

A web-based dashboard for exploring the PluG2 Ukrainian linguistic corpus metadata using Dash and Plotly.

## Features

- **Interactive Visualizations**: Multiple chart types including temporal, demographic, and geographic analyses
- **Dynamic Filtering**: Filter data by genre, publication year, and other metadata fields
- **Real-time Statistics**: Overview cards showing key corpus statistics
- **Data Table**: Searchable and sortable table for detailed record exploration
- **Responsive Design**: Bootstrap-based UI that works on desktop and mobile devices

## Available Visualizations

1. **Publications by Year**: Timeline showing publication frequency over time
2. **Authors by Gender**: Pie chart of author gender distribution
3. **Genre Distribution**: Bar chart of most common literary genres
4. **Geographic Distribution**: Author locations by country
5. **Publication Cities**: Most frequent publication locations

## Prerequisites

- Python 3.7 or higher
- The `PluG2_metadata.psv` file in the project root directory

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Ensure the `PluG2_metadata.psv` file is in the same directory as `app.py`
2. Run the application:
   ```bash
   python app.py
   ```
3. Open your web browser and navigate to `http://localhost:8050`

## Interface Guide

### Statistics Cards
- **Total Records**: Total number of entries in the corpus
- **Unique Authors**: Number of distinct authors
- **Publication Years**: Range of years covered
- **Genres**: Number of different literary genres

### Controls
- **Visualization Type**: Choose from different chart types
- **Genre Filter**: Filter data by specific literary genres
- **Year Range**: Adjust the time period for analysis

### Interactive Features
- **Hover Effects**: Hover over chart elements for detailed information
- **Data Table**: Search, sort, and filter the raw data
- **Real-time Updates**: All visualizations update automatically when filters change

## Data Structure

The application expects a pipe-separated values (PSV) file with the following key columns:
- `Name`: Title of the work
- `Publication Year`: Year of publication
- `Genre Code`: Literary genre classification
- `Author 1 Name`: Primary author name
- `Author 1 Sex`: Author gender
- `Publication City`: City of publication
- Additional metadata fields for comprehensive analysis

## Technical Details

### Built With
- **Dash**: Web application framework
- **Plotly**: Interactive visualization library
- **Pandas**: Data manipulation and analysis
- **Bootstrap**: Responsive UI components

### Performance
- Optimized for large datasets with efficient data loading
- Lazy loading and caching for improved performance
- Error handling for robust operation

## Customization

The application can be easily extended with additional visualizations by:
1. Adding new options to the `chart-type-dropdown`
2. Implementing corresponding visualization logic in the `update_chart` callback
3. Adding new filtering options or controls as needed

## Troubleshooting

### Common Issues
1. **File not found**: Ensure `PluG2_metadata.psv` is in the correct directory
2. **Memory errors**: For very large datasets, consider implementing data sampling
3. **Port conflicts**: Change the port in `app.run_server()` if 8050 is in use

### Error Handling
The application includes comprehensive error handling for:
- Missing or corrupted data files
- Invalid data formats
- Memory limitations
- Network connectivity issues

## Contributing

To extend the application:
1. Add new visualization functions
2. Implement additional data processing features
3. Enhance the user interface with new controls
4. Add export functionality for charts and data

## License

This project is part of the PluG2 linguistic corpus research and follows the same licensing terms as the corpus data.
