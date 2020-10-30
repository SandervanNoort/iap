import logging
import pexpect


def sql_check_root(root_pass):
    "Check if the mysql root pass is correct"""

    _output, exit_status = pexpect.run(
        "mysqladmin -u root -p version",
        events={".*password.*": root_pass + "\n"},
        withexitstatus=True)
    print(root_pass)
    if exit_status == 0:
        return True
    else:
        logging.error("Wrong root password for mysql")
        return False
