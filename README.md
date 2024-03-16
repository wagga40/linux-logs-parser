# Linux Logs Parser (LLP)

## Introduction

**IMPORTANT** : If you have syslog.log or auth.log files coming from a Linux system, you are at the right place. If the systems you are getting logs from have `journald`, **do not use LLP and do this instead** : `journalctl --output=json`.

Linux Logs Parser is a tool designed to parse various log formats found in Linux systems. Utilizing the power of the `pyparsing` library, it can, by default, parse logs from syslog, auth.log, and other files related to user and group management activities. The parser supports multiple timestamp formats and can easily be modified to handle more.

**Please note that this is a Work In Progress**

**Tested with :** auth.log and syslog.log

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
python3 llp.py -l /path/to/your/logfile.log -o /path/to/output/parsed.jsonl
```

## Example 

Auth.log : 

```log
Feb 10 16:25:26 ubuntu groupadd[324]: new group: name=lxd, GID=1000
Feb 10 16:25:26 ubuntu groupadd[330]: group added to /etc/gshadow: name=netdev
Feb 10 16:25:26 ubuntu useradd[336]: new group: name=ubuntu, GID=1002
Feb 10 16:25:26 ubuntu useradd[336]: new user: name=ubuntu, UID=1000, GID=1002, home=/home/ubuntu, shell=/bin/bash, from=none
Feb 10 16:25:26 ubuntu useradd[336]: add 'ubuntu' to group 'adm'
Feb 10 16:25:26 ubuntu useradd[336]: add 'ubuntu' to shadow group 'netdev'
Feb 10 16:25:26 ubuntu passwd[344]: password for 'ubuntu' changed by 'root'
Feb 10 16:26:15 ubuntu sudo:     root : PWD=/ ; USER=root ; COMMAND=/usr/sbin/usermod --shell /usr/bin/fish root
Feb 10 16:26:15 ubuntu sudo:     root : PWD=/ ; USER=root ; COMMAND=/usr/bin/wget https://raw.githubusercontent.com/oh-my-fish/oh-my-fish/master/bin/install -O install
````

From the CLI : 

```sh
python3 llp.py -l auth.log -o out.jsonl
```

Result : 

```json
{"timestamp": "2024-02-10T16:25:26+00:00", "hostname": "ubuntu", "appname": "groupadd", "pid": "324", "message": "new group: name=lxd, GID=1000", "Action": "new group", "Group": "lxd", "GID": "1000"}
{"timestamp": "2024-02-10T16:25:26+00:00", "hostname": "ubuntu", "appname": "groupadd", "pid": "330", "message": "group added to /etc/group: name=netdev, GID=1001", "Action": "added", "List": "/etc/group", "Group": "netdev", "GID": "1001"}
{"timestamp": "2024-02-10T16:25:26+00:00", "hostname": "ubuntu", "appname": "groupadd", "pid": "330", "message": "group added to /etc/gshadow: name=netdev", "Action": "added", "List": "/etc/gshadow", "Group": "netdev"}
{"timestamp": "2024-02-10T16:25:26+00:00", "hostname": "ubuntu", "appname": "useradd", "pid": "336", "message": "new group: name=ubuntu, GID=1002", "Action": "new group", "Group": "ubuntu", "GID": "1002"}
{"timestamp": "2024-02-10T16:25:26+00:00", "hostname": "ubuntu", "appname": "useradd", "pid": "336", "message": "new user: name=ubuntu, UID=1000, GID=1002, home=/home/ubuntu, shell=/bin/bash, from=none", "Action": "new user", "Username": "ubuntu", "UID": "1000", "GID": "1002", "Home": "/home/ubuntu", "Shell": "/bin/bash", "From": "none"}
{"timestamp": "2024-02-10T16:25:26+00:00", "hostname": "ubuntu", "appname": "useradd", "pid": "336", "message": "add 'ubuntu' to group 'adm'", "Action": "add", "Username": "ubuntu", "Group": "adm"}
{"timestamp": "2024-02-10T16:25:26+00:00", "hostname": "ubuntu", "appname": "useradd", "pid": "336", "message": "add 'ubuntu' to shadow group 'netdev'", "Action": "add", "Username": "ubuntu", "Type": "shadow", "Group": "netdev"}
{"timestamp": "2024-02-10T16:25:26+00:00", "hostname": "ubuntu", "appname": "passwd", "pid": "344", "message": "password for 'ubuntu' changed by 'root'", "Username": "ubuntu", "Action": "changed", "By": "root"}
{"timestamp": "2024-02-10T16:26:15+00:00", "hostname": "ubuntu", "appname": "sudo", "pid": "", "message": "root : PWD=/ ; USER=root ; COMMAND=/usr/sbin/usermod --shell /usr/bin/fish root", "User": "root", "PWD": "/", "Username": "root", "CommandLine": "/usr/sbin/usermod --shell /usr/bin/fish root"}
{"timestamp": "2024-02-10T16:26:15+00:00", "hostname": "ubuntu", "appname": "sudo", "pid": "", "message": "root : PWD=/ ; USER=root ; COMMAND=/usr/bin/wget https://raw.githubusercontent.com/oh-my-fish/oh-my-fish/master/bin/install -O install", "User": "root", "PWD": "/", "Username": "root", "CommandLine": "/usr/bin/wget https://raw.githubusercontent.com/oh-my-fish/oh-my-fish/master/bin/install -O install"}
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
