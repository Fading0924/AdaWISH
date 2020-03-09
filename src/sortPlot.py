import os
import sys
import re
import matplotlib
import math
import time
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
wf = open('/tmp/weights', 'r')
sf = open('/tmp/sample', 'r')

for line in sf.readlines():
    sampley = float(re.split(r'\n', line)[0])

yw = []
for line in wf.readlines():
    yw.append(float(re.split(r'\n', line)[0]))

xw = [i for i in range(len(yw))]

postfix = int(time.time())
plt.plot(xw, yw, '-')
plt.plot(xw, sampley*np.ones(len(yw)), '--')
plt.savefig("/tmp/weight_{}.pdf".format(postfix))

plt.figure()
y = []
for i in range(int(math.log2(len(yw)))):
    y.append(yw[2**i])
plt.plot(y)
plt.plot(sampley*np.ones(len(y)), '--')
plt.savefig("/tmp/logweight_{}.pdf".format(postfix))

plt.figure()
y = np.array(y)
w_exact = np.log10(np.power(10, y - y[0]).sum()) + y[0]
y[y < y[int(math.log2(len(yw))/4)]] = sampley
w_sample = np.log10(np.power(10, y - y[0]).sum()) + y[0]
print(w_exact/w_sample)
plt.savefig("/tmp/sample_{}.pdf".format(postfix))