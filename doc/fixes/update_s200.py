import iap

times, errors = iap.utils.get_times(["ALL"])
for period in times["periods"]:
    if not iap.utils.period_available(period):
        continue
    iap.utils.query("""alter table survey_{period}
        change s200 
            s200 int not null default 0""".format(period=period))
