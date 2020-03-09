#include <fstream>
#include <iostream>
#include <cstdlib>
#include <ostream>
#include <dai/alldai.h>
#include <dai/io.h>

using namespace std;
using namespace dai;

bool verbose = true;
bool surgery = true;
size_t ia_verbose = 0;
size_t seed = 7;
string task="PR";
string method;
struct PRbest {
    Real value;
    Real maxdiff;
    bool ready;
    PRbest() : value(0.0), maxdiff(INFINITY), ready(false) {}
};


int main(int argc, char *argv[])
{
    try {
        method = argv[3];
    } catch (exception e) {
        cerr << "Method has to be determined" << endl;
        return -1;
    }
    rnd_seed(seed);
    // get time and memory limits
    char *buf = getenv("UAI_TIME");
    double UAI_time = (buf != NULL)? fromString<double>(buf):
                                    INFINITY;
    buf = getenv("UAI_MEMORY");
    double UAI_memory = (buf != NULL)?
                    fromString<double>(buf) * 1024 * 1024 * 1024:
                    INFINITY;

    // get output filename
    vector<string> pathComponents = tokenizeString( string(argv[1]), true, "/" );
    string outfile = pathComponents.back() + "_" + method +"_" + task;

    // open output file
    ofstream os;
    os.open( outfile.c_str() );
    if( !os.is_open() )
        DAI_THROWE(CANNOT_WRITE_FILE,"Cannot write to file " + outfile);

    // read uai file
    vector<Var> vars;
    vector<Factor> facs0;
    vector<Permute> permutations;

    if (verbose)
        cout << "reading uai file" << endl;
    ReadUaiAieFactorGraphFile(argv[1], verbose, vars, facs0, permutations);

    // TODO: add args parser and determine whether is grid
    // check if it could be a grid
    bool couldBeGrid = true;
    FactorGraph fg0( facs0.begin(), facs0.end(), vars.begin(), vars.end(), facs0.size(), vars.size() );
    for( size_t i = 0; i < fg0.nrVars(); i++ ){
        if( fg0.delta(i).size() > 4 ) {
            couldBeGrid = false;
            break;
        }
    }

    if(couldBeGrid) {
        for( size_t I = 0; I < fg0.nrFactors(); I++ ) {
            if( fg0.factor(I).vars().size() > 2 ) {
                couldBeGrid = false;
                break;
            }
        }
    }

    // read evidence file (in our case, empty evidence file)
    if (verbose)
        cout << "reading evid file" << endl;
    vector<map<size_t,size_t> > evid = ReadUaiAieEvidenceFile(argv[2], verbose);
    if (verbose)
        cout << "evid size" << evid.size() << endl;
    // write output header
    os << task << endl;
    vector<FactorGraph> fgs;
    fgs.reserve(evid.size());
    for(size_t ev = 0; ev < evid.size(); ev++) {
        // copy vector of factors
        vector<Factor> facs(facs0);
        // change factor graph to reflect observed evidence
        if(surgery) {
            // replace factors with clamped variables with slices
            for( size_t I = 0; I < facs.size(); I++ ) {
                for( map<size_t,size_t>::const_iterator e = evid[ev].begin(); e != evid[ev].end(); e++ ) {
                    if( facs[I].vars() >> vars[e->first] )
                        facs[I] = facs[I].slice(vars[e->first], e->second);
                }
            }
            // remove empty factors
            Real logZcorr = 0.0;
            for( vector<Factor>::iterator I = facs.begin(); I != facs.end(); ) {
                if( I->vars().size() == 0 ) {
                    logZcorr += std::log((Real)(*I)[0]);
                    I = facs.erase( I );
                }
                else I++;
            }

            // multiply with logZcorr constant
            if( facs.size() == 0 )
                facs.push_back(Factor(VarSet(), std::exp(logZcorr)));
            else
                facs.front() *= std::exp(logZcorr);
        }
        // add delta factors corresponding to observed variable values
        for(map<size_t,size_t>::const_iterator e = evid[ev].begin(); e != evid[ev].end(); e++)
            facs.push_back(createFactorDelta( vars[e->first], e->second));

        // construct clamped factor graph
        fgs.push_back(FactorGraph(facs.begin(), facs.end(), vars.begin(), vars.end(), facs.size(), vars.size()));
    }

    InfAlg *ia = NULL;
    double tic = toc();
    bool failed = false;
    bool first = true;
    int subsolver = 0;

    vector<PRbest> bestPR(evid.size());
    for(size_t ev = 0; ev < evid.size(); ) {
        if (verbose)
            cout << "solving evid num " << ev << endl;
        bool improved = false;
        try {
            if (verbose)
                cout << "begin solving" << endl;
            string maxtimestr=",maxtime=3600";

            if (method == "bp")
                ia = newInfAlgFromString( "BP[inference=SUMPROD,updates=SEQRND,logdomain=" + toString(subsolver) + ",tol=1e-9,maxiter=10000" + maxtimestr + ",damping=0.0,verbose=" + toString(ia_verbose) + "]", fgs[ev] );
            else if (method == "trwbp")
                ia = newInfAlgFromString( "TRWBP[inference=SUMPROD,updates=SEQRND,logdomain=" + toString(subsolver) + ",nrtrees=100,tol=1e-9,maxiter=10000" + maxtimestr + ",damping=0.0,verbose=" + toString(ia_verbose) + "]", fgs[ev] );
            else if (method == "mf")
                ia = newInfAlgFromString( "MF[inference=SUMPROD,updates=HARDSPIN,logdomain=" + toString(subsolver) + ",tol=1e-9,maxiter=1000000" + maxtimestr + ",damping=0.0,verbose=" + toString(ia_verbose) + "]", fgs[ev] );
            else if (method == "jt")
                ia = newInfAlgFromString( "JTREE[inference=SUMPROD,updates=SHSH,logdomain=" + toString(subsolver) + ",tol=1e-9,maxiter=1000000" + maxtimestr + ",damping=0.0,verbose=" + toString(ia_verbose) + "]", fgs[ev] );
            else if (method == "hak")
                ia = newInfAlgFromString( "HAK[doubleloop=1,clusters=DELTA,logdomain=" + toString(subsolver) + ",tol=1e-9,maxiter=1000000" + maxtimestr + ",damping=0.0,verbose=" + toString(ia_verbose) + "]", fgs[ev] );
            else {
                cerr << "Unsupported method(algorithm) type" << endl;
                return -1;
            }
            

            ia->init();
            ia->run();
        } catch (Exception &e) {
            failed = true;
            cerr << "Inference algorithm failed" << endl;
            cerr << "Throw Exception: " << e.what() << endl;
        }
        
        if (!failed) {
            PRbest cur;
            // calculate PR value
            cur.value = ia->logZ() / dai::log((Real)10.0);
            // get maxdiff
            try {
                cur.maxdiff = ia->maxDiff();
            } catch( Exception &e ) {
                cur.maxdiff = 1e-9;
            }

            // only update if this run has converged
            if( ((cur.maxdiff <= 1e-9) || (cur.maxdiff <= bestPR[ev].maxdiff)) && !dai::isnan(cur.value) ) {
                bestPR[ev] = cur;
                improved = true;
            }
        }

        if (!failed)
            delete ia;
        if (improved) {
            if (first)
                first = false;
            else
                os << "-BEGIN-" << endl;
            os << evid.size() << endl;
            for(size_t ev = 0; ev < evid.size(); ev++)
                os << bestPR[ev].value << endl;
            os.flush();
        }
        else
            subsolver++;
        if (improved || subsolver > 2)
            ev++;
    }
    os.close();
    return 0;
}
    
