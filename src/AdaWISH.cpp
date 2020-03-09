#include <vector>
#include <iostream>
#include <cmath>
#include <cstring>
#include <algorithm>
#include <fstream>
#include <thread>
#include <ctime>
#include <cstdlib>
using namespace std;


/*
    A toy simulation code for the ideal case, 
    where query can return the exacty value.

    *Enumerate* all the configurations.

*/

struct funcVars {
    const int nb;
    const int var1;
    const int var2;

    funcVars():
        nb(0), var1(-1), var2(-1) {}

    funcVars(int n, int v1, int v2):
        nb(n), var1(v1), var2(v2) {}
};

bool DEBUG = false;
bool PARALLEL = false;
string output = "/tmp/weights.txt";
char instanceName[1024];

char pbname[1024];
int nbvar;
int nbfunc;
vector<funcVars> funcvar;
vector<vector<double> > functable;
vector<double> weights;

double mybeta = 8;
int queryCnt = 0;

void parseArgs(int argc, char **argv)
{
    if (argc <= 1) {
        cerr << "ERROR: instance name must be specified" << endl;
        exit(1);
    }

    for (int argIndex=1; argIndex < argc; ++argIndex) {
        if (!strcmp(argv[argIndex], "-beta")) {
            // must be the instance name
            ++argIndex;
            mybeta = atof(argv[argIndex]);
        }
        else if (!strcmp(argv[argIndex], "-debug")) {
            DEBUG = true;
        }
        else if (!strcmp(argv[argIndex], "-parallel")) {
            PARALLEL = true;
        }
        else if (argv[argIndex][0] != '-') {
            // must be the instance name
            strcpy(instanceName, argv[argIndex]);
        }
        else {
            cerr << "ERROR: Unexpected option: " << argv[argIndex] << endl
                << "       See usage (iloglue_uai -h)" << endl;
            exit(1);
        }
    }
}

void parseFile()
{
    ifstream file(instanceName);
    if (!file) {
      cerr << "Could not open file " << instanceName << endl;
      exit(1);
    }

    cerr << "Parsing file"<< endl;
    file >> pbname;
    file >> nbvar;

    int itmp;
    for (int i = 0; i < nbvar; ++i) {
        file >> itmp;
        if (itmp != 2) {
            cerr << "Currently only support binary variables" << endl;
            exit(1);
        }
    }

    cerr << "Parsing function table"<< endl;
    file >> nbfunc;
    functable.resize(nbfunc);
    for (int nb, var1, var2, i = 0; i < nbfunc; ++i) {
        vector<double> funcinstance;
        nb = 0, var1 = -1, var2 = -1;
        file >> nb;
        file >> var1;
        if (nb == 2) file >> var2;
        funcvar.push_back(funcVars(nb, var1, var2));
    }

    int parity;
    double dtmp;
    for (int c = 0; c < nbfunc; ++c) {
        vector<double> funcinstance;
        file >> parity;
        if (parity != 2 && parity != 4)
            cerr << "Unsupported function" << endl;
        for (int p = 0; p < parity; ++p) {
            file >> dtmp;
            funcinstance.push_back(log10(dtmp));
        }
        functable[c] = funcinstance;
    }
}

double funcIndex(const int funcNo, vector<bool> configuration)
{
    funcVars vars = funcvar[funcNo];
    if (vars.var2 == -1)
        return functable[funcNo][configuration[vars.var1]? 1:0];
    else {
        int row = configuration[vars.var1]? 1:0;
        int col = configuration[vars.var2]? 1:0;
        return functable[funcNo][(row << 1) + col];
    }
}

vector<bool> int2boolvec(int maxbit, int a)
{
    vector<bool> vec;
    vec.resize(maxbit);

    int tmp = a;
    vec[0] = a & 1;
    for (int i = 1; i < maxbit; ++i) {
        a >>= 1;
        vec[i] = (a & 1);
    }
    return vec;
}

bool cmp(const double &a, const double &b) {
    return a > b;
}

void getConfigurationWeight(int c)
{
    double w = 0;
    vector<bool> vec = int2boolvec(nbvar, c);
    for (int j = 0; j < nbfunc; ++j)
        w += funcIndex(j, vec);
    weights[c] = w;
}

void preCalculate()
{
    long long res = 1 << nbvar;
    weights.resize(res);
    // if (PARALLEL) {
        
    // }
    // else {
    for (int i = 0; i < res; ++i) {
        if (i % 10000 == 0)
            cout << i << endl;
        double w = 0;
        vector<bool> vec = int2boolvec(nbvar, i);
        for (int j = 0; j < nbfunc; ++j)
            w += funcIndex(j, vec);
        weights[i] = w;
    }
    // }
    sort(weights.begin(), weights.end(), cmp);
}

const double query(int i) {
    ++queryCnt;
    return weights[(1 << i) - 1];
}

void adaSearch(double wb[], double interval[], int l, int r)
{
    double rate = log10(mybeta);
    if (r == l + 1 || wb[l] < rate + wb[r]) {
        // stop condition
        double value = (wb[l] + wb[r]) / 2;
        for (int i = l + 1; i < r; ++i) {
            wb[i] = value;
            interval[i - 1] = value;
        }
    }
    else {
        int mid = (r + l) >> 1;
        wb[mid] = query(mid);
        adaSearch(wb, interval, l, mid);
        adaSearch(wb, interval, mid, r);
    }
}

void adaWish()
{
    int n = nbvar;
    double wb[n + 1]{0}, interval[n]{0};
    wb[0] = query(0);
    wb[n] = query(n);

    adaSearch(wb, interval, 0, n);

    double curmax = wb[0], W(pow(10, wb[n] - curmax));
    for (int i = 0; i < n; ++i) {
        W += pow(10, wb[i] - curmax);
        W += ((1 << i) - 1) * pow(10, interval[i] - curmax);
    }
    // cout << "Partition function = " << W << endl;
    W = log10(W) + curmax;
    
    cout << "Query time = " << queryCnt << endl;
    cout << "Partition function = " << W << endl;
    
    if (DEBUG) {
        cout << "wb = [ ";
        for (int i = 0; i <= n; ++i) {
            cout << wb[i] << " ";
        }
        cout << "]" << endl;
        cout << "interval = [ ";
        for (int i = 0; i < n; ++i) {
            cout << interval[i] << " ";
        }
        cout << "]" << endl;
        double accurate(0);
        for (vector<double>::iterator itr = weights.begin(); itr != weights.end(); ++itr) {
            accurate += pow(10, *itr);
        }
        accurate = log10(accurate);
        cout << "Approximate / Accurate = " << W / accurate << endl;
    }
}


int main(int argc, char **argv)
{
    parseArgs(argc, argv);
    parseFile();
    preCalculate();

    adaWish();
    fstream f(output, ios::out);
    vector<double>::iterator itr = weights.begin();
    while (itr != weights.end()) {
        f << *itr << endl;
        ++itr;
    }
    f.close();

    return 0;


    
}