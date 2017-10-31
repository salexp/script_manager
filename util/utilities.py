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


def from_bytes(byte_list):
    lsb_bytes = byte_list[::-1]
    out_int = 0
    for i, byte in enumerate(lsb_bytes):
        out_int += byte << (8 * i)

    return out_int


def make_bytes(value, bytes=1):
    outbytes = []
    while value:
        # rem = bin(value % 256)[2:].zfill(8)
        rem = value % 256
        outbytes.append(rem)
        value = value >> 8

    if len(outbytes) < bytes:
        outbytes = outbytes + [0] * (bytes - len(outbytes))

    outbytes = outbytes[::-1]
    return outbytes
