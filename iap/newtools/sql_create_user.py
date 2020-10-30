import logging
import pexpect
from .sql_allow_user import sql_allow_user


def sql_create_user(user, passwd, root_pass, database=None, force=False):
    """Create a user, and force if it already exists"""
    # (too many returns) pylint: disable=R0911

    logging.info("Adding user %s", user)

    child = pexpect.spawn(
        "mysql -u root -p" +
        " -e \"SELECT user FROM mysql.user WHERE User='{0}'\"".format(user))
    child.expect(".*password.*")
    child.sendline(root_pass)
    output = child.read().strip()
    child.close()
    if child.exitstatus:
        logging.error("Cannot find mysql users: %s", output)
        return False

    if output:
        if force:
            logging.info("Dropping old user")
            output, exit_status = pexpect.run(
                "mysql -u root -p -e \"DROP USER {0}\"".format(user),
                events={".*password.*": root_pass + "\n"},
                withexitstatus=True)
            if exit_status:
                logging.error("Cannot drop user: %s", output)
                return False

            output, exit_status = pexpect.run(
                "mysqladmin -u root -p flush-privileges",
                events={".*password.*": root_pass + "\n"},
                withexitstatus=True)
            if exit_status:
                logging.error("Cannot flush privileges: %s", output)
                return False
        else:
            logging.error("ERROR: User %s already exists", user)
            return False

    output, exit_status = pexpect.run(
        "mysql -u root -p" +
        " -e \"CREATE USER {user} identified by '{passwd}'\"".format(
            user=user, passwd=passwd),
        events={".*password.*": root_pass + "\n"},
        withexitstatus=True)
    if exit_status:
        logging.error("Cannot create user: %s", output)
        return False
    output, exit_status = pexpect.run(
        "mysqladmin -u root -p flush-privileges",
        events={".*password.*": root_pass + "\n"},
        withexitstatus=True)
    if exit_status:
        logging.error("Cannot flush privileges: %s", output)
        return False

    if database is not None:
        sql_allow_user(user, database, root_pass)

    return True
