# StorageIOAnalyzer

Storage IO Analyzer is a Python-based tool with a QT interface designed to analyze and visualize storage I/O operations. This tool helps in understanding and optimizing storage performance by providing detailed insights into I/O patterns and behaviors, particularly focused on NAND-based storage systems.

**Note: This is a preliminary version of the tool. For inquiries or support, please contact sanghune.jung@gmail.com.**

## Features

- Simulation of host and NAND operations timing
- Analysis of bandwidth and latency in storage systems
- Calculation of Die operation overhead based on tR and Data Out (TLC standards)
- Simulation of host queue patterns and operation timing
- LRU-based Read buffer cache hit determination
- Customizable parameters for various storage configurations

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- PyQt5

### Steps

1. Clone the repository:
   ```
   git clone https://github.com/sanghunejung/StorageIOAnalyzer.git
   cd StorageIOAnalyzer
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

## Usage

1. Launch the application by running `main.py`.
2. Configure the simulation parameters in the GUI:
   - Set NAND and host operation timings
   - Adjust queue depths and patterns
   - Configure cache sizes and LRU parameters
3. Start the simulation and observe real-time results.
4. Analyze the output data for insights on storage system performance.

## Contributing

As this is a preliminary version, we are not actively seeking contributions at this time. However, feedback and suggestions are welcome. Please contact sanghune.jung@gmail.com with any ideas or issues.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For any questions, issues, or support needs, please email " "  As this is a preliminary version, we appreciate your patience and feedback as we continue to improve the tool.

## Acknowledgments

- This tool was developed as part of research into optimizing ZNS (Zoned Namespace) SSD performance.
- Special thanks to all contributors and researchers in the field of storage systems optimization.

## Disclaimer

This is a preliminary version of the Storage IO Analyzer. Features may be incomplete or subject to change. Use at your own discretion and please report any issues or suggestions to the email provided above.
```
