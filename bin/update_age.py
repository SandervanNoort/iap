import iap
import sys

times, errors = iap.utils.get_times(["INET"])
for period in times["periods"]:
    update = iap.Update(period)
    update.intake_update(True)
