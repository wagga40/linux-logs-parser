# Linux Logs Parser (LLP)

## Introduction

**IMPORTANT** : If you have syslog.log or auth.log files coming from a Linux system, you are at the right place. If the systems you are getting logs from have `journald`, **do not use LLP and do this instead** : `journalctl --output=json`.

Linux Logs Parser is a tool designed to parse various log formats found in Linux systems. Utilizing the power of the `pyparsing` library, it can, by default, parse logs from syslog, auth.log, and other files related to user and group management activities. The parser supports multiple timestamp formats and can easily be modified to handle more.

**Please note that this is a Work In Progress**

## Installation

Before installing Linux Logs Parser, ensure you have Python 3.8 or newer installed on your system. 

To install the tool :

1. Clone the repository:
   ```sh
   git clone https://github.com/wagga40/linux-logs-parser.git
   ```
2. Navigate to the cloned directory:
   ```sh
   cd linux-logs-parser
   ```
3. (Optional) Create and activate a virtual environment:
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

To parse a log file with Linux Logs Parser, run the following command:

```sh
python log_parser.py -l /path/to/your/logfile.log -o /path/to/output/parsed.jsonl
```

### Command Line Arguments
- `-l`, `--logs`: Specifies the path to the log file to be parsed (required)
- `-o`, `--output`: Specifies the path to the output file where parsed logs will be saved (default: `parsed.jsonl`)
- `-c`, `--config`: Specifies the path to the config file (default: `config.yml`)
- `-v`, `--verbose`: Enables verbose output (optional).

## Contributing
We welcome contributions to the Linux Logs Parser project! If you have suggestions for improvements, please open an issue or submit a pull request.

## License
This project is licensed under the MIT License.
