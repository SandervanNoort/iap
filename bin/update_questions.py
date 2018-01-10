import iap
import sys

old_news = [("intake", "q1100", "q1500"),
        ("intake", "q600", "q500"),
        ("survey", "s100", "s1000")]
iap.utils.period_valid(None)


for table, qa_old, qa_new in old_news: 
    qold, sold, aold = iap.utils.split_qa(qa_old, ("__", "_"))
    qnew, snew, anew = iap.utils.split_qa(qa_new, ("__", "_"))

    srcs = []
#     for period in iap.PERIODS["valid"]:
    for period in ["pt05"]:
        try:
            convert = iap.Convert(period)
        except iap.IAPError:
            continue
        if convert.src in srcs:
            continue
        srcs.append(convert.src)


        print convert.src
        for column in iap.TABLE[table].keys():
            if column == qold:
                print "rename section {0} to {1}".format(column, qnew)


        for qa_cur in convert.dbini[table].keys():
            qcur, scur, acur = iap.utils.split_qa(qa_cur, ("__", "_"))

            if qa_cur == qa_old:
                print "full rename {0} to {1}".format(qa_cur, qa_new)
            elif qcur == qold:
                print "col rename {0} to {1}{2}{3}".format(qa_cur, 
                        qnew, scur, acur)

        for lang in iap.TRANSLATE.keys():
            if table not in iap.TRANSLATE[lang]:
                continue
            if qold in iap.TRANSLATE[lang][table]:
                print "rename translate {0}:{1} to {2}".format(table,
                        qold, qnew)
            else:
                print "{0} not found in translate {1}".format(qold, table)

        if qold in iap.TABLE[table]:
            print "rename {0}:{1} to {2}".format(table,
                    qold, qnew)
        else:
            print "{0} not found in {1}".format(qold, table)

#         with codecs.open("/tmp/{0}.ini".format(convert.src),
#                          "w", encoding="utf8") as fobj:
#             convert.dbini.ignore_comments = False
#             convert.dbini.key_align = False
#             convert.dbini.write(fobj)
        print
