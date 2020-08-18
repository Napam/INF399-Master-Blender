import numpy as np 
from matplotlib import pyplot as plt 
from mpl_toolkits.mplot3d import Axes3D

# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')

def lol():
    R = 10
    N = 20
    thetas = np.linspace(0, 2*np.pi, N)[:-1]
    phis = np.linspace(0, 2*np.pi, N)[:-1]

    T, P = np.meshgrid(thetas, phis)
    thetas, phis = np.array([T.ravel(), P.ravel()])

    R_ = R*np.sin(phis)
    locs_ = np.array([R_*np.cos(thetas), R_*np.sin(thetas), R*np.cos(phis)]).T

    # print(locs_.T)
    # exit()
    
    ax.scatter(*locs_.T)
    plt.show()

def lol2():
    res = 1000
    xrange = np.linspace(0.1,20, res)
    amp = 2
    phis = 2*amp+np.sin(np.linspace(0,2*np.pi,res))*4
    plt.plot(xrange, phis)
    plt.plot(xrange, np.zeros_like(xrange))
    # plt.legend()
    plt.show()

lol2()