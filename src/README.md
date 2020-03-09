### Repo file usage:
* 3SATGenerator.py: 
    A python script for generation of 3SAT instances, on which our method will be tested. Note that we use the implementation of random K-SAT instances generator by [RalfRothenberger](https://github.com/RalfRothenberger/Power-Law-Random-SAT-Generator).

    > Example: 
    > 
    > python 3SATGenerator.py -n [nums of each set of vars/constrains, e.g. 100]

* AdaWISH.cpp:
    The C++ implementation of case 1, where each query returns the exact value of the b(i). We use a brute-force algorithm in sorting the weights of all the possible configurations for the required monocity constraint. 

    [July 29, 2019] TODO: Accelerate by supporting parallel computation.

    > Example:
    > 
    > cd /path/to/src
    >
    > g++ -o AdaWISH AdaWISH.cpp
    > 
    > chmod x AdaWISH
    > 
    > ./AdaWISH /path/to/datafile(UAI) -beta [int, will guarantee 2beta-approximation] -debug (if listed, will print details info in shell) -parallel(!To be supported)

* DataGenerator.py:
    This python script invokes generation of pairwise Ising model with binary variables. 

    [July 29, 2019] Additionally, we add some structure by introducing a closed chain of strong repulsive interactioins as describbed in WISH.

    > Example:
    > 
    > cd /path/to/src
    > 
    > python DataGenerator.py

* LaunchIloglue.sh:
    Adapted from Stefano's PBS job launching script.
* XorAdaWish.py;
    Invokes cplex batch jobs, executed on the front-end.

    [July 29, 2019] To be modified, we may need a better implementation with TCP/SOCKET protocals in the future.
* transformer.py:
    Converting SAT instances from *cnf* format into *uai*.

    > Example:
    > 
    > cd /path/to/src
    > 
    > python transformer.py srcdata.cnf [-o samplename.uai]
