rowtype = option("python", "sql")
dbtype = option("epi", "zip", "sql", "dump")
interval = integer(default=7)
# country = string
delimiter = string(default=",")
extra_import = string_list(default=list())
multi_sep = string(default=",")
