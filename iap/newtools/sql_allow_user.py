import logging
import pexpect


def sql_allow_user(user, database, root_pass):
    """Create a user, and force if it already exists"""

    logging.info("Add access rights to %s on %s", user, database)

    output, exit_status = pexpect.run(
        "mysql -u root -p -e \"GRANT ALL ON {db}.* TO {user}\"".format(
            user=user, db=database),
        events={".*password.*": root_pass + "\n"},
        withexitstatus=True)
    if exit_status:
        logging.error("Cannot grant privileges: %s", output)
        return False

    output, exit_status = pexpect.run(
        "mysql -u root -p -e \"GRANT FILE ON *.* TO {0}\"".format(user),
        events={".*password.*": root_pass + "\n"},
        withexitstatus=True)
    if exit_status:
        logging.error("Cannot grant file: %s", output)
        return False

    output, exit_status = pexpect.run(
        "mysqladmin -u root -p flush-privileges",
        events={".*password.*": root_pass + "\n"},
        withexitstatus=True)
    if exit_status:
        logging.error("Cannot flush privileges: %s", output)
        return False

    return True
