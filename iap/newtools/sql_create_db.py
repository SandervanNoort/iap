import logging
import pexpect


def sql_create_db(database, root_pass, force=False):
    """Create a database, and force if it already exists"""

    logging.info("Creating database %s", database)
    child = pexpect.spawn(
        "mysql -u root -p -e \"SHOW DATABASES LIKE '{0}'\"".format(database))
    child.expect(".*password.*")
    child.sendline(root_pass)
    output = child.read().strip()
    child.close()
    if child.exitstatus:
        logging.error("Cannot show databases: %s", output)
        return

    if output:
        # there are database with the same name
        if force:
            logging.info("Dropping old database")
            output, exit_status = pexpect.run(
                "mysqladmin -u root -p --force drop {0}".format(database),
                events={".*password.*": root_pass + "\n"},
                withexitstatus=True)
            if exit_status > 0:
                logging.error("Cannot delete existing database %s", database)
                return False
        else:
            logging.error("Database %s already exists", database)
            return False

    output, exit_status = pexpect.run(
        "mysqladmin -u root -p create {0}".format(database),
        events={".*password.*": root_pass + "\n"},
        withexitstatus=True)
    if exit_status > 0:
        logging.error("Cannot create database %s", database)
        return False

    return True
