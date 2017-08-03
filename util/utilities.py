import datetime


def calc_sma(nums, length):
    averages = []
    for i, n in enumerate(nums):
        if i >= length-1:
            avg = sum(nums[i-length+1:i+1]) / length
            averages.append(avg)

    return averages


def first_per_month(datetimes):
    found_months = []
    output = []

    for dt in datetimes:
        key = (dt.month, dt.year)
        if key not in found_months:
            found_months.append(key)
            output.append(dt)

    return output


def first_per_year(datetimes):
    found_years = []
    output = []

    for dt in datetimes:
        key = (dt.year)
        if key not in found_years:
            found_years.append(key)
            output.append(dt)

    return output
