#!/usr/bin/env python

import pstats
p = pstats.Stats('profile.txt')
p1 = p.strip_dirs().sort_stats(-1).print_stats()
print("")
print("===================")
print("")
p2 = p.sort_stats('cumulative').print_stats(15)
