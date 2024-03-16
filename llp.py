import sys
import json
import argparse
from datetime import datetime
import rich.progress
from pyparsing import (
    Word,
    alphas,
    alphanums,
    Suppress,
    Combine,
    nums,
    string,
    Optional,
    Regex,
    printables,
    Literal,
    ZeroOrMore,
    pyparsing_common
)
import yaml 
from zoneinfo import ZoneInfo

class LogParser(object):
    """
    A class for parsing various log files.

    Args:
        configFile (str, optional): The path to the configuration file. Defaults to "config.yml".

    Attributes:
        fieldnames (dict): A dictionary containing the field names and their corresponding keys.
        syslogPattern (pyparsing.ParseResults): A pyparsing pattern for parsing syslog messages.
        sudo (pyparsing.ParseResults): A pyparsing pattern for parsing sudo messages.
        useradd (pyparsing.ParseResults): A pyparsing pattern for parsing useradd messages.
        groupadd (pyparsing.ParseResults): A pyparsing pattern for parsing groupadd messages.
        passwd (pyparsing.ParseResults): A pyparsing pattern for parsing passwd messages.
        userdel (pyparsing.ParseResults): A pyparsing pattern for parsing userdel messages.

    """
    def __init__(self, configFile="config.yml"):
        # Load fieldnames from config.yaml file
        fieldnames = self.load_config(configFile)

        # Helpers
        ints                        = Word(nums)
        GrammarUserOrGroupWithQuote = Suppress("'") + Word(alphas + nums + "_" + "-" + ".") + Suppress("'")
        GrammarGID                  = Combine(Suppress(Literal("GID=")) + ints)
        GrammarUserEquals           = Combine(Suppress(Literal("name=")) + Word(alphas + nums + "_" + "-" + "."))
        
        # SYSLOG        
        priority  = Optional(Suppress("<") + ints + Suppress(">"))
        month     = Word(string.ascii_uppercase, string.ascii_lowercase, exact=3)
        day       = ints
        hour      = Combine(ints + ":" + ints + ":" + ints)

        # Timestamps supported 
        # 1- Feb 10 16:25:26 -> the year is assumed to be the current one (datetime.now().year)
        # 2- 2024-02-01T17:23:45.446679+00:00
        timestamp = Combine((month + " " + Optional(" ") + day + " " + hour).set_parse_action(
            lambda t: datetime.strptime(
                str(datetime.now().year) + " " + " ".join(t), "%Y %b %d %H:%M:%S"
            )
            .replace(tzinfo=ZoneInfo("UTC"))
            .isoformat()
        )) | Combine(pyparsing_common.iso8601_datetime)

        hostname  = Word(alphas + nums + "_" + "-" + ".")
        appname   = Optional(
            Combine(
                Optional(Suppress("("))
                + Word(alphanums + "/" + "-" + "_" + ".")
                + Optional(Suppress(")"))
            )
        )
        pid = Combine(Optional(Suppress("[") + ints + Suppress("]")) + Suppress(":"))
        # message
        message = Regex(".*")
        # pattern build
        self.syslogPattern = (
            priority.set_results_name(fieldnames["priority"])
            + timestamp.set_results_name(fieldnames["timestamp"])
            + hostname.set_results_name(fieldnames["hostname"])
            + appname.set_results_name(fieldnames["appname"])
            + pid.set_results_name(fieldnames["pid"])
            + message.set_results_name(fieldnames["message"])
        )

        # SUDO / System-d login
        # Sample : 
        #     wagga : TTY=pts/1 ; PWD=/Users/wagga ; USER=root ; COMMAND=/usr/bin/ls -al
        sudo_user     = Combine(Word(printables) + Suppress(" ") + Suppress(":"))
        sudo_tty      = Combine(Suppress(Literal("TTY=")) + Word(printables))
        sudo_pwd      = Combine(Suppress(Literal("PWD=")) + Word(printables))
        sudo_username = Combine(Suppress(Literal("USER=")) + Word(printables))
        sudo_cmd      = Combine(Suppress(Literal("COMMAND=")) + Word(printables) + Regex(".*"))

        # Samples : 
        # pam_unix(sudo:session): session opened for user root(uid=0) by (uid=501)
        # pam_unix(sudo:session): session closed for user root
        # pam_unix(systemd-user:session): session opened for user wagga(uid=501) by (uid=0)
        sudo_origin   = Combine(Word(alphas + nums + "_" + "-" + "." + "(" + ")") + Literal(":") + Word(alphas + nums + "_" + "-" + "." + "(" + ")") + Suppress(Literal(":")))
        sudo_session  = Combine(Suppress(Literal("session")) + Suppress(" ") + (Literal("opened") | Literal("closed")))
        sudo_user_as2 = Combine(Suppress(Literal("for user")) + Suppress(" ") + Word(alphas + nums + "_" + "-" + "."))
        sudo_user_uid = Combine(Suppress(Word(printables) + Suppress(" ") + Literal("by")) + Suppress(" ") + Suppress("(") + Suppress(Literal("uid")) + Suppress("=") + ints + Suppress(")"))

        self.sudo = (
            sudo_user.set_results_name(fieldnames["User"])
            + Optional(sudo_tty.set_results_name(fieldnames["TTY"]) + Suppress(";"))
            + sudo_pwd.set_results_name(fieldnames["PWD"]) + Suppress(";")
            + sudo_username.set_results_name(fieldnames["Username"]) + Suppress(";")
            + sudo_cmd.set_results_name(fieldnames["CommandLine"])
        ) | (
            sudo_origin.set_results_name(fieldnames["Origin"])
            + sudo_session.set_results_name(fieldnames["Session"])
            + sudo_user_as2.set_results_name(fieldnames["Username"])
            + ZeroOrMore(sudo_user_uid.set_results_name(fieldnames["UID"]))
        )

        # Auth.log user/group add/delete ...

        # Useradd 
        # Sample : 
        # new user: name=ubuntu, UID=1000, GID=1002, home=/home/ubuntu, shell=/bin/bash, from=none
        useradd_user_action   = Combine(Literal("new user") + Suppress(":"))
        useradd_user_username = GrammarUserEquals
        useradd_user_uid      = Combine(Suppress(Literal("UID=")) + ints)
        useradd_user_gid      = GrammarGID
        useradd_user_home     = Combine(Suppress(Literal("home=")) + Word(alphanums + "/" + "-" + "_" + "."))
        useradd_user_shell    = Combine(Suppress(Literal("shell=")) + Word(alphanums + "/" + "-" + "_" + "."))
        useradd_user_from     = Combine(Suppress(Literal("from=")) + Word(printables) + Regex(".*"))
        
        # new group: name=ubuntu, GID=1002
        useradd_group_action = Combine(Literal("new group") + Suppress(":"))
        useradd_group_name   = GrammarUserEquals
        useradd_group_gid    = GrammarGID

        # add 'ubuntu' to group 'adm'
        useradd_group_list_action = Literal("add")
        useradd_group_list_user   = Combine(Suppress("'") + Word(alphas + nums + "_" + "-" + ".") + Suppress("'"))
        useradd_group_list_type   = Combine(Literal("shadow"))
        useradd_group_list_group  = Combine(Suppress(Literal("group")) + Suppress(" ") + Suppress("'") + Word(alphas + nums + "_" + "-" + ".") + Suppress("'"))

        # Pattern
        self.useradd = (
            useradd_user_action.set_results_name(fieldnames["Action"])
            + useradd_user_username.set_results_name(fieldnames["Username"])
            + Suppress(",")
            + useradd_user_uid.set_results_name(fieldnames["UID"])
            + Suppress(",")
            + useradd_user_gid.set_results_name(fieldnames["GID"])
            + Suppress(",")
            + useradd_user_home.set_results_name(fieldnames["Home"])
            + Suppress(",")
            + useradd_user_shell.set_results_name(fieldnames["Shell"])
            + Suppress(",")
            + useradd_user_from.set_results_name(fieldnames["From"])
        ) | (
            useradd_group_action.set_results_name(fieldnames["Action"])
            + useradd_group_name.set_results_name(fieldnames["Group"])
            + Suppress(",")
            + useradd_group_gid.set_results_name(fieldnames["GID"])
        ) | (
            useradd_group_list_action.set_results_name(fieldnames["Action"])
            + useradd_group_list_user.set_results_name(fieldnames["Username"])
            + Suppress("to")
            + Optional(useradd_group_list_type.set_results_name(fieldnames["Type"]))
            + useradd_group_list_group.set_results_name(fieldnames["Group"])
        )

        # Groupadd
        # Sample : 
        # new group: name=lxd, GID=1000
        groupadd_group_action = Combine(Literal("new group") + Suppress(":"))
        groupadd_group_name   = GrammarUserEquals
        groupadd_group_gid    = GrammarGID

        # group added to /etc/group: name=lxd, GID=1000
        groupadd_group_list_action = Combine(Suppress(Literal("group")) + Suppress(" ") + Literal("added") + Suppress(" ") + Suppress(Literal("to")))
        groupadd_group_list_list   = Combine(Literal("/etc/") + Word(alphas) + Suppress(":"))
        groupadd_group_List_name   = GrammarUserEquals
        groupadd_group_list_gid    = GrammarGID

        # Pattern
        self.groupadd = (
            groupadd_group_action.set_results_name(fieldnames["Action"])
            + groupadd_group_name.set_results_name(fieldnames["Group"])
            + Suppress(",")
            + groupadd_group_gid.set_results_name(fieldnames["GID"])
        ) | (
            groupadd_group_list_action.set_results_name(fieldnames["Action"])
            + groupadd_group_list_list.set_results_name(fieldnames["List"])
            + groupadd_group_List_name.set_results_name(fieldnames["Group"])
            + Optional(Suppress(",") + groupadd_group_list_gid.set_results_name(fieldnames["GID"]))
        )

        # Passwd
        # Sample : 
        # password for 'ubuntu' changed by 'root'
        passwd_user_action  = Combine(Literal("password") + Suppress(" ") + Suppress("for"))
        passwd_user_user    = Combine(GrammarUserOrGroupWithQuote)
        passwd_user_action2 = Combine(Literal("changed") + Suppress(" ") + Suppress("by"))
        passwd_user_by      = Combine(GrammarUserOrGroupWithQuote)

        # Pattern
        self.passwd = (
            Suppress(passwd_user_action)
            + passwd_user_user.set_results_name(fieldnames["Username"])
            + passwd_user_action2.set_results_name(fieldnames["Action"])
            + passwd_user_by.set_results_name(fieldnames["By"])
        )

        # Userdel
        # Sample : 
        # delete user 'ubuntu'
        userdel_user_action = Combine(Literal("delete"))
        userdel_user_type   = Combine(Literal("user"))
        userdel_user_user   = Combine(GrammarUserOrGroupWithQuote)

        # delete 'ubuntu' from group 'adm'
        userdel_user_del_action = Combine(Literal("delete"))
        userdel_user_del_user   = Combine(Suppress("'") + Word(alphas + nums + "_" + "-" + ".") + Suppress("'"))
        userdel_user_del_type   = Combine(Literal("shadow"))
        userdel_user_del_group  = Combine(Suppress(Literal("group")) + Suppress(" ") + GrammarUserOrGroupWithQuote)

        # removed group 'ubuntu' owned by 'ubuntu'
        userdel_group_del_action = Combine(Literal("removed"))
        userdel_group_del_type   = Combine(Literal("shadow"))
        userdel_group_del_group  = Combine(GrammarUserOrGroupWithQuote)
        userdel_group_del_user   = Combine(Suppress(Literal("owned by")) + Suppress(" ") + GrammarUserOrGroupWithQuote)

        # Pattern
        self.userdel = (
            userdel_user_action.set_results_name(fieldnames["Action"])
            + userdel_user_type.set_results_name(fieldnames["Type"])
            + userdel_user_user.set_results_name(fieldnames["Username"])
        ) | (
            userdel_user_del_action.set_results_name(fieldnames["Action"])
            + userdel_user_del_user.set_results_name(fieldnames["Username"])
            + Suppress("from")
            + Optional(userdel_user_del_type.set_results_name(fieldnames["Type"]))
            + userdel_user_del_group.set_results_name(fieldnames["Group"])
        ) | (
            userdel_group_del_action.set_results_name(fieldnames["Action"])
            + Optional(userdel_group_del_type.set_results_name(fieldnames["Type"]))
            + Suppress("group")
            + userdel_group_del_group.set_results_name(fieldnames["Group"])
            + userdel_group_del_user.set_results_name(fieldnames["Owner"])
        )

    def parseGrammar(self, grammar, msg):
        # For debug puproses :)
        #for toks in grammar.searchString(msg):
        #    print(toks)
        return grammar.parseString(msg).as_dict()

    def parseLine(self, line):
        """
        Parses a single line from a log file.

        Args:
            line (str): A single line from a log file.

        Returns:
            dict: A dictionary containing the parsed fields from the log line.

        """
        result = self.syslogPattern.parseString(line).as_dict()
        messagePattern = None
        if "appname" in result and "message" in result :
             # /var/log/syslog - Sudo 
            if result["appname"] == "sudo":
                messagePattern = self.sudo
            # /var/log/auth.log - Systemd login
            elif result["appname"] == "systemd" and "session opened for" in result["message"]:
                messagePattern = self.sudo
            # /var/log/auth.log - useradd
            elif result["appname"] == "useradd":
                messagePattern = self.useradd
            # /var/log/auth.log - groupadd
            elif result["appname"] == "groupadd":
                messagePattern = self.groupadd
            # /var/log/auth.log - passwd
            elif result["appname"] == "passwd":
                messagePattern = self.passwd
            elif result["appname"] == "userdel":
                messagePattern = self.userdel

            try:
                if messagePattern is not None:
                    result.update(self.parseGrammar(messagePattern, result["message"]))
            except  Exception as e:
                print(f'Message Field NOT PARSED : {result["message"]}')
                print(e)

        return result

    # Load YAML configuration
    def load_config(self, yaml_file):
        """Load YAML configuration.

        Args:
            yaml_file (str): Path to the YAML configuration file.

        Returns:
            dict: A dictionary containing fieldnames from the YAML configuration file.

        """
        with open(yaml_file, 'r') as file:
            config = yaml.safe_load(file)
        fieldnames = {}
        for item in config['fieldnames']:
            for key, value in item.items():
                fieldnames[key] = value
        return fieldnames


# Helper : count lines in log files
# From : https://stackoverflow.com/questions/845058/how-to-get-the-line-count-of-a-large-file-cheaply-in-python
def _make_gen(reader):
    b = reader(1024 * 1024)
    while b:
        yield b
        b = reader(1024*1024)

def rawgencount(filename):
    f = open(filename, 'rb')
    f_gen = _make_gen(f.raw.read)
    return sum(buf.count(b'\n') for buf in f_gen)

def main():
# Some code has been shamelessly borrowed from : 
# https://gist.github.com/leandrosilva/3651640
# https://stackoverflow.com/questions/41137742/syslog-parsing-using-pyparsing
    
    print("""                
 __    __    _____ 
|  |  |  |  |  _  |
|  |__|  |__|   __|
|_____|_____|__|   

-= Linux Logs Parser =-
          
    """)

    argsParser = argparse.ArgumentParser()
    argsParser.add_argument("-l", "--logs", help="Path to the log file", required=True)
    argsParser.add_argument("-o", "--output", help="Output file", default="parsed.jsonl")
    argsParser.add_argument("-c", "--config", help="Configuration file", default="config.yml")
    argsParser.add_argument("-v", "--verbose", help="Verbose mode")
    args = argsParser.parse_args()

    syslogPath = args.logs
    outputPath = args.output

    parser = LogParser()

    lineCount = rawgencount(syslogPath)

    with open(syslogPath) as syslogFile:
        with open(outputPath, "w") as outputFile:
            for line in rich.progress.track(syslogFile, description="Processing...", total=lineCount):
                try:
                    parsed = parser.parseLine(line)
                    outputFile.write(json.dumps(parsed, ensure_ascii=False) + "\n")
                except Exception as e:
                    if args.verbose:
                        print(f'PARSE ERROR : {line.strip()}')
                        print(e)
        print(f"[+] Saved output to {outputPath}")
if __name__ == "__main__":
    main()
