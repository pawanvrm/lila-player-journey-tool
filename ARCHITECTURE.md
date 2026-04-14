# Architecture

## Data Flow
Parquet files → DuckDB → Pandas → Streamlit UI → Plotly Visualization

## Components
- DuckDB: Reads parquet data efficiently
- Pandas: Data cleaning and transformation
- Streamlit: UI and interaction
- Plotly: Visualization (movement, events, heatmap)

## Filtering Logic
Map → Match → Player filtering hierarchy

## Coordinate Mapping
World coordinates are normalized to minimap size using min-max scaling.
Y-axis is flipped to align with image coordinate system.

## Design Decisions
- Lightweight architecture for fast development
- No backend server required
- Focused on usability for Level Designers

## Trade-offs
- Used approximate coordinate mapping instead of exact calibration
- No real-time data streaming

## Future Improvements
- Accurate coordinate mapping using map metadata
- Multi-match comparison
- Real-time analytics