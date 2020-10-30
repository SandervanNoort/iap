import rpy2.robjects

stata_fname = "/home/vnoort/dev/dengue/data/butantan/bo_dengue2013.dta"
csv_fname = "/home/vnoort/2013.csv"
run_r = rpy2.robjects.r
run_r.library("foreign")
# run_r.library("haven")
# run_r("d = read.dta('{0}')".format(stata_fname))
run_r("write.csv(read.dta('{stata_fname}'), file='{csv_fname}', row.names=FALSE)".format(
    stata_fname=stata_fname, csv_fname=csv_fname))
