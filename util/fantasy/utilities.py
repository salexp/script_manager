from bisect import bisect
from itertools import groupby
from math import exp
from operator import itemgetter


def add_ranks(lst, compare_index=None):
    rks = range(1, len(lst) + 1)
    for line in lst:
        ind = lst.index(line)
        if ind > 0:
            if compare_index is None:
                compare = [sum(lst[ind][1]) / lst[ind][2], sum(lst[ind - 1][1]) / lst[ind - 1][2]]
            else:
                compare = [lst[ind][compare_index], lst[ind - 1][compare_index]]
            if compare[0] == compare[1]:
                rks[ind-1] = 'T{}'.format(rks[ind-1].replace('T', ''))
                rks[ind] = rks[ind-1]
            else:
                rks[ind] = '{}'.format(rks[ind])
        else:
            rks[ind] = '{}'.format(rks[ind])

    for rk in rks:
        # if '1' in rk and '10' not in rk:
        #     new = rk + 'st'
        # elif '2' in rk[-1]:
        #     new = rk + 'nd'
        # elif '3' in rk[-1]:
        #     new = rk + 'rd'
        # elif rk[-1] == '1' and '11' not in rk:
        #     new = rk + 'st'
        # else:
        #     new = rk + 'th'
        new = add_suffix(rk)
        rks[rks.index(rk)] = new

    return [x + [rks[lst.index(x)]] for x in lst]


def add_suffix(num):
    num = str(num)
    if '1' in num and num not in ['10', '11', '12', '13', '14', '15', '16', '17', '18', '19']:
        new = num + 'st'
    elif '2' in num[-1] and num not in ['12']:
        new = num + 'nd'
    elif '3' in num[-1] and num not in ['13']:
        new = num + 'rd'
    elif num[-1] == '1' and '11' not in num:
        new = num + 'st'
    else:
        new = num + 'th'

    if len(new) == 3:
        new += "."

    return new


def average(lst, rnd=1):
    if len(lst) != 0:
        avg = round(sum([float(i) for i in lst]) / len(lst), rnd)
    else:
        avg = 0

    return avg


def consecutive_years(years):
    ranges = []
    yrs = [int(y) for y in years]
    for key, group in groupby(enumerate(yrs), lambda (index, item): index - item):
        group = map(itemgetter(1), group)
        ranges.append((group[0], group[-1]))

    str = ""
    for i, rng in enumerate(ranges):
        if rng[0] == rng[1]:
            str += "{}".format(rng[0])
        else:
            str += "{}-{}".format(rng[0], rng[1])
        if i < len(ranges)-1:
            str += ", "

    if str == "":
        str = "None"

    return str


def get_initials(name):
    fi = name.split(' ')[0][0]
    li = name.split(' ')[1][0]

    return fi + li


def get_team(yr, xr, sht):
    if 'D/ST' not in sht.cell_value(yr, xr):
        tmm = sht.cell_value(yr, xr).split(', ')[1].split(u'\xa0')[0].upper()
        tmm = tmm.replace('JAC', 'JAX')
        tmm = tmm.replace('WAS', 'WSH')
    else:
        tmm = sht.cell_value(yr, xr).split(' D/ST')[0]
        tmm = nfl_names[tmm]

    return tmm


def get_oppnt(yr, xr):
    val = sh.cell_value(yr, xr)

    oppnt = val.replace('@', '').replace('*', '').replace(' ', '').upper().replace('JAC', 'JAX').replace('WAS', 'WSH')

    return oppnt


def make_score(pa, pb):
    return "{}-{}".format(pa if pa > pb else pb, pa if pa < pb else pb)


def make_list_games(dict, consolation=False):
    lst = []
    for year in sorted(dict.keys()):
        weeks = dict[year].keys()
        weeks = sorted([int(w) for w in weeks])
        for wk in weeks:
            mtch = dict[year][str(wk)]
            if mtch.game.is_consolation and not consolation:
                pass
            elif mtch.game.played:
                lst.append(mtch)

    return lst


def normpdf(x, mu=1.0, sigma=1.0):
    sigma += 0.000001
    var = float(sigma) ** 2
    pi = 3.1415926
    denom = (2 * pi * var) ** .5
    num = exp(-(float(x) - float(mu)) ** 2 / (2 * var))

    return num / denom


def remove_dupes(lst):
    seen = set()
    seen_add = seen.add
    return [x for x in lst if not (x in seen or seen_add(x))]


def reverse_bisect(list, x):
    lst = sorted(list)
    bsct = bisect(lst, x)
    return len(list) - bsct


def stats(lst):
    mu = sum(lst) / len(lst)
    ssq = sum([i ** 2 for i in lst])
    sigma = (1.0 / len(lst)) * (len(lst) * ssq - sum(lst) ** 2) ** 0.5

    return mu, sigma


def sumpdf(x, mu=1.0, sigma=1.0):
    sigma += 0.000001
    sum = 0.0
    for i in range(int(x * 100)):
        j = i / 100.0
        var = float(sigma) ** 2
        pi = 3.1415926
        denom = (2 * pi * var) ** .5
        num = exp(-(float(j) - float(mu)) ** 2 / (2 * var))
        sum += (num / denom) * 0.01

    return 1 - sum


def get_wins(str):
    return int(str.split('-')[0])
